import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.header import Header
from email import encoders, utils
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MailSender:
    """完全模拟Django EmailMultiAlternatives的实现"""

    def __init__(self):
        # 完全按照Django配置
        self.smtp_server = "m32.coreserver.jp"
        self.smtp_port = 465
        self.username = "tobprint@tob.co.jp"
        self.password = "tob1234"
        self.from_email = "tobprint@tob.co.jp"
        self.use_ssl = True
        print(f"!!! MailSender初始化: {self.smtp_server}:{self.smtp_port}")

    def get_connection(self):
        """模拟Django get_connection()"""
        if self.use_ssl:
            connection = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        else:
            connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            connection.starttls()

        connection.login(self.username, self.password)
        return connection

    def send_simple_email(self, to_email: str, subject: str, body: str):
        """完全模拟Java hutool MailUtil的发送方式"""
        print(f"!!! 发送简单邮件到: {to_email}")

        try:
            # 获取连接
            connection = self.get_connection()

            # 完全按照Java MailUtil的方式创建邮件
            msg = MIMEText(body, 'plain', 'utf-8')

            # 关键：设置所有必要的邮件头，模拟Java MailUtil
            msg['Subject'] = subject  # 不要Header编码，直接使用
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Date'] = utils.formatdate(localtime=True)
            msg['Message-ID'] = utils.make_msgid()

            # 发送
            print(f"!!! 邮件内容预览:\n{msg.as_string()[:500]}...")
            connection.sendmail(self.from_email, [to_email], msg.as_string())
            connection.quit()

            print(f"!!! 邮件发送成功: {to_email}")
            logger.info(f"邮件发送成功: {to_email}")

        except Exception as e:
            print(f"!!! 邮件发送失败: {str(e)}")
            logger.error(f"邮件发送失败: {str(e)}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str = None,
        html_body: str = None,
        attachment_files: List[tuple] = None,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None
    ):
        """完整的邮件发送功能 - 支持附件"""
        print(f"!!! send_email调用: {to_email}, 附件数量: {len(attachment_files) if attachment_files else 0}")

        try:
            connection = self.get_connection()

            # 如果有附件，使用MIMEMultipart
            if attachment_files:
                msg = MIMEMultipart()

                # 添加文本内容
                text_part = MIMEText(body or "Hello World", 'plain', 'utf-8')
                msg.attach(text_part)

                # 添加附件 - 完全按照Django方式
                for attachment in attachment_files:
                    if len(attachment) >= 2:
                        filename = attachment[0]
                        file_content = attachment[1]
                        content_type = attachment[2] if len(attachment) > 2 else "application/octet-stream"

                        # 创建附件
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file_content)
                        encoders.encode_base64(part)

                        # 设置附件头 - 按照Django方式
                        part.add_header(
                            'Content-Disposition',
                            'attachment',
                            filename=filename
                        )
                        msg.attach(part)
            else:
                # 没有附件，使用简单文本
                msg = MIMEText(body or "Hello World", 'plain', 'utf-8')

            # 设置相同的邮件头 - 保持与工作版本一致
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Date'] = utils.formatdate(localtime=True)
            msg['Message-ID'] = utils.make_msgid()

            # 处理抄送
            recipients = [to_email]
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)

            # 发送
            print(f"!!! 邮件大小: {len(msg.as_string())} 字符")
            connection.sendmail(self.from_email, recipients, msg.as_string())
            connection.quit()

            print(f"!!! 邮件发送成功: {to_email}")
            logger.info(f"邮件发送成功: {to_email}")

        except Exception as e:
            print(f"!!! 邮件发送失败: {str(e)}")
            logger.error(f"邮件发送失败: {str(e)}")
            raise

    async def send_mail_with_attachments(
        self,
        mail: str,
        attachment_files: List[tuple] = None,
        template_params: Dict[str, Any] = None
    ):
        """兼容原有接口 - 支持附件"""
        print(f"!!! send_mail_with_attachments调用: {mail}")

        if template_params:
            subject = template_params.get("subject", "EasyWork邮件")
            content = template_params.get("content", "Hello World")
            cc_str = template_params.get("cc", "")
            bcc_str = template_params.get("bcc", "")
        else:
            subject = "EasyWork邮件"
            content = "Hello World"
            cc_str = ""
            bcc_str = ""

        # 解析抄送邮箱
        cc_emails = [email.strip() for email in cc_str.split(",") if email.strip()] if cc_str else None
        bcc_emails = [email.strip() for email in bcc_str.split(",") if email.strip()] if bcc_str else None

        # 调用完整的send_email方法
        self.send_email(
            to_email=mail,
            subject=subject,
            body=content,
            attachment_files=attachment_files,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails
        )


# 全局实例
mail_sender = MailSender()


# 测试函数
def test_simple_mail():
    """最简单的邮件测试"""
    try:
        print("=== 开始最简单邮件测试 ===")
        mail_sender.send_simple_email(
            to_email="742525070@qq.com",
            subject="Hello World",
            body="这是最简单的测试邮件"
        )
        print("=== 测试成功 ===")
    except Exception as e:
        print(f"=== 测试失败: {e} ===")
        import traceback
        traceback.print_exc()


def test_attachment_mail():
    """带附件的邮件测试"""
    try:
        print("=== 开始附件邮件测试 ===")

        # 创建测试附件
        test_content = "这是测试附件内容".encode('utf-8')
        attachment_files = [
            ("测试文件.txt", test_content, "text/plain")
        ]

        mail_sender.send_email(
            to_email="742525070@qq.com",
            subject="附件测试邮件",
            body="这是带附件的测试邮件",
            attachment_files=attachment_files
        )
        print("=== 附件测试成功 ===")
    except Exception as e:
        print(f"=== 附件测试失败: {e} ===")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_simple_mail()
    print()
    test_attachment_mail()