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
    },
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
        showToast('Môi trường Windows hiện đang được nghiên cứu và chưa được hỗ trợ đầy đủ. Vui lòng chọn Android (Termux).', 'warning', 5000);
        return; 
    }

    showToast(`Đã chọn môi trường: ${env === 'android' ? 'Android (Termux)' : 'Windows'}`, 'success', 2000);
    goToStep(2);
}

function selectDirection(dir) {
    transferState.direction = dir;
    
    // Suy luận thiết bị nguồn và đích
    if (dir === 'export') {
        transferState.sourceDevice = 'A (Thiết bị chạy tool)';
        transferState.targetDevice = 'B (Thiết bị nhận)';
    } else { // import
        transferState.sourceDevice = 'B (Thiết bị nguồn)';
        transferState.targetDevice = 'A (Thiết bị chạy tool)';
    }

    console.log('Direction selected:', dir);
    console.log('Source:', transferState.sourceDevice, 'Target:', transferState.targetDevice);
    showToast(`Đã chọn hướng: ${dir === 'export' ? 'Xuất Dữ Liệu' : 'Nhập Dữ Liệu'}`, 'success', 2000);
    
    buildStep3();
    goToStep(3);
}

function buildStep3() {
    // This function now acts as a router based on the environment.
    if (transferState.environment === 'android') {
        buildStep3_Android_DeviceA();
    } else {
        buildStep3_Default();
    }
}

function buildStep3_Default() {
    const container = document.getElementById('adb-connection-options');
    container.innerHTML = `
        <h2 class="text-3xl font-bold mb-2 text-white">Bước 3: Kết nối Thiết bị</h2>
        <p class="text-gray-400 mb-8">Chọn phương thức kết nối với thiết bị đích.</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <button onclick="selectConnectionType('usb')" class="bg-gradient-to-br from-gray-700 to-gray-800 hover:from-cyan-600 hover:to-blue-700 hover:text-white transition-all p-4 md:p-6 rounded-xl text-center shadow-lg hover:shadow-2xl transform hover:scale-105 cursor-pointer">
                <span class="text-5xl block mb-3">🔌</span>
                <h3 class="text-2xl font-bold mb-2">USB Debugging</h3>
                <p class="text-gray-300 text-sm">Kết nối qua cáp USB (nhanh hơn)</p>
            </button>
            <button onclick="showWirelessForm()" class="bg-gradient-to-br from-gray-700 to-gray-800 hover:from-cyan-600 hover:to-blue-700 hover:text-white transition-all p-4 md:p-6 rounded-xl text-center shadow-lg hover:shadow-2xl transform hover:scale-105 cursor-pointer">
                <span class="text-5xl block mb-3">📶</span>
                <h3 class="text-2xl font-bold mb-2">Wireless Debugging</h3>
                <p class="text-gray-300 text-sm">Kết nối không dây (linh hoạt hơn)</p>
            </button>
        </div>
        <div id="wireless-form" class="hidden bg-gray-700 p-6 rounded-xl mb-6 border border-gray-600"></div>
        <div id="connection-status" class="mt-6"></div>
    `;
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

function showWirelessForm() {
    const formContainer = document.getElementById('wireless-form');
    formContainer.classList.remove('hidden');
    formContainer.innerHTML = getWirelessFormHTML('connectDeviceB()', 'Ghép nối & Kết nối');
    formContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function selectConnectionType(type) {
    transferState.connection.type = type;
    if (type === 'usb') {
        const statusDiv = document.getElementById('connection-status');
        statusDiv.innerHTML = `<p class="text-yellow-400 flex items-center gap-2"><span class="spinner">⏳</span> Đang kiểm tra thiết bị USB...</p>`;
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/adb/check?environment=${transferState.environment}`);
            const result = await response.json();
            if (result.success && result.output.includes('device')) {
                // Find the first device serial
                const deviceId = result.output.split('\n').find(line => line.includes('device')).split('\t')[0];
                transferState.connection.deviceId = deviceId; // Store device ID
                statusDiv.innerHTML = `<div class="bg-green-900/30 border border-green-700/50 rounded-lg p-4"><p class="text-green-400 font-semibold">✓ Thiết bị đã kết nối qua USB</p><pre class="text-xs text-green-300 mt-2">${result.output}</pre></div>`;
                showToast('Thiết bị USB đã được phát hiện!', 'success', 2000);
                setTimeout(() => buildStep4(), 1500);
            } else {
                statusDiv.innerHTML = `<div class="bg-red-900/30 border border-red-700/50 rounded-lg p-4"><p class="text-red-400 font-semibold">✗ Không tìm thấy thiết bị USB</p><p class="text-red-300 text-sm mt-2">Hãy đảm bảo bạn đã bật USB Debugging trên thiết bị.</p></div>`;
                showToast('Không tìm thấy thiết bị USB. Kiểm tra kết nối!', 'error', 3000);
            }
        } catch (error) {
            statusDiv.innerHTML = `<div class="bg-red-900/30 border border-red-700/50 rounded-lg p-4"><p class="text-red-400 font-semibold">✗ Lỗi kết nối</p><p class="text-red-300 text-sm mt-2">${error.message}</p></div>`;
            showToast('Lỗi kết nối: ' + error.message, 'error', 3000);
        }
    }
}

async function connectDeviceA() {
    await performWirelessConnection(true);
}
async function connectDeviceB() {
    await performWirelessConnection(false);
}

async function performWirelessConnection(isDeviceA) {
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
            
            if (isDeviceA) {
                transferState.connection.deviceA = deviceId;
                 showToast(`Kết nối thành công Thiết bị A: ${deviceId}`, 'success', 2000);
                setTimeout(() => buildStep3_Android_DeviceB(), 1000);
            } else {
                transferState.connection.deviceB = deviceId;
                 showToast(`Kết nối thành công Thiết bị B: ${deviceId}`, 'success', 2000);
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
    const environmentText = transferState.environment === 'android' ? 'Android (Termux)' : 'Windows';

    let connectionSummaryHTML = '';
    if (transferState.environment === 'android') {
        connectionSummaryHTML = `
            <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <span class="text-gray-400">Kết nối (Máy A):</span>
                <span class="font-semibold text-cyan-400">📶 Wireless (${transferState.connection.deviceA})</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <span class="text-gray-400">Kết nối (Máy B):</span>
                <span class="font-semibold text-cyan-400">📶 Wireless (${transferState.connection.deviceB})</span>
            </div>
        `;
    } else {
        connectionSummaryHTML = `
            <div class="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                <span class="text-gray-400">Kết nối:</span>
                <span class="font-semibold text-cyan-400">${transferState.connection.type === 'usb' ? `🔌 USB (${transferState.connection.deviceId})` : `📶 Wireless (${transferState.connection.ip})`}</span>
            </div>
        `;
    }
    
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
