#!/bin/sh
# Creates the test database next to the dev one (first boot of the postgres volume only).
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE ${POSTGRES_DB}_test;
EOSQL
