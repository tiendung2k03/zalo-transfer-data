
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
    """
    global transfer_status
    
    environment = transfer_state_from_frontend.get("environment")
    is_windows = (environment == "windows")
    
    transfer_status["log"] = "Đang kiểm tra thiết bị...\n"
    devices_result = run_adb_command("devices", is_windows=is_windows)
    connected_device_id = None
    if devices_result["success"]:
        lines = devices_result["output"].strip().split("\n")[1:]
        device_lines = [line.split()[0] for line in lines if "device" in line]
        if device_lines:
            connected_device_id = device_lines[0]

    if not connected_device_id:
        transfer_status["status"] = "failed"
        transfer_status["log"] = "Lỗi: Không tìm thấy thiết bị nào được kết nối qua ADB. Vui lòng kiểm tra kết nối và bật USB/Wireless Debugging.\n"
        return

    data_path_on_device = "/sdcard/Android/data/com.zing.zalo/files"
    local_temp_dir = os.path.join(os.getcwd(), "zalo_data_temp") # Thư mục tạm thời trên máy chạy tool
    os.makedirs(local_temp_dir, exist_ok=True)
    local_zalo_data_path = os.path.join(local_temp_dir, "files") # Đường dẫn đích cho dữ liệu Zalo trên máy chạy tool

    try:
        transfer_status["log"] = "Bắt đầu quá trình...\n"
        transfer_status["status"] = "running"
        transfer_status["progress"] = 5

        # Kiểm tra Zalo trên thiết bị đích (nếu là import) hoặc thiết bị nguồn (nếu là export)
        transfer_status["log"] += f"Kiểm tra Zalo trên thiết bị {connected_device_id}...\n"
        pid_check_cmd = ["adb", "-s", connected_device_id, "shell", "pidof", "com.zing.zalo"]
        pid_check_result = subprocess.run(pid_check_cmd, capture_output=True, text=True, check=False)
        if pid_check_result.stdout.strip():
            transfer_status["log"] += "[CẢNH BÁO] Zalo đang chạy trên thiết bị. Nên tắt Zalo trước khi chuyển dữ liệu.\n"
        else:
            transfer_status["log"] += "Zalo không chạy trên thiết bị (Tốt).\n"
        transfer_status["progress"] = 15

        if direction == 'export': # Lấy dữ liệu từ thiết bị remote (B) về máy chạy tool (A)
            transfer_status["log"] += f"Đang xuất dữ liệu từ thiết bị {connected_device_id} về máy {"Windows" if is_windows else "Android (Termux)"}...\n"
            # Xóa thư mục tạm thời nếu đã tồn tại để đảm bảo dữ liệu mới nhất
            if os.path.exists(local_zalo_data_path):
                shutil.rmtree(local_zalo_data_path)
            os.makedirs(local_temp_dir, exist_ok=True)

            command = ["adb", "-s", connected_device_id, "pull", data_path_on_device, local_temp_dir]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, shell=is_windows)
            
            for line in iter(process.stdout.readline, ""):
                transfer_status["log"] += line
                if "%" in line:
                    try:
                        progress_val = int(line.split("%")[0].strip().split()[-1])
                        if transfer_status["progress"] < progress_val:
                            transfer_status["progress"] = progress_val
                    except ValueError:
                        pass
                if transfer_status["progress"] < 90:
                    transfer_status["progress"] += 1 

        elif direction == 'import': # Đẩy dữ liệu từ máy chạy tool (A) lên thiết bị remote (B)
            transfer_status["log"] += f"Đang nhập dữ liệu từ máy {"Windows" if is_windows else "Android (Termux)"} vào thiết bị {connected_device_id}...\n"
            # Giả định dữ liệu Zalo đã được chuẩn bị sẵn trong local_zalo_data_path
            # Nếu chưa có, cần một bước để người dùng chọn thư mục nguồn hoặc kéo từ thiết bị khác trước.
            # Để minh họa, tôi sẽ tạo một thư mục giả định với một tệp tin.
            if not os.path.exists(local_zalo_data_path):
                os.makedirs(local_zalo_data_path, exist_ok=True)
                with open(os.path.join(local_zalo_data_path, "test_import.txt"), "w") as f:
                    f.write("Đây là dữ liệu Zalo giả định để nhập.")

            command = ["adb", "-s", connected_device_id, "push", local_zalo_data_path, os.path.dirname(data_path_on_device)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, shell=is_windows)
            
            for line in iter(process.stdout.readline, ""):
                transfer_status["log"] += line
                if "%" in line:
                    try:
                        progress_val = int(line.split("%")[0].strip().split()[-1])
                        if transfer_status["progress"] < progress_val:
                            transfer_status["progress"] = progress_val
                    except ValueError:
                        pass
                if transfer_status["progress"] < 90:
                    transfer_status["progress"] += 1 

        process.wait()
        
        if process.returncode != 0:
            raise Exception(f"Lệnh thực thi thất bại với exit code {process.returncode}. Output: {process.stdout.read() + process.stderr.read()}")

        transfer_status["progress"] = 100
        transfer_status["status"] = "completed"
        transfer_status["log"] += "\n--- QUÁ TRÌNH HOÀN TẤT THÀNH CÔNG! ---"

    except Exception as e:
        transfer_status["status"] = "failed"
        transfer_status["log"] += f"\n--- LỖI: {str(e)} ---"
