/**
 * 页面加载完成后执行初始化
 */
document.addEventListener('DOMContentLoaded', async function () {
    try {
        await loadReportData();
        // 下载报告按钮事件监听
        const downloadBtn = document.getElementById('download-report-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', handleDownloadReport);
        }
        // 分享报告按钮事件监听
        const shareBtn = document.getElementById('share-report-btn');
        if (shareBtn) {
            shareBtn.addEventListener('click', () => {
                alert('分享功能将在未来版本中推出');
            });
        }
    } catch (error) {
        console.error('初始化页面时发生错误:', error);
        alert('加载报告失败，请刷新页面重试。');
    }
});

/**
 * 处理报告下载逻辑
 */
async function handleDownloadReport() {
    const downloadBtn = document.getElementById('download-report-btn');
    const originalBtnText = downloadBtn.innerHTML;
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 正在生成报告...';
    try {
        const interviewResults = JSON.parse(sessionStorage.getItem('interviewResults') || '{}');
        if (!interviewResults || Object.keys(interviewResults).length === 0) {
            alert('没有找到面试结果数据，无法生成报告。');
            return;
        }
        // 准备发送到后端的数据
        const requestData = {
            job_type: interviewResults.job_type || '未知职位',
            image_result: interviewResults.image_result || '',
            speech_result: interviewResults.speech_result || '',
            text_result: interviewResults.text_result || '',
            conversation_history: interviewResults.conversation_analysis || [], // 注意：后端可能期望 List[str] 或 List[Dict]
            model_predictions: interviewResults.model_predictions || {},
            processed_frame_paths: interviewResults.processed_frame_paths || [],
            processed_audio_path: interviewResults.processed_audio_path || '',
            processed_text_content_path: interviewResults.processed_text_content_path || ''
        };

        // --- 修正：发送到 /analyze_for_report/ 生成雷达图数据 ---
        // 1. 先调用 /analyze_for_report/ 获取雷达图HTML (如果后端能直接生成)
        //    或者调用 /generate_radar_chart/ (如果这是独立的端点)
        // 移除对 /generate_radar_chart/ 的独立调用，雷达图路径将从 /generate_report/ 的响应中获取
        // let radarChartHtml = ''; // 不再需要这个变量，直接从 result 中获取路径

        // 2. 然后调用 /generate_report/ 生成PDF
        const response = await fetch('/generate_report/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`HTTP错误! 状态码: ${response.status}`);
        }

        const result = await response.json();
        const pdfFilePath = result.pdf_file_path;
        const radarChartPath = result.radar_chart_path; // 从后端获取雷达图路径

        if (pdfFilePath) {
            // 触发文件下载
            const link = document.createElement('a');
            link.href = pdfFilePath;
            link.download = `AI面试报告_${interviewResults.job_type || '未知职位'}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            alert('报告下载成功！');
        } else {
            alert('报告生成成功，但未获取到下载链接。');
        }

        // 3. 显示雷达图 (使用从后端获取的路径)
        if (radarChartPath) {
            displayRadarChart(radarChartPath); // 调用现有函数来显示雷达图
        } else {
            console.log("未能获取到雷达图内容进行显示。");
        }

    } catch (error) {
        console.error('下载报告时发生错误:', error);
        alert('下载报告失败，请稍后再试。');
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = originalBtnText;
    }
}

// 修改函数：用于显示后端生成的雷达图
function displayRadarChart(chartPath) {
    const container = document.getElementById('radar-chart-container');
    if (container) {
        // 清空旧内容
        container.innerHTML = '';
        // 创建一个iframe来加载雷达图HTML
        const iframe = document.createElement('iframe');
        iframe.src = chartPath;
        iframe.style.width = '100%';
        iframe.style.height = '400px'; // 根据需要调整高度
        iframe.style.border = 'none';
        container.appendChild(iframe);
    } else {
        console.warn('雷达图容器未找到');
    }
}

/**
 * 从 sessionStorage 加载报告数据并渲染页面
 */
async function loadReportData() {
    // 从sessionStorage获取数据，不使用模拟数据
    let interviewResults = JSON.parse(sessionStorage.getItem('interviewResults') || '{}');
    console.log('从 sessionStorage 获取的 interviewResults:', interviewResults);

    // 检查数据是否存在
    const dataExists = interviewResults && Object.keys(interviewResults).length > 0 && interviewResults.overall_score !== undefined;
    console.log('dataExists:', dataExists);

    // 如果数据不存在或不完整，尝试从后端获取
    if (!dataExists) {
        console.warn('sessionStorage中未找到面试结果数据，尝试从后端获取');
        try {
            const storedDataForAnalysis = JSON.parse(sessionStorage.getItem('storedDataForAnalysis') || '{}');
            // 检查是否有必要的初始分析数据
            if (!storedDataForAnalysis || Object.keys(storedDataForAnalysis).length === 0 ||
                !storedDataForAnalysis.image_result || Object.keys(storedDataForAnalysis.image_result).length === 0 ||
                !storedDataForAnalysis.speech_result || Object.keys(storedDataForAnalysis.speech_result).length === 0 ||
                !storedDataForAnalysis.text_result || Object.keys(storedDataForAnalysis.text_result).length === 0 ||
                !storedDataForAnalysis.model_predictions || storedDataForAnalysis.model_predictions.length === 0) {
                console.error("sessionStorage中缺少初始分析数据，无法从后端获取完整报告");
                // 不使用模拟数据，保持interviewResults为空
            } else {
                // 从后端获取完整报告数据
                const response = await fetch('/analyze_for_report/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        job_type: interviewResults?.job_type || storedDataForAnalysis?.job_type || 'python_engineer',
                        image_result: storedDataForAnalysis.image_result,
                        speech_result: storedDataForAnalysis.speech_result,
                        text_result: storedDataForAnalysis.text_result,
                        conversation_history: storedDataForAnalysis.conversation_analysis || [], // 注意类型匹配
                        model_predictions: storedDataForAnalysis.model_predictions,
                        processed_frame_paths: storedDataForAnalysis.processed_frame_paths || [],
                        processed_audio_path: storedDataForAnalysis.processed_audio_path || '',
                        processed_text_content_path: storedDataForAnalysis.processed_text_content_path || ''
                    })
                });
                if (!response.ok) {
                    throw new Error(`HTTP错误! 状态码: ${response.status}`);
                }
                const fullReportData = await response.json();
                console.log('从后端获取的 fullReportData:', fullReportData);
                // 合并数据
                interviewResults = { ...interviewResults, ...fullReportData };
                sessionStorage.setItem('interviewResults', JSON.stringify(interviewResults));
                console.log("从后端获取完整报告数据成功，合并后的 interviewResults:", interviewResults);
            }
        } catch (error) {
            console.error('从后端获取完整报告数据失败:', error);
            // 不使用模拟数据，保持interviewResults为空或现有值
        }
    }

    // --- **关键修改：初始化对话历史** ---
    // 在渲染数据之前，初始化用于AI对话的 conversationHistory
    window.currentConversationHistory = []; // 使用 window 对象存储全局状态
    const conversationContainer = document.getElementById('conversation-analysis');
    if (conversationContainer) {
        conversationContainer.innerHTML = ''; // 清空容器
    }

    // 将从 sessionStorage 或后端获取的 conversation_analysis 作为初始历史加载
    if (interviewResults.conversation_analysis && Array.isArray(interviewResults.conversation_analysis) && interviewResults.conversation_analysis.length > 0) {
        // interviewResults.conversation_analysis 格式是 [{ speaker: 'AI/User', text: '...' }, ...]
        interviewResults.conversation_analysis.forEach(msgObj => {
            if (msgObj && typeof msgObj === 'object' && msgObj.speaker && msgObj.text !== undefined) {
                // 转换为后端 /chat_with_ai/ 期望的格式 { role: 'user/assistant', content: '...' }
                const role = msgObj.speaker.toLowerCase() === 'user' ? 'user' : 'assistant'; // 标准化角色名
                window.currentConversationHistory.push({ role: role, content: msgObj.text });
                // 同时渲染到页面上
                appendMessageToContainer(msgObj.speaker, msgObj.text);
            } else if (typeof msgObj === 'string') {
                 // 如果是字符串，尝试解析或直接显示（兼容旧格式）
                 console.warn('Received conversation_analysis item as string:', msgObj);
                 let speaker = 'Unknown';
                 let text = msgObj;
                 if (msgObj.toLowerCase().startsWith('ai:')) {
                     speaker = 'AI';
                     text = msgObj.substring(3).trim();
                 } else if (msgObj.toLowerCase().startsWith('user:')) {
                      speaker = 'User';
                      text = msgObj.substring(5).trim();
                 }
                 const role = speaker.toLowerCase() === 'user' ? 'user' : 'assistant';
                 window.currentConversationHistory.push({ role: role, content: text });
                 appendMessageToContainer(speaker, text);
            }
        });
    } else {
         console.log("没有初始对话历史可供加载。");
         // 可以选择显示一条AI的欢迎消息
         appendMessageToContainer('AI', '你好！我是你的AI面试助手。你可以问我关于这份评估报告的任何问题。');
    }

    // 渲染页面数据（无论数据是否存在）
    renderReportData(interviewResults || {});
}

/**
 * 渲染报告数据到页面
 * @param {Object} interviewResults - 面试结果数据对象
 */
function renderReportData(interviewResults) {
    // 更新报告日期（始终显示当前日期）
    const reportDateElement = document.getElementById('report-date');
    if (reportDateElement) {
        reportDateElement.textContent = new Date().toLocaleString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    // 更新职位类型
    const jobTypeElement = document.getElementById('job-type-display');
    if (jobTypeElement) {
        jobTypeElement.textContent = interviewResults.job_type || '暂无职位信息';
    }
    // 渲染总分
    const overallScoreElement = document.getElementById('overall-score');
    if (overallScoreElement) {
        overallScoreElement.innerText = interviewResults.overall_score !== undefined
            ? interviewResults.overall_score
            : '暂无';
    }
    // 更新总分和环形进度条
    if (interviewResults.overall_score !== undefined) {
        updateTotalScore(interviewResults.overall_score);
    } else {
        // 清除进度条
        const progressPath = document.getElementById('score-progress');
        if (progressPath) {
            progressPath.style.strokeDasharray = '';
            progressPath.style.strokeDashoffset = '';
        }
        // 更新反馈文字
        const feedbackElement = document.getElementById('overall-feedback');
        if (feedbackElement) {
            feedbackElement.textContent = "暂无评分";
        }
    }
    // 渲染评分明细
    const scoreDetailsElement = document.getElementById('score-details');
    if (scoreDetailsElement) {
        if (interviewResults.score_details && Object.keys(interviewResults.score_details).length > 0) {
            scoreDetailsElement.innerHTML = Object.entries(interviewResults.score_details)
                .map(([key, value]) => `<p><strong>${key}:</strong> ${value}</p>`)
                .join('');
            // 更新评分详情进度条
            updateScoreDetails(interviewResults.score_details);
        } else {
            scoreDetailsElement.innerText = '暂无评分明细。';
        }
    }
    // 渲染 AI 综合评价
    const aiAnalysisContentElement = document.getElementById('ai-analysis-content');
    if (aiAnalysisContentElement) {
        if (interviewResults.ai_analysis && Object.keys(interviewResults.ai_analysis).length > 0) {
            let aiAnalysisHtml = '';
            if (interviewResults.ai_analysis['综合评价']) {
                aiAnalysisHtml += `<p><strong>综合评价:</strong> ${interviewResults.ai_analysis['综合评价']}</p>`;
            }
            if (interviewResults.ai_analysis['优势']) {
                aiAnalysisHtml += `<p><strong>优势:</strong> ${interviewResults.ai_analysis['优势']}</p>`;
            }
            if (interviewResults.ai_analysis['待改进']) {
                aiAnalysisHtml += `<p><strong>待改进:</strong> ${interviewResults.ai_analysis['待改进']}</p>`;
            }
            aiAnalysisContentElement.innerHTML = aiAnalysisHtml || '暂无 AI 综合评价。';
        } else {
            aiAnalysisContentElement.innerText = '暂无 AI 综合评价。';
        }
        // 更新关键亮点
        updateKeyHighlights(interviewResults.ai_analysis);
    }
    // 渲染辅助多模态模型量化分数
    const modelPredictionsElement = document.getElementById('model-predictions-content');
    if (modelPredictionsElement) {
        if (interviewResults.model_predictions && Object.keys(interviewResults.model_predictions).length > 0) {
            const predictionLabels = {
                "proficiency": "熟练度",
                "frameworks": "框架",
                "optimization": "优化",
                "versioning": "版本控制",
                "involvement": "投入度",
                "impact": "影响力",
                "outcomes": "成果",
                "logic": "逻辑",
                "communication": "沟通",
                "solving": "解决问题",
                "learning": "学习能力"
            };
            let predictionsHtml = '<div class="grid grid-cols-2 gap-2">';
            for (const key in interviewResults.model_predictions) {
                if (interviewResults.model_predictions.hasOwnProperty(key)) {
                    const label = predictionLabels[key] || key; // 使用中文标签，如果没有则使用原始键名
                    const value = (interviewResults.model_predictions[key] * 100).toFixed(2); // 转换为百分比，保留两位小数
                    predictionsHtml += `<div class="flex justify-between items-center bg-white p-2 rounded-md shadow-sm"><span class="text-sm font-medium text-dark-light">${label}:</span><span class="text-sm font-bold text-primary">${value}%</span></div>`;
                }
            }
            predictionsHtml += '</div>';
            modelPredictionsElement.innerHTML = predictionsHtml;
        } else {
            modelPredictionsElement.innerText = '暂无模型预测数据。';
        }
    }

    // --- **注意**: conversation-analysis 容器的内容现在在 loadReportData 中处理 ---
    // 渲染 AI 对话分析 (初始历史已加载，此处无需重复)
    // const conversationAnalysisElement = document.getElementById('conversation-analysis');
    // if (conversationAnalysisElement) {
    //     if (interviewResults.conversation_analysis && interviewResults.conversation_analysis.length > 0) {
    //         updateConversationAnalysis(interviewResults.conversation_analysis); // 始终调用此函数处理
    //     } else {
    //         conversationAnalysisElement.innerText = '暂无对话分析数据。';
    //     }
    // }

    // 渲染AI分析与建议
    updateAiAnalysis(interviewResults);

    // 渲染能力雷达图 (如果后端直接返回了HTML或路径)
    // const radarChartPath = interviewResults.radar_chart_path;
    // if (radarChartPath) {
    //     displayRadarChart(radarChartPath);
    // } else {
    const radarChartPath = interviewResults.radar_chart_path; // 假设后端返回路径
    if (radarChartPath) {
        displayRadarChart(radarChartPath);
    } else {
        const container = document.getElementById('radar-chart-container');
        if (container) {
            container.innerText = '点击下载报告生成能力雷达图。';
        }
    }
    // }
}

/**
 * 更新总分和环形进度条
 * @param {number} score - 总分 (0-100)
 */
function updateTotalScore(score) {
    const totalScoreElement = document.getElementById('total-score-text');
    const progressPath = document.getElementById('score-progress');
    if (!totalScoreElement || !progressPath) {
        console.warn('总分或进度条元素未找到');
        return;
    }
    // 确保分数在0-100范围内
    const normalizedScore = Math.max(0, Math.min(100, score));
    totalScoreElement.textContent = normalizedScore;
    const circumference = 2 * Math.PI * 15.9155; // SVG 中圆的周长
    const offset = circumference - (normalizedScore / 100) * circumference;
    progressPath.style.strokeDasharray = circumference;
    progressPath.style.strokeDashoffset = offset;
    // 根据分数更新反馈文字
    const feedbackElement = document.getElementById('overall-feedback');
    if (feedbackElement) {
        if (normalizedScore >= 90) {
            feedbackElement.textContent = "卓越";
        } else if (normalizedScore >= 80) {
            feedbackElement.textContent = "优秀";
        } else if (normalizedScore >= 70) {
            feedbackElement.textContent = "良好";
        } else if (normalizedScore >= 60) {
            feedbackElement.textContent = "及格";
        } else {
            feedbackElement.textContent = "待提高";
        }
    }
}

/**
 * 更新评分明细
 * @param {Object} details - 包含各维度分数的对象
 */
function updateScoreDetails(details) {
    const container = document.getElementById('score-details');
    if (!container) {
        console.warn('评分明细容器未找到');
        return;
    }
    container.innerHTML = ''; // 清空容器
    if (!details || typeof details !== 'object' || Object.keys(details).length === 0) {
        container.innerHTML = '<p class="text-sm text-dark-light">暂无评分详情。</p>';
        return;
    }
    Object.entries(details).forEach(([category, score]) => {
        // 确保分数是有效的数字
        const validScore = typeof score === 'number' ? Math.max(0, Math.min(100, score)) : 0;
        const detailItem = `
            <div>
                <div class="flex justify-between mb-1">
                    <span class="text-sm text-dark-light">${category}</span>
                    <span class="text-sm font-medium text-dark">${validScore}</span>
                </div>
                <div class="w-full bg-light-gray rounded-full h-2">
                    <div class="bg-primary h-2 rounded-full" style="width: ${validScore}%"></div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', detailItem);
    });
}

/**
 * 更新关键亮点（AI综合评价）
 * @param {Object} aiAnalysis - AI综合评价对象
 */
function updateKeyHighlights(aiAnalysis) {
    const container = document.getElementById('key-highlights');
    if (!container) {
        console.warn('关键亮点容器未找到');
        return;
    }
    container.innerHTML = '';
    if (!aiAnalysis || typeof aiAnalysis !== 'object' || Object.keys(aiAnalysis).length === 0) {
        container.innerHTML = '<p class="text-sm text-dark-light">暂无AI综合评价。</p>';
        return;
    }
    // 遍历AI分析结果
    for (const key in aiAnalysis) {
        if (aiAnalysis.hasOwnProperty(key) && aiAnalysis[key]) {
            const item = `
                <div class="flex items-start mb-2">
                    <div class="flex-shrink-0 mt-1">
                        <i class="fa fa-lightbulb-o text-primary"></i>
                    </div>
                    <p class="ml-3 text-sm text-dark"><strong>${key}:</strong> ${aiAnalysis[key]}</p>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', item);
        }
    }
}

/**
 * 更新AI分析与建议
 * @param {Object} results - 面试结果对象
 */
function updateAiAnalysis(results) {
    const container = document.getElementById('ai-analysis');
    const predictionsDisplay = document.getElementById('model-predictions-content');
    if (!container || !predictionsDisplay) {
        console.warn('AI分析容器或模型预测容器未找到');
        return;
    }
    container.innerHTML = '';
    let hasContent = false;
    // 添加分析项的辅助函数
    function addAnalysisItem(title, content) {
        if (content && typeof content === 'string' && content.trim() !== '') {
            const item = `
                <div class="mb-4 last:mb-0">
                    <h4 class="font-medium text-dark mb-2">${title}</h4>
                    <div class="text-dark-light prose prose-sm max-w-none">${marked.parse(content)}</div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', item);
            hasContent = true;
        }
    }
    // 添加核心分析 (来自 ai_analysis)
    if (results.ai_analysis && typeof results.ai_analysis === 'object') {
        for (const [section, content] of Object.entries(results.ai_analysis)) {
            addAnalysisItem(section, content);
        }
    }
    // 添加多模态分析结果
    addAnalysisItem('图像分析结果', results.image_result);
    addAnalysisItem('语音分析结果', results.speech_result);
    addAnalysisItem('文本内容评估结果', results.text_result);
    // 显示模型预测分数
    if (results.model_predictions && typeof results.model_predictions === 'object' && Object.keys(results.model_predictions).length > 0) {
        const predictionLabels = {
            "proficiency": "熟练度",
            "frameworks": "框架",
            "optimization": "优化",
            "versioning": "版本控制",
            "involvement": "投入度",
            "impact": "影响力",
            "outcomes": "成果",
            "logic": "逻辑",
            "communication": "沟通",
            "solving": "解决问题",
            "learning": "学习能力"
        };
        let predictionsHtml = '<div class="grid grid-cols-2 gap-2">';
        for (const key in results.model_predictions) {
            if (results.model_predictions.hasOwnProperty(key)) {
                const label = predictionLabels[key] || key; // 使用中文标签，如果没有则使用原始键名
                const value = (results.model_predictions[key] * 100).toFixed(2); // 转换为百分比，保留两位小数
                predictionsHtml += `<div class="flex justify-between items-center bg-white p-2 rounded-md shadow-sm"><span class="text-sm font-medium text-dark-light">${label}:</span><span class="text-sm font-bold text-primary">${value}%</span></div>`;
            }
        }
        predictionsHtml += '</div>';
        predictionsDisplay.innerHTML = predictionsHtml;
        hasContent = true;
    } else {
        predictionsDisplay.textContent = '暂无量化分数。';
    }
    if (!hasContent) {
        container.innerHTML = '<p class="text-dark-light">暂无AI分析与建议。</p>';
    }
}



/**
 * 在指定容器中显示雷达图 (使用路径，如果需要)
 * @param {string} chartPath - 雷达图图片路径
 */
function displayRadarChart(chartPath) {
    const container = document.getElementById('radar-chart-container');
    if (!container || !chartPath) {
        console.warn('雷达图容器未找到或路径无效');
        return;
    }
    container.innerHTML = `
        <iframe src="${chartPath}" title="能力雷达图" style="width: 100%; height: 500px; border: none;"></iframe>
    `;
}


// --- **新增或修改的通用消息渲染函数** ---
/**
 * 将消息追加到对话容器
 * @param {string} speaker - 发言者 ('User' 或 'AI')
 * @param {string} text - 消息内容
 */
function appendMessageToContainer(speaker, text) {
    const container = document.getElementById('conversation-analysis');
    if (!container) return;

    const speakerIcon = speaker === 'User' ? 'fa-user' : 'fa-robot';
    const speakerColor = speaker === 'User' ? 'text-accent' : 'text-primary';
    const bgColor = speaker === 'User' ? 'bg-blue-50' : 'bg-white';
    const alignment = speaker === 'User' ? 'justify-end' : 'justify-start';

    // 使用 marked 解析 Markdown (如果需要)
    const displayedText = marked.parse(text);

    const messageHtml = `
        <div class="flex ${alignment} mb-4">
            ${speaker === 'AI' ? `
            <div class="flex-shrink-0 mt-1">
                <div class="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center ${speakerColor}">
                    <i class="fa ${speakerIcon}"></i>
                </div>
            </div>
            ` : ''}
            <div class="ml-3 mr-3 ${bgColor} rounded-lg p-4 shadow-sm max-w-[70%]">
                <p class="text-dark">${displayedText}</p>
            </div>
            ${speaker === 'User' ? `
            <div class="flex-shrink-0 mt-1">
                <div class="h-8 w-8 rounded-full bg-accent/10 flex items-center justify-center ${speakerColor}">
                    <i class="fa ${speakerIcon}"></i>
                </div>
            </div>
            ` : ''}
        </div>
    `;
    container.insertAdjacentHTML('beforeend', messageHtml);
    container.scrollTop = container.scrollHeight;
}


// --- **处理 AI 对话分析的交互** ---
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('user-chat-input');
    const sendButton = document.getElementById('send-chat-btn');
    const conversationContainer = document.getElementById('conversation-analysis');

    // --- **关键修改：使用全局的 currentConversationHistory** ---
    // let currentConversationHistory = []; // 删除这行，使用 window.currentConversationHistory

    if (chatInput && sendButton && conversationContainer) {
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        async function sendMessage() {
            const userMessage = chatInput.value.trim();
            if (userMessage === '') return;

            // 显示用户消息
            appendMessageToContainer('User', userMessage);
            // --- **关键修改：更新全局历史** ---
            window.currentConversationHistory.push({ role: 'user', content: userMessage });
            chatInput.value = '';
            chatInput.disabled = true;
            sendButton.disabled = true;

            try {
                // --- **关键修改：发送包含初始历史的完整历史** ---
                const response = await fetch('/chat_with_ai/', { // 统一使用带斜杠的路径
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: userMessage,
                        conversation_history: window.currentConversationHistory // 发送完整历史
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                appendMessageToContainer('AI', data.reply);

                // --- **关键修改：更新全局历史** ---
                // 推荐使用后端返回的历史，因为它可能包含更完整的上下文处理
                // window.currentConversationHistory = data.conversation_history;
                // 或者，如果后端只返回当前回复，则手动添加
                 window.currentConversationHistory.push({ role: 'assistant', content: data.reply });

            } catch (error) {
                console.error('Error chatting with AI:', error);
                appendMessageToContainer('AI', `抱歉，与AI的对话出现问题。请稍后再试。 (${error.message})`);
            } finally {
                 chatInput.disabled = false;
                 sendButton.disabled = false;
                 chatInput.focus();
            }
        }

    }
});