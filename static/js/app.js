// 全局变量
let currentCommentType = 'main'; // 'main' 或 'sub'
let allComments = {
    main: [],
    sub: []
};
let sentimentChart = null;
let currentPage = 1;
const commentsPerPage = 10;

// 当前筛选的BV号
let currentBvFilter = null;
// 当前统计筛选的BV号
let currentStatBvFilter = null;

// 筛选设置
let filterSettings = {
    location: 'all',
    sentiment: 'all',
    confidence: 'all'
};

// DOM 元素
const analyzeBtn = document.getElementById('analyzeBtn');
const bvInput = document.getElementById('bvInput');
const statusBox = document.getElementById('statusBox');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const showMainComments = document.getElementById('showMainComments');
const showSubComments = document.getElementById('showSubComments');
const commentsTable = document.getElementById('commentsTable');
const commentsPagination = document.getElementById('commentsPagination');
const locationFilter = document.getElementById('locationFilter');
const sentimentFilter = document.getElementById('sentimentFilter');
const confidenceFilter = document.getElementById('confidenceFilter');
const bvFilter = document.getElementById('bvFilter');
const applyBvFilter = document.getElementById('applyBvFilter');
const resetBvFilter = document.getElementById('resetBvFilter');
const bvFilterInfo = document.getElementById('bvFilterInfo');
const statBvFilter = document.getElementById('statBvFilter');
const applyStatBvFilter = document.getElementById('applyStatBvFilter');
const resetStatBvFilter = document.getElementById('resetStatBvFilter');
const statBvFilterInfo = document.getElementById('statBvFilterInfo');

// 新增变量：标记是否正在刷新评论数据
let isRefreshingComments = false;

// 状态轮询间隔（毫秒）
let statusPollingInterval = 5000; // 默认5秒
let statusPollingTimer = null;
let lastTaskRunning = false; // 跟踪上次任务是否在运行

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    // 注册事件监听器
    document.getElementById('searchForm').addEventListener('submit', handleFormSubmit);
    showMainComments.addEventListener('click', () => switchCommentType('main'));
    showSubComments.addEventListener('click', () => switchCommentType('sub'));
    
    // 筛选器事件监听
    locationFilter.addEventListener('change', handleFilterChange);
    sentimentFilter.addEventListener('change', handleFilterChange);
    confidenceFilter.addEventListener('change', handleFilterChange);
    
    // BV号筛选事件监听
    applyBvFilter.addEventListener('click', handleBvFilter);
    resetBvFilter.addEventListener('click', resetBvFilterHandler);
    bvFilter.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleBvFilter();
        }
    });
    
    // 统计筛选事件监听
    applyStatBvFilter.addEventListener('click', handleStatBvFilter);
    resetStatBvFilter.addEventListener('click', resetStatBvFilterHandler);
    statBvFilter.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleStatBvFilter();
        }
    });
    
    // 尝试获取已有数据
    fetchStatistics();
    fetchComments();
    
    // 启动状态轮询 - 修改为使用变量控制轮询频率
    startStatusPolling();
});

// 开始状态轮询
function startStatusPolling() {
    // 初始检查一次状态
    checkStatus();
    
    // 设置周期性检查
    statusPollingTimer = setInterval(checkStatus, statusPollingInterval);
}

// 更新轮询频率
function updatePollingFrequency(isTaskRunning) {
    // 如果任务状态发生变化
    if (isTaskRunning !== lastTaskRunning) {
        lastTaskRunning = isTaskRunning;
        
        // 清除现有的定时器
        if (statusPollingTimer) {
            clearInterval(statusPollingTimer);
        }
        
        // 根据任务状态设置新的轮询频率
        statusPollingInterval = isTaskRunning ? 1000 : 5000; // 运行中:1秒, 空闲时:5秒
        
        // 创建新的定时器
        statusPollingTimer = setInterval(checkStatus, statusPollingInterval);
    }
}

// 处理表单提交
function handleFormSubmit(event) {
    event.preventDefault();
    const bv = bvInput.value.trim();
    
    if (!bv) {
        alert('请输入有效的BV号！');
        return;
    }
    
    // 禁用按钮，显示加载状态
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
    
    // 发送请求
    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ bv }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusBox.innerHTML = `<div class="alert alert-info">
                <i class="bi bi-info-circle-fill me-2"></i>${data.message}
            </div>`;
        } else {
            statusBox.innerHTML = `<div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>${data.message}
            </div>`;
            
            // 恢复按钮状态
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>开始分析';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        statusBox.innerHTML = `<div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>请求失败，请稍后重试
        </div>`;
        
        // 恢复按钮状态
        analyzeBtn.disabled = false;
        analyzeBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>开始分析';
    });
}

// 轮询检查状态
function checkStatus() {
    // 如果正在刷新评论数据，跳过此次状态检查
    if (isRefreshingComments) {
        return;
    }
    
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            // 更新进度条
            progressBar.style.width = `${data.progress}%`;
            progressText.textContent = `${data.progress}%`;
            
            // 根据任务是否运行更新轮询频率
            updatePollingFrequency(data.is_running);
            
            // 更新状态消息
            if (data.is_running) {
                statusBox.innerHTML = `<div class="alert alert-info">
                    <i class="bi bi-info-circle-fill me-2"></i>${data.message}
                </div>`;
                analyzeBtn.disabled = true;
                analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
            } else if (data.progress === 100) {
                statusBox.innerHTML = `<div class="alert alert-success">
                    <i class="bi bi-check-circle-fill me-2"></i>${data.message}
                </div>`;
                
                // 恢复按钮状态
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>开始分析';
                
                // 判断是否需要刷新数据
                // 只有当任务从运行状态刚刚变为完成状态时才刷新数据
                if (lastTaskRunning) {
                    // 刷新统计数据
                    fetchStatistics();
                    // 保持当前页面位置刷新评论数据
                    fetchComments(true);
                }
            } else if (data.message) {
                statusBox.innerHTML = `<div class="alert alert-secondary">
                    <i class="bi bi-info-circle-fill me-2"></i>${data.message}
                </div>`;
                
                // 恢复按钮状态
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i class="bi bi-play-fill me-2"></i>开始分析';
            }
        })
        .catch(error => {
            console.error('Status check error:', error);
        });
}

// 获取统计数据
function fetchStatistics() {
    // 根据是否有BV筛选决定使用哪个API
    const apiUrl = currentStatBvFilter ? 
        `/statistics_by_bv?bv=${encodeURIComponent(currentStatBvFilter)}` : 
        '/statistics';
    
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP错误 ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Statistics error:', data.error);
                
                // 更新BV筛选提示
                if (currentStatBvFilter) {
                    statBvFilterInfo.innerHTML = `<span class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>获取统计数据失败</span>`;
                }
                return;
            }
            
            // 更新统计显示
            updateStatisticsDisplay(data);
            
            // 更新筛选提示信息
            if (currentStatBvFilter && data.oid) {
                statBvFilterInfo.textContent = `已筛选视频 ${currentStatBvFilter} 的统计数据（AV${data.oid}）`;
            }
        })
        .catch(error => {
            console.error('Statistics fetch error:', error);
            
            // 更新BV筛选提示如果有错误
            if (currentStatBvFilter) {
                statBvFilterInfo.innerHTML = `<span class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>${error.message}</span>`;
            }
        });
}

// 更新统计显示
function updateStatisticsDisplay(data) {
    // 检查数据是否与当前显示的数据相同，如果相同则不更新
    const currentTotal = document.getElementById('totalComments').textContent;
    const currentPositive = document.getElementById('positiveComments').textContent;
    const currentNegative = document.getElementById('negativeComments').textContent;
    
    // 只有当数据发生变化时才更新UI
    if (currentTotal !== data.total.total.toString() || 
        currentPositive !== data.total.positive.toString() || 
        currentNegative !== data.total.negative.toString()) {
        
        // 更新统计卡片
        document.getElementById('totalComments').textContent = data.total.total;
        document.getElementById('positiveComments').textContent = data.total.positive;
        document.getElementById('negativeComments').textContent = data.total.negative;
        
        // 计算百分比
        const positivePercent = data.total.total > 0 
            ? Math.round((data.total.positive / data.total.total) * 100) 
            : 0;
        const negativePercent = data.total.total > 0 
            ? Math.round((data.total.negative / data.total.total) * 100) 
            : 0;
        
        document.getElementById('positivePercentage').textContent = `${positivePercent}%`;
        document.getElementById('negativePercentage').textContent = `${negativePercent}%`;
        
        // 更新图表
        updateChart(data);
    }
}

// 获取评论数据
function fetchComments(keepCurrentPage = false) {
    // 标记正在刷新评论数据
    isRefreshingComments = true;
    
    // 保存当前页码和评论类型，以便后续恢复
    const savedPage = currentPage;
    const savedCommentType = currentCommentType;
    
    // 根据是否有BV筛选决定使用哪个API
    const apiUrl = currentBvFilter ? 
        `/get_comments_by_bv?bv=${encodeURIComponent(currentBvFilter)}` : 
        '/get_comments';
    
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP错误 ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Comments error:', data.error);
                commentsTable.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center text-danger py-3">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            获取评论数据失败: ${data.error}
                        </td>
                    </tr>
                `;
                isRefreshingComments = false;
                
                // 更新BV筛选提示
                if (currentBvFilter) {
                    bvFilterInfo.innerHTML = `<span class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>获取评论失败</span>`;
                }
                return;
            }
            
            // 检查数据是否与当前相同（比较长度作为简单判断）
            const mainCommentsChanged = (data.main_comments || []).length !== allComments.main.length;
            const subCommentsChanged = (data.sub_comments || []).length !== allComments.sub.length;
            
            // 只有在数据发生变化时才更新
            if (mainCommentsChanged || subCommentsChanged) {
                // 保存评论数据
                allComments.main = data.main_comments || [];
                allComments.sub = data.sub_comments || [];
                
                // 如果没有任何数据，显示特定消息
                if (allComments.main.length === 0 && allComments.sub.length === 0) {
                    commentsTable.innerHTML = `
                        <tr>
                            <td colspan="5" class="text-center text-muted py-3">
                                <i class="bi bi-info-circle-fill me-2"></i>
                                当前视频暂无评论数据或评论获取失败
                            </td>
                        </tr>
                    `;
                    commentsPagination.innerHTML = '';
                    isRefreshingComments = false;
                    return;
                }
                
                // 更新IP属地筛选选项
                updateLocationOptions();
            }
            
            // 更新BV筛选信息
            if (currentBvFilter && data.oid) {
                bvFilterInfo.textContent = `已筛选视频 ${currentBvFilter} 的评论（AV${data.oid}）`;
            } else if (!currentBvFilter) {
                bvFilterInfo.textContent = '显示所有评论数据';
            }
            
            // 如果需要保持当前页码，并且当前页码有效，则恢复之前的页码
            if (keepCurrentPage && savedPage > 0) {
                // 确保评论类型也恢复为之前的类型
                currentCommentType = savedCommentType;
                
                const totalPages = Math.ceil(allComments[currentCommentType].length / commentsPerPage);
                // 确保所恢复的页码不超过评论总页数
                currentPage = Math.min(savedPage, totalPages);
                
                // 恢复评论类型按钮状态
                if (currentCommentType === 'main') {
                    showMainComments.className = 'btn btn-sm btn-light';
                    showSubComments.className = 'btn btn-sm btn-outline-light';
                } else {
                    showMainComments.className = 'btn btn-sm btn-outline-light';
                    showSubComments.className = 'btn btn-sm btn-light';
                }
            } else {
                // 否则重置为第一页
                currentPage = 1;
            }
            
            // 如果数据发生变化或强制刷新，才显示当前评论类型
            if (mainCommentsChanged || subCommentsChanged || !keepCurrentPage) {
                displayComments(currentPage);
            }
            
            isRefreshingComments = false;
        })
        .catch(error => {
            console.error('Comments fetch error:', error);
            commentsTable.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center text-danger py-3">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        网络错误，无法获取评论数据: ${error.message}
                    </td>
                </tr>
            `;
            
            // 更新BV筛选提示如果有错误
            if (currentBvFilter) {
                bvFilterInfo.innerHTML = `<span class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>${error.message}</span>`;
            }
            
            isRefreshingComments = false;
        });
}

// 更新IP属地选项
function updateLocationOptions() {
    // 收集所有唯一的属地
    const locations = new Set();
    
    // 从主评论和子评论中收集
    allComments.main.forEach(comment => {
        if (comment.location) {
            locations.add(comment.location);
        }
    });
    
    allComments.sub.forEach(comment => {
        if (comment.location) {
            locations.add(comment.location);
        }
    });
    
    // 清空当前选项（保留"全部"选项）
    while (locationFilter.options.length > 1) {
        locationFilter.remove(1);
    }
    
    // 添加新选项
    const sortedLocations = Array.from(locations).sort();
    sortedLocations.forEach(location => {
        const option = document.createElement('option');
        option.value = location;
        option.textContent = location;
        locationFilter.appendChild(option);
    });
}

// 切换评论类型
function switchCommentType(type) {
    currentCommentType = type;
    currentPage = 1;
    
    // 更新按钮样式
    if (type === 'main') {
        showMainComments.className = 'btn btn-sm btn-light';
        showSubComments.className = 'btn btn-sm btn-outline-light';
    } else {
        showMainComments.className = 'btn btn-sm btn-outline-light';
        showSubComments.className = 'btn btn-sm btn-light';
    }
    
    // 显示对应评论
    displayComments(currentPage);
}

// 显示评论数据
function displayComments(page) {
    const comments = allComments[currentCommentType];
    
    // 根据筛选条件过滤评论
    const filteredComments = comments.filter(comment => {
        // 筛选IP属地
        if (filterSettings.location !== 'all' && comment.location !== filterSettings.location) {
            return false;
        }
        
        // 筛选情感倾向
        if (filterSettings.sentiment !== 'all' && comment.result !== filterSettings.sentiment) {
            return false;
        }
        
        // 筛选置信度
        if (filterSettings.confidence !== 'all') {
            const confidenceThreshold = parseFloat(filterSettings.confidence);
            if (!comment.probability || comment.probability < confidenceThreshold) {
                return false;
            }
        }
        
        return true;
    });
    
    const startIndex = (page - 1) * commentsPerPage;
    const endIndex = Math.min(startIndex + commentsPerPage, filteredComments.length);
    const totalPages = Math.ceil(filteredComments.length / commentsPerPage);
    
    // 清空表格
    commentsTable.innerHTML = '';
    
    // 如果没有评论，显示提示
    if (filteredComments.length === 0) {
        commentsTable.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted py-3">
                    ${comments.length > 0 ? '没有符合筛选条件的评论' : '尚无评论数据'}
                </td>
            </tr>
        `;
        commentsPagination.innerHTML = '';
        return;
    }
    
    // 显示当前页评论
    for (let i = startIndex; i < endIndex; i++) {
        const comment = filteredComments[i];
        const sentimentClass = getSentimentClass(comment.result);
        
        commentsTable.innerHTML += `
            <tr>
                <td>${comment.uname || '匿名用户'}</td>
                <td>${comment.location || '未知'}</td>
                <td>${comment.content}</td>
                <td>
                    <span class="sentiment-tag ${sentimentClass}">
                        ${comment.result || '未知'}
                    </span>
                </td>
                <td>${comment.probability ? (comment.probability * 100).toFixed(2) + '%' : '-'}</td>
            </tr>
        `;
    }
    
    // 更新分页
    updatePagination(page, totalPages);
}

// 更新分页
function updatePagination(currentPage, totalPages) {
    commentsPagination.innerHTML = '';
    
    // 上一页按钮
    const prevBtn = document.createElement('li');
    prevBtn.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevBtn.innerHTML = `<a class="page-link" href="#" tabindex="-1">上一页</a>`;
    prevBtn.onclick = function() {
        if (currentPage > 1) {
            displayComments(currentPage - 1);
        }
        return false;
    };
    commentsPagination.appendChild(prevBtn);
    
    // 页码按钮
    const maxPages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPages / 2));
    let endPage = Math.min(totalPages, startPage + maxPages - 1);
    
    if (endPage - startPage + 1 < maxPages) {
        startPage = Math.max(1, endPage - maxPages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('li');
        pageBtn.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageBtn.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        pageBtn.onclick = function() {
            displayComments(i);
            return false;
        };
        commentsPagination.appendChild(pageBtn);
    }
    
    // 下一页按钮
    const nextBtn = document.createElement('li');
    nextBtn.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextBtn.innerHTML = `<a class="page-link" href="#">下一页</a>`;
    nextBtn.onclick = function() {
        if (currentPage < totalPages) {
            displayComments(currentPage + 1);
        }
        return false;
    };
    commentsPagination.appendChild(nextBtn);
}

// 获取情感对应的样式类
function getSentimentClass(sentiment) {
    if (!sentiment) return '';
    
    switch (sentiment) {
        case '正向':
            return 'sentiment-positive';
        case '负向':
            return 'sentiment-negative';
        case '未提及':
            return 'sentiment-neutral';
        default:
            return '';
    }
}

// 更新图表
function updateChart(data) {
    const ctx = document.getElementById('sentimentChart').getContext('2d');
    
    // 如果已有图表，先销毁
    if (sentimentChart) {
        sentimentChart.destroy();
    }
    
    // 检查是否有数据
    if (data.total.total === 0) {
        // 如果没有数据，显示一个空图表或提示信息
        document.getElementById('sentimentChart').parentNode.innerHTML = `
            <div class="alert alert-info text-center my-3">
                <i class="bi bi-info-circle-fill me-2"></i>
                尚无评论数据进行情感分析
            </div>
        `;
        return;
    }
    
    // 创建新图表
    sentimentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['正向评论', '负向评论', '中性评论'],
            datasets: [{
                data: [
                    data.total.positive,
                    data.total.negative,
                    data.total.total - data.total.positive - data.total.negative
                ],
                backgroundColor: [
                    '#28a745',
                    '#dc3545',
                    '#6c757d'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 处理筛选变化
function handleFilterChange() {
    // 更新筛选设置
    filterSettings.location = locationFilter.value;
    filterSettings.sentiment = sentimentFilter.value;
    filterSettings.confidence = confidenceFilter.value;
    
    // 重置到第一页
    currentPage = 1;
    
    // 应用筛选并显示结果
    displayComments(currentPage);
}

// BV号筛选事件
function handleBvFilter() {
    const bv = bvFilter.value.trim();
    
    if (!bv) {
        alert('请输入有效的BV号！');
        return;
    }
    
    // 显示加载状态
    bvFilterInfo.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>正在加载...';
    applyBvFilter.disabled = true;
    
    // 清空当前评论并重置页码
    allComments = {
        main: [],
        sub: []
    };
    currentPage = 1;
    
    // 保存当前BV筛选
    currentBvFilter = bv;
    
    // 发送请求获取对应BV号的评论
    fetch(`/get_comments_by_bv?bv=${encodeURIComponent(bv)}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP错误 ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // 更新全局评论数据
            allComments.main = data.main_comments || [];
            allComments.sub = data.sub_comments || [];
            
            // 更新筛选信息提示
            bvFilterInfo.textContent = `已筛选视频 ${bv} 的评论（AV${data.oid}）`;
            
            // 更新IP属地筛选选项
            updateLocationOptions();
            
            // 显示评论
            displayComments(1);
            
            // 恢复按钮状态
            applyBvFilter.disabled = false;
        })
        .catch(error => {
            console.error('BV筛选错误:', error);
            bvFilterInfo.innerHTML = `<span class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>${error.message}</span>`;
            
            // 恢复按钮状态
            applyBvFilter.disabled = false;
        });
}

// 重置BV号筛选
function resetBvFilterHandler() {
    // 重置输入框和提示
    bvFilter.value = '';
    bvFilterInfo.textContent = '显示所有评论数据';
    
    // 清除当前BV筛选
    currentBvFilter = null;
    
    // 重新获取所有评论
    fetchComments();
}

// 统计筛选事件
function handleStatBvFilter() {
    const bv = statBvFilter.value.trim();
    
    if (!bv) {
        alert('请输入有效的BV号！');
        return;
    }
    
    // 显示加载状态
    statBvFilterInfo.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>正在加载...';
    applyStatBvFilter.disabled = true;
    
    // 保存当前统计筛选
    currentStatBvFilter = bv;
    
    // 发送请求获取对应BV号的统计数据
    fetch(`/statistics_by_bv?bv=${encodeURIComponent(bv)}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `HTTP错误 ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // 更新统计信息提示
            statBvFilterInfo.textContent = `已筛选视频 ${bv} 的统计数据（AV${data.oid}）`;
            
            // 更新统计显示
            updateStatisticsDisplay(data);
            
            // 恢复按钮状态
            applyStatBvFilter.disabled = false;
        })
        .catch(error => {
            console.error('统计筛选错误:', error);
            statBvFilterInfo.innerHTML = `<span class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>${error.message}</span>`;
            
            // 恢复按钮状态
            applyStatBvFilter.disabled = false;
        });
}

// 重置统计筛选
function resetStatBvFilterHandler() {
    // 重置输入框和提示
    statBvFilter.value = '';
    statBvFilterInfo.textContent = '显示所有评论的情感统计';
    
    // 清除当前统计筛选
    currentStatBvFilter = null;
    
    // 重新获取所有统计数据
    fetchStatistics();
} 