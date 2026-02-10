
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

def _run_shell_command(command, log_message, is_windows=False):
    """Hàm phụ để chạy một lệnh shell phức tạp, xử lý output và báo lỗi."""
    global transfer_status
    transfer_status["log"] += log_message + "\n"
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, universal_newlines=True, bufsize=1)
    
    output_lines = []
    for line in iter(process.stdout.readline, ''):
        output_lines.append(line)
        # Thêm output vào log chính để người dùng thấy có hoạt động
        # Tránh các dòng quá dài (thường là lỗi binary)
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
    các hạn chế về quyền của Scoped Storage trên Android 11+.
    """
    global transfer_status
    
    try:
        environment = transfer_state_from_frontend.get("environment")
        is_windows = (environment == "windows")
        connection_details = transfer_state_from_frontend.get("connection", {})
        
        remote_zalo_root = "/sdcard/Android/data/com.zing.zalo"
        data_dir_name = "files"
        remote_data_path = os.path.join(remote_zalo_root, data_dir_name)
        
        local_temp_dir = "/data/data/com.termux/files/home/zalo_data_temp"
        local_data_path = os.path.join(local_temp_dir, data_dir_name) # Path to data in local temp folder

        remote_temp_dir = "/sdcard/Download/zalo_temp" # Temporary directory on Android device
        remote_temp_data_path = os.path.join(remote_temp_dir, data_dir_name) # Path to data in remote temp folder

        transfer_status["log"] = "Bắt đầu quá trình (phương pháp RUN-AS + ADB PULL/PUSH)...\n"
        transfer_status["status"] = "running"
        transfer_status["progress"] = 5

        # Dọn dẹp thư mục tạm cục bộ cũ
        if os.path.exists(local_temp_dir):
            shutil.rmtree(local_temp_dir)
        os.makedirs(local_temp_dir)
        transfer_status["progress"] = 10

        # Xác định thiết bị nguồn và đích
        if environment == 'android':
            device_a_id = connection_details.get("deviceA")
            device_b_id = connection_details.get("deviceB")
            if not all([device_a_id, device_b_id]):
                raise Exception("Lỗi: Thiếu thông tin kết nối cho Thiết bị A hoặc B.")
            
            source_device, target_device = (device_a_id, device_b_id) if direction == 'export' else (device_b_id, device_a_id)
            transfer_status["log"] += f"Nguồn: {source_device} | Đích: {target_device}\n"

        else: # Windows/PC
            device_id = connection_details.get("deviceId") or f"{connection_details.get('ip')}:{connection_details.get('connect_port', '5555')}"
            if not device_id:
                raise Exception("Không tìm thấy thiết bị nào được kết nối.")
            source_device = target_device = device_id
            transfer_status["log"] += f"Đang làm việc với thiết bị: {device_id}\n"

        # --- BƯỚC 1: LẤY DỮ LIỆU TỪ NGUỒN ---
        transfer_status["log"] += "\n--- BƯỚC 1: Lấy dữ liệu từ nguồn ---\n"
        transfer_status["progress"] = 15
        if environment == 'android' or (is_windows and direction == 'export'):
            # 1.a. Dọn dẹp thư mục tạm trên thiết bị nguồn
            pre_copy_cleanup_cmd = f'adb -s {source_device} shell "rm -rf {remote_temp_dir}"'
            _run_shell_command(pre_copy_cleanup_cmd, f"Dọn dẹp thư mục tạm trên nguồn {source_device}...", is_windows)
            transfer_status["progress"] = 20

            # 1.b. Sao chép dữ liệu từ Zalo app data sang thư mục tạm công khai trên thiết bị nguồn bằng run-as
            transfer_status["log"] += f"Sao chép dữ liệu trên {source_device} vào thư mục tạm bằng run-as...\n"
            # create remote_temp_dir first
            create_temp_dir_cmd = f"adb -s {source_device} shell \"mkdir -p {remote_temp_dir}\""
            _run_shell_command(create_temp_dir_cmd, f"Tạo thư mục tạm {remote_temp_dir} trên {source_device}...", is_windows)
            
            run_as_copy_cmd = f"run-as com.zing.zalo cp -r {remote_data_path} {remote_temp_dir}/"
            copy_on_device_cmd = f"adb -s {source_device} shell \"{run_as_copy_cmd}\""
            _run_shell_command(copy_on_device_cmd, f"Sao chép dữ liệu trên {source_device} bằng run-as...", is_windows)
            transfer_status["progress"] = 30

            # 1.c. Kéo dữ liệu từ thư mục tạm trên thiết bị nguồn về máy tính cục bộ
            transfer_status["log"] += f"Kéo dữ liệu từ thư mục tạm trên {source_device} về máy tính...\n"
            pull_cmd = f"adb -s {source_device} pull {remote_temp_data_path} {local_data_path}"
            _run_shell_command(pull_cmd, f"Kéo dữ liệu từ {source_device}...", is_windows)
            transfer_status["progress"] = 40

            # 1.d. Dọn dẹp thư mục tạm trên thiết bị nguồn
            post_copy_cleanup_cmd = f'adb -s {source_device} shell "rm -rf {remote_temp_dir}"'
            _run_shell_command(post_copy_cleanup_cmd, f"Dọn dẹp thư mục tạm trên nguồn {source_device}...", is_windows)
            
        elif is_windows and direction == 'import':
            # Dữ liệu cục bộ trên PC đã có sẵn trong local_data_path
            if not os.path.isdir(local_data_path):
                 raise Exception(f"Thư mục nguồn '{local_data_path}' không tồn tại. Hãy đặt thư mục 'files' của Zalo vào trong '{local_temp_dir}' trước khi nhập.")
            transfer_status["log"] += "Dữ liệu nguồn cục bộ đã sẵn sàng.\n"
        
        transfer_status["progress"] = 50

        # --- BƯỚC 2: CHUYỂN DỮ LIỆU TỚI ĐÍCH ---
        transfer_status["log"] += f"\n--- BƯỚC 2: Đẩy dữ liệu tới đích ---\n"
        transfer_status["progress"] = 55
        if environment == 'android' or (is_windows and direction == 'import'):
            # 2.a. Dọn dẹp thư mục Zalo cũ và thư mục tạm trên thiết bị đích
            pre_push_cleanup_cmd = f'adb -s {target_device} shell "rm -rf {remote_data_path}"'
            _run_shell_command(pre_push_cleanup_cmd, f"Dọn dẹp đích trên {target_device}...", is_windows)
            
            pre_push_temp_cleanup_cmd = f'adb -s {target_device} shell "rm -rf {remote_temp_dir}"'
            _run_shell_command(pre_push_temp_cleanup_cmd, f"Dọn dẹp thư mục tạm trên đích {target_device}...", is_windows)
            transfer_status["progress"] = 60

            # 2.b. Đẩy dữ liệu từ máy tính cục bộ vào thư mục tạm công khai trên thiết bị đích
            transfer_status["log"] += f"Đẩy dữ liệu tới thư mục tạm trên {target_device}...\n"
            push_to_temp_cmd = f"adb -s {target_device} push {local_data_path} {remote_temp_dir}/"
            _run_shell_command(push_to_temp_cmd, f"Đẩy dữ liệu tới thư mục tạm trên {target_device}...", is_windows)
            transfer_status["progress"] = 70

            # 2.c. Sao chép dữ liệu từ thư mục tạm công khai vào Zalo app data trên thiết bị đích bằng run-as
            transfer_status["log"] += f"Sao chép dữ liệu vào Zalo trên {target_device} bằng run-as...\n"
            run_as_paste_cmd = f"run-as com.zing.zalo cp -r {remote_temp_data_path} {remote_zalo_root}/"
            paste_on_device_cmd = f"adb -s {target_device} shell \"{run_as_paste_cmd}\""
            _run_shell_command(paste_on_device_cmd, f"Sao chép dữ liệu vào Zalo trên {target_device} bằng run-as...", is_windows)
            transfer_status["progress"] = 80

            # 2.d. Dọn dẹp thư mục tạm trên thiết bị đích
            post_paste_cleanup_cmd = f'adb -s {target_device} shell "rm -rf {remote_temp_dir}"'
            _run_shell_command(post_paste_cleanup_cmd, f"Dọn dẹp thư mục tạm trên đích {target_device}...", is_windows)
            
        elif is_windows and direction == 'export':
            # Dữ liệu đã được pull về local_data_path. Không cần làm gì thêm ở đây.
            transfer_status["log"] += "Dữ liệu đã được kéo về máy cục bộ.\n"

        transfer_status["progress"] = 100
        transfer_status["status"] = "completed"
        transfer_status["log"] += "\n--- QUÁ TRÌNH HOÀN TẤT THÀNH CÔNG! ---\n"

    except Exception as e:
        transfer_status["status"] = "failed"
        transfer_status["log"] += f"\n--- LỖI: {str(e)} ---"
    finally:
        # Không cần dọn dẹp file tar nữa, chỉ cần dọn dẹp thư mục cục bộ
        if os.path.exists(local_temp_dir):
            shutil.rmtree(local_temp_dir)


