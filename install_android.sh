#!/bin/bash

echo "========================================="
echo "Zalo Transfer Tool - Android (Termux) Setup"
echo "========================================="

# Cập nhật danh sách gói
echo "\n[*] Đang cập nhật Termux packages..."
pkg update -y && pkg upgrade -y

# Cài đặt các gói cần thiết
echo "\n[*] Đang cài đặt python và android-tools (adb)..."
pkg install python android-tools -y

# Kiểm tra cài đặt thành công
if ! command -v python &> /dev/null || ! command -v adb &> /dev/null;
then
    echo "\n[ERROR] Cài đặt python hoặc android-tools đã thất bại. Vui lòng thử lại."
    exit 1
fi
echo "==> Các gói cần thiết đã được cài đặt."

# Cài đặt các thư viện Python
if [ -f "requirements.txt" ]; then
    echo "\n[*] Đang cài đặt các thư viện Python từ requirements.txt..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "\n[ERROR] Cài đặt thư viện Python thất bại."
        exit 1
    fi
    echo "==> Các thư viện Python đã được cài đặt."
else
    echo "\n[WARNING] Không tìm thấy file requirements.txt. Bỏ qua bước cài đặt thư viện Python."
fi


echo "\n========================================="
echo "==> CÀI ĐẶT HOÀN TẤT! <=="
echo "========================================="
echo "\nĐể chạy tool, hãy làm theo các bước sau:"
echo "1. Chạy ứng dụng:"
echo "   python run.py"
echo ""
echo "2. Mở trình duyệt trên điện thoại và truy cập: http://127.0.0.1:5000"
echo "========================================="

exit 0
