#!/bin/bash

#for celery beat
python manage.py migrate

# For cache transaction report you can add mode and type and also you can add merchantId to report a user's transactions
python manage.py update_transaction_summary

#for Sending daily report with email and sms at 00:00
python manage.py setup_periodic_tasks

exec "$@"
