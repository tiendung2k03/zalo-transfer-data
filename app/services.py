
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

def _run_shell_command(command, log_message, is_windows=False, output_file=None):
    """Hàm phụ để chạy một lệnh shell phức tạp, xử lý output và báo lỗi."""
    global transfer_status
    transfer_status["log"] += log_message + "\n"
    
    if output_file:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, shell=True, universal_newlines=True)
        output_lines = []
        for line in iter(process.stderr.readline, ''):
            output_lines.append(line)
            if len(line) < 200:
                transfer_status["log"] += f"[ERR] {line}"
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, universal_newlines=True, bufsize=1)
        
        output_lines = []
        for line in iter(process.stdout.readline, ''):
            output_lines.append(line)
            if len(line) < 200:
                transfer_status["log"] += line
    
    return_code = process.wait()

    if return_code != 0:
        full_output = "".join(output_lines)
        raise Exception(f"Lệnh '{command}' thất bại với mã lỗi {return_code}.\nOutput:\n{full_output.strip()}")
    
    transfer_status["log"] += "Hoàn tất bước.\n"


def start_transfer_thread(direction, transfer_state_from_frontend):
    """
    Hàm chính thực hiện việc chuyển dữ liệu. Sử dụng 'tar' để vượt qua 
    các hạn chế về quyền của Scoped Storage trên Android 11+ và tối ưu tốc độ.
    Chỉ hỗ trợ chuyển dữ liệu giữa hai thiết bị Android.
    """
    global transfer_status
    
    # Khởi tạo giá trị mặc định cho các serial thiết bị
    source_device_serial = None
    target_device_serial = None
    
    try:
        environment = transfer_state_from_frontend.get("environment")
        is_windows = (environment == "windows") # Xác định host có phải Windows không

        # Xác định thư mục tạm cục bộ dựa trên môi trường
        if is_windows:
            local_temp_dir = os.path.join(os.getcwd(), "zalo_transfer_temp")
        else: # Android (Termux)
            local_temp_dir = "/data/data/com.termux/files/home/zalo_transfer_temp"


        connection_details = transfer_state_from_frontend.get("connection", {})
        
        # Định nghĩa các đường dẫn
        zalo_package_name = "com.zing.zalo"
        zalo_data_parent_dir = "/storage/emulated/0/Android/data" # Thư mục chứa com.zing.zalo
        
        # Tạo thư mục tạm cục bộ
        if os.path.exists(local_temp_dir):
            shutil.rmtree(local_temp_dir)
        os.makedirs(local_temp_dir)
        local_tar_path = os.path.join(local_temp_dir, "zalo.tar") # File tar cục bộ

        # Đường dẫn file tar trên /sdcard của thiết bị Android (nơi công khai)
        remote_tar_path = "/sdcard/zalo.tar" 

        transfer_status["log"] = "Bắt đầu quá trình chuyển giao (phương pháp TAR)....\n"
        transfer_status["status"] = "running"
        transfer_status["progress"] = 5

        # Logic chỉ còn cho chuyển giữa hai điện thoại (Android -> Android, hoặc Android qua Windows host)
        device_a_id = connection_details.get("deviceA")
        device_b_id = connection_details.get("deviceB")
        if not all([device_a_id, device_b_id]):
            raise Exception("Lỗi: Thiếu thông tin kết nối cho Thiết bị A hoặc B.")
        
        # direction 'export' là từ A đến B (A là nguồn, B là đích)
        # direction 'import' là từ B đến A (B là nguồn, A là đích)
        source_device_serial = device_a_id if direction == 'export' else device_b_id
        target_device_serial = device_b_id if direction == 'export' else device_a_id
        
        transfer_status["log"] += f"Nguồn: {source_device_serial} | Đích: {target_device_serial}\n"

        # --- BƯỚC 1: TẠO VÀ TẢI FILE DỮ LIỆU TỪ THIẾT BỊ NGUỒN (SOURCE_DEVICE_SERIAL) ---
        transfer_status["log"] += f"\n--- BƯỚC 1: Nén và tải dữ liệu từ {source_device_serial} ---\n"
        transfer_status["progress"] = 15

        # Lệnh tar trên thiết bị nguồn, loại bỏ run-as
        tar_cmd = f'adb -s {source_device_serial} exec-out "cd {zalo_data_parent_dir} && tar -cf - {zalo_package_name}" > "{local_tar_path}"'
        _run_shell_command(tar_cmd, f"Đang nén dữ liệu từ {source_device_serial} và lưu vào {local_tar_path}...", is_windows, output_file=local_tar_path)
        
        if not os.path.exists(local_tar_path) or os.path.getsize(local_tar_path) == 0:
            raise Exception("Không thể tạo file sao lưu hoặc file rỗng. Dữ liệu Zalo có thể không tồn tại hoặc không thể truy cập.")
        
        transfer_status["log"] += f"Đã tạo file sao lưu tạm thời tại: {local_tar_path} ({os.path.getsize(local_tar_path)} bytes)\n"
        transfer_status["progress"] = 40

        # --- BƯỚC 2: CHUYỂN FILE DỮ LIỆU TỚI THIẾT BỊ ĐÍCH (TARGET_DEVICE_SERIAL) ---
        transfer_status["log"] += f"\n--- BƯỚC 2: Tải file sao lưu lên {target_device_serial} ---\n"
        transfer_status["progress"] = 45

        _run_shell_command(f'adb -s {target_device_serial} shell "rm -f {remote_tar_path}"', f"Dọn dẹp file cũ trên {target_device_serial}...", is_windows)

        push_cmd = f'adb -s {target_device_serial} push "{local_tar_path}" "{remote_tar_path}"'
        _run_shell_command(push_cmd, f"Đang đẩy {os.path.basename(local_tar_path)} tới {target_device_serial}...", is_windows)
        transfer_status["progress"] = 70

        # --- BƯỚC 3: GIẢI NÉN FILE DỮ LIỆU TRÊN THIẾT BỊ ĐÍCH (TARGET_DEVICE_SERIAL) ---
        transfer_status["log"] += f"\n--- BƯỚC 3: Giải nén dữ liệu trên {target_device_serial} ---\n"
        transfer_status["progress"] = 75

        # Xóa thư mục Zalo cũ trên thiết bị đích, loại bỏ run-as
        cleanup_old_data_cmd = f'adb -s {target_device_serial} shell "rm -rf {zalo_data_parent_dir}/{zalo_package_name}"'
        _run_shell_command(cleanup_old_data_cmd, f"Đang xóa dữ liệu Zalo cũ trên {target_device_serial}...", is_windows)

        # Giải nén file tar trên thiết bị đích, loại bỏ run-as
        untar_cmd = f'adb -s {target_device_serial} shell "cd {zalo_data_parent_dir} && tar -xf {remote_tar_path}"'
        _run_shell_command(untar_cmd, f"Đang giải nén dữ liệu trên {target_device_serial}...", is_windows)
        transfer_status["progress"] = 90

        transfer_status["progress"] = 100
        transfer_status["status"] = "completed"
        transfer_status["log"] += "\n--- QUÁ TRÌNH CHUYỂN DỮ LIỆU HOÀN TẤT THÀNH CÔNG! ---\n"


    except Exception as e:
        transfer_status["status"] = "failed"
        transfer_status["log"] += f"\n--- LỖI: {str(e)} ---\n"
    finally:
        # Dọn dẹp thư mục tạm cục bộ
        if os.path.exists(local_temp_dir):
            shutil.rmtree(local_temp_dir)
            transfer_status["log"] += f"Đã dọn dẹp thư mục tạm cục bộ: {local_temp_dir}\n"
        
        # Luôn dọn dẹp file tar trên thiết bị đích nếu nó đã được đẩy lên
        if target_device_serial: # Chỉ dọn dẹp nếu có thiết bị đích được xác định
            try:
                _run_shell_command(f'adb -s {target_device_serial} shell "rm -f {remote_tar_path}"', f"Dọn dẹp file tar trên đích {target_device_serial}...", is_windows)
            except Exception as cleanup_e:
                transfer_status["log"] += f"Lỗi khi dọn dẹp file tar trên thiết bị đích {target_device_serial}: {cleanup_e}\n"
