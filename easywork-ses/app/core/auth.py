import httpx

from app.settings.config import settings


class AuthClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=16.0)

    async def validate(self, token: str) -> dict:
        """
        调用 SSO 校验 token，返回用户信息 dict
        """
        try:
            print(f"Validating token with URL: {settings.SSO_BASE_URL}/auth/check-token")
            print(f"Token: {token[:20]}...")
            resp = await self.client.get(f"{settings.SSO_BASE_URL}/auth/check-token", params={"token": token})
            print(f"Response status: {resp.status_code}")
            print(f"Response body: {resp.text}")
        except httpx.RequestError as e:
            print(f"Request error: {str(e)}")
            raise Exception("SSO service unavailable")

        if resp.status_code != 200:
            raise Exception("SSO server error")
        body = resp.json()
        if body["code"] != 0:
            raise Exception("Invalid token")
        return body["data"]


auth_client = AuthClient()
