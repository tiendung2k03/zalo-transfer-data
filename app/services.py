
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

def start_transfer_thread(direction, transfer_state_from_frontend):
    """
    Hàm chính thực hiện việc chuyển dữ liệu trong một thread riêng.
    Xử lý logic cho cả môi trường Windows (1 thiết bị) và Android (2 thiết bị).
    """
    global transfer_status
    
    environment = transfer_state_from_frontend.get("environment")
    is_windows = (environment == "windows")
    connection_details = transfer_state_from_frontend.get("connection", {})
    
    data_path_on_device = "/sdcard/Android/data/com.zing.zalo/files"
    # Thư mục tạm thời trên máy chạy tool (phải là nơi Termux có quyền ghi)
    local_temp_dir = "/data/data/com.termux/files/home/zalo_data_temp"
    os.makedirs(local_temp_dir, exist_ok=True)
    # Đường dẫn này là nơi thư mục 'files' sẽ được kéo về, ví dụ: /data/data/com.termux/files/home/zalo_data_temp/files
    local_zalo_data_path = os.path.join(local_temp_dir, "files")

    try:
        transfer_status["log"] = "Bắt đầu quá trình...\n"
        transfer_status["status"] = "running"
        transfer_status["progress"] = 5

        if environment == 'android':
            # Logic cho môi trường Android (2 thiết bị)
            device_a_id = connection_details.get("deviceA")
            device_b_id = connection_details.get("deviceB")

            if not all([device_a_id, device_b_id]):
                raise Exception("Lỗi: Thiếu thông tin kết nối cho Thiết bị A hoặc Thiết bị B.")

            transfer_status["log"] += f"Thiết bị A (máy chạy tool): {device_a_id}\n"
            transfer_status["log"] += f"Thiết bị B (máy từ xa): {device_b_id}\n"

            # Xóa thư mục tạm thời nếu đã tồn tại để đảm bảo dữ liệu mới nhất
            if os.path.exists(local_zalo_data_path):
                transfer_status["log"] += f"Xóa thư mục tạm thời cũ: {local_zalo_data_path}\n"
                shutil.rmtree(local_zalo_data_path)
            os.makedirs(local_zalo_data_path, exist_ok=True)

            if direction == 'export': # A -> B
                transfer_status["log"] += f"\n--- BƯỚC 1: Lấy dữ liệu từ Thiết bị A ---\n"
                # Pull từ chính nó (A) vào thư mục tạm của Termux
                pull_cmd_A = ["adb", "-s", device_a_id, "pull", data_path_on_device, local_temp_dir]
                _run_adb_process(pull_cmd_A, is_windows, "Đang lấy dữ liệu từ máy A...")
                
                transfer_status["log"] += f"\n--- BƯỚC 2: Chuyển dữ liệu đến Thiết bị B ---\n"
                # Push từ thư mục tạm của Termux lên thiết bị B
                push_cmd_B = ["adb", "-s", device_b_id, "push", local_zalo_data_path, os.path.dirname(data_path_on_device)]
                _run_adb_process(push_cmd_B, is_windows, "Đang đẩy dữ liệu tới máy B...")

            elif direction == 'import': # B -> A
                transfer_status["log"] += f"\n--- BƯỚC 1: Lấy dữ liệu từ Thiết bị B ---\n"
                # Pull từ thiết bị B vào thư mục tạm của Termux
                pull_cmd_B = ["adb", "-s", device_b_id, "pull", data_path_on_device, local_temp_dir]
                _run_adb_process(pull_cmd_B, is_windows, "Đang lấy dữ liệu từ máy B...")

                transfer_status["log"] += f"\n--- BƯỚC 2: Chuyển dữ liệu đến Thiết bị A ---\n"
                # Push từ thư mục tạm của Termux vào chính nó (A)
                push_cmd_A = ["adb", "-s", device_a_id, "push", local_zalo_data_path, os.path.dirname(data_path_on_device)]
                _run_adb_process(push_cmd_A, is_windows, "Đang đẩy dữ liệu tới máy A...")

        else: # Logic cũ cho Windows (1 thiết bị)
            devices_result = run_adb_command("devices", is_windows=is_windows)
            device_id = connection_details.get("deviceId") or connection_details.get("ip") + ":" + connection_details.get("connect_port", "5555")

            if not device_id:
                raise Exception("Không tìm thấy thiết bị nào được kết nối.")
                
            transfer_status["log"] += f"Đang làm việc với thiết bị: {device_id}\n"

            if direction == 'export':
                pull_cmd = ["adb", "-s", device_id, "pull", data_path_on_device, local_temp_dir]
                _run_adb_process(pull_cmd, is_windows, "Đang xuất dữ liệu từ thiết bị...")
            elif direction == 'import':
                push_cmd = ["adb", "-s", device_id, "push", local_zalo_data_path, os.path.dirname(data_path_on_device)]
                _run_adb_process(push_cmd, is_windows, "Đang nhập dữ liệu vào thiết bị...")

        transfer_status["progress"] = 100
        transfer_status["status"] = "completed"
        transfer_status["log"] += "\n--- QUÁ TRÌNH HOÀN TẤT THÀNH CÔNG! ---"

    except Exception as e:
        transfer_status["status"] = "failed"
        transfer_status["log"] += f"\n--- LỖI: {str(e)} ---"

def _run_adb_process(command, is_windows, initial_log):
    """Hàm phụ để chạy một tiến trình ADB và cập nhật log/progress."""
    global transfer_status
    transfer_status["log"] += initial_log + "\n"
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, shell=is_windows)
    
    for line in iter(process.stdout.readline, ""):
        transfer_status["log"] += line
        # Cập nhật progress bar một cách đơn giản
        if transfer_status["progress"] < 95:
            transfer_status["progress"] += 0.1 
    
    process.wait()
    
    if process.returncode != 0:
        # Cố gắng đọc thêm output nếu có lỗi
        error_output = process.stdout.read()
        raise Exception(f"Lệnh '{" ".join(command)}' thất bại với exit code {process.returncode}. Output: {error_output}")
    
    transfer_status["log"] += "Hoàn tất bước.\n"
    transfer_status["progress"] = int(transfer_status["progress"]) + 5 # Tăng progress sau mỗi bước

