import httpx

SSO_BASE_URL = "http://13.158.219.191:8081/admin-api/system/user"


class UserClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=3.0)

    async def get_user_by_id(self, user_id: int, token = None) -> dict:
        headers = {"Authorization": f"{token}"} if token else {}
        resp = await self.client.get(f"{SSO_BASE_URL}/get", params={"id": user_id}, headers=headers)
        if resp.status_code != 200:
            raise Exception("SSO user service error")
        body = resp.json()
        if body["code"] != 0:
            raise Exception(f"Failed to get user: {body.get('msg')}")
        return body["data"]

    async def get_users_by_ids(self, user_ids: list[int] , token: str = None) -> dict[int, dict]:
        """
        根据多个user_id批量获取用户信息。
        返回: {user_id: user_info, ...}
        """
        headers = {"Authorization": f"{token}"} if token else {}
        resp = await self.client.post(f"{SSO_BASE_URL}/batch", json={"ids": user_ids}, headers=headers)
        if resp.status_code != 200:
            raise Exception("SSO user batch service error")
        body = resp.json()
        if body["code"] != 0:
            raise Exception(f"Failed to batch get users: {body.get('msg')}")
        return {u["id"]: u for u in body["data"]}

user_client = UserClient()
