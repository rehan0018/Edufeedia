#!/bin/sh
set -e

echo "Running Alembic baseline migrations..."
alembic upgrade head

echo "Starting Edufeedia API..."
exec "$@"
