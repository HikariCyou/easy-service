import httpx
from typing import Dict, Any

from app.models.order import Order
from app.settings import settings


class MailController:
    """邮件模板控制器"""

    @staticmethod
    async def get_filled_template(template_id: int, order_id: int = None, token: str = None) -> Dict[str, Any]:
        """获取填充后的邮件模板"""
        
        # 从SSO获取模板
        template_data = await MailController._fetch_template_from_sso(template_id, token)
        
        # 填充模板数据
        if order_id:
            filled_content = await MailController._fill_order_template(template_data, order_id)
        else:
            # 如果没有业务数据，返回原模板
            filled_content = template_data["content"]
        
        return {"content": filled_content}

    @staticmethod
    async def _fetch_template_from_sso(template_id: int, token: str = None) -> Dict[str, Any]:
        """从SSO获取邮件模板"""
        url = f"{settings.SSO_BASE_URL}/mail-template/get"
        headers = {"Authorization": f"{token}"} if token else {}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"id": template_id}, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if result["code"] != 0:
                raise Exception(f"获取模板失败: {result.get('msg', '未知错误')}")
            
            return result["data"]

    @staticmethod
    async def _fill_order_template(template_data: Dict[str, Any], order_id: int) -> Dict[str, Any]:
        """填充注文書相关模板"""
        # 获取注文書数据
        order = await Order.get_or_none(id=order_id).select_related(
            "personnel__bp_employee_detail__bp_company",
            "case"
        )
        
        if not order:
            raise Exception("注文書が見つかりません")
        
        # 获取相关数据
        personnel = await order.personnel
        bp_employee_detail = await personnel.bp_employee_detail  
        bp_company = await bp_employee_detail.bp_company
        case = await order.case
        
        year, month = order.year_month.split('-')
        
        # 构建替换数据
        replace_data = {
            "partner": bp_company.name,
            "company": "株式会社TOB", 
            "month": f"{int(month)}",
            "order_number": order.order_number,
            "personnel_name": personnel.name
        }
        
        # 替换模板中的占位符
        filled_content = template_data["content"]
        
        for key, value in replace_data.items():
            filled_content = filled_content.replace(f"{{{key}}}", str(value))
        
        return filled_content