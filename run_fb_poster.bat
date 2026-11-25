@echo off
chcp 65001 > nul
echo ==============================================================================
echo  🚀 KHỞI ĐỘNG HANOI HOME - FACEBOOK GROUPS AUTO POSTER (V6 - PYTHON 3.15)
echo ==============================================================================
echo.
cd /d "%~dp0"
python HanoiHome_FBGroupPoster.py
if errorlevel 1 (
    echo.
    echo ⚠️ Có lỗi xảy ra trong quá trình chạy ứng dụng.
    pause
)
