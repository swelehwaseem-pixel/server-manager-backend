# Example: Execute T-SQL against MSSQL
@router.post("/mssql/query")
async def execute_sql(payload: SQLQueryInput, current_user = Depends(get_current_user)):
    # Use asyncio.to_thread to run pyodbc (which is sync)
    def sync_query():
        conn = pyodbc.connect(f"DSN={payload.dsn};UID={payload.user};PWD={payload.password}")
        cursor = conn.cursor()
        cursor.execute(payload.sql_query)
        return cursor.fetchall()
    
    result = await asyncio.to_thread(sync_query)
    return {"data": result}

@router.post("/mssql/backup")
async def backup_database(payload: BackupInput, current_user = Depends(get_current_user)):
    # Runs: sqlcmd -Q "BACKUP DATABASE [db] TO DISK = '/backups/db.bak'"
    process = await asyncio.create_subprocess_exec(
        "sqlcmd", "-S", payload.server, "-U", payload.user, "-P", payload.password,
        "-Q", f"BACKUP DATABASE [{payload.database}] TO DISK = '{payload.backup_path}'"
    )
    ...
