			// 全局变量
			const recordsPerPage = 5;
			let currentPage = 1;
			let allRecords = [];
			let filteredRecords = [];
			// API基础URL - 在实际部署时替换为真实API地址
			const API_BASE_URL = '/api/interviews';

			// DOM元素
			const historyContainer = document.getElementById('interview-history');
			const searchInput = document.getElementById('search-input');
			const typeFilter = document.getElementById('interview-type-filter');
			const timeFilter = document.getElementById('time-filter');
			const prevPageBtn = document.getElementById('prev-page');
			const nextPageBtn = document.getElementById('next-page');
			const mobilePrevPageBtn = document.getElementById('mobile-prev-page');
			const mobileNextPageBtn = document.getElementById('mobile-next-page');
			const paginationContainer = document.getElementById('pagination-container');
			const startRecordEl = document.getElementById('start-record');
			const endRecordEl = document.getElementById('end-record');
			const totalRecordsEl = document.getElementById('total-records');
			const noRecordsEl = document.getElementById('no-records');
			const resetFiltersBtn = document.getElementById('reset-filters');
			const mobileMenuButton = document.getElementById('mobile-menu-button');
			const mobileMenu = document.getElementById('mobile-menu');
			const errorMessage = document.getElementById('error-message');
			const errorText = document.getElementById('error-text');

			// 初始化
			document.addEventListener('DOMContentLoaded', function() {
				// 从API加载数据
				fetchInterviewDataFromAPI();
				
				// 事件监听
				setupEventListeners();
			});

			// 设置事件监听
			function setupEventListeners() {
				// 筛选器变化事件
				searchInput.addEventListener('input', applyFilters);
				typeFilter.addEventListener('change', applyFilters);
				timeFilter.addEventListener('change', applyFilters);
				
				// 分页按钮事件
				prevPageBtn.addEventListener('click', () => changePage(currentPage - 1));
				nextPageBtn.addEventListener('click', () => changePage(currentPage + 1));
				mobilePrevPageBtn.addEventListener('click', () => changePage(currentPage - 1));
				mobileNextPageBtn.addEventListener('click', () => changePage(currentPage + 1));
				
				// 重置筛选条件
				resetFiltersBtn.addEventListener('click', resetFilters);
				
				// 移动端菜单
				mobileMenuButton.addEventListener('click', () => {
					mobileMenu.classList.toggle('hidden');
				});
				
				// 导航栏滚动效果
				window.addEventListener('scroll', function() {
					const nav = document.querySelector('nav');
					if (window.scrollY > 10) {
						nav.classList.add('shadow');
						nav.classList.remove('shadow-sm');
					} else {
						nav.classList.remove('shadow');
						nav.classList.add('shadow-sm');
					}
				});
			}

			// 从API获取面试数据
			async function fetchInterviewDataFromAPI(filters = {}) {
				try {
					// 显示加载状态
					showLoadingState();
					// 隐藏错误信息
					errorMessage.classList.add('hidden');
					
					// 构建查询参数
					const params = new URLSearchParams();
					if (filters.type) params.append('type', filters.type);
					if (filters.startDate) params.append('startDate', filters.startDate);
					if (filters.endDate) params.append('endDate', filters.endDate);
					if (filters.search) params.append('search', filters.search);
					
					// 构建API URL
					const url = params.toString() ? `${API_BASE_URL}?${params.toString()}` : API_BASE_URL;
					
					// 发送请求
					const response = await fetch(url, {
						method: 'GET',
						headers: {
							'Content-Type': 'application/json',
							// 添加认证令牌（实际应用中使用）
							// 'Authorization': `Bearer ${getAuthToken()}`
						},
						// 处理跨域请求
						credentials: 'include'
					});
					
					// 检查响应状态
					if (!response.ok) {
						throw new Error(`HTTP错误，状态码: ${response.status}`);
					}
					
					// 解析响应数据
					const data = await response.json();
					
					// 检查数据格式是否正确
					if (!Array.isArray(data)) {
						throw new Error('API返回数据格式不正确，期望数组');
					}
					
					// 存储数据
					allRecords = data;
					
					// 应用筛选
					applyFilters();
					
				} catch (error) {
					// 处理错误
					handleDataFetchError(error);
				}
			}

			// 显示加载状态
			function showLoadingState() {
				historyContainer.innerHTML = `
					<tr class="animate-pulse-slow">
						<td colspan="6" class="px-6 py-12 text-center text-dark-light">
							<div class="flex flex-col items-center justify-center">
								<div class="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin mb-4"></div>
								<p>正在加载历史记录...</p>
							</div>
						</td>
					</tr>
				`;
			}

			// 处理数据获取错误
			function handleDataFetchError(error) {
				console.error('获取面试数据失败:', error);
				
				// 显示错误信息
				errorText.textContent = error.message || '加载数据时发生错误，请稍后重试';
				errorMessage.classList.remove('hidden');
				
				// 显示错误状态
				historyContainer.innerHTML = `
					<tr>
						<td colspan="6" class="px-6 py-12 text-center text-dark-light">
							<div class="flex flex-col items-center justify-center">
								<div class="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mb-4">
									<i class="fa fa-exclamation-triangle text-red-500"></i>
								</div>
								<p class="mb-2">加载失败</p>
								<button id="retry-load" class="text-primary hover:text-accent transition-colors duration-300">
									重试
								</button>
							</div>
						</td>
					</tr>
				`;
				
				// 添加重试按钮事件
				document.getElementById('retry-load').addEventListener('click', () => {
					fetchInterviewDataFromAPI();
				});
				
				// 重置分页信息
				startRecordEl.textContent = '0';
				endRecordEl.textContent = '0';
				totalRecordsEl.textContent = '0';
				
				// 禁用分页按钮
				prevPageBtn.disabled = true;
				nextPageBtn.disabled = true;
				mobilePrevPageBtn.disabled = true;
				mobileNextPageBtn.disabled = true;
				
				// 清空分页容器
				paginationContainer.innerHTML = '';
			}

			// 应用筛选条件
			function applyFilters() {
				const searchTerm = searchInput.value.toLowerCase().trim();
				const typeValue = typeFilter.value;
				const timeValue = timeFilter.value;
				
				// 筛选逻辑
				filteredRecords = allRecords.filter(record => {
					// 搜索筛选
					const matchesSearch = searchTerm === '' || 
										  (record.position && record.position.toLowerCase().includes(searchTerm)) ||
										  (record.type && record.type.toLowerCase().includes(searchTerm));
					
					// 类型筛选
					const matchesType = typeValue === '' || (record.typeKey && record.typeKey === typeValue);
					
					// 时间筛选
					const matchesTime = timeValue === '' || (record.date && filterByTime(record.date, timeValue));
					
					return matchesSearch && matchesType && matchesTime;
				});
				
				// 重置当前页码
				currentPage = 1;
				
				// 更新显示
				updateDisplay();
			}

			// 按时间筛选
			function filterByTime(dateString, timeFilter) {
				const recordDate = new Date(dateString);
				if (isNaN(recordDate.getTime())) {
					return false; // 日期格式无效
				}
				
				const today = new Date();
				const startOfToday = new Date(today.setHours(0, 0, 0, 0));
				
				// 获取本周的第一天（周一）
				const dayOfWeek = today.getDay() || 7; // 转换为周一为1，周日为7
				const diffToMonday = dayOfWeek - 1;
				const startOfWeek = new Date(today);
				startOfWeek.setDate(today.getDate() - diffToMonday);
				startOfWeek.setHours(0, 0, 0, 0);
				
				// 获取本月的第一天
				const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
				
				// 获取今年的第一天
				const startOfYear = new Date(today.getFullYear(), 0, 1);
				
				switch(timeFilter) {
					case 'today':
						return recordDate >= startOfToday;
					case 'week':
						return recordDate >= startOfWeek;
					case 'month':
						return recordDate >= startOfMonth;
					case 'year':
						return recordDate >= startOfYear;
					default:
						return true;
				}
			}

			// 更新显示
			function updateDisplay() {
				// 清空容器
				historyContainer.innerHTML = '';
				
				// 计算总页数
				const totalPages = Math.ceil(filteredRecords.length / recordsPerPage);
				
				// 计算当前页记录范围
				const startIndex = (currentPage - 1) * recordsPerPage;
				const endIndex = Math.min(startIndex + recordsPerPage, filteredRecords.length);
				const currentRecords = filteredRecords.slice(startIndex, endIndex);
				
				// 更新分页信息
				startRecordEl.textContent = filteredRecords.length > 0 ? startIndex + 1 : 0;
				endRecordEl.textContent = filteredRecords.length > 0 ? endIndex : 0;
				totalRecordsEl.textContent = filteredRecords.length;
				
				// 更新分页按钮状态
				prevPageBtn.disabled = currentPage === 1;
				nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
				mobilePrevPageBtn.disabled = currentPage === 1;
				mobileNextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
				
				// 更新分页按钮
				updatePaginationButtons(totalPages);
				
				// 显示或隐藏无记录提示
				if (filteredRecords.length === 0) {
					noRecordsEl.classList.remove('hidden');
					return;
				} else {
					noRecordsEl.classList.add('hidden');
				}
				
				// 添加记录到表格
				currentRecords.forEach((record, index) => {
					// 确保记录有必要的字段
					if (!record.id || !record.date || !record.type) {
						return;
					}
					
					const row = document.createElement('tr');
					row.className = 'table-row-hover hover:bg-ultra-light/50 animate-fade-in cursor-pointer';
					row.style.animationDelay = `${0.1 + index * 0.1}s`;
					
					// 点击行查看详情
					row.addEventListener('click', () => {
						// 跳转到详情页
						window.location.href = `interview-detail.html?id=${record.id}`;
					});
					
					// 状态标签样式
					let statusClass = '';
					switch(record.status) {
						case '已完成':
							statusClass = 'bg-green-100 text-green-800';
							break;
						case '进行中':
							statusClass = 'bg-blue-100 text-blue-800';
							break;
						case '未开始':
							statusClass = 'bg-yellow-100 text-yellow-800';
							break;
						default:
							statusClass = 'bg-gray-100 text-gray-800';
					}
					
					// 分数颜色
					let scoreColor = 'text-green-600';
					if (record.score !== undefined) {
						if (record.score < 70) scoreColor = 'text-red-600';
						else if (record.score < 80) scoreColor = 'text-orange-600';
					}
					
					row.innerHTML = `
						<td class="px-6 py-4 whitespace-nowrap text-sm text-dark">${record.date}</td>
						<td class="px-6 py-4 whitespace-nowrap text-sm text-dark">${record.type}</td>
						<td class="px-6 py-4 whitespace-nowrap text-sm text-dark">${record.position || '-'}</td>
						<td class="px-6 py-4 whitespace-nowrap text-sm">
							<div class="flex items-center">
								<span class="font-medium ${scoreColor} mr-2">${record.score !== undefined ? record.score : '-'}</span>
								${record.score !== undefined ? `
									<div class="w-24 bg-gray-200 rounded-full h-2 overflow-hidden">
										<div class="bg-primary h-2 rounded-full transition-all duration-1000 ease-out" style="width: 0%" 
											onload="this.style.width='${record.score}%'"></div>
									</div>
								` : ''}
							</div>
						</td>
						<td class="px-6 py-4 whitespace-nowrap text-sm">
							<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusClass}">
								${record.status || '未知'}
							</span>
						</td>
						<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
							<a href="interview-detail.html?id=${record.id}" class="text-primary hover:text-accent mr-3 transition-colors duration-300" onclick="event.stopPropagation()">查看详情</a>
							<a href="report-download.html?id=${record.id}" class="text-dark-light hover:text-dark transition-colors duration-300" onclick="event.stopPropagation()">下载报告</a>
						</td>
					`;
					
					historyContainer.appendChild(row);
				});
			}

			// 更新分页按钮
			function updatePaginationButtons(totalPages) {
				paginationContainer.innerHTML = '';
				
				// 最多显示5个页码按钮
				let startPage = Math.max(1, currentPage - 2);
				let endPage = Math.min(totalPages, startPage + 4);
				
				// 调整显示范围
				if (endPage - startPage < 4 && totalPages > 5) {
					startPage = Math.max(1, endPage - 4);
				}
				
				// 添加页码按钮
				for (let i = startPage; i <= endPage; i++) {
					const pageBtn = document.createElement('button');
					pageBtn.className = `pagination-link btn-effect relative inline-flex items-center px-4 py-2 border border-light-gray text-sm font-medium transition-all duration-300 ${i === currentPage ? 'bg-primary text-white' : 'bg-white text-dark-light hover:bg-ultra-light hover:text-primary'}`;
					pageBtn.textContent = i;
					pageBtn.addEventListener('click', () => changePage(i));
					paginationContainer.appendChild(pageBtn);
				}
			}

			// 改变页码
			function changePage(page) {
				if (page < 1 || page > Math.ceil(filteredRecords.length / recordsPerPage)) {
					return;
				}
				
				currentPage = page;
				updateDisplay();
				
				// 平滑滚动到表格顶部
				historyContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}

			// 重置筛选条件
			function resetFilters() {
				searchInput.value = '';
				typeFilter.value = '';
				timeFilter.value = '';
				
				noRecordsEl.classList.add('hidden');
				applyFilters();
			}

			// 获取认证令牌（实际应用中实现）
			function getAuthToken() {
				// 在实际应用中，这里会从localStorage或cookie中获取认证令牌
				// return localStorage.getItem('authToken');
				return '';
			}
			
			// 新增：历史记录页面交互增强
			document.addEventListener('DOMContentLoaded', function() {
				// 时间线视图切换
				const timelineToggle = document.getElementById('timeline-view-toggle');
				const tableContainer = document.querySelector('table');
				const timelineView = document.getElementById('timeline-view');
				
				timelineToggle.addEventListener('click', function() {
					tableContainer.classList.toggle('hidden');
					timelineView.classList.toggle('hidden');
					
					// 切换按钮文本和图标
					const icon = timelineToggle.querySelector('i');
					const text = timelineToggle.querySelector('span');
					
					if (timelineView.classList.contains('hidden')) {
						icon.className = 'fa fa-clock-o mr-2';
						text.textContent = '时间线视图';
					} else {
						icon.className = 'fa fa-table mr-2';
						text.textContent = '表格视图';
						// 加载时间线数据
						loadTimelineData();
					}
				});
				
				// 模拟加载历史统计数据
				setTimeout(() => {
					document.getElementById('total-interviews').textContent = '12';
					document.getElementById('average-score').textContent = '86.5';
					document.getElementById('highest-score').textContent = '94';
					document.getElementById('highest-score-date').textContent = '2023-11-15';
				}, 800);
				
				// 滚动动画效果
				const animateOnScroll = () => {
					const elements = document.querySelectorAll('.history-row');
					elements.forEach(element => {
						const elementTop = element.getBoundingClientRect().top;
						const elementVisible = 150;
						if (elementTop < window.innerHeight - elementVisible) {
							element.classList.add('animate-slide-up');
						}
					});
				};
				
				window.addEventListener('scroll', animateOnScroll);
				animateOnScroll(); // 初始检查
			});
			
			// 加载时间线数据
			function loadTimelineData() {
				// 模拟时间线数据
				const timelineData = [
					{
						date: '2023-11-20',
						time: '14:30',
						type: '技术面试',
						position: '前端开发工程师',
						score: 88,
						status: '已完成'
					},
					{
						date: '2023-11-15',
						time: '10:15',
						type: 'HR面试',
						position: '产品经理',
						score: 94,
						status: '已完成'
					},
					{
						date: '2023-11-10',
						time: '09:00',
						type: '行为面试',
						position: 'UI设计师',
						score: 82,
						status: '已完成'
					},
					{
						date: '2023-11-05',
						time: '16:45',
						type: '技术面试',
						position: '后端开发工程师',
						score: 79,
						status: '已完成'
					}
				];
				
				const timelineContainer = document.getElementById('timeline-view').querySelector('.relative');
				timelineContainer.innerHTML = '';
				
				timelineData.forEach((item, index) => {
					const timelineItem = document.createElement('div');
					timelineItem.className = 'mb-8 relative history-row pl-8 lg:pl-0';
					
					// 确定评分颜色
					let scoreColor = 'text-green-500';
					if (item.score < 70) scoreColor = 'text-red-500';
					else if (item.score < 85) scoreColor = 'text-yellow-500';
					
					// 确定状态徽章样式
					let statusBadge = '';
					switch(item.status) {
						case '已完成':
							statusBadge = '<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">已完成</span>';
							break;
						case '进行中':
							statusBadge = '<span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">进行中</span>';
							break;
						case '已取消':
							statusBadge = '<span class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">已取消</span>';
							break;
					}
					
					timelineItem.innerHTML = `
						<div class="hidden lg:block absolute left-[-24px] top-1 w-px h-full bg-primary/10 -z-10"></div>
						<div class="history-timeline-marker font-medium text-dark">${item.date} ${item.time}</div>
						<div class="mt-2 bg-ultra-light/50 rounded-lg p-4 transition-all duration-300 hover:bg-ultra-light">
							<div class="flex flex-col md:flex-row md:items-center md:justify-between">
								<div>
									<h4 class="font-medium text-dark">${item.position}</h4>
									<p class="text-dark-light text-sm mt-1">${item.type}</p>
								</div>
								<div class="mt-3 md:mt-0 flex items-center space-x-3">
									<span class="${scoreColor} font-medium">${item.score}分</span>
									${statusBadge}
								</div>
							</div>
							<div class="mt-4 flex justify-end">
								<button class="text-primary text-sm hover:text-primary/80 transition-colors duration-300 flex items-center">
									<i class="fa fa-eye mr-1"></i> 查看详情
								</button>
							</div>
						</div>
					`;
					
					// 添加动画延迟
					timelineItem.style.animationDelay = `${0.1 + (index * 0.1)}s`;
					
					timelineContainer.appendChild(timelineItem);
				});
			}