document.getElementById('login-form').addEventListener('submit', async function(e) {
	e.preventDefault();
	const email = document.getElementById('login-email').value.trim();
	const password = document.getElementById('login-password').value.trim();

	if (!email || !password) {
		alert('请输入邮箱和密码');
		return;
	}

	try {
		const response = await fetch('/auth/login', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				email: email,
				password: password
			})
		});

		const data = await response.json();
		if (response.ok) {
			alert(data.message);
			localStorage.setItem('user', JSON.stringify(data.user));
			localStorage.setItem('token', data.token);
			localStorage.setItem('expiration', Date.now() + 3600 * 1000); // Token expires in 1 hour
            if (data.redirect) {
                location.href = data.redirect;
            } else {
                location.href = '/ui/dashboard.html';
            }
		} else {
			alert(data.detail || '登录失败');
		}
	} catch (error) {
		console.error('登录请求失败:', error);
		alert('网络错误，请稍后再试');
	}
});