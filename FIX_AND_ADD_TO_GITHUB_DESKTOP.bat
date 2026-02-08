@echo off
cd /d "%~dp0"
echo Current folder: %CD%
echo.

echo Removing .git from PARENT folder (Cursor) if it exists...
if exist "..\.git" (
    rmdir /s /q "..\.git"
    echo   Removed parent .git. Parent is no longer a repo.
) else (
    echo   Parent has no .git.
)
echo.

echo This folder .git:
if exist ".git" (echo   OK - this folder is a Git repo.) else (echo   MISSING - run: git init)
echo.

echo Git status from THIS folder:
git status
echo.
echo If you see "Untracked: AIG-RLIC-REFINE-DEMO/" then GitHub Desktop is still using the wrong repo.
echo In GitHub Desktop: File -^> Remove (remove current repo), then File -^> Add local repository
echo and choose THIS folder: %CD%
echo.
pause
