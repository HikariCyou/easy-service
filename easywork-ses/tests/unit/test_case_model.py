from datetime import date, datetime

import pytest

from app.models.case import Case, CaseCandidate
from app.models.enums import CandidateStatus, CaseStatus


@pytest.mark.asyncio
async def test_case_creation(db):
    """测试案件创建"""
    case = await Case.create(
        title="测试案件",
        client_company_id=1,
        location="東京都",
        station="新宿駅",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        required_skills="Python, FastAPI",
        unit_price=600000,
        required_members=2,
        status=CaseStatus.OPEN,
        description="テスト案件です",
    )

    assert case.id is not None
    assert case.title == "測試案件"
    assert case.status == CaseStatus.OPEN
    assert case.required_members == 2


@pytest.mark.asyncio
async def test_case_terminate(db):
    """测试案件终了功能"""
    # 创建测试案件
    case = await Case.create(title="終了テスト案件", client_company_id=1, status=CaseStatus.OPEN)

    # 执行终了操作
    result = await case.terminate_case(termination_date=date(2024, 12, 31), reason="テスト終了", terminated_by="テストユーザー")

    # 验证案件状态变更
    await case.refresh_from_db()
    assert case.status == CaseStatus.CLOSED
    assert case.end_date == date(2024, 12, 31)

    # 验证返回结果
    assert result["message"] is not None
    assert result["case_id"] == case.id
    assert result["terminated_contracts"] == 0  # 没有关联契约的情况


@pytest.mark.asyncio
async def test_case_candidate_creation(db):
    """测试案件候选者创建"""
    case = await Case.create(title="候補者テスト案件", client_company_id=1)

    candidate = await CaseCandidate.create(
        case=case,
        personnel_id=1,
        recommend_date=date(2024, 1, 15),
        status=CandidateStatus.PENDING,
        proposed_unit_price=550000,
    )

    assert candidate.id is not None
    assert candidate.case_id == case.id
    assert candidate.status == CandidateStatus.PENDING
    assert candidate.proposed_unit_price == 550000
