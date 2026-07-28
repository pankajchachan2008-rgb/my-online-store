@echo off
echo Starting CGSmart Database Backup...

:: 1. Apne folder ka rasta set karein
SET PROJECT_DIR=C:\my_online_store
SET BACKUP_DIR=%PROJECT_DIR%\local_backups

:: Agar backup folder nahi hai toh bana do
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: 2. Date aur Time nikalne ka safe tareeka (Powershell ke through)
FOR /F "tokens=* USEBACKQ" %%F IN (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'"`) DO (
    SET TIMESTAMP=%%F
)

:: 3. SQLite Database copy karein
copy "%PROJECT_DIR%\db.sqlite3" "%BACKUP_DIR%\db_backup_%TIMESTAMP%.sqlite3"

echo ✅ Backup successfully saved at: %BACKUP_DIR%\db_backup_%TIMESTAMP%.sqlite3

:: 4. 7 din se purane backups delete karein storage bachane ke liye
ForFiles /p "%BACKUP_DIR%" /m db_backup_*.sqlite3 /d -7 /c "cmd /c del /q @file" >nul 2>&1

echo 🧹 Old backups cleaned up. Space optimized.