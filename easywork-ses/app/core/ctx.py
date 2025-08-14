import contextvars

from starlette.background import BackgroundTasks

CTX_USER_ID: contextvars.ContextVar[int] = contextvars.ContextVar("user_id", default=0)
CTX_USER_INFO: contextvars.ContextVar[dict] = contextvars.ContextVar("CTX_USER_INFO", default=None)
CTX_BG_TASKS: contextvars.ContextVar[BackgroundTasks] = contextvars.ContextVar("bg_task", default=None)
