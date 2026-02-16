const API_BASE_URL = window.location.origin; // Sử dụng origin hiện tại để linh hoạt hơn

// State object to hold user choices
const transferState = {
    environment: null, // 'android' or 'windows'
    direction: null,   // 'import' or 'export'
    connection: {
        type: null, // 'usb' or 'wireless'
        ip: null,
        pairing_port: null,
        pairing_code: null,
        connect_port: null,
        deviceA: null, // Serial của thiết bị A
        deviceB: null, // Serial của thiết bị B
    },
    windowsMode: null, // 'single_phone', 'two_phones' (chỉ dùng khi environment là 'windows')
    sourceDevice: null, // 'A' (local) or 'B' (remote)
    targetDevice: null, // 'A' (local) or 'B' (remote)
};

// Toast notification system
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    let typeClasses = '';
    switch (type) {
        case 'error':
            typeClasses = 'bg-red-600 text-white';
            break;
        case 'success':
            typeClasses = 'bg-green-600 text-white';
            break;
        case 'warning':
            typeClasses = 'bg-yellow-600 text-white';
            break;
        case 'info':
            typeClasses = 'bg-blue-600 text-white';
            break;
    }
    toast.className = `toast ${typeClasses} p-4 rounded-lg shadow-lg flex items-center justify-between gap-4`;
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '✕';
    closeBtn.className = 'text-lg cursor-pointer hover:opacity-75';
    closeBtn.onclick = () => toast.remove();
    
    toast.appendChild(messageSpan);
    toast.appendChild(closeBtn);
    container.appendChild(toast);
    
    if (duration > 0) {
        setTimeout(() => toast.remove(), duration);
    }
}

// Update step indicator
function updateStepIndicator(step) {
    for (let i = 1; i <= 4; i++) {
        const dot = document.getElementById(`step-indicator-${i}`);
        if (i < step) {
            dot.classList.add('completed');
            dot.classList.remove('active');
            dot.textContent = '✓';
        } else if (i === step) {
            dot.classList.add('active');
            dot.classList.remove('completed');
            dot.textContent = i;
        } else {
            dot.classList.remove('active', 'completed');
            dot.textContent = i;
        }
        
        if (i < step) {
            const line = document.getElementById(`step-line-${i}`);
            if (line) line.classList.add('active');
        } else {
            const line = document.getElementById(`step-line-${i}`);
            if (line) line.classList.remove('active');
        }
    }
}

function goToStep(stepNumber) {
    document.querySelectorAll('.step-container').forEach(div => {
        div.classList.remove('active');
    });
    document.getElementById(`step-${stepNumber}`).classList.add('active');
    updateStepIndicator(stepNumber);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function selectEnvironment(env) {
    transferState.environment = env;
    console.log('Environment selected:', env);

    if (env === 'windows') {
        buildStep2_WindowsModeSelection(); // Chuyển đến bước lựa chọn chế độ Windows
    } else {
        showToast(`Đã chọn môi trường: Android (Termux)`, 'success', 2000);
        goToStep(2);
    }
}

// Hàm mới để hiển thị lựa chọn chế độ Windows
function buildStep2_WindowsModeSelection() {
    const container = document.getElementById('step-2');
    container.innerHTML = `
        <h2 class="text-3xl font-bold mb-2 text-white">Bước 2: Chọn Chế Độ Hoạt Động (Windows)</h2>
        <p class="text-gray-400 mb-8">Bạn muốn Windows đóng vai trò gì?</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <button onclick="selectWindowsMode('single_phone')" class="bg-gradient-to-br from-gray-700 to-gray-800 hover:from-purple-600 hover:to-indigo-700 hover:text-white transition-all p-4 md:p-6 rounded-xl text-center shadow-lg hover:shadow-2xl transform hover:scale-105 cursor-pointer">
                <span class="text-5xl block mb-3">📱↔️💻</span>
                <h3 class="text-2xl font-bold mb-2">PC ↔️ Điện Thoại</h3>
                <p class="text-gray-300 text-sm mb-3">Sao lưu/Khôi phục dữ liệu Zalo giữa PC và một điện thoại.</p>
            </button>
            <button onclick="selectWindowsMode('two_phones')" class="bg-gradient-to-br from-gray-700 to-gray-800 hover:from-cyan-600 hover:to-blue-700 hover:text-white transition-all p-4 md:p-6 rounded-xl text-center shadow-lg hover:shadow-2xl transform hover:scale-105 cursor-pointer">
                <span class="text-5xl block mb-3">📱↔️💻↔️📱</span>
                <h3 class="text-2xl font-bold mb-2">Điện Thoại ↔️ Điện Thoại (qua PC)</h3>
                <p class="text-gray-300 text-sm mb-3">Chuyển dữ liệu Zalo giữa hai điện thoại, dùng PC làm trung gian.</p>
            </button>
        </div>
        <button onclick="goToStep(1)" class="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg transition-all duration-300 mt-8 w-full md:w-auto">← Quay lại</button>
    `;
    goToStep(2); // Vẫn ở bước 2 nhưng hiển thị nội dung khác
}

// Hàm xử lý lựa chọn chế độ Windows
function selectWindowsMode(mode) {
    transferState.windowsMode = mode;
    console.log('Windows mode selected:', mode);

    if (mode === 'single_phone') {
        showToast('Hiện tại chế độ này (Sao lưu/Khôi phục giữa PC và Điện Thoại) đang được nghiên cứu và chưa được hỗ trợ đầy đủ do sự khác biệt về cấu trúc dữ liệu. Vui lòng chọn chế độ khác hoặc sử dụng môi trường Android (Termux) để chuyển giữa hai điện thoại.', 'warning', 10000);
        buildStep2_WindowsModeSelection(); // Giữ người dùng ở đây để chọn lại
        return;
    }

    // Nếu là 'two_phones', chuyển sang bước chọn hướng (Xuất/Nhập)
    showToast(`Đã chọn chế độ: Điện Thoại ↔️ Điện Thoại (qua PC)`, 'success', 2000);
    // Hiển thị lại nội dung chọn hướng Xuất/Nhập.
    const step2Container = document.getElementById('step-2');
    step2Container.innerHTML = `
        <h2 class="text-3xl font-bold mb-2 text-white">Bước 2: Chọn Hướng Chuyển Dữ Liệu</h2>
        <p class="text-gray-400 mb-8">Bạn muốn xuất hay nhập dữ liệu?</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <button onclick="selectDirection('export')" class="bg-gradient-to-br from-gray-700 to-gray-800 hover:from-cyan-600 hover:to-blue-700 hover:text-white transition-all p-4 md:p-6 rounded-xl text-center shadow-lg hover:shadow-2xl transform hover:scale-105 cursor-pointer">
                <span class="text-5xl block mb-3">📤</span>
                <h3 class="text-2xl font-bold mb-2">Xuất Dữ Liệu</h3>
                <p class="text-gray-300 text-sm mb-3">Lấy dữ liệu từ Thiết bị A sang Thiết bị B.</p>
                <div class="bg-gray-700 rounded-lg p-2 text-cyan-400 font-mono text-sm">A ➜ B</div>
            </button>
            <button onclick="selectDirection('import')" class="bg-gradient-to-br from-gray-700 to-gray-800 hover:from-cyan-600 hover:to-blue-700 hover:text-white transition-all p-4 md:p-6 rounded-xl text-center shadow-lg hover:shadow-2xl transform hover:scale-105 cursor-pointer">
                <span class="text-5xl block mb-3">📥</span>
                <h3 class="text-2xl font-bold mb-2">Nhập Dữ Liệu</h3>
                <p class="text-gray-300 text-sm mb-3">Lấy dữ liệu từ Thiết bị B vào Thiết bị A.</p>
                <div class="bg-gray-700 rounded-lg p-2 text-cyan-400 font-mono text-sm">B ➜ A</div>
            </button>
        </div>
        <button onclick="buildStep2_WindowsModeSelection()" class="bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded-lg transition-all duration-300 mt-8 w-full md:w-auto">← Quay lại</button>
    `;
    goToStep(2);
}

function selectDirection(dir) {
    transferState.direction = dir;
    
    // Suy luận thiết bị nguồn và đích cho Android và Windows (chế độ two_phones)
    if (dir === 'export') {
        transferState.sourceDevice = 'A (Thiết bị nguồn)';
        transferState.targetDevice = 'B (Thiết bị nhận)';
    } else { // import
        transferState.sourceDevice = 'B (Thiết bị nguồn)';
        transferState.targetDevice = 'A (Thiết bị nhận)';
    }

    console.log('Direction selected:', dir);
    console.log('Source:', transferState.sourceDevice, 'Target:', transferState.targetDevice);
    showToast(`Đã chọn hướng: ${dir === 'export' ? 'Xuất Dữ Liệu' : 'Nhập Dữ Liệu'}`, 'success', 2000);
    
    buildStep3();
    goToStep(3);
}

function buildStep3() {
    if (transferState.environment === 'android') {
        buildStep3_Android_DeviceA();
    } else if (transferState.environment === 'windows' && transferState.windowsMode === 'two_phones') {
        buildStep3_Windows_DeviceA(); // Bắt đầu kết nối thiết bị A cho Windows
    }
}

function buildStep3_Android_DeviceA() {
    transferState.connection.type = 'wireless'; // Default connection type
    const container = document.getElementById('adb-connection-options');
    container.innerHTML = `
        <h2 class="text-3xl font-bold mb-2 text-white">Bước 3.1: Kết nối Thiết bị A (Máy chạy Tool)</h2>
        <p class="text-gray-400 mb-8">Do giới hạn bảo mật Android, tool cần kết nối ADB với chính nó. Hãy bật "Gỡ lỗi không dây" và nhập thông tin bên dưới.</p>
        <div id="wireless-form" class="bg-gray-700 p-6 rounded-xl mb-6 border border-gray-600">
            ${getWirelessFormHTML('connectDeviceA()', 'Ghép nối & Kết nối Thiết bị A')}
        </div>
        <div id="connection-status" class="mt-6"></div>
    `;
}

function buildStep3_Android_DeviceB() {
    const container = document.getElementById('adb-connection-options');
    container.innerHTML = `
        <h2 class="text-3xl font-bold mb-2 text-white">Bước 3.2: Kết nối Thiết bị B (Máy Nhận/Nguồn)</h2>
        <p class="text-gray-400 mb-8">Bây giờ, hãy nhập thông tin "Gỡ lỗi không dây" của thiết bị thứ hai.</p>
        <div id="wireless-form" class="bg-gray-700 p-6 rounded-xl mb-6 border border-gray-600">
            ${getWirelessFormHTML('connectDeviceB()', 'Ghép nối & Kết nối Thiết bị B')}
        </div>
        <div id="connection-status" class="mt-6"></div>
    `;
}

function buildStep3_Windows_DeviceA() {
    transferState.connection.type = 'wireless'; // Windows cũng dùng wireless debugging
    const container = document.getElementById('adb-connection-options');
    container.innerHTML = `
        <h2 class="text-3xl font-bold mb-2 text-white">Bước 3.1: Kết nối Thiết bị A (Nguồn/Đích)</h2>
        <p class="text-gray-400 mb-8">Kết nối điện thoại đầu tiên (Thiết bị A) với PC của bạn thông qua Wireless Debugging.</p>
        <div id="wireless-form" class="bg-gray-700 p-6 rounded-xl mb-6 border border-gray-600">
            ${getWirelessFormHTML('connectDeviceA()', 'Ghép nối & Kết nối Thiết bị A')}
        </div>
        <div id="connection-status" class="mt-6"></div>
    `;
}

function buildStep3_Windows_DeviceB() {
    const container = document.getElementById('adb-connection-options');
    container.innerHTML = `
        <h2 class="text-3xl font-bold mb-2 text-white">Bước 3.2: Kết nối Thiết bị B (Nguồn/Đích)</h2>
        <p class="text-gray-400 mb-8">Kết nối điện thoại thứ hai (Thiết bị B) với PC của bạn thông qua Wireless Debugging.</p>
        <div id="wireless-form" class="bg-gray-700 p-6 rounded-xl mb-6 border border-gray-600">
            ${getWirelessFormHTML('connectDeviceB()', 'Ghép nối & Kết nối Thiết bị B')}
        </div>
        <div id="connection-status" class="mt-6"></div>
    `;
}


function getWirelessFormHTML(buttonOnclick, buttonText) {
    return `
        <h3 class="text-lg font-bold mb-4 text-white">Cấu hình Wireless Debugging</h3>
        <div class="space-y-4">
            <div>
                <label for="device-ip" class="block text-sm font-medium text-gray-300 mb-2">Địa chỉ IP Thiết bị</label>
                <input type="text" id="device-ip" placeholder="ví dụ: 192.168.1.100" class="w-full bg-gray-700 border border-gray-600 rounded-lg shadow-sm py-3 px-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all">
            </div>
            <div>
                <label for="pairing-port" class="block text-sm font-medium text-gray-300 mb-2">Pairing Port</label>
                <input type="text" id="pairing-port" placeholder="ví dụ: 32867" class="w-full bg-gray-700 border border-gray-600 rounded-lg shadow-sm py-3 px-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all">
            </div>
            <div>
                <label for="pairing-code" class="block text-sm font-medium text-gray-300 mb-2">Pairing Code</label>
                <input type="text" id="pairing-code" placeholder="ví dụ: 123456" class="w-full bg-gray-700 border border-gray-600 rounded-lg shadow-sm py-3 px-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all">
            </div>
            <div>
                <label for="connect-port" class="block text-sm font-medium text-gray-300 mb-2">Connect Port</label>
                <input type="text" id="connect-port" placeholder="ví dụ: 41217" class="w-full bg-gray-700 border border-gray-600 rounded-lg shadow-sm py-3 px-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all">
            </div>
            <button onclick="${buttonOnclick}" class="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 text-white font-bold py-2 px-4 text-sm md:py-3 md:px-6 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 w-full">${buttonText}</button>
        </div>
    `;
}

async function connectDeviceA() {
    await performWirelessConnection('deviceA');
}
async function connectDeviceB() {
    await performWirelessConnection('deviceB');
}

async function performWirelessConnection(deviceKey) { // deviceKey là 'deviceA' hoặc 'deviceB'
    const ip = document.getElementById('device-ip').value;
    const pairing_port = document.getElementById('pairing-port').value;
    const pairing_code = document.getElementById('pairing-code').value;
    const connect_port = document.getElementById('connect-port').value;

    if (!ip || !pairing_port || !pairing_code || !connect_port) {
        showToast('Vui lòng điền đầy đủ tất cả các thông tin kết nối!', 'warning', 3000);
        return;
    }

    const statusDiv = document.getElementById('connection-status');
    statusDiv.innerHTML = `<p class="text-yellow-400 flex items-center gap-2"><span class="spinner">⏳</span> Đang thử ghép nối với ${ip}:${pairing_port}...</p>`;

    try {
        const pairResponse = await fetch(`${API_BASE_URL}/api/adb/pair`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, pairing_port, pairing_code, environment: transferState.environment }),
        });
        const pairResult = await pairResponse.json();

        if (!pairResult.success) {
            statusDiv.innerHTML = `<div class="bg-red-900/30 border border-red-700/50 rounded-lg p-4"><p class="text-red-400 font-semibold">✗ Ghép nối thất bại</p><pre class="text-red-300 text-xs mt-2">${pairResult.error}</pre></div>`;
            showToast('Ghép nối thất bại. Kiểm tra lại thông tin!', 'error', 3000);
            return;
        }

        statusDiv.innerHTML = `<p class="text-green-400 flex items-center gap-2"><span class="spinner">⏳</span> Ghép nối thành công! Đang kết nối...</p>`;

        const connectResponse = await fetch(`${API_BASE_URL}/api/adb/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, connect_port, environment: transferState.environment }),
        });
        const connectResult = await connectResponse.json();

        if (connectResult.success) {
            const deviceId = `${ip}:${connect_port}`;
            transferState.connection[deviceKey] = deviceId; // Lưu deviceId vào deviceA hoặc deviceB
            showToast(`Kết nối thành công ${deviceKey.toUpperCase()}: ${deviceId}`, 'success', 2000);

            if (deviceKey === 'deviceA') {
                // Sau khi kết nối Device A, chuyển sang kết nối Device B
                if (transferState.environment === 'android') {
                    setTimeout(() => buildStep3_Android_DeviceB(), 1000);
                } else if (transferState.environment === 'windows' && transferState.windowsMode === 'two_phones') {
                    setTimeout(() => buildStep3_Windows_DeviceB(), 1000);
                }
            } else if (deviceKey === 'deviceB') {
                // Sau khi kết nối Device B, chuyển sang Bước 4 (Tóm tắt & Thực thi)
                setTimeout(() => buildStep4(), 1000);
            }

        } else {
            statusDiv.innerHTML = `<div class="bg-red-900/30 border border-red-700/50 rounded-lg p-4"><p class="text-red-400 font-semibold">✗ Kết nối thất bại</p><p class="text-red-300 text-sm mt-2">${connectResult.error}</p></div>`;
            showToast('Kết nối thất bại. Thử lại!', 'error', 3000);
        }

    } catch (error) {
        statusDiv.innerHTML = `<div class="bg-red-900/30 border border-red-700/50 rounded-lg p-4"><p class="text-red-400 font-semibold">✗ Lỗi nghiêm trọng</p><p class="text-red-300 text-sm mt-2">${error.message}</p></div>`;
        showToast('Lỗi: ' + error.message, 'error', 3000);
    }
}


function buildStep4() {
    const summaryDiv = document.getElementById('transfer-summary');
    const directionText = transferState.direction === 'export' ? '📤 Xuất Dữ Liệu' : '📥 Nhập Dữ Liệu';
    const environmentText = transferState.environment === 'android' ? 'Android (Termux)' : 'Windows (PC)';

    let connectionSummaryHTML = '';
    // Hiển thị thông tin kết nối cho hai thiết bị A và B (cả Android và Windows)
    connectionSummaryHTML = `
        <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
            <span class="text-gray-400">Kết nối (Thiết bị A):</span>
            <span class="font-semibold text-cyan-400">📶 Wireless (${transferState.connection.deviceA})</span>
        </div>
        <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
            <span class="text-gray-400">Kết nối (Thiết bị B):</span>
            <span class="font-semibold text-cyan-400">📶 Wireless (${transferState.connection.deviceB})</span>
        </div>
    `;
    
    summaryDiv.innerHTML = `
        <div class="space-y-3">
            <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <span class="text-gray-400">Môi trường:</span>
                <span class="font-semibold text-cyan-400">${environmentText}</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <span class="text-gray-400">Hướng chuyển:</span>
                <span class="font-semibold text-cyan-400">${directionText}</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <span class="text-gray-400">Từ:</span>
                <span class="font-semibold text-blue-400">${transferState.sourceDevice}</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <span class="text-gray-400">Đến:</span>
                <span class="font-semibold text-blue-400">${transferState.targetDevice}</span>
            </div>
            ${connectionSummaryHTML}
        </div>
    `;
    goToStep(4);
}


document.addEventListener('DOMContentLoaded', () => {
    // Initial setup
    goToStep(1);
    
    document.getElementById('start-transfer-btn').addEventListener('click', async () => {
        const logContainer = document.getElementById('log-container');
        const progressContainer = document.getElementById('progress-container');
        const logOutput = document.getElementById('log-output');
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const startBtn = document.getElementById('start-transfer-btn');

        logContainer.classList.remove('hidden');
        progressContainer.classList.remove('hidden');
        logOutput.textContent = '';
        startBtn.disabled = true;
        startBtn.classList.add('opacity-50', 'cursor-not-allowed');

        const endpoint = `${API_BASE_URL}/api/transfer/${transferState.direction}`;
        
        logOutput.textContent = '🚀 Bắt đầu quá trình...\n';
        showToast('Bắt đầu chuyển dữ liệu...', 'info', 2000);
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(transferState)
            });
            const result = await response.json();
            
            logOutput.textContent += `${result.message || result.error}\n`;

            // Bắt đầu theo dõi status
            const intervalId = setInterval(async () => {
                try {
                    const statusResponse = await fetch(`${API_BASE_URL}/api/status`);
                    const statusResult = await statusResponse.json();
                    
                    const formattedProgress = statusResult.progress.toFixed(1);
                    progressBar.style.width = formattedProgress + '%';
                    progressText.textContent = formattedProgress + '%';
                    logOutput.textContent = statusResult.log;
                    logOutput.scrollTop = logOutput.scrollHeight;

                    if (statusResult.status === 'completed' || statusResult.status === 'failed') {
                        clearInterval(intervalId);
                        startBtn.disabled = false;
                        startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                        
                        if (statusResult.status === 'completed') {
                            logOutput.textContent += `\n✓ Quá trình hoàn tất thành công!`;
                            showToast('Chuyển dữ liệu thành công!', 'success', 4000);
                        } else {
                            logOutput.textContent += `\n✗ Quá trình thất bại!`;
                            showToast('Chuyển dữ liệu thất bại. Kiểm tra log để biết chi tiết!', 'error', 4000);
                        }
                    }
                } catch (error) {
                    console.error('Error fetching status:', error);
                }
            }, 250);

        } catch (error) {
            logOutput.textContent += `✗ Lỗi kết nối tới backend: ${error.message}\n`;
            showToast('Lỗi kết nối: ' + error.message, 'error', 3000);
            startBtn.disabled = false;
            startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    });
});