@echo off
setlocal

echo =========================================
echo Zalo Transfer Tool - Windows Setup
echo =========================================

echo.
echo [*] Kiểm tra Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python không được tìm thấy trong PATH.
    echo Vui lòng cài đặt Python 3.8+ từ https://www.python.org/downloads/windows/ và đảm bảo nó được thêm vào PATH.
    echo Sau đó chạy lại script này.
    goto :eof
)
echo ==> Python đã được tìm thấy.

echo.
echo [*] Kiểm tra ADB (Android Debug Bridge)...
where adb >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] ADB không được tìm thấy trong PATH.
    echo Vui lòng cài đặt Android SDK Platform-Tools từ https://developer.android.com/studio/releases/platform-tools
    echo và thêm thư mục platform-tools vào biến môi trường PATH.
    echo Sau đó chạy lại script này.
    goto :eof
)
echo ==> ADB đã được tìm thấy.

echo.
echo [*] Đang cài đặt các thư viện Python từ requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Cài đặt thư viện Python thất bại. Vui lòng kiểm tra lỗi bên trên.
    goto :eof
)
echo ==> Các thư viện Python đã được cài đặt.

echo.
echo =========================================
echo ==> CÀI ĐẶT HOÀN TẤT! <=^
echo =========================================
echo.
echo Để chạy tool, hãy làm theo các bước sau:
echo 1. Chạy ứng dụng:
echo    python run.py
echo.
echo 2. Mở trình duyệt web và truy cập: http://127.0.0.1:5000
echo =========================================

endlocal
exit /b 0
