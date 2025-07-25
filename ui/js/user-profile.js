// DOM元素
			const mobileMenuButton = document.getElementById('mobile-menu-button');
			const mobileMenu = document.getElementById('mobile-menu');
			const profileTabs = document.querySelectorAll('.profile-tab');
			const profileContents = document.querySelectorAll('.profile-content');
			const imageUpload = document.getElementById('image-upload');
			const profileImage = document.getElementById('profile-image');
			const saveButtons = [
				document.getElementById('save-basic-info'),
				document.getElementById('save-account-settings'),
				document.getElementById('save-security-settings'),
				document.getElementById('save-notification-settings')
			];
			const successToast = document.getElementById('success-toast');
			const logoutBtn = document.getElementById('logout-btn');
			const exportDataBtn = document.getElementById('export-data');
			const clearHistoryBtn = document.getElementById('clear-history');
			const confirmDialog = document.getElementById('confirm-dialog');
			const cancelConfirm = document.getElementById('cancel-confirm');
			const confirmAction = document.getElementById('confirm-action');
			const confirmTitle = document.getElementById('confirm-title');
			const confirmMessage = document.getElementById('confirm-message');
			const twoFactorAuth = document.getElementById('two-factor-auth');

			// 初始化
			document.addEventListener('DOMContentLoaded', function() {
				setupEventListeners();
				initToggleSwitches();
			});

			// 设置事件监听
			function setupEventListeners() {
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

				// 切换标签页
				profileTabs.forEach(tab => {
					tab.addEventListener('click', () => {
						const tabId = tab.getAttribute('data-tab');
						
						// 更新标签状态
						profileTabs.forEach(t => t.classList.remove('active'));
						tab.classList.add('active');
						
						// 更新内容区域
						profileContents.forEach(content => {
							content.classList.add('hidden');
							content.classList.remove('active');
						});
						
						const activeContent = document.getElementById(`${tabId}-content`);
						activeContent.classList.remove('hidden');
						activeContent.classList.add('active');
					});
				});

				// 头像上传
				profileImage.parentElement.nextElementSibling.addEventListener('click', () => {
					imageUpload.click();
				});

				imageUpload.addEventListener('change', function(e) {
					if (e.target.files && e.target.files[0]) {
						const reader = new FileReader();
						
						reader.onload = function(e) {
							profileImage.src = e.target.result;
							showSuccessToast();
						}
						
						reader.readAsDataURL(e.target.files[0]);
					}
				});

				// 保存按钮
				saveButtons.forEach(button => {
					if (button) {
						button.addEventListener('click', showSuccessToast);
					}
				});

				// 退出登录
				logoutBtn.addEventListener('click', () => {
					confirmTitle.textContent = '确认退出登录？';
					confirmMessage.textContent = '您将退出当前账户，需要重新登录才能继续使用系统。';
					confirmDialog.classList.remove('hidden');
					
					// 设置确认按钮动作
					confirmAction.onclick = function() {
						confirmDialog.classList.add('hidden');
						// 实际应用中这里会执行退出登录逻辑
						showSuccessToast('已成功退出登录');
						setTimeout(() => {
							window.location.href = 'login.html';
						}, 1500);
					};
				});

				// 导出数据
				exportDataBtn.addEventListener('click', () => {
					confirmTitle.textContent = '确认导出数据？';
					confirmMessage.textContent = '系统将导出您的所有面试记录和评估结果，以CSV格式提供下载。';
					confirmDialog.classList.remove('hidden');
					
					// 设置确认按钮动作
					confirmAction.onclick = function() {
						confirmDialog.classList.add('hidden');
						showSuccessToast('数据导出已开始');
						// 实际应用中这里会执行导出数据逻辑
					};
				});

				// 清除历史
				clearHistoryBtn.addEventListener('click', () => {
					confirmTitle.textContent = '确认清除所有历史记录？';
					confirmMessage.textContent = '此操作将永久删除您的所有面试历史记录，且无法恢复。';
					confirmDialog.classList.remove('hidden');
					
					// 设置确认按钮动作
					confirmAction.onclick = function() {
						confirmDialog.classList.add('hidden');
						showSuccessToast('历史记录已清除');
						// 实际应用中这里会执行清除历史记录逻辑
					};
				});

				// 取消确认
				cancelConfirm.addEventListener('click', () => {
					confirmDialog.classList.add('hidden');
				});

				// 点击对话框外部关闭
				confirmDialog.addEventListener('click', (e) => {
					if (e.target === confirmDialog) {
						confirmDialog.classList.add('hidden');
					}
				});
			}

			// 初始化开关按钮
			function initToggleSwitches() {
				const toggles = document.querySelectorAll('input[type="checkbox"]');
				
				toggles.forEach(toggle => {
					// 初始化已选中的开关
					if (toggle.checked) {
						const label = toggle.nextElementSibling;
						label.classList.remove('bg-light-gray');
						label.classList.add('bg-primary');
					}
					
					toggle.addEventListener('change', function() {
						const label = this.nextElementSibling;
						
						if (this.checked) {
							label.classList.remove('bg-light-gray');
							label.classList.add('bg-primary');
						} else {
							label.classList.remove('bg-primary');
							label.classList.add('bg-light-gray');
						}
						
						// 两步验证特殊处理
						if (this.id === 'two-factor-auth') {
							if (this.checked) {
								confirmTitle.textContent = '启用两步验证？';
								confirmMessage.textContent = '启用后，每次登录都需要输入验证码。请确保您的邮箱或手机可以正常接收验证码。';
								confirmDialog.classList.remove('hidden');
								
								// 临时取消选中状态，等待用户确认
								this.checked = false;
								label.classList.remove('bg-primary');
								label.classList.add('bg-light-gray');
								
								// 设置确认按钮动作
								const self = this;
								confirmAction.onclick = function() {
									confirmDialog.classList.add('hidden');
									self.checked = true;
									label.classList.remove('bg-light-gray');
									label.classList.add('bg-primary');
									showSuccessToast('两步验证已启用');
								};
							}
						}
					});
				});
			}

			// 显示成功提示
			function showSuccessToast(message = '设置已成功保存') {
				const toastMessage = successToast.querySelector('span');
				toastMessage.textContent = message;
				
				successToast.classList.remove('hidden');
				
				// 3秒后自动隐藏
				setTimeout(() => {
					successToast.classList.add('hidden');
				}, 3000);
			}