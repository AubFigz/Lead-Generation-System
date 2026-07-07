from database_management import cleanup_table

if __name__ == "__main__":
    cleanup_table('leads', retention_days=30)
