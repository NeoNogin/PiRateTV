@echo off
setlocal

:: Check if ffmpeg is installed/accessible
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: FFmpeg not found in PATH.
    echo Please install FFmpeg and add it to your system PATH.
    pause
    exit /b
)

:: Create an output directory
if not exist "converted" mkdir "converted"

echo Converting files for Pirate Audio (240x240 @ 15fps)...
echo Output saved to "converted" folder.
echo.

:loop
:: Check if we have any arguments left (files to process)
if "%~1"=="" goto done

set "input_file=%~1"
set "file_name=%~nx1"

echo Processing: "%file_name%"

:: FFmpeg conversion
:: We are no longer inside a 'for' loop block, so the parentheses in the filter string
:: "(ow-iw)/2" will won't break the script anymore.
ffmpeg -i "%input_file%" -vf "scale=240:240:force_original_aspect_ratio=decrease,pad=240:240:(ow-iw)/2:(oh-ih)/2" -r 15 -c:v libx264 -preset fast -crf 23 -c:a copy "converted\%file_name%"

if %errorlevel% equ 0 (
    echo [OK] Done.
) else (
    echo [ERROR] Failed to convert "%file_name%"
)
echo ---------------------------------------------------

:: Move to the next file in the list
shift
goto loop

:done
echo.
echo All conversions complete!
pause