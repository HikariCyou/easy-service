import pytest
from datetime import date, datetime
from app.models.case import Case
from app.models.contract import Contract
from app.models.enums import CaseStatus, ContractStatus


@pytest.mark.asyncio
async def test_case_termination_with_contracts(db):
    """测试案件终了时关联契约的处理"""
    # 创建测试案件
    case = await Case.create(
        title="契約連動テスト案件",
        client_company_id=1,
        status=CaseStatus.OPEN
    )
    
    # 创建关联契约
    contract1 = await Contract.create(
        contract_type="BP",
        case=case,
        personnel_id=1,
        contract_start_date=date(2024, 1, 1),
        contract_end_date=date(2024, 12, 31),
        status=ContractStatus.ACTIVE,
        unit_price=600000
    )
    
    contract2 = await Contract.create(
        contract_type="自社",
        case=case,
        personnel_id=2,
        contract_start_date=date(2024, 2, 1),
        contract_end_date=date(2025, 1, 31),
        status=ContractStatus.ACTIVE,
        unit_price=700000
    )
    
    # 执行案件终了
    termination_date = date(2024, 6, 30)
    result = await case.terminate_case(
        termination_date=termination_date,
        reason="プロジェクト完了",
        terminated_by="プロジェクトマネージャー"
    )
    
    # 验证案件状态
    await case.refresh_from_db()
    assert case.status == CaseStatus.CLOSED
    assert case.end_date == termination_date
    
    # 验证契约状态变更
    await contract1.refresh_from_db()
    await contract2.refresh_from_db()
    
    assert contract1.status == ContractStatus.TERMINATED
    assert contract2.status == ContractStatus.TERMINATED
    assert contract1.actual_end_date == termination_date
    assert contract2.actual_end_date == termination_date
    
    # 验证返回结果
    assert result["terminated_contracts"] == 2
    assert len(result["contract_details"]) == 2


@pytest.mark.asyncio
async def test_case_termination_no_active_contracts(db):
    """测试没有有效契约时的案件终了"""
    # 创建测试案件
    case = await Case.create(
        title="無契約テスト案件",
        client_company_id=1,
        status=CaseStatus.OPEN
    )
    
    # 创建已终了的契约
    terminated_contract = await Contract.create(
        contract_type="BP",
        case=case,
        personnel_id=1,
        status=ContractStatus.TERMINATED,
        unit_price=500000
    )
    
    # 执行案件终了
    result = await case.terminate_case(
        termination_date=date(2024, 6, 30),
        reason="案件終了"
    )
    
    # 验证结果
    assert result["terminated_contracts"] == 0
    assert "有効な契約は見つかりませんでした" in result["message"]
    
    # 验证已终了的契约状态不变
    await terminated_contract.refresh_from_db()
    assert terminated_contract.status == ContractStatus.TERMINATED