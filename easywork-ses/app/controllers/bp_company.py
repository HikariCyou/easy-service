from typing import List, Dict, Any, Optional, Tuple
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.bp import BPCompany, BPSalesRepresentative
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

    # ==================== BP営業担当者関連のメソッド ====================

    async def get_bp_sales_reps_with_filters(
        self, page: int = 1, page_size: int = 10, search: Q = None
    ) -> Tuple[List[Dict], int]:
        """BP営業担当者一覧取得（フィルタ付き）"""
        query = BPSalesRepresentative.all()
        
        if search:
            query = query.filter(search)
        
        total = await query.count()
        sales_reps = await query.prefetch_related("bp_company").order_by('-updated_at').limit(page_size).offset((page - 1) * page_size).all()
        
        data = []
        for rep in sales_reps:
            rep_dict = await rep.to_dict()
            rep_dict["bp_company_name"] = rep.bp_company.name
            data.append(rep_dict)
        
        return data, total

    async def get_bp_sales_rep_dict_by_id(self, sales_rep_id: int) -> Optional[Dict[str, Any]]:
        """ID指定でBP営業担当者取得（辞書形式）"""
        rep = await BPSalesRepresentative.get_or_none(id=sales_rep_id).prefetch_related("bp_company")
        if rep:
            rep_dict = await rep.to_dict()
            rep_dict["bp_company_name"] = rep.bp_company.name
            return rep_dict
        return None

    async def create_bp_sales_rep_dict(self, sales_rep_data: Dict[str, Any]) -> Dict[str, Any]:
        """BP営業担当者作成"""
        rep_data = sales_rep_data.dict() if hasattr(sales_rep_data, 'dict') else sales_rep_data
        
        # BP会社の存在確認
        bp_company = await BPCompany.get_or_none(id=rep_data.get('bp_company_id'))
        if not bp_company:
            raise ValueError("指定されたBP会社が見つかりませんでした")
        
        async with in_transaction():
            rep = await BPSalesRepresentative.create(**clean_dict(rep_data))
            created_rep = await BPSalesRepresentative.get(id=rep.id).prefetch_related("bp_company")
            
            rep_dict = await created_rep.to_dict()
            rep_dict["bp_company_name"] = created_rep.bp_company.name
            return rep_dict

    async def update_bp_sales_rep_dict(self, sales_rep_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """BP営業担当者更新"""
        rep_data = sales_rep_data.dict() if hasattr(sales_rep_data, 'dict') else sales_rep_data
        rep_id = rep_data.get('id')
        
        if not rep_id:
            return None
            
        rep = await BPSalesRepresentative.get_or_none(id=rep_id)
        if not rep:
            return None

        async with in_transaction():
            # IDを除外して更新
            update_data = {k: v for k, v in rep_data.items() if k != 'id'}
            await rep.update_from_dict(clean_dict(update_data))
            await rep.save()
            
            updated_rep = await BPSalesRepresentative.get(id=rep.id).prefetch_related("bp_company")
            rep_dict = await updated_rep.to_dict()
            rep_dict["bp_company_name"] = updated_rep.bp_company.name
            return rep_dict

    async def delete_bp_sales_rep(self, sales_rep_id: int) -> bool:
        """BP営業担当者削除"""
        rep = await BPSalesRepresentative.get_or_none(id=sales_rep_id)
        if rep:
            async with in_transaction():
                await rep.delete()
            return True
        return False

    async def get_sales_reps_by_company(self, bp_company_id: int) -> List[Dict[str, Any]]:
        """BP会社の営業担当者取得"""
        reps = await BPSalesRepresentative.filter(
            bp_company_id=bp_company_id, 
            is_active=True
        ).all()
        
        data = []
        for rep in reps:
            rep_dict = await rep.to_dict(exclude_fields=["bp_company_id", "gender", "is_active", "remark", "created_at", "updated_at"])
            data.append(rep_dict)
        
        return data


# グローバルインスタンス
bp_company_controller = BPCompanyController()