
# app/services.py
import os
import subprocess
import threading
import time
import shutil
from .models import transfer_status

def run_adb_command(command, device_serial=None, is_windows=False):
    """Thực thi một lệnh ADB và trả về kết quả."""
    try:
        if isinstance(command, str):
            command = command.split()
        
        base_command = ["adb"]
        if device_serial:
            base_command.extend(["-s", device_serial])
        base_command.extend(command)

        # Sử dụng shell=True trên Windows để tìm adb.exe trong PATH
        shell_exec = is_windows

        result = subprocess.run(
            base_command,
            capture_output=True,
            text=True,
            check=False,
            shell=shell_exec
        )
        if result.returncode == 0:
            return {"success": True, "output": result.stdout.strip()}
        else:
            return {"success": False, "error": result.stderr.strip() or "Lỗi không xác định."}
    except FileNotFoundError:
        return {"success": False, "error": "Lệnh \'adb\' không được tìm thấy. Hãy chắc chắn rằng bạn đã cài đặt Android SDK Platform-Tools và thêm nó vào PATH."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _run_shell_command(command, log_message, is_windows=False, capture_stdout=True):
    """Hàm phụ để chạy một lệnh shell, xử lý output và báo lỗi."""
    global transfer_status
    transfer_status["log"] += log_message + "\n"
    
    try:
        # Sử dụng shell=True để hỗ trợ các lệnh phức tạp
        result = subprocess.run(
            command,
            capture_output=capture_stdout,
            text=isinstance(command, str) if capture_stdout else False,
            shell=True,
            check=False
        )

        if result.returncode != 0:
            error_msg = ""
            if capture_stdout:
                error_msg = result.stderr.strip() or "Lỗi không xác định."
            raise Exception(f"Lệnh thất bại (Mã lỗi {result.returncode}): {error_msg}")
        
        transfer_status["log"] += "Hoàn tất bước.\n"
        return result.stdout if capture_stdout else None
    except Exception as e:
        raise Exception(f"Lỗi khi thực thi lệnh: {str(e)}")


def start_transfer_thread(direction, transfer_state_from_frontend):
    """
    Hàm chính thực hiện việc chuyển dữ liệu.
    Đã tối ưu cho cả Windows (tránh hỏng file binary) và Termux (đường dẫn động).
    """
    global transfer_status
    
    source_device_serial = None
    target_device_serial = None
    local_temp_dir = ""
    remote_tar_path = "/sdcard/zalo_transfer.tar"
    zalo_package_name = "com.zing.zalo"
    zalo_data_parent_dir = "/storage/emulated/0/Android/data"
    is_windows = False

    try:
        environment = transfer_state_from_frontend.get("environment")
        is_windows = (environment == "windows")

        # Xác định thư mục tạm cục bộ (Dùng expanduser để linh hoạt trên Termux/Linux)
        if is_windows:
            local_temp_dir = os.path.join(os.getcwd(), "zalo_transfer_temp")
        else:
            home_dir = os.path.expanduser("~")
            local_temp_dir = os.path.join(home_dir, "zalo_transfer_temp")

        connection_details = transfer_state_from_frontend.get("connection", {})
        device_a_id = connection_details.get("deviceA")
        device_b_id = connection_details.get("deviceB")

        if not all([device_a_id, device_b_id]):
            raise Exception("Thiếu thông tin kết nối thiết bị.")
        
        source_device_serial = device_a_id if direction == 'export' else device_b_id
        target_device_serial = device_b_id if direction == 'export' else device_a_id
        
        transfer_status["log"] = f"Môi trường: {'Windows' if is_windows else 'Termux/Linux'}\n"
        transfer_status["log"] += f"Tiến trình: {source_device_serial} -> {target_device_serial}\n"
        transfer_status["status"] = "running"
        transfer_status["progress"] = 5

        # Tạo thư mục tạm
        if os.path.exists(local_temp_dir):
            shutil.rmtree(local_temp_dir)
        os.makedirs(local_temp_dir)
        local_tar_path = os.path.join(local_temp_dir, "zalo_backup.tar")

        # --- BƯỚC 0: Dọn dẹp video trên máy nguồn ---
        transfer_status["log"] += f"\n--- BƯỚC 0: Xóa Video Chat trên máy nguồn ---\n"
        video_chat_dir = f"{zalo_data_parent_dir}/{zalo_package_name}/files/zalo/video/chat"
        _run_shell_command(f'adb -s {source_device_serial} shell "rm -rf {video_chat_dir}"', "Đang xóa video/chat...", is_windows)
        transfer_status["progress"] = 10

        # --- BƯỚC 1: Nén và tải dữ liệu (Sử dụng Python ghi file để tránh lỗi binary trên Windows) ---
        transfer_status["log"] += f"\n--- BƯỚC 1: Nén và tải dữ liệu từ máy nguồn ---\n"
        
        # Lệnh ADB để nén (không dùng > redirection ở shell)
        tar_cmd = f'adb -s {source_device_serial} exec-out "cd {zalo_data_parent_dir} && tar -cf - {zalo_package_name}"'
        
        transfer_status["log"] += "Đang stream dữ liệu tar (Vui lòng không ngắt kết nối...)\n"
        
        # Mở file bằng Python ở chế độ 'wb' (write binary) để đảm bảo an toàn tuyệt đối
        with open(local_tar_path, 'wb') as f:
            process = subprocess.run(tar_cmd, stdout=f, stderr=subprocess.PIPE, shell=True)
            if process.returncode != 0:
                raise Exception(f"Lỗi nén dữ liệu: {process.stderr.decode().strip()}")
        
        if not os.path.exists(local_tar_path) or os.path.getsize(local_tar_path) < 1000:
            raise Exception("File backup quá nhỏ hoặc không tồn tại. Kiểm tra quyền ADB.")

        file_size_mb = os.path.getsize(local_tar_path) // (1024 * 1024)
        transfer_status["log"] += f"Đã tải xong: {file_size_mb} MB\n"
        transfer_status["progress"] = 50

        # --- BƯỚC 2: Tải dữ liệu lên máy đích ---
        transfer_status["log"] += f"\n--- BƯỚC 2: Đẩy dữ liệu lên máy đích ---\n"
        _run_shell_command(f'adb -s {target_device_serial} push "{local_tar_path}" "{remote_tar_path}"', "Đang push file .tar lên /sdcard/...", is_windows)
        transfer_status["progress"] = 80

        # --- BƯỚC 3: Giải nén trên máy đích ---
        transfer_status["log"] += f"\n--- BƯỚC 3: Giải nén dữ liệu trên máy đích ---\n"
        _run_shell_command(f'adb -s {target_device_serial} shell "rm -rf {zalo_data_parent_dir}/{zalo_package_name}"', "Xóa dữ liệu cũ...", is_windows)
        
        # Giải nén trực tiếp vào thư mục data
        untar_cmd = f'adb -s {target_device_serial} shell "tar -xf {remote_tar_path} -C {zalo_data_parent_dir}"'
        _run_shell_command(untar_cmd, "Đang giải nén (Vui lòng đợi...)", is_windows)
        
        transfer_status["progress"] = 100
        transfer_status["status"] = "completed"
        transfer_status["log"] += "\n--- CHUYỂN DỮ LIỆU THÀNH CÔNG! ---\n"
        transfer_status["log"] += "LƯU Ý quan trọng:\n1. Mở Zalo máy mới.\n2. Đăng nhập đúng tài khoản.\n3. Chọn 'KHÔI PHỤC TIN NHẮN' khi được hỏi.\n"

    except Exception as e:
        transfer_status["status"] = "failed"
        transfer_status["log"] += f"\n[LỖI NGHIÊM TRỌNG] {str(e)}\n"
        print(f"Transfer Error: {e}")
    finally:
        # Dọn dẹp file tạm
        if local_temp_dir and os.path.exists(local_temp_dir):
            shutil.rmtree(local_temp_dir)
        if target_device_serial:
            try:
                subprocess.run(f'adb -s {target_device_serial} shell "rm -f {remote_tar_path}"', shell=True, capture_output=True)
            except:
                pass
