# This is for database forensics for postgres.

#!/bin/bash

# PostgreSQL credentials
DB_NAME="username"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_PASSWORD="your_password"  # Add your password here

# Export the password to avoid prompt
export PGPASSWORD=$DB_PASSWORD

# Output log file
LOG_FILE="forensics_log.txt"

# Fetch all tables from the public schema
tables=$(psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -Atc "SELECT tablename FROM pg_tables WHERE schemaname='public';")

# Loop through each table
for table in $tables; do
    echo "Processing table: $table" | tee -a $LOG_FILE
    
    # Table Structure
    echo "Table structure for $table:" | tee -a $LOG_FILE
    psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -c "\d+ $table" | tee -a $LOG_FILE
    
    # Table Constraints
    echo "Constraints for $table:" | tee -a $LOG_FILE
    psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -c "
    SELECT
        conname AS constraint_name,
        pg_catalog.pg_get_constraintdef(r.oid, true) as constraint_definition
    FROM
        pg_catalog.pg_constraint r
    WHERE
        r.conrelid = '$table'::regclass;" | tee -a $LOG_FILE

    # Table Size
    echo "Table size for $table:" | tee -a $LOG_FILE
    psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -c "SELECT pg_size_pretty(pg_total_relation_size('$table')) AS total_size;" | tee -a $LOG_FILE

    # Dead Rows Analysis
    echo "Dead rows for $table:" | tee -a $LOG_FILE
    psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -c "SELECT n_dead_tup, n_live_tup FROM pg_stat_all_tables WHERE relname = '$table';" | tee -a $LOG_FILE

    # Autovacuum Logs
    echo "Autovacuum logs for $table:" | tee -a $LOG_FILE
    psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -c "SELECT last_autovacuum, last_analyze FROM pg_stat_user_tables WHERE relname = '$table';" | tee -a $LOG_FILE

    # Index Stats
    echo "Index stats for $table:" | tee -a $LOG_FILE
    psql -U $DB_USER -d $DB_NAME -h $DB_HOST -p $DB_PORT -c "
    SELECT
        indexrelname AS index_name,
        idx_scan AS index_scans,
        idx_tup_read AS tuples_read,
        idx_tup_fetch AS tuples_fetched
    FROM
        pg_stat_user_indexes
    WHERE
        relname = '$table';" | tee -a $LOG_FILE

    echo "----------------------------" | tee -a $LOG_FILE
done