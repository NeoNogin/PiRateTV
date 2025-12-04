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
if not exist "browser_compatible" mkdir "browser_compatible"

echo Converting files for browser playback (240x240, AAC Audio)...
echo This script will re-encode audio to AAC for browser compatibility.
echo The video stream will be processed as before.
echo Output saved to "browser_compatible" folder.
echo.

:loop
:: Check if we have any arguments left (files to process)
if "%~1"=="" goto done

set "input_file=%~1"
set "file_name=%~nx1"

echo Processing: "%file_name%"

:: FFmpeg conversion with AAC audio
:: -c:v libx264 : Keeps the video encoding the same.
:: -vf "..."   : Your original video filter for scaling and padding.
:: -r 15         : Keeps the frame rate at 15fps.
:: -c:a aac    : Re-encodes the audio to AAC format.
:: -b:a 128k   : Sets a standard audio bitrate of 128kbps.
ffmpeg -i "%input_file%" -vf "scale=240:240:force_original_aspect_ratio=decrease,pad=240:240:(ow-iw)/2:(oh-ih)/2" -r 15 -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k "browser_compatible\%file_name%"

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