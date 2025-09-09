#!/usr/bin/env python3
"""
契約期限チェックスクリプト
定期実行して契約の期限をチェックし、人材の稼働状態を自動更新
"""

import asyncio
from datetime import date, timedelta
from tortoise import Tortoise

from app.models.contract import Contract
from app.models.personnel import Personnel
from app.models.enums import ContractStatus, EmploymentStatus


async def check_expired_contracts():
    """期限切れの契約をチェックして自動終了"""
    today = date.today()
    
    # 期限切れの有効契約を取得
    expired_contracts = await Contract.filter(
        status=ContractStatus.ACTIVE,
        contract_end_date__lt=today
    ).prefetch_related("personnel")
    
    print(f"Found {len(expired_contracts)} expired contracts")
    
    for contract in expired_contracts:
        print(f"Terminating expired contract: {contract.contract_number}")
        
        # 契約を終了状態に変更
        contract.status = ContractStatus.TERMINATED
        await contract.save()
        
        # 人材の稼働状態を自動更新
        if contract.personnel:
            await contract.personnel.check_and_update_status_by_contracts()


async def check_expiring_soon_contracts(days_ahead: int = 30):
    """期限間近の契約をチェック（通知用）"""
    today = date.today()
    expiry_date = today + timedelta(days=days_ahead)
    
    # 期限間近の有効契約を取得
    expiring_contracts = await Contract.filter(
        status=ContractStatus.ACTIVE,
        contract_end_date__gte=today,
        contract_end_date__lte=expiry_date
    ).prefetch_related("personnel", "case")
    
    print(f"Found {len(expiring_contracts)} contracts expiring within {days_ahead} days:")
    
    for contract in expiring_contracts:
        days_remaining = (contract.contract_end_date - today).days
        print(f"  - Contract {contract.contract_number}: {days_remaining} days remaining")
        print(f"    Personnel: {contract.personnel.name if contract.personnel else 'N/A'}")
        print(f"    Case: {contract.case.case_name if contract.case else 'N/A'}")


async def update_all_personnel_status():
    """全人材の稼働状態を契約に基づいて一括更新"""
    personnel_list = await Personnel.filter(
        employment_status__in=[EmploymentStatus.WORKING, EmploymentStatus.AVAILABLE]
    ).all()
    
    print(f"Updating employment status for {len(personnel_list)} personnel")
    
    for personnel in personnel_list:
        await personnel.check_and_update_status_by_contracts()


async def main():
    """メイン実行関数"""
    # Tortoise ORM初期化
    await Tortoise.init(
        db_url="mysql://root:password@localhost:3306/easywork_ses",  # 実際の設定に合わせて調整
        modules={"models": ["app.models"]}
    )
    
    print("=" * 50)
    print(f"Contract Expiry Check - {date.today()}")
    print("=" * 50)
    
    try:
        # 1. 期限切れ契約の自動終了
        print("\n1. Checking expired contracts...")
        await check_expired_contracts()
        
        # 2. 期限間近契約の確認
        print("\n2. Checking contracts expiring soon...")
        await check_expiring_soon_contracts(30)
        
        # 3. 全人材の稼働状態更新
        print("\n3. Updating all personnel employment status...")
        await update_all_personnel_status()
        
        print("\nContract expiry check completed successfully!")
        
    except Exception as e:
        print(f"Error during contract expiry check: {e}")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())