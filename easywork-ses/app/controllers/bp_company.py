from typing import List, Dict, Any, Optional, Tuple
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.bp import BPCompany
from app.models.enums import BPCompanyStatus
from app.utils.common import clean_dict


class BPCompanyController:
    """協力会社管理コントローラー"""

    def __init__(self):
        pass

    async def get_bp_companies_with_filters(
        self, page: int = 1, page_size: int = 10, name: str = None,
        representative: str = None, status: str = None
    ) -> Tuple[List[Dict], int]:
        """協力会社一覧取得（フィルタ付き）"""
        query = BPCompany.all()
        
        if name:
            query = query.filter(name__icontains=name)
        if representative:
            query = query.filter(representative__icontains=representative)
        if status:
            query = query.filter(status=status)
        
        total = await query.count()
        companies = await query.order_by('-updated_at').limit(page_size).offset((page - 1) * page_size).all()
        
        data = []
        for company in companies:
            company_dict = await company.to_dict()
            data.append(company_dict)
        
        return data, total

    async def get_bp_company_dict_by_id(self, bp_company_id: int) -> Optional[Dict[str, Any]]:
        """ID指定で協力会社取得（辞書形式）"""
        company = await BPCompany.get_or_none(id=bp_company_id)
        if company:
            return await company.to_dict()
        return None

    async def create_bp_company_dict(self, bp_company: Dict[str, Any]) -> Dict[str, Any]:
        """協力会社作成"""
        company_data = bp_company.dict() if hasattr(bp_company, 'dict') else bp_company
        
        async with in_transaction():
            company = await BPCompany.create(**clean_dict(company_data))
            return await company.to_dict()

    async def update_bp_company_dict(self, bp_company: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """協力会社更新"""
        company_data = bp_company.dict() if hasattr(bp_company, 'dict') else bp_company
        company_id = company_data.get('id')
        
        if not company_id:
            return None
            
        company = await BPCompany.get_or_none(id=company_id)
        if not company:
            return None

        async with in_transaction():
            # IDを除外して更新
            update_data = {k: v for k, v in company_data.items() if k != 'id'}
            await company.update_from_dict(clean_dict(update_data))
            await company.save()
            return await company.to_dict()

    async def delete_bp_company(self, bp_company_id: int) -> bool:
        """協力会社削除"""
        company = await BPCompany.get_or_none(id=bp_company_id)
        if company:
            async with in_transaction():
                await company.delete()
            return True
        return False


# グローバルインスタンス
bp_company_controller = BPCompanyController()