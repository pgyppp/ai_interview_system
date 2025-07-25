document.addEventListener('DOMContentLoaded', async function () {

    // 发送验证码逻辑
    const sendVerificationCodeBtn = document.getElementById('send-verification-code');

    if (sendVerificationCodeBtn) {
        sendVerificationCodeBtn.addEventListener('click', async function () {
        const email = document.getElementById('register-email').value.trim();
        if (!email) {
            alert('请输入邮箱');
            return;
        }

        if (!isValidEmail(email)) {
            alert('请输入有效的邮箱地址');
            return;
        }

        const sendBtn = this;
        sendBtn.disabled = true;
        sendBtn.textContent = '发送中...';

        const { ok, data } = await apiRequest('/auth/send_verification_code', { email });

        if (ok) {
            alert(data.message || '验证码已发送');
            let countdown = data.cooldown || 60;
            const timer = setInterval(() => {
                countdown--;
                if (countdown > 0) {
                    sendBtn.textContent = `重新发送 (${countdown}s)`;
                } else {
                    clearInterval(timer);
                    sendBtn.textContent = '发送验证码';
                    sendBtn.disabled = false;
                }
            }, 1000);
        } else {
            alert(data.detail || '发送失败');
            sendBtn.disabled = false;
            sendBtn.textContent = '发送验证码';
        }
    });
    }

    // 注册表单提交逻辑
    document.getElementById('register-form').addEventListener('submit', async function (e) {
        e.preventDefault();

        const name = document.getElementById('register-name').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm-password').value;
        const verificationCode = document.getElementById('register-verification-code').value.trim();

        if (!name || !email || !password || !confirmPassword || !verificationCode) {
            alert('请填写完整信息');
            return;
        }

        if (!isValidEmail(email)) {
            alert('请输入有效的邮箱地址');
            return;
        }

        if (!isValidPassword(password)) {
            alert('密码至少8位，并包含字母和数字');
            return;
        }

        if (password !== confirmPassword) {
            alert('两次输入的密码不一致');
            return;
        }

        const { ok, data } = await apiRequest('/auth/register', {
            username: name,
            email: email,
            password: password,
            confirm_password: confirmPassword,
            verification_code: verificationCode
         });

        if (ok) {
            alert(data.message || '注册成功');
            window.location.href = data.redirect || 'index.html';
        } else {
            alert(data.detail || '注册失败');
        }
    });
});

// 工具方法：通用 fetch 封装
async function apiRequest(url, body) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        const data = await response.json();
        if (response.ok && data.redirect) {
            window.location.href = data.redirect;
        }
        return { ok: response.ok, data };
    } catch (error) {
        console.error(`请求失败: ${url}`, error);
        return { ok: false, data: { detail: '网络错误，请稍后再试' } };
    }
}

// 校验邮箱格式
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 校验密码强度
function isValidPassword(password) {
    const re = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$/;
    return re.test(password);
}