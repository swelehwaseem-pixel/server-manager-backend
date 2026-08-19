import asyncio
import os
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_user
from app.database import User
from app.schemas.db_admin import DBInstanceControlInput, SilentDBCARequestInput

router = APIRouter(prefix="/api/v1/oracle", tags=["Oracle Engine"])

# 🔐 NEW: Strict path validation to prevent sudo injection
def validate_oracle_home(path: str):
    # Restrict to typical Oracle installation paths on Linux
    if not (path.startswith("/u01/app/oracle/product/") or 
            path.startswith("/u02/app/oracle/product/") or
            path.startswith("/opt/oracle/product/")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Oracle home path is restricted to standard installation directories."
        )
    if not os.path.isdir(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Oracle home directory does not exist on the host system."
        )

@router.post("/instance-control")
async def control_oracle_instance(payload: DBInstanceControlInput, current_user: User = Depends(get_current_user)):
    # 🔐 Validate the path before using it in subprocess
    validate_oracle_home(payload.oracle_home)
    
    binary_target = "dbstart" if payload.action == "start" else "dbshut"
    binary_path = f"{payload.oracle_home}/bin/{binary_target}"
    
    custom_env = {
        "ORACLE_HOME": payload.oracle_home,
        "ORACLE_SID": payload.oracle_sid,
        "PATH": f"{payload.oracle_home}/bin:/usr/local/bin:/usr/bin:/bin"
    }

    process = await asyncio.create_subprocess_exec(
        "sudo", "-u", "oracle", binary_path, payload.oracle_home,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=custom_env
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Oracle Exec Error: {stderr.decode().strip()}")

    return {"status": "Success", "stdout": stdout.decode().strip()}

@router.post("/create-database")
async def create_database_silent(payload: SilentDBCARequestInput, current_user: User = Depends(get_current_user)):
    # 🔐 Validate the path before using it in subprocess
    validate_oracle_home(payload.oracle_home)
    
    dbca_binary = f"{payload.oracle_home}/bin/dbca"
    cmd = [
        "sudo", "-u", "oracle", dbca_binary, "-silent", "-createDatabase",
        "-templateName", "General_Purpose.dbc", "-sid", payload.sid,
        "-gdbname", payload.global_db_name, "-sysPassword", payload.sys_password,
        "-systemPassword", payload.system_password, "-databaseType", "MULTIPURPOSE",
        "-memoryMgmtType", "AUTO_SGA", "-totalMemory", str(payload.total_memory_mb),
        "-responseFile", "NO_VALUE", "-ignorePreReqs"
    ]

    if payload.create_as_cdb:
        cmd.extend([
            "-createAsContainerDatabase", "true", "-numberOfPDBs", str(payload.number_of_pdbs),
            "-pdbName", payload.pdb_name, "-pdbAdminPassword", payload.pdb_admin_password
        ])
    else:
        cmd.extend(["-createAsContainerDatabase", "false"])

    custom_env = {"ORACLE_HOME": payload.oracle_home, "PATH": f"{payload.oracle_home}/bin:/usr/bin:/bin"}

    try:
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=custom_env)
        asyncio.create_task(monitor_dbca_process(process, payload.sid))
        return {"status": "Processing Spawning", "message": f"DBCA initialization tasked for SID: {payload.sid}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process Pipeline Failed: {str(e)}")

async def monitor_dbca_process(process, sid: str):
    stdout, stderr = await process.communicate()
    print(f"[DBCA Finished] SID: {sid} Code: {process.returncode}")
