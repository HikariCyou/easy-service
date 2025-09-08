import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_case_list(async_client: AsyncClient, db):
    """测试案件一览取得API"""
    response = await async_client.get("/api/v1/case/list")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "data" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_add_case(async_client: AsyncClient, db):
    """测试案件新规作成API"""
    case_data = {
        "title": "テストAPI案件",
        "client_company_id": 1,
        "location": "東京都渋谷区",
        "station": "渋谷駅",
        "required_skills": "Python, FastAPI, Vue.js",
        "unit_price": 650000,
        "required_members": 1,
        "status": "open",
        "description": "APIテスト用案件"
    }
    
    response = await async_client.post("/api/v1/case/add", json=case_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


@pytest.mark.asyncio
async def test_get_case_by_id(async_client: AsyncClient, db):
    """测试ID案件取得API"""
    # 先创建一个案件
    case_data = {
        "title": "ID取得テスト案件",
        "client_company_id": 1,
        "required_members": 1
    }
    
    create_response = await async_client.post("/api/v1/case/add", json=case_data)
    created_case = create_response.json()["data"]
    case_id = created_case["id"]
    
    # 通过ID取得案件
    response = await async_client.get(f"/api/v1/case/get?id={case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == case_id
    assert data["data"]["title"] == "ID取得テスト案件"


@pytest.mark.asyncio
async def test_terminate_case(async_client: AsyncClient, db):
    """测试案件终了API"""
    # 先创建一个案件
    case_data = {
        "title": "終了テスト案件",
        "client_company_id": 1,
        "required_members": 1
    }
    
    create_response = await async_client.post("/api/v1/case/add", json=case_data)
    created_case = create_response.json()["data"]
    case_id = created_case["id"]
    
    # 终了案件
    termination_data = {
        "case_id": case_id,
        "termination_date": "2024-12-31",
        "reason": "APIテスト終了",
        "terminated_by": "テストユーザー"
    }
    
    response = await async_client.post("/api/v1/case/terminate", json=termination_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["case_id"] == case_id
    assert data["data"]["terminated_contracts"] == 0