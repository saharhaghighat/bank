from requests import get
from django.core.mail import send_mail
from django.conf import settings
from utills.db_connection import db
from utills.message_log import log_message
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded


@shared_task(bind=True, soft_time_limit=20)
def send_email_task(self, recipient, message):
    try:
        # time.sleep(22)  for test
        send_mail(
            subject='Notification',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient]
        )
        print(f"Sending email Message to {recipient}: {message}")
        log_message('email', recipient, message, 'success')
        return True, None
    except SoftTimeLimitExceeded:
        log_message('email', recipient, message, 'timeout')
        raise
    except Exception as e:
        log_message('email', recipient, message, f'failed: {str(e)}')
        raise self.retry(exc=e)


@shared_task(bind=True, soft_time_limit=20)
def send_sms_task(self, recipient, message):
    try:
        print(f"Sending SMS to {recipient}: {message}")
        log_message('sms', recipient, message, 'success')
        return True, None
    except SoftTimeLimitExceeded:
        log_message('sms', recipient, message, 'timeout')
        raise
    except Exception as e:
        log_message('sms', recipient, message, f'failed: {str(e)}')
        raise self.retry(exc=e)


@shared_task(bind=True, soft_time_limit=20)
def send_push_notification_task(self, recipient, message):
    try:
        print(f"Sending Push Notification to {recipient}: {message}")
        log_message('push', recipient, message, 'success')
        return True, None
    except SoftTimeLimitExceeded:
        log_message('push', recipient, message, 'timeout')
        raise
    except Exception as e:
        log_message('push', recipient, message, f'failed: {str(e)}')
        raise self.retry(exc=e)


@shared_task(bind=True, soft_time_limit=20)
def send_telegram_message_task(self, recipient, message):
    try:
        print(f"Sending Telegram Message to {recipient}: {message}")
        log_message('telegram', recipient, message, 'success')
        return True, None
    except SoftTimeLimitExceeded:
        log_message('telegram', recipient, message, 'timeout')
        raise
    except Exception as e:
        log_message('telegram', recipient, message, f'failed: {str(e)}')
        raise self.retry(exc=e)


@shared_task(bind=True, default_retry_delay=5 * 60, max_retries=3)
def send_reports(self):
    report_url = 'http://localhost:8000/api/transaction-report/'

    try:
        merchant_ids = db.transactions.distinct('merchantId')

        for merchant_id in merchant_ids:
            merchant = db.transactions.find_one({'merchantId': merchant_id})
            if not merchant:
                continue

                # merchant_email = merchant.get('email')
            # merchant_phone_number = merchant.get('phone_number')

            # for test
            merchant_email = 'sahar@gmail.com'
            merchant_phone_number = '09021166394'

            if not merchant_email or not merchant_phone_number:
                continue

            report_summary = {'daily': {'count': 0, 'amount': 0}}

            for report_type in ['count', 'amount']:
                try:
                    response = get(report_url, params={
                        'type': report_type,
                        'mode': 'daily',
                        'merchantId': merchant_id
                    })

                    if response.status_code == 200:
                        report = response.json()
                        total_count = sum(item['value'] for item in report if item['key'].startswith('تعداد'))
                        total_amount = sum(item['value'] for item in report if item['key'].startswith('مقدار'))

                        report_summary['daily'][report_type] = total_count if report_type == 'count' else total_amount

                    else:
                        report_summary['daily'][report_type] = 0
                        print(f"Failed to retrieve report. HTTP Status: {response.status_code}")

                except Exception as e:
                    self.retry(exc=e)

            daily_count = report_summary['daily']['count']
            daily_amount = report_summary['daily']['amount']

            message = (f'''
                        Hello,
                        your daily report is as follows:
                        Count: {daily_count}, Amount: {daily_amount}.
                        ''')

            send_email_task.delay(
                recipient=merchant_email,
                message=message
            )

            send_sms_task.delay(
                recipient=merchant_phone_number,
                message=message
            )

    except Exception as e:
        self.retry(exc=e)
