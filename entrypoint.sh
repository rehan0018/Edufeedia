#!/bin/sh
set -e

echo "Verifying database readiness..."
python -c "
import time, os, sys
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL', '')
if 'postgresql' in db_url or 'postgres' in db_url:
    try:
        import psycopg2
        p = urlparse(db_url)
        user = p.username or 'postgres'
        password = p.password or 'postgres'
        host = p.hostname or 'localhost'
        port = p.port or 5432
        dbname = p.path.lstrip('/') or 'edufeedia'

        for attempt in range(1, 31):
            try:
                conn = psycopg2.connect(host=host, port=port, user=user, password=password, dbname=dbname, connect_timeout=3)
                conn.close()
                print('Database connected successfully.')
                sys.exit(0)
            except Exception as e:
                print(f'Waiting for database (attempt {attempt}/30)...')
                time.sleep(2)
        print('Failed to connect to database after 30 attempts.')
        sys.exit(1)
    except ImportError:
        pass
" || true

echo "Running Alembic baseline migrations..."
alembic upgrade head

echo "Starting Edufeedia API..."
exec "$@"
