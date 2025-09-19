import httpx
from typing import Optional, Dict, Any

from app.settings.config import settings


class SSOClient:
    """统一的SSO服务客户端"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=3.0)

    async def request(self, url: str, method: str = "GET", params: Optional[Dict] = None,
                     json: Optional[Dict] = None, token: Optional[str] = None) -> Dict[str, Any]:
        """统一的SSO请求方法"""
        headers = {"Authorization": f"{token}"} if token else {}
        full_url = f"{settings.SSO_BASE_URL}{url}"

        if method.upper() == "GET":
            resp = await self.client.get(full_url, params=params, headers=headers)
        elif method.upper() == "POST":
            resp = await self.client.post(full_url, params=params, json=json, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if resp.status_code != 200:
            raise Exception(f"SSO service error: {resp.status_code}")

        body = resp.json()
        if body.get("code") != 0:
            raise Exception(f"SSO API error: {body.get('msg')}")

        return body["data"]

    async def get_config(self, config_id: int, token: Optional[str] = None) -> Dict[str, Any]:
        """获取配置信息"""
        return await self.request(f"/admin-api/infra/config/get", params={"id": config_id}, token=token)

    async def get_tax_rate(self, token: Optional[str] = None) -> float:
        """获取消费税率"""
        config = await self.get_config(13, token)  # tax配置ID为13
        return float(config.get("value", 10.0))


class UserClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=3.0)

    async def get_user_by_id(self, user_id: int, token=None) -> dict:
        headers = {"Authorization": f"{token}"} if token else {}
        resp = await self.client.get(f"{settings.SSO_BASE_URL}/user/get", params={"id": user_id}, headers=headers)
        if resp.status_code != 200:
            raise Exception("SSO user service error")
        body = resp.json()
        if body["code"] != 0:
            raise Exception(f"Failed to get user: {body.get('msg')}")
        return body["data"]

    async def get_users_by_ids(self, user_ids: list[int], token: str = None) -> dict[int, dict]:
        """
        根据多个user_id批量获取用户信息。
        返回: {user_id: user_info, ...}
        """
        headers = {"Authorization": f"{token}"} if token else {}
        resp = await self.client.post(f"{settings.SSO_BASE_URL}/user/batch", json={"ids": user_ids}, headers=headers)
        if resp.status_code != 200:
            raise Exception("SSO user batch service error")
        body = resp.json()
        if body["code"] != 0:
            raise Exception(f"Failed to batch get users: {body.get('msg')}")
        return {u["id"]: u for u in body["data"]}


sso_client = SSOClient()
user_client = UserClient()
