import asyncio
import decimal
from datetime import date, datetime, time, timedelta

from tortoise import fields, models

from app.settings import settings


class BaseModel(models.Model):
    id = fields.BigIntField(pk=True, index=True)

    async def to_dict(self, m2m: bool = False, exclude_fields: list[str] | None = None):
        if exclude_fields is None:
            exclude_fields = []

        d = {}
        for field in self._meta.db_fields:
            if field not in exclude_fields:
                value = getattr(self, field)
                if isinstance(value, datetime):
                    value = value.strftime(settings.DATETIME_FORMAT)
                elif isinstance(value, date):
                    value = value.isoformat()
                elif isinstance(value, time):
                    value = value.strftime("%H:%M:%S")
                elif isinstance(value, timedelta):
                    value = str(value)  # 或者 int(value.total_seconds())
                elif isinstance(value, decimal.Decimal):
                    value = float(value)
                d[field] = value

        if m2m:
            tasks = [
                self.__fetch_m2m_field(field, exclude_fields)
                for field in self._meta.m2m_fields
                if field not in exclude_fields
            ]
            results = await asyncio.gather(*tasks)
            for field, values in results:
                d[field] = values

        return d

    async def __fetch_m2m_field(self, field, exclude_fields):
        values = await getattr(self, field).all().values()
        formatted_values = []

        for value in values:
            formatted_value = {}
            for k, v in value.items():
                if k not in exclude_fields:
                    if isinstance(v, datetime):
                        formatted_value[k] = v.strftime(settings.DATETIME_FORMAT)
                    elif isinstance(v, date):
                        formatted_value[k] = v.isoformat()
                    elif isinstance(v, time):
                        formatted_value[k] = v.strftime("%H:%M:%S")
                    elif isinstance(v, timedelta):
                        formatted_value[k] = str(v)
                    elif isinstance(v, decimal.Decimal):
                        formatted_value[k] = float(v)
                    else:
                        formatted_value[k] = v
            formatted_values.append(formatted_value)

        return field, formatted_values

    class Meta:
        abstract = True


class UUIDModel:
    uuid = fields.UUIDField(unique=True, pk=False, index=True)


class TimestampMixin:
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True, index=True)
