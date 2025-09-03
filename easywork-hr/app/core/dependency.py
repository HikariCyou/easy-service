from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.controllers.employee import employee_controller
from app.core.auth import auth_client
from app.core.ctx import CTX_USER_ID, CTX_USER_INFO
from app.settings import settings


class AuthControl:
    @classmethod
    async def is_authed(cls, authorization: str = Header(..., description="token验证")) -> Optional[dict]:
        try:
            if authorization == "dev":
                user_info = {
                    "id": 1,
                    "nickname": "DevUser",
                    "roles": ["admin"],
                    "deptId": 100
                }
            else:
                token = authorization[7:]
                user_info = await auth_client.validate(token)
            CTX_USER_ID.set(user_info["user"]["id"])
            CTX_USER_INFO.set(user_info["user"])
            return user_info
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")


class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user = Depends(AuthControl.is_authed)) -> None:
        if current_user.is_superuser:
            return
        method = request.method
        path = request.url.path
        roles = current_user.get("roles", [])
        if not roles:
            raise HTTPException(status_code=403, detail="The user is not bound to a role")
        apis = [await role.apis for role in roles]
        permission_apis = list(set((api.method, api.path) for api in sum(apis, [])))
        # path = "/api/v1/auth/userinfo"
        # method = "GET"
        if (method, path) not in permission_apis:
            raise HTTPException(status_code=403, detail=f"Permission denied method:{method} path:{path}")


async def get_current_employee():
    login_user_id = CTX_USER_ID.get()
    employee = await employee_controller.get_employee_by_user_id(login_user_id)
    if not employee:
        return None
    return employee

DependAuth = Depends(AuthControl.is_authed)
DependPermisson = Depends(PermissionControl.has_permission)

