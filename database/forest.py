#Postgres Forensics Script -- Untested, BEWARE!!!!!

import psycopg2
from psycopg2 import sql

# PostgreSQL credentials
DB_NAME = "your_db"
DB_USER = "your_user"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_PASSWORD = "your_password"

# Output log file
LOG_FILE = "forensics_log.txt"

def log_message(message):
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")
    print(message)

def execute_query(cursor, query, table_name):
    try:
        cursor.execute(sql.SQL(query).format(sql.Identifier(table_name)))
        return cursor.fetchall()
    except Exception as e:
        log_message(f"Error executing query on {table_name}: {e}")
        return []

def main():
    conn = None
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
        cursor = conn.cursor()

        # Fetch all tables in the 'public' schema
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            log_message(f"Processing table: {table_name}")

            # Table Structure
            log_message(f"Table structure for {table_name}:")
            cursor.execute(f"SELECT * FROM information_schema.columns WHERE table_name = '{table_name}';")
            for row in cursor.fetchall():
                log_message(str(row))

            # Table Constraints
            log_message(f"Constraints for {table_name}:")
            query_constraints = """
            SELECT conname, pg_catalog.pg_get_constraintdef(r.oid, true)
            FROM pg_catalog.pg_constraint r
            WHERE r.conrelid = '{}'::regclass;
            """
            for row in execute_query(cursor, query_constraints, table_name):
                log_message(str(row))

            # Table Size
            log_message(f"Table size for {table_name}:")
            cursor.execute(f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}')) AS total_size;")
            log_message(str(cursor.fetchone()))

            # Dead Rows Analysis
            log_message(f"Dead rows for {table_name}:")
            cursor.execute(f"SELECT n_dead_tup, n_live_tup FROM pg_stat_all_tables WHERE relname = '{table_name}';")
            log_message(str(cursor.fetchone()))

            # Autovacuum Logs
            log_message(f"Autovacuum logs for {table_name}:")
            cursor.execute(f"SELECT last_autovacuum, last_analyze FROM pg_stat_user_tables WHERE relname = '{table_name}';")
            log_message(str(cursor.fetchone()))

            # Index Stats
            log_message(f"Index stats for {table_name}:")
            query_index = """
            SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE relname = '{}';
            """
            for row in execute_query(cursor, query_index, table_name):
                log_message(str(row))

            log_message("----------------------------")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn is not None:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()