from datetime import datetime
from bson import ObjectId
from django.core.management.base import BaseCommand
from transaction.views import convert_to_jalali
from utills.db_connection import db


class Command(BaseCommand):
    help = 'Update transaction summary collection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            choices=['daily', 'weekly', 'monthly'],
            help='Specify the mode: daily, weekly, or monthly'
        )
        parser.add_argument(
            '--type',
            choices=['count', 'amount'],
            help='Specify the type: count or amount'
        )
        parser.add_argument(
            '--merchant-id',
            type=str,
            help='Specify the merchant ID to filter transactions by merchant'
        )

    def handle(self, *args, **kwargs):
        mode = kwargs.get('mode')
        report_type = kwargs.get('type')
        merchant_id = kwargs.get('merchant_id')

        if mode and report_type:
            self.update_summary(mode, report_type, merchant_id)
        elif mode:
            for rtype in ['count', 'amount']:
                self.update_summary(mode, rtype, merchant_id)
        elif report_type:
            for mtype in ['daily', 'weekly', 'monthly']:
                self.update_summary(mtype, report_type, merchant_id)
        else:
            for mtype in ['daily', 'weekly', 'monthly']:
                for rtype in ['count', 'amount']:
                    self.update_summary(mtype, rtype, merchant_id)

        self.stdout.write(self.style.SUCCESS('Successfully updated transaction summary'))

    def update_summary(self, mode, report_type, merchant_id=None):
        pipeline = []

        if merchant_id:
            try:
                merchant_id = ObjectId(merchant_id)
                pipeline.append({'$match': {'merchantId': merchant_id}})
            except Exception:
                self.stdout.write(self.style.ERROR(f'Invalid merchantId: {merchant_id}'))
                return

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

        for result in results:
            try:
                year = result['_id']['year']
                month = result['_id'].get('month')
                day = result['_id'].get('day')
                week = result['_id'].get('week')

                if mode == 'daily' or mode == 'weekly':
                    date_obj = datetime(year, month, day)

                else:  # monthly
                    date_obj = datetime(year, month, 1)

                key = convert_to_jalali(date_obj, mode, week)

                summary_data = {
                    'mode': mode,
                    'type': report_type,
                    'key': key,
                    'value': result['value']
                }

                if merchant_id:
                    summary_data['merchantId'] = merchant_id

                db.transaction_summary.update_one(
                    {'mode': mode, 'type': report_type, 'key': key,
                     **({'merchantId': merchant_id} if merchant_id else {})},
                    {'$set': summary_data},
                    upsert=True
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing result: {e}'))
