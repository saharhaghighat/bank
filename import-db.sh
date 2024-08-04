#!/bin/bash

BACKUP_FILE="transaction.gz"
MONGO_HOST="mongo"
MONGO_PORT="27017"

# Wait for MongoDB to start
echo "Waiting for MongoDB to start..."
until nc -z -v -w30 $MONGO_HOST $MONGO_PORT
do
  echo "MongoDB is unavailable - sleeping"
  sleep 1
done

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "Restoring database from $BACKUP_FILE..."
mongorestore --host $MONGO_HOST --port $MONGO_PORT --archive=$BACKUP_FILE --gzip

if [ $? -eq 0 ]; then
  echo "Database restore successful."
else
  echo "Database restore failed."
  exit 1
fi
