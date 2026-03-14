#!/bin/bash
set -e

detect_bootstrap_state() {
    python -c "import sys; from app.database.auto_migrate import is_database_empty, is_database_uninitialized; sys.exit(20 if is_database_empty() else (30 if is_database_uninitialized() else 10))"
}

if [ "$1" = "api" ]; then
    set +e
    detect_bootstrap_state
    status=$?
    set -e

    if [ "$status" -eq 20 ]; then
        echo "database is empty, bootstrapping schema with init_data.py and stamping alembic head"
        python init_data.py
        python migrate.py stamp head
    elif [ "$status" -eq 30 ]; then
        echo "database schema exists but seed data is missing, running init_data.py"
        python init_data.py
    else
        if [ "$status" -ne 10 ]; then
            exit "$status"
        fi
        echo "database already initialized, skipping init_data.py"
    fi
    python main.py
elif [ "$1" = "worker" ]; then
    celery -A celery_app worker --loglevel=info --pool=gevent --concurrency=${CELERY_CONCURRENCY:-10}
elif [ "$1" = "beat" ]; then
    celery -A celery_app beat --loglevel=info
else
    echo "mode error"
    exit 1
fi 
