import httpx

from app.settings.config import settings


class ProcessClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=18.0)

    async def run_process(
        self, process_key: str, business_key: str, variables: str = None, token: str = None
    ) -> dict[int, dict]:
        """
        启动一个流程实例，并返回与该流程实例的ID
        """
        headers = {"Authorization": f"{token}"} if token else {}
        resp = await self.client.post(
            f"{settings.PROCESS_BASE_URL}/run",
            json={"processKey": process_key, "businessKey": business_key, "variables": variables},
            headers=headers,
        )
        if resp.status_code != 200:
            raise Exception("PROCESS run failed")
        body = resp.json()
        if body["code"] != 0:
            raise Exception(f"Failed to run process: {body.get('msg')}")
        return body["data"]


process_client = ProcessClient()
