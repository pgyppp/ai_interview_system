from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from email.mime.text import MIMEText
import random
import smtplib
import string
import time
import socket
from config.mail_config import MAIL_CONFIG, VERIFICATION_CODE_CONFIG

class EmailService:
    def __init__(self):
        self.smtp_server = MAIL_CONFIG['MAIL_SERVER']
        self.smtp_port = MAIL_CONFIG['MAIL_PORT']
        self.sender = MAIL_CONFIG['MAIL_USERNAME']
        self.password = MAIL_CONFIG['MAIL_PASSWORD']
        self.use_ssl = MAIL_CONFIG['MAIL_USE_SSL']
        self.sender_name = MAIL_CONFIG.get('SENDER_NAME', '本草智鉴')
        self.max_retries = MAIL_CONFIG.get('RETRY_COUNT', 5)
        self.retry_delay = MAIL_CONFIG.get('RETRY_DELAY', 3)
        self.smtp_timeout = MAIL_CONFIG.get('SMTP_TIMEOUT', 30)

    def generate_verification_code(self, length=6):
        return ''.join(random.choices(string.digits, k=length))

    def send_verification_email(self, email, code):
        for attempt in range(self.max_retries):
            try:
                message = MIMEMultipart()
                # 根据RFC5322和RFC2047标准，正确设置From头
                # 如果发件人名称包含非ASCII字符，需要使用Header进行编码

                # 根据RFC5322标准正确格式化发件人信息

                from email.header import Header
                # 处理中文发件人名称编码
                encoded_name = Header(self.sender_name, 'utf-8').encode()
                message['From'] = formataddr((encoded_name, self.sender))
                message['To'] = email
                message['Subject'] = Header(VERIFICATION_CODE_CONFIG['subject'], 'utf-8')
                html_content = VERIFICATION_CODE_CONFIG['template'].format(
                    code=code,
                    expire_minutes=VERIFICATION_CODE_CONFIG['expire_minutes']
                )
                message.attach(MIMEText(html_content, 'html', 'utf-8'))
                socket.setdefaulttimeout(self.smtp_timeout)
                if self.use_ssl:
                    smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=self.smtp_timeout)
                else:
                    smtp = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.smtp_timeout)
                    smtp.starttls()
                smtp.set_debuglevel(1)
                login_success = False
                for login_attempt in range(3):
                    try:
                        smtp.login(self.sender, self.password)
                        login_success = True
                        break
                    except smtplib.SMTPServerDisconnected as e:
                        if login_attempt < 2:
                            if self.use_ssl:
                                smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=self.smtp_timeout)
                            else:
                                smtp = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.smtp_timeout)
                                smtp.starttls()
                            smtp.set_debuglevel(1)
                            time.sleep(2)
                        else:
                            raise
                if not login_success:
                    raise smtplib.SMTPAuthenticationError(535, "登录失败，请检查邮箱和授权码设置")
                # 使用UTF-8编码发送邮件，而不是默认的ASCII
                smtp.sendmail(self.sender, [email], message.as_string().encode('utf-8'))
                smtp.quit()
                return True, "验证码发送成功"
            except smtplib.SMTPAuthenticationError as e:
                return False, f"邮箱服务器认证失败: {str(e)}"
            except smtplib.SMTPServerDisconnected as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * 2)
                    continue
                return False, "邮件服务器连接断开，请稍后再试"
            except smtplib.SMTPException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False, f"邮件服务器错误: {str(e)}"
            except socket.timeout as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False, "邮件服务器连接超时，请稍后再试"
            except Exception as e:
                return False, f"发送验证码失败: {str(e)}"