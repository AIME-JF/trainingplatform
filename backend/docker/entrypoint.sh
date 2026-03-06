#!/bin/bash

if [ "$1" = "api" ]; then
    python main.py
elif [ "$1" = "worker" ]; then
    celery -A celery_app worker --loglevel=info --pool=gevent --concurrency=${CELERY_CONCURRENCY:-10}
elif [ "$1" = "beat" ]; then
    celery -A celery_app beat --loglevel=info
else
    echo "mode error"
    exit 1
fi 