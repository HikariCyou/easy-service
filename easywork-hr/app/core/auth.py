import httpx

SSO_BASE_URL = "http://localhost:48080/admin-api/system/auth"

class AuthClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=16.0)

    async def validate(self, token: str) -> dict:
        """
        调用 SSO 校验 token，返回用户信息 dict
        """
        try:
            resp = await self.client.get(f"{SSO_BASE_URL}/validate", params={"token": token})
        except httpx.RequestError:
            raise Exception("SSO service unavailable")
        
        if resp.status_code != 200:
            raise Exception("SSO server error")
        body = resp.json()
        if body["code"] != 0:
            raise Exception("Invalid token")
        return body["data"]

auth_client = AuthClient()
