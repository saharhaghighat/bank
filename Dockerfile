FROM python:3.12

WORKDIR /app

COPY requirements.txt /app/
COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn

RUN pip install celery redis

COPY import-db.sh /app/
COPY entrypoint.sh /app/

RUN chmod +x import-db.sh entrypoint.sh


EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["sh", "-c", "if [ \"$SERVICE_TYPE\" = 'django' ]; then gunicorn --bind 0.0.0.0:8000 bank.wsgi:application; elif [ \"$SERVICE_TYPE\" = 'celery' ]; then celery -A bank worker --loglevel=info; elif [ \"$SERVICE_TYPE\" = 'beat' ]; then celery -A bank beat --loglevel=info; else echo 'Invalid SERVICE_TYPE'; exit 1; fi"]
