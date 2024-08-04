from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule


class Command(BaseCommand):
    help = 'Set up periodic tasks'

    def handle(self, *args, **kwargs):
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='0',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )

        PeriodicTask.objects.get_or_create(
            crontab=schedule,
            name='Send Daily Transaction Reports',
            task='transaction.tasks.send_reports'
        )
        self.stdout.write(self.style.SUCCESS('Successfully set up periodic tasks'))
