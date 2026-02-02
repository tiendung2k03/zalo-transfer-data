# Zalo Data Transfer Tool (Phiên bản đơn giản hóa)

Công cụ này cho phép bạn chuyển dữ liệu Zalo (`/sdcard/Android/data/com.zing.zalo/files`) giữa hai thiết bị Android, hoặc giữa PC và Android một cách an toàn thông qua ADB.

**Kiến trúc:**
*   **Backend & Frontend:** Một ứng dụng Python (Flask) duy nhất, vừa cung cấp API điều khiển ADB, vừa phục vụ giao diện người dùng.

---

## Yêu cầu Hệ thống

### Chung
*   Đã bật **Developer Options** và **USB Debugging** (hoặc **Wireless Debugging**) trên các thiết bị Android.
*   Kiến thức cơ bản về dòng lệnh.

### Cho Windows
*   **Python 3.8+**: [Tải về tại đây](https://www.python.org/downloads/windows/). Nhớ tick vào ô "Add Python to PATH" khi cài đặt.
*   **Android SDK Platform-Tools (ADB)**: [Tải về tại đây](https://developer.android.com/studio/releases/platform-tools). Giải nén và thêm đường dẫn của thư mục `platform-tools` vào biến môi trường `PATH` của hệ thống.

### Cho Android (Termux)
*   Ứng dụng **Termux** từ F-Droid.
*   Cài đặt các gói cần thiết trong Termux:
    ```bash
    pkg update && pkg upgrade
    pkg install python android-tools # android-tools cung cấp lệnh adb
    ```

---

## Cài đặt và Chạy

### 1. Cài đặt Nhanh (Khuyến khích)

Sau khi đã clone hoặc tải về project, bạn có thể sử dụng các script cài đặt nhanh sau:

*   **Trên Android (Termux):**
    ```bash
    chmod +x install_android.sh
    ./install_android.sh
    ```
*   **Trên Windows:**
    ```cmd
    install_windows.bat
    ```
Các script này sẽ tự động cài đặt các thư viện Python cần thiết.

### 2. Chạy Ứng dụng

Sau khi cài đặt xong, bạn chỉ cần ở trong thư mục `zalo_data_transfer` và chạy lệnh sau để khởi động công cụ:

```bash
python run.py
```

### 3. Mở Giao diện

Mở trình duyệt web và truy cập vào địa chỉ: `http://127.0.0.1:5000`

---

## Hướng dẫn Sử dụng Giao diện

Giao diện của tool được thiết kế theo dạng wizard từng bước:

1.  **Bước 1: Chọn Môi trường:** Chọn xem bạn đang chạy tool này trên `Windows` hay `Android (Termux)`.
2.  **Bước 2: Chọn Hướng Dữ liệu:**
    *   **Xuất (Export):** Lấy dữ liệu từ máy đang chạy tool (Máy A) sang máy kia (Máy B).
    *   **Nhập (Import):** Lấy dữ liệu từ máy kia (Máy B) vào máy đang chạy tool (Máy A).
3.  **Bước 3: Kết nối Thiết bị:**
    *   **USB:** Kết nối thiết bị qua cáp USB và đảm bảo đã bật USB Debugging. Tool sẽ tự động kiểm tra.
    *   **Wireless Debugging:** Bật Wireless Debugging trên thiết bị Android đích, sau đó nhập IP, Cổng ghép nối (Pairing Port), và Mã ghép nối (Pairing Code) hiển thị trên màn hình điện thoại.
4.  **Bước 4: Bắt đầu:**
    *   Kiểm tra lại thông tin tóm tắt.
    *   Nhấn nút **Bắt đầu** để thực hiện quá trình chuyển dữ liệu.
    *   Theo dõi thanh tiến trình và log hiển thị thời gian thực.

---

## Cảnh báo An toàn

*   Tool này chỉ thao tác với dữ liệu trên thiết bị của bạn thông qua ADB và không gửi bất kỳ thông tin nào lên Internet.
*   Thao tác **Nhập dữ liệu (Import)** sẽ **GHI ĐÈ** thư mục Zalo trên thiết bị đích. Luôn sao lưu dữ liệu quan trọng trước khi thực hiện.
*   Nhà phát triển không chịu trách nhiệm cho bất kỳ mất mát dữ liệu nào. Hãy sử dụng một cách cẩn trọng.
