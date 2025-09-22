import logging
import smtplib
from email import encoders, utils
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MailSender:
    def __init__(self):
        # 完全按照Django配置
        self.smtp_server = "m32.coreserver.jp"
        self.smtp_port = 465
        self.username = "tobprint@tob.co.jp"
        self.password = "tob1234"
        self.from_email = "tobprint@tob.co.jp"
        self.use_ssl = True

    def get_connection(self):
        if self.use_ssl:
            connection = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
        else:
            connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            connection.starttls()

        connection.login(self.username, self.password)
        return connection

    def send_simple_email(self, to_email: str, subject: str, body: str, is_html: bool = True):
        try:
            # 获取连接
            connection = self.get_connection()

            # 默认发送HTML邮件，支持富文本格式
            content_type = "html" if is_html else "plain"
            msg = MIMEText(body, content_type, "utf-8")

            # 关键：设置所有必要的邮件头，模拟Java MailUtil
            msg["Subject"] = subject  # 不要Header编码，直接使用
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Date"] = utils.formatdate(localtime=True)
            msg["Message-ID"] = utils.make_msgid()

            # 发送
            connection.sendmail(self.from_email, [to_email], msg.as_string())
            connection.quit()
            logger.info(f"邮件发送成功: {to_email}")

        except Exception as e:
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
        bcc_emails: List[str] = None,
        is_html: bool = True,
    ):
        try:
            connection = self.get_connection()

            # 确定邮件内容和类型
            email_content = html_body or body or "Hello World"
            content_type = "html" if (is_html or html_body) else "plain"

            # 如果有附件，使用MIMEMultipart
            if attachment_files:
                msg = MIMEMultipart()

                # 添加文本内容 - 支持HTML格式
                text_part = MIMEText(email_content, content_type, "utf-8")
                msg.attach(text_part)

                # 添加附件 - 完全按照Django方式
                for attachment in attachment_files:
                    if len(attachment) >= 2:
                        filename = attachment[0]
                        file_content = attachment[1]

                        # 创建附件
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(file_content)
                        encoders.encode_base64(part)

                        # 设置附件头 - 按照Django方式
                        part.add_header("Content-Disposition", "attachment", filename=filename)
                        msg.attach(part)
            else:
                # 没有附件，使用HTML或纯文本
                msg = MIMEText(email_content, content_type, "utf-8")

            # 设置完整的邮件头，包括编码处理
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Date"] = utils.formatdate(localtime=True)
            msg["Message-ID"] = utils.make_msgid()

            # 处理抄送
            recipients = [to_email]
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)

            # 发送
            connection.sendmail(self.from_email, recipients, msg.as_string())
            connection.quit()

            logger.info(f"邮件发送成功: {to_email}")

        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            raise

    async def send_mail_with_attachments(
        self, mail: str, attachment_files: List[tuple] = None, template_params: Dict[str, Any] = None
    ):
        # 获取邮件内容
        if template_params:
            subject = template_params.get("subject", "HTML附件测试邮件")
            content = template_params.get("content", "<h1>测试邮件</h1>")
        else:
            subject = "HTML附件测试邮件"
            content = "<h1>测试邮件</h1>"

        html_content = f"""
           <!DOCTYPE html>
            <html lang="ja">
            <head>
            <meta charset="UTF-8">
            </head>
            <body>
            {content}
            </body>
            </html>
        """

        mail_sender.send_email(
            to_email=mail,
            subject=subject,
            html_body=html_content,
            attachment_files=attachment_files,
            is_html=True,
        )


# 全局实例
mail_sender = MailSender()


# 测试函数
def test_simple_mail():
    """HTML邮件测试"""
    try:
        print("=== 开始HTML邮件测试 ===")
        html_content = """
        <html>
        <body>
            <h1 style="color: #333;">EasyWork 系统通知</h1>
            <p>这是一封<strong>HTML格式</strong>的测试邮件。</p>
            <ul>
                <li>支持<em>富文本</em>格式</li>
                <li>支持<span style="color: red;">颜色</span>样式</li>
                <li>支持链接：<a href="https://www.example.com">点击这里</a></li>
            </ul>
            <hr>
            <p style="font-size: 12px; color: #666;">
                这是由 EasyWork 系统自动发送的邮件。
            </p>
        </body>
        </html>
        """
        mail_sender.send_simple_email(to_email="742525070@qq.com", subject="HTML邮件测试", body=html_content, is_html=True)
        print("=== HTML邮件测试成功 ===")
    except Exception as e:
        print(f"=== 测试失败: {e} ===")
        import traceback

        traceback.print_exc()


def test_attachment_mail():
    """带附件的HTML邮件测试"""
    try:
        print("=== 开始HTML附件邮件测试 ===")

        # 创建测试附件
        test_content = "这是测试附件内容".encode("utf-8")
        attachment_files = [("测试文件.txt", test_content)]

        # 清理HTML内容，去掉可能有问题的字符
        real_content = """
        <!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
</head>
<body>
<p><strong>株式会社KYO! 御中</strong></p>
<p>いつもお世話になっております。</p>
<p>株式会社TOBでございます。</p>
<p>次の通りお送り致しますので、ご確認、ご対応の程お願い申し上げます。</p>
<p>なお、添付ファイルの解凍パスワードは、追って別メールでお知らせ致します。</p>

<p><strong>《送付物》</strong></p>
<p>「注文書」</p>
<p>「注文請書」</p>
<p>各1通</p>

<p><strong>《お願い》</strong></p>
<p>1.8月分の御注文内容の御確認</p>
<p> 「注文書」</p>
<p>2.問題有り</p>
<p> メールに記載し御返信</p>
<p>3.問題無し</p>
<p> 「注文請書」に署名・捺印の上、PDFをご返送ください。</p>

<p>締切：8月15日</p>
<p>御手数ではございますが、ご協力の程お願い申し上げます。</p>
</body>
</html>
        """

        mail_sender.send_email(
            to_email="742525070@qq.com",
            subject="真实内容测试邮件",
            html_body=real_content,
            attachment_files=attachment_files,
            is_html=True,
        )
        print("=== 真实内容测试成功 ===")
    except Exception as e:
        print(f"=== 真实内容测试失败: {e} ===")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_simple_mail()
    print()
    test_attachment_mail()
