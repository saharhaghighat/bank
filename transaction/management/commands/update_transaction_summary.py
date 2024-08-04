from django.core.management.base import BaseCommand
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
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

        pipeline.append({'$match': {'createdAt': {'$exists': True, '$ne': None}}})

        if mode == 'daily':
            group_id = {
                'year': {'$year': '$createdAt'},
                'month': {'$month': '$createdAt'},
                'day': {'$dayOfMonth': '$createdAt'}
            }
        elif mode == 'weekly':
            group_id = {
                'year': {'$year': '$createdAt'},
                'week': {'$week': '$createdAt'}
            }
        else:  # monthly
            group_id = {
                'year': {'$year': '$createdAt'},
                'month': {'$month': '$createdAt'}
            }

        if report_type == 'count':
            aggregation = {'$sum': 1}
        else:
            aggregation = {'$sum': '$amount'}

        pipeline.extend([
            {'$group': {'_id': group_id, 'value': aggregation}},
            {'$sort': {'_id': 1}}
        ])

        results = db.transaction.aggregate(pipeline)

        for result in results:
            summary_data = {
                'mode': mode,
                'type': report_type,
                'year': result['_id']['year'],
                'value': result['value']
            }

            if mode == 'daily':
                summary_data.update({
                    'month': result['_id']['month'],
                    'day': result['_id']['day']
                })
            elif mode == 'weekly':
                summary_data.update({
                    'week': result['_id']['week']
                })
            else:  # monthly
                summary_data.update({
                    'month': result['_id']['month']
                })

            if merchant_id:
                summary_data['merchantId'] = merchant_id

            db.transaction_summary.update_one(
                {'mode': mode, 'type': report_type, **summary_data},
                {'$set': summary_data},
                upsert=True
            )
