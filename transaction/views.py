import time
from billiard.exceptions import SoftTimeLimitExceeded
from bson import ObjectId
from datetime import datetime
from persiantools.jdatetime import JalaliDate
from utills.db_connection import db
from django.http import JsonResponse
from django.views import View
from .tasks import send_email_task, send_sms_task, send_push_notification_task, send_telegram_message_task

persian_months = {
    1: "فروردین",
    2: "اردیبهشت",
    3: "خرداد",
    4: "تیر",
    5: "مرداد",
    6: "شهریور",
    7: "مهر",
    8: "آبان",
    9: "آذر",
    10: "دی",
    11: "بهمن",
    12: "اسفند"
}


def get_jalali_week(date_obj):
    jalali_date = JalaliDate(date_obj)
    week_number = jalali_date.week_of_year()
    return week_number, jalali_date.year


def convert_to_jalali(date_obj, mode, week=None):
    if mode == 'daily':
        jalali_date = JalaliDate(date_obj)
        key = jalali_date.strftime("%Y/%m/%d")
    elif mode == 'weekly':
        week_number, jalali_year = get_jalali_week(date_obj)
        key = f"هفته {week_number} سال {jalali_year}"
    else:  # monthly
        jalali_date = JalaliDate(date_obj)
        persian_month = persian_months.get(jalali_date.month, str(jalali_date.month))
        key = f"ماه {persian_month} سال {jalali_date.year}"
    return key


class TransactionReportView(View):
    def get(self, request):
        report_type = request.GET.get('type')
        mode = request.GET.get('mode')
        merchant_id = request.GET.get('merchantId')

        if not report_type or report_type not in ['count', 'amount']:
            return JsonResponse({'error': 'Invalid type'}, status=400)

        if not mode or mode not in ['daily', 'weekly', 'monthly']:
            return JsonResponse({'error': 'Invalid mode'}, status=400)

        pipeline = []

        if merchant_id:
            try:
                merchant_id = ObjectId(merchant_id)
                pipeline.append({'$match': {'merchantId': merchant_id}})
            except Exception:
                return JsonResponse({'error': 'Invalid merchantId'}, status=400)

        pipeline.append({'$match': {'createdAt': {'$exists': True, '$ne': None}}})

        group_id = {
            'year': {'$year': '$createdAt'},
            'month': {'$month': '$createdAt'},
            'day': {'$dayOfMonth': '$createdAt'},
            'week': {'$week': '$createdAt'} if mode == 'weekly' else None
        }
        group_id = {k: v for k, v in group_id.items() if v is not None}

        aggregation = {'$sum': 1} if report_type == 'count' else {'$sum': '$amount'}

        pipeline.extend([
            {'$group': {'_id': group_id, 'value': aggregation}},
            {'$sort': {'_id': 1}}
        ])

        results = db.transaction.aggregate(pipeline)

        response_data = []
        aggregated_results = {}

        for result in results:
            try:
                year = result['_id']['year']
                month = result['_id'].get('month')
                day = result['_id'].get('day')
                week = result['_id'].get('week')
                if mode == 'daily' or mode == 'weekly':
                    date_obj = datetime(year, month, day)
                else:
                    date_obj = datetime(year, month or 1, 1)
                key = convert_to_jalali(date_obj, mode, week)

                if key in aggregated_results:
                    aggregated_results[key] += result['value']
                else:
                    aggregated_results[key] = result['value']
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        for key, value in aggregated_results.items():
            response_data.append({'key': key, 'value': value})

        return JsonResponse(response_data, safe=False)


class TransactionSummaryView(View):
    def get(self, request):
        report_type = request.GET.get('type')
        mode = request.GET.get('mode')
        merchant_id = request.GET.get('merchantId')

        if not report_type or report_type not in ['count', 'amount']:
            return JsonResponse({'error': 'Invalid type'}, status=400)

        if not mode or mode not in ['daily', 'weekly', 'monthly']:
            return JsonResponse({'error': 'Invalid mode'}, status=400)

        pipeline = []

        if merchant_id:
            try:
                merchant_id = ObjectId(merchant_id)
                pipeline.append({'$match': {'merchantId': merchant_id}})
            except Exception:
                return JsonResponse({'error': 'Invalid merchantId'}, status=400)

        pipeline.append({'$match': {'mode': mode, 'type': report_type}})

        pipeline.extend([
            {'$sort': {'key': 1}}
        ])

        results = db.transaction_summary.aggregate(pipeline)

        response_data = []
        for result in results:
            response_data.append({
                'key': result.get('key'),
                'value': result.get('value')
            })

        return JsonResponse(response_data, safe=False)


class SendNotificationView(View):
    TASK_MAP = {
        'email': send_email_task,
        'sms': send_sms_task,
        'push': send_push_notification_task,
        'telegram': send_telegram_message_task
    }

    def get(self, request):
        medium = request.GET.get('medium')
        recipient = request.GET.get('recipient')
        message = request.GET.get('message')

        if not medium or not recipient or not message:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        media = medium.split(',')
        recipient_list = recipient.split('|')
        errors = []

        tasks = []
        for med in media:
            if med not in self.TASK_MAP:
                errors.append(f'Unsupported medium: {med}')
                continue

            recipients = recipient_list[media.index(med)].split(';') if media.index(med) < len(recipient_list) else []
            for rec in recipients:
                tasks.append((med, self.TASK_MAP[med], rec))

        success_flag = False
        for med, task, rec in tasks:
            result = task.delay(rec, message)
            start_time = time.time()

            success = False
            error = None

            while not result.ready() and time.time() - start_time < 20:
                time.sleep(1)

            if result.ready():
                try:
                    success, error = result.get(timeout=1)
                except SoftTimeLimitExceeded:
                    error = 'Timeout'
                except Exception as e:
                    error = str(e)
            else:
                error = 'Timeout'

            if success:
                success_flag = True
                break
            else:
                errors.append(f'{med} to {rec}: {error}')

        if success_flag:
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'status': 'failed', 'errors': errors}, status=500)
