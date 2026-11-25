@echo off
chcp 65001 > nul
echo ==============================================================================
echo  🔑 MỞ GOOGLE CHROME GỐC ĐỂ ĐĂNG NHẬP FACEBOOK VÀ GOOGLE (KHÔNG BỊ CHẶN)
echo ==============================================================================
echo.

set "PROFILE_DIR=%~dp0app_data\fb_chrome_profile"
if exist "E:\Cho Thuê Chung Cư\" set "PROFILE_DIR=E:\Cho Thuê Chung Cư\fb_chrome_profile"
if not exist "%PROFILE_DIR%" mkdir "%PROFILE_DIR%"

set "CHROME_EXE=chrome.exe"
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME_EXE=%LocalAppData%\Google\Chrome\Application\chrome.exe"

echo Đang mở Google Chrome với Profile riêng: %PROFILE_DIR% ...
start "" "%CHROME_EXE%" --user-data-dir="%PROFILE_DIR%" "https://www.facebook.com" "https://docs.google.com/spreadsheets/d/1fVq7q7RB6qGI5PR1-8X24bP5EOqwAX52wcpeigb4gcw/edit?gid=0#gid=0"
echo.
echo ✅ Đã mở Chrome! Bạn hãy đăng nhập tài khoản trên 2 tab vừa mở.
echo Sau khi đăng nhập thành công cả Facebook và Google, bạn hãy đóng cửa sổ Chrome lại!
echo.
pause
