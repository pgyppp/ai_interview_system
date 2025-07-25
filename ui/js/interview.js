document.addEventListener('DOMContentLoaded', function() {
    // Debug: Check if the context is secure
    console.log("Is Secure Context (required for getUserMedia):", window.isSecureContext);

    // 开始面试按钮事件监听
    document.getElementById('start-interview-btn').addEventListener('click', async function() {
        const interviewType = document.getElementById('interview-type').value;
        const positionType = document.getElementById('position-type').value;
        console.log(`Selected Interview Type: ${interviewType}`);
        console.log(`Selected Position Type: ${positionType}`);
        // 将职位类型存储到 sessionStorage，以便报告页面使用
        let interviewResults = JSON.parse(sessionStorage.getItem('interviewResults') || '{}');
        interviewResults.job_type = positionType;
        sessionStorage.setItem('interviewResults', JSON.stringify(interviewResults));
        // 禁用按钮，防止重复点击
        this.disabled = true;
        this.textContent = '正在生成问题...';
        try {
            const response = await fetch('/generate_questions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    interview_type: interviewType,
                    job_type: positionType
                })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Generated Questions:', data.questions);
            console.log('Audio Paths:', data.audio_paths);
            // 显示问题列表
            displayQuestions(data.questions, data.audio_paths);
        } catch (error) {
            console.error('生成问题失败:', error);
            alert('生成问题失败，请稍后再试。');
        } finally {
            // 重新启用按钮
            this.disabled = false;
            this.textContent = '生成面试题目并面试';
        }
    });
});

function displayQuestions(questions, audioPaths) {
    const questionsContainer = document.getElementById('questions-container');
    const interviewSettings = document.getElementById('interview-settings');
    const initialView = document.getElementById('initial-view');
    const interviewView = document.getElementById('interview-view');

    // 清空现有内容并隐藏面试设置
    questionsContainer.innerHTML = '';
    initialView.classList.add('hidden'); // 隐藏初始视图
    interviewView.classList.remove('hidden'); // 显示面试视图
    interviewSettings.classList.add('hidden');
    questionsContainer.classList.remove('hidden');
    questions.forEach((question, index) => {
        const audioPath = audioPaths[index].replace(/\\/g, '/');
        const questionElement = document.createElement('div');
        questionElement.className = 'bg-white rounded-xl shadow-card p-6 mb-4';
        questionElement.innerHTML = `
            <div class="flex items-center justify-between">
                <p class="text-lg font-medium text-dark">${index + 1}. ${question}</p>
                <button onclick="playQuestion('${audioPath}')" class="p-2 rounded-full text-primary hover:bg-primary/10 focus:outline-none">
                    <i class="fa fa-play"></i>
                </button>
            </div>
        `;
        questionsContainer.appendChild(questionElement);
    });
}

function playQuestion(audioPath) {
    const audio = new Audio(audioPath.replace(/\\/g, '/'));
    audio.play().catch(e => console.error("音频播放失败:", e));
}

// 视频录制功能
let mediaRecorder;
let recordedChunks = [];

document.getElementById('start-record-btn').addEventListener('click', async function() {
    // --- 更严格的检查 ---
    // 1. 检查 API 是否存在
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('浏览器不支持 navigator.mediaDevices.getUserMedia API。');
        alert('您的浏览器不支持访问摄像头和麦克风。请尝试使用最新版的 Chrome、Firefox 或 Edge。');
        return;
    }
    // 2. 检查是否在安全上下文中 (HTTPS 或 localhost)
    if (!window.isSecureContext) {
        console.error('getUserMedia 需要在安全上下文中运行 (HTTPS 或 localhost)。当前协议:', window.location.protocol);
        alert('视频录制功能需要在安全连接下使用。\n' +
              '请通过 HTTPS (例如 https://yourdomain.com/page) 或本地开发环境 (例如 http://localhost:8000/page) 访问此页面。');
        return;
    }
    // --- 检查结束 ---

    try {
        // 请求音视频权限
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: true
        });
        // 显示预览视频，隐藏占位符
        document.getElementById('preview-video').srcObject = stream;
        document.getElementById('video-placeholder').classList.add('hidden');
        // 开始录制
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = []; // 确保每次开始录制时都清空旧数据
        mediaRecorder.ondataavailable = function(e) {
            if (e.data.size > 0) {
                recordedChunks.push(e.data);
            }
        };
        mediaRecorder.onstop = function() {
            const blob = new Blob(recordedChunks, {
                type: 'video/webm'
            });
            const videoUrl = URL.createObjectURL(blob);
            document.getElementById('recorded-video').src = videoUrl;
            document.getElementById('video-processing').classList.remove('hidden');
            document.getElementById('video-controls').classList.add('hidden');
            // 上传视频到后端
            uploadVideo(blob, 'recorded_video.webm');
        };
        mediaRecorder.start();
        this.classList.add('hidden');
        document.getElementById('stop-record-btn').classList.remove('hidden');
    } catch (error) {
        console.error('获取媒体设备失败:', error);
        // 区分用户拒绝权限和其它错误
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
             alert('无法访问摄像头或麦克风。请确保已授予权限，并允许浏览器访问这些设备。');
        } else if (error.name === 'NotFoundError' || error.name === 'OverconstrainedError') {
             alert('找不到可用的摄像头或麦克风。请检查设备是否连接正确。');
        } else {
             alert('启动摄像头或麦克风时发生未知错误: ' + error.message);
        }
        // 重置按钮状态以防万一
        this.classList.remove('hidden');
        document.getElementById('stop-record-btn').classList.add('hidden');
        document.getElementById('video-placeholder').classList.remove('hidden');
        document.getElementById('preview-video').srcObject = null;
    }
});

document.getElementById('stop-record-btn').addEventListener('click', function() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        this.classList.add('hidden');
        document.getElementById('start-record-btn').classList.remove('hidden');
        document.getElementById('video-processing').classList.remove('hidden');
        // 模拟处理进度
        let progress = 0;
        const progressBar = document.getElementById('progress-bar');
        const statusText = document.getElementById('processing-status');
        const interval = setInterval(() => {
            progress += 5;
            progressBar.style.width = `${progress}%`;
            if (progress < 30) {
                statusText.textContent = '正在上传视频...';
            } else if (progress < 70) {
                statusText.textContent = 'AI分析中...';
            } else if (progress < 90) {
                statusText.textContent = '生成评估报告...';
            } else {
                statusText.textContent = '处理完成！';
            }
            if (progress >= 100) {
                clearInterval(interval);
            }
        }, 200);
        // 停止录制后，立即开始上传和处理
        // mediaRecorder.onstop 中已经包含了上传逻辑，这里不需要重复调用
        // 确保 mediaRecorder.onstop 逻辑正确触发即可
    }
});

document.getElementById('upload-video-btn').addEventListener('click', function() {
    document.getElementById('video-file-input').click();
});

document.getElementById('video-file-input').addEventListener('change', function(e) {
    if (e.target.files && e.target.files[0]) {
        const file = e.target.files[0];
        if (file.type.startsWith('video/')) {
            const videoUrl = URL.createObjectURL(file);
            document.getElementById('recorded-video').src = videoUrl;
            document.getElementById('video-processing').classList.remove('hidden');
            document.getElementById('video-controls').classList.add('hidden');
            // 调用上传函数
            uploadVideo(file, file.name);
        } else {
            alert('请选择视频文件');
        }
    }
});

document.getElementById('play-video-btn').addEventListener('click', function() {
    const video = document.getElementById('recorded-video');
    if (video.paused) {
        video.play();
        this.innerHTML = '<i class="fa fa-pause mr-2"></i> 暂停';
    } else {
        video.pause();
        this.innerHTML = '<i class="fa fa-play mr-2"></i> 播放';
    }
});

document.getElementById('retry-record-btn').addEventListener('click', function() {
    document.getElementById('video-controls').classList.add('hidden');
    document.getElementById('video-placeholder').classList.remove('hidden');
    document.getElementById('preview-video').srcObject = null;
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    recordedChunks = [];
});

document.getElementById('submit-video-btn').addEventListener('click', function() {
    // 提交评估到后端API
    alert('评估已提交，结果将显示在报告中心');
    window.location.href = 'reports.html';
});

async function uploadVideo(videoBlob, filename) {
    const formData = new FormData();
    formData.append('file', videoBlob, filename);
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('processing-status');
    // 重置进度条
    progressBar.style.width = '0%';
    statusText.textContent = '正在上传视频...';
    try {
        const uploadResponse = await fetch('/upload_video/', {
            method: 'POST',
            body: formData,
        });
        if (!uploadResponse.ok) {
            throw new Error(`HTTP error! status: ${uploadResponse.status}`);
        }
        const uploadData = await uploadResponse.json();
        console.log('视频上传成功:', uploadData);
        // 视频上传成功后，调用后端接口进行AI分析
        processInterview(uploadData.file_path.replace(/\\/g, '/'));
    } catch (error) {
        console.error('视频上传失败:', error);
        alert('视频上传失败，请检查网络或稍后再试。');
        document.getElementById('video-processing').classList.add('hidden');
        document.getElementById('video-controls').classList.remove('hidden');
    }
}

async function processInterview(videoPath) {
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('processing-status');
    // 更新状态文本
    statusText.textContent = 'AI分析中...';
    // 视频上传完成，进度条设置为30%
    progressBar.style.width = '30%';
    statusText.textContent = 'AI分析中... (视频处理中)';
    try {
        const processResponse = await fetch('/process_interview/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_path: videoPath,
                frame_interval: 8, // 默认值
                job_type: document.getElementById('position-type').value || 'python_engineer' // 从下拉菜单获取或使用默认值
            })
        });
        if (!processResponse.ok) {
            throw new Error(`HTTP error! status: ${processResponse.status}`);
        }
        const processData = await processResponse.json();
        console.log('面试处理结果:', processData);
        // 视频处理完成，进度条设置为70%
        progressBar.style.width = '70%';
        statusText.textContent = 'AI分析中... (对话分析中)';
        // 调用 /start_conversation/ 接口获取初始对话内容和对话历史
        const conversationResponse = await fetch('/start_conversation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_result: processData.image_result,
                speech_result: processData.speech_result,
                text_result: processData.text_result,
                model_predictions: processData.model_predictions,
                conversation_history: []
            })
        });
        if (!conversationResponse.ok) {
            throw new Error(`HTTP error! status: ${conversationResponse.status}`);
        }
        const conversationData = await conversationResponse.json();
        console.log('初始对话结果:', conversationData);
        // 对话分析完成，进度条设置为100%
        progressBar.style.width = '100%';
        statusText.textContent = '处理完成！';
        // 将结果存储在 sessionStorage 中，以便报告页面获取
        const jobType = document.getElementById('position-type').value || 'python_engineer';
        processData.job_type = jobType;
        processData.conversation_analysis = conversationData.conversation_history.map(entry => `[${entry.role}]: ${entry.content}`);
        sessionStorage.setItem('interviewResults', JSON.stringify(processData));
        sessionStorage.setItem('storedDataForAnalysis', JSON.stringify(processData));
        setTimeout(() => {
            document.getElementById('video-processing').classList.add('hidden');
            document.getElementById('video-controls').classList.remove('hidden');
            // 跳转到报告页面
            window.location.href = 'reports.html';
        }, 1000);
    } catch (error) {
        console.error('面试处理失败:', error);
        alert('面试处理失败，请稍后再试。');
        progressBar.style.width = '0%'; // 重置进度条
        document.getElementById('video-processing').classList.add('hidden');
        document.getElementById('video-controls').classList.remove('hidden');
    }
}
