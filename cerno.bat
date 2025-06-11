@echo off
setlocal

REM --- ANSI Color Setup for Windows ---
for /f %%a in ('echo prompt $E^| cmd') do (
  set "ESC=%%a"
)
set "COLOR_CYAN=%ESC%[96m"
set "COLOR_GREEN=%ESC%[92m"
set "COLOR_YELLOW=%ESC%[93m"
set "COLOR_RED=%ESC%[91m"
set "COLOR_RESET=%ESC%[0m"

REM --- Configuration ---
set VENV_DIR=venv
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe
set VENV_PIP=%VENV_DIR%\Scripts\pip.exe
set VENV_CERNO_CLI=%VENV_DIR%\Scripts\cerno.exe

REM --- Argument Parsing for --verbose ---
set "VERBOSE_FLAG=false"
set "SETUP_ARGS="
for %%a in (%*) do (
    if /i "%%~a" == "--verbose" (
        set "VERBOSE_FLAG=true"
        set "SETUP_ARGS=--verbose"
    )
)

REM --- Main Logic ---

REM Create venv if it doesn't exist
if not exist "%VENV_DIR%\" (
    echo.
    echo %COLOR_CYAN%Virtual environment not found. Creating one now...%COLOR_RESET%
    python -m venv %VENV_DIR% > NUL
    if %errorlevel% neq 0 (
        echo %COLOR_RED%Error: Failed to create virtual environment.%COLOR_RESET%
        exit /b 1
    )
    echo %COLOR_GREEN%Virtual environment created successfully.%COLOR_RESET%
    echo.
)

REM Check if the project is installed
if not exist "%VENV_CERNO_CLI%" (
    echo.
    echo %COLOR_CYAN%Cerno project not yet installed. Running one-time setup...%COLOR_RESET%
    echo (This may take a few minutes.)
    echo.
    echo %COLOR_CYAN%Starting Cerno Setup%COLOR_RESET%
    echo.
    echo %COLOR_CYAN%[1/2] Installing Python dependencies...%COLOR_RESET%

    if "%VERBOSE_FLAG%"=="true" (
        echo %COLOR_CYAN%Verbose mode activated. Installing dependencies...%COLOR_RESET%
        %VENV_PIP% install -r requirements.txt
        if %errorlevel% neq 0 (
            echo %COLOR_RED%Error: Failed to install Python dependencies. Please check the output above.%COLOR_RESET%
            exit /b 1
        )
    ) else (
        %VENV_PIP% install -r requirements.txt > NUL 2>&1
        if %errorlevel% neq 0 (
            echo %COLOR_YELLOW%Initial quiet installation failed. Retrying in verbose mode...%COLOR_RESET%
            %VENV_PIP% install -r requirements.txt
            if %errorlevel% neq 0 (
                echo %COLOR_RED%Error: Failed to install Python dependencies. Please check the output above.%COLOR_RESET%
                exit /b 1
            )
        )
    )

    echo.
    echo %COLOR_CYAN%[2/2] Installing project and Node modules...%COLOR_RESET%
    %VENV_PYTHON% cerno_cli.py setup %SETUP_ARGS%
    if %errorlevel% neq 0 (
        echo %COLOR_RED%Project setup failed. Please check the output above.%COLOR_RESET%
        exit /b 1
    )

    echo.
    echo %COLOR_GREEN%Setup completed successfully!%COLOR_RESET%
    echo.

    REM Check if the CLI was installed successfully
    if not exist "%VENV_CERNO_CLI%" (
        echo %COLOR_RED%Error: Installation completed but cerno CLI not found.%COLOR_RESET%
        echo Please run the setup manually or check for errors above.
        exit /b 1
    )
)

REM If we get here, the CLI should be installed - run the actual command
%VENV_CERNO_CLI% %*