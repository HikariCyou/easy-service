from typing import Optional, List
from pydantic import BaseModel, Field


class MailTemplateRequest(BaseModel):
    """邮件模板请求"""
    template_id: int = Field(..., description="模板ID")
    order_id: Optional[int] = Field(None, description="注文書ID")


class SendMailRequest(BaseModel):
    """发送邮件请求"""
    to: str = Field(..., description="收件人邮箱")
    cc: Optional[List[str]] = Field(None, description="抄送邮箱列表")
    bcc: Optional[List[str]] = Field(None, description="密送邮箱列表")
    subject: str = Field(..., description="邮件主题")
    content: str = Field(..., description="邮件内容")
    
    # 密码邮件相关
    password_subject: Optional[str] = Field(None, description="密码邮件主题")
    password_content: Optional[str] = Field(None, description="密码邮件内容")