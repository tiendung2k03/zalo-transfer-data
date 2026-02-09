# app/routes.py
import threading
import subprocess # Thêm import subprocess
from flask import Blueprint, jsonify, request, render_template
from .services import run_adb_command, start_transfer_thread
from .models import transfer_status

# Sử dụng Blueprint để tổ chức các routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/api/adb/check', methods=['GET'])
def adb_check():
    environment = request.args.get("environment", "android") # Default to android if not provided
    is_windows = (environment == "windows")
    result = run_adb_command("devices", is_windows=is_windows)
    return jsonify(result)

@main_bp.route('/api/adb/pair', methods=['POST'])
def adb_pair():
    data = request.json
    environment = data.get("environment", "android")
    is_windows = (environment == "windows")
    ip, port, code = data.get("ip"), data.get("pairing_port"), data.get("pairing_code")
    if not all([ip, port, code]):
        return jsonify({"success": False, "error": "Thiếu thông tin IP, pairing port, hoặc pairing code."}), 400
    
    # Lệnh pair của ADB cần input, không thể chạy trực tiếp bằng helper `run_adb_command`
    # Do đó, logic Popen được giữ lại ở đây.
    try:
        command = ["adb", "pair", f"{ip}:{port}"]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=is_windows)
        stdout, stderr = process.communicate(input=code)
        if process.returncode == 0 and "Successfully paired" in stdout:
             return jsonify({"success": True, "output": stdout})
        else:
             error_output = f"Stdout: {stdout.strip()}, Stderr: {stderr.strip()}"
             return jsonify({"success": False, "error": error_output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@main_bp.route('/api/adb/connect', methods=['POST'])
def adb_connect():
    data = request.json
    environment = data.get("environment", "android")
    is_windows = (environment == "windows")
    ip = data.get("ip")
    port = data.get("connect_port")
    if not ip or not port:
        return jsonify({"success": False, "error": "Thiếu địa chỉ IP hoặc Connect Port."}), 400
    result = run_adb_command(f"connect {ip}:{port}", is_windows=is_windows)
    return jsonify(result)

@main_bp.route('/api/transfer/<direction>', methods=['POST'])
def transfer_start(direction):
    global transfer_status
    if direction not in ['export', 'import']:
        return jsonify({"success": False, "error": "Hướng không hợp lệ."}), 400
    
    if transfer_status.get("status") == "running":
        return jsonify({"success": False, "error": "Một quá trình khác đang chạy."}), 409

    frontend_state = request.json
    
    # Reset state
    transfer_status.update({
        "status": "starting",
        "progress": 0,
        "log": "Đang khởi tạo...",
        "thread": None
    })
    
    thread = threading.Thread(target=start_transfer_thread, args=(direction, frontend_state))
    thread.daemon = True
    thread.start()
    transfer_status["thread"] = thread

    return jsonify({"success": True, "message": "Bắt đầu quá trình..."})

@main_bp.route('/api/status', methods=['GET'])
def get_status():
    status_copy = transfer_status.copy()
    status_copy.pop('thread', None)
    return jsonify(status_copy)
