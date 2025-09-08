from typing import Optional

from fastapi import APIRouter, Query
from tortoise.exceptions import DoesNotExist

from app.models.bank import Bank, BankAccount, BankBranch
from app.schemas import Fail, Success
from app.schemas.bank import (AddBankAccountSchema, BankAccountResponseSchema,
                              BankBranchSchema, BankSchema, BankSyncResultSchema,
                              UpdateBankAccountSchema)
from app.utils.bank_service import bank_service

router = APIRouter()


# ==================== 銀行データ同期関連のAPI ====================

@router.post("/sync/banks", summary="銀行データ同期")
async def sync_banks():
    """外部APIから銀行一覧を取得してローカルDBに同期"""
    try:
        updated_count = await bank_service.sync_banks()
        return Success(data={"banks": updated_count}, msg=f"{updated_count}件の銀行データを同期しました")
    except Exception as e:
        return Fail(msg=f"銀行データ同期エラー: {str(e)}")


@router.post("/sync/branches/{bank_code}", summary="指定銀行の支店データ同期")
async def sync_bank_branches(bank_code: str):
    """指定銀行の支店データを外部APIから取得してローカルDBに同期"""
    try:
        updated_count = await bank_service.sync_branches(bank_code)
        return Success(data={"branches": updated_count}, msg=f"{updated_count}件の支店データを同期しました")
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"支店データ同期エラー: {str(e)}")


@router.post("/sync/all-branches", summary="全銀行の支店データ同期")
async def sync_all_branches(limit: Optional[int] = Query(None, description="処理する銀行数の制限")):
    """全銀行の支店データを同期"""
    try:
        result = await bank_service.sync_all_branches(limit_banks=limit)
        return Success(
            data=result, 
            msg=f"{result['banks']}行の銀行で{result['branches']}件の支店データを同期しました"
        )
    except Exception as e:
        return Fail(msg=f"全支店データ同期エラー: {str(e)}")


# ==================== 銀行検索関連のAPI ====================

@router.get("/banks", summary="銀行一覧取得")
async def get_banks(
    keyword: Optional[str] = Query(None, description="銀行名検索キーワード"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(50, ge=1, le=200),
):
    """ローカルDBから銀行一覧を取得"""
    try:
        if keyword:
            banks = await bank_service.search_banks(keyword)
        else:
            banks = await bank_service.get_banks()
        
        total = len(banks)
        offset = (page - 1) * pageSize
        banks_page = banks[offset:offset + pageSize]
        
        data = []
        for bank in banks_page:
            bank_data = await bank.to_dict()
            data.append(bank_data)
        
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/branches/{bank_code}", summary="指定銀行の支店一覧取得")
async def get_bank_branches(
    bank_code: str,
    keyword: Optional[str] = Query(None, description="支店名検索キーワード"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(50, ge=1, le=200),
):
    """指定銀行の支店一覧を取得"""
    try:
        # 支店データが存在しない場合は自動同期
        if not await bank_service.is_branch_data_exists(bank_code):
            await bank_service.sync_branches(bank_code)
        
        if keyword:
            branches = await bank_service.search_branches(bank_code, keyword)
        else:
            branches = await bank_service.get_branches(bank_code)
        
        total = len(branches)
        offset = (page - 1) * pageSize
        branches_page = branches[offset:offset + pageSize]
        
        data = []
        for branch in branches_page:
            branch_data = await branch.to_dict()
            branch_data["bank_code"] = branch.bank.code
            branch_data["bank_name"] = branch.bank.name
            data.append(branch_data)
        
        return Success(data=data, total=total)
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


# ==================== BP会社銀行口座管理API ====================

@router.get("/accounts", summary="銀行口座一覧取得")
async def get_bank_accounts(
    bp_company_id: Optional[int] = Query(None, description="BP会社ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """銀行口座一覧を取得"""
    try:
        query = BankAccount.all().prefetch_related("bank", "branch", "bp_company")
        
        if bp_company_id is not None:
            query = query.filter(bp_company_id=bp_company_id)
        
        total = await query.count()
        offset = (page - 1) * pageSize
        accounts = await query.order_by("-is_default", "-updated_at").offset(offset).limit(pageSize)
        
        data = []
        for account in accounts:
            account_data = await account.to_dict()
            account_data["bp_company_name"] = account.bp_company.name
            account_data["bank_code"] = account.bank.code
            account_data["bank_name"] = account.bank.name
            account_data["branch_code"] = account.branch.code
            account_data["branch_name"] = account.branch.name
            data.append(account_data)
        
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/accounts/{account_id}", summary="銀行口座詳細取得")
async def get_bank_account(account_id: int):
    """指定IDの銀行口座詳細を取得"""
    try:
        account = await BankAccount.get(id=account_id).prefetch_related("bank", "branch", "bp_company")
        
        account_data = await account.to_dict()
        account_data["bp_company_name"] = account.bp_company.name
        account_data["bank_code"] = account.bank.code
        account_data["bank_name"] = account.bank.name
        account_data["branch_code"] = account.branch.code
        account_data["branch_name"] = account.branch.name
        
        return Success(data=account_data)
    except DoesNotExist:
        return Fail(msg="指定された銀行口座が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/accounts", summary="銀行口座新規作成")
async def add_bank_account(account_data: AddBankAccountSchema):
    """新しい銀行口座を作成"""
    try:
        # デフォルト口座の場合、同じBP会社の他の口座のデフォルトを解除
        if account_data.is_default:
            await BankAccount.filter(bp_company_id=account_data.bp_company_id).update(is_default=False)
        
        account = await BankAccount.create(**account_data.model_dump())
        created_account = await BankAccount.get(id=account.id).prefetch_related("bank", "branch", "bp_company")
        
        account_dict = await created_account.to_dict()
        account_dict["bp_company_name"] = created_account.bp_company.name
        account_dict["bank_code"] = created_account.bank.code
        account_dict["bank_name"] = created_account.bank.name
        account_dict["branch_code"] = created_account.branch.code
        account_dict["branch_name"] = created_account.branch.name
        
        return Success(data=account_dict)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/accounts", summary="銀行口座更新")
async def update_bank_account(account_data: UpdateBankAccountSchema):
    """銀行口座情報を更新"""
    try:
        account = await BankAccount.get(id=account_data.id)
        
        # デフォルト口座の場合、同じBP会社の他の口座のデフォルトを解除
        update_data = account_data.model_dump(exclude_unset=True, exclude={"id"})
        if update_data.get("is_default"):
            await BankAccount.filter(
                bp_company_id=update_data.get("bp_company_id", account.bp_company_id)
            ).update(is_default=False)
        
        for field, value in update_data.items():
            setattr(account, field, value)
        
        await account.save()
        updated_account = await BankAccount.get(id=account.id).prefetch_related("bank", "branch", "bp_company")
        
        account_dict = await updated_account.to_dict()
        account_dict["bp_company_name"] = updated_account.bp_company.name
        account_dict["bank_code"] = updated_account.bank.code
        account_dict["bank_name"] = updated_account.bank.name
        account_dict["branch_code"] = updated_account.branch.code
        account_dict["branch_name"] = updated_account.branch.name
        
        return Success(data=account_dict)
    except DoesNotExist:
        return Fail(msg="指定された銀行口座が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/accounts/{account_id}", summary="銀行口座削除")
async def delete_bank_account(account_id: int):
    """銀行口座を削除"""
    try:
        account = await BankAccount.get(id=account_id)
        await account.delete()
        return Success(msg="銀行口座を削除しました")
    except DoesNotExist:
        return Fail(msg="指定された銀行口座が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/accounts/by-company/{bp_company_id}", summary="BP会社の銀行口座取得")
async def get_accounts_by_company(bp_company_id: int):
    """指定BP会社の銀行口座一覧を取得"""
    try:
        accounts = await BankAccount.filter(
            bp_company_id=bp_company_id,
            is_active=True
        ).prefetch_related("bank", "branch").order_by("-is_default", "id")
        
        data = []
        for account in accounts:
            account_data = await account.to_dict(exclude_fields=["bp_company_id", "remark", "created_at", "updated_at"])
            account_data["bank_code"] = account.bank.code
            account_data["bank_name"] = account.bank.name
            account_data["branch_code"] = account.branch.code
            account_data["branch_name"] = account.branch.name
            data.append(account_data)
        
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/accounts/{account_id}/set-default", summary="デフォルト口座設定")
async def set_default_account(account_id: int):
    """指定口座をデフォルトに設定"""
    try:
        account = await BankAccount.get(id=account_id)
        
        # 同じBP会社の他の口座のデフォルトを解除
        await BankAccount.filter(bp_company_id=account.bp_company_id).update(is_default=False)
        
        # 指定口座をデフォルトに設定
        account.is_default = True
        await account.save()
        
        return Success(msg="デフォルト口座を設定しました")
    except DoesNotExist:
        return Fail(msg="指定された銀行口座が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))