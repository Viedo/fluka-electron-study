@echo off
setlocal DisableDelayedExpansion
set "FLUKA_BASH=%ProgramFiles%\Git\bin\bash.exe"
if exist "%FLUKA_BASH%" goto launch
set "FLUKA_BASH=%LocalAppData%\Programs\Git\bin\bash.exe"
if exist "%FLUKA_BASH%" goto launch
echo ERROR: Git Bash not found. See docs\windows.md.
exit /b 1
:launch
"%FLUKA_BASH%" "%~dp0scripts\fluka.sh" %*
exit /b %ERRORLEVEL%
