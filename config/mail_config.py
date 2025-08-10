# QQ邮箱配置
MAIL_CONFIG = {
    # Flask-Mail配置
    'MAIL_SERVER': 'smtp.qq.com',  # QQ邮箱SMTP服务器
    'MAIL_PORT': 465,  # SMTP端口（QQ邮箱推荐使用465）
    'MAIL_USE_SSL': True,  # 必须使用SSL连接
    'MAIL_USE_TLS': False,
    'MAIL_USERNAME': 'Your email@qq.com',  # 发件人邮箱
    'MAIL_PASSWORD': 'xdpxqdzbhiradeci', 
    # 获取新授权码后，请将上面的旧授权码替换为新的授权码
    'MAIL_DEFAULT_SENDER': 'Your email@qq.com',  # 默认发件人
    'MAIL_DEBUG': True,
    
    # 额外配置（用于EmailService类）
    'SENDER_NAME': 'AI面试系统',  # 发件人名称
    'RETRY_COUNT': 5,  # 增加重试次数
    'RETRY_DELAY': 3,  # 增加重试延迟(秒)
    'SMTP_TIMEOUT': 30  # 设置SMTP超时时间(秒)
}

# 验证码配置
VERIFICATION_CODE_CONFIG = {
    'expire_minutes': 1,  # 验证码有效期（分钟）
    'code_length': 6,  # 验证码长度
    'subject': 'AI面试系统 - 邮箱验证码',  # 邮件主题
    'template': '''
<div style="font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; max-width: 600px; margin: 0 auto; padding: 25px; border: 1px solid #e0f0ff; border-radius: 12px; background-color: #f9fcff; box-shadow: 0 3px 15px rgba(100, 149, 237, 0.1);">
    <div style="text-align: center; margin-bottom: 25px;">
        <h2 style="color: #4a90e2; margin: 0; font-size: 24px; font-weight: 500;">AI面试系统</h2>
        <div style="width: 80px; height: 3px; background: linear-gradient(90deg, #4a90e2, #5bc0de); margin: 10px auto;"></div>
    </div>
    <p style="color: #334e68; font-size: 16px; line-height: 1.6;">尊敬的用户：</p>
    <p style="color: #334e68; font-size: 16px; line-height: 1.6;">您好！感谢您注册AI面试系统。您的邮箱验证码为：</p>
    <div style="background: linear-gradient(135deg, #eef7ff, #d1e7fe); padding: 15px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 8px; color: #2c6ecb; margin: 25px 0; border-radius: 8px; border: 1px dashed #96c6ff;">{code}</div>
    <p style="color: #5a6b7c; font-size: 14px; line-height: 1.6;">验证码有效期为<span style="color: #2c6ecb; font-weight: bold;">{expire_minutes}分钟</span>，请勿将验证码泄露给他人。</p>
    <p style="color: #5a6b7c; font-size: 14px; line-height: 1.6;">如果您没有进行相关操作，请忽略此邮件。</p>
    <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #e6f2ff;">
        <p style="color: #889aad; font-size: 12px; text-align: center; margin: 5px 0;">此邮件由系统自动发送，请勿直接回复</p>
        <p style="color: #889aad; font-size: 12px; text-align: center; margin: 5px 0;">&copy; 2025 AI面试系统 版权所有</p>
    </div>
</div>
'''
}
