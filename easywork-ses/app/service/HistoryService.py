
from app.models import EmployeeHistory


class HistoryService:

    @staticmethod
    async def save_json_history(employee, model_name, data_dict, changed_by=None):
        # 获取最新版本号
        latest = await EmployeeHistory.filter(employee=employee, model_name=model_name).order_by("-version").first()
        version = (latest.version + 1) if latest else 1

        await EmployeeHistory.create(
            employee=employee, model_name=model_name, data=data_dict, version=version, changed_by=changed_by
        )

    @staticmethod
    async def get_latest_history(employee, model_name):
        """
        获取最新版本
        """
        return await EmployeeHistory.filter(employee=employee, model_name=model_name).order_by("-version").first()

    @staticmethod
    async def get_all_histories(employee, model_name):
        """
        获取所有历史版本
        """
        return await EmployeeHistory.filter(employee=employee, model_name=model_name).order_by("version")
