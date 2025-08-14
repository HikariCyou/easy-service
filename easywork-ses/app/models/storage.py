from tortoise import fields
from tortoise.models import Model


class InfraFile(Model):
    id = fields.BigIntField(pk=True, index=True)
    config_id = fields.BigIntField(index=True, description="関連した設定ID")
    name = fields.CharField(max_length=255, description="ファイル名")
    path = fields.CharField(max_length=255, description="ファイルパス")
    url = fields.CharField(max_length=255, null=True, description="ファイルURL")
    type = fields.CharField(max_length=255, description="ファイルタイプ")
    size = fields.IntField(description="ファイルサイズ（バイト単位）")
    creator = fields.BigIntField(index=True, description="作成者ID")
    create_time = fields.DatetimeField(auto_now_add=True, description="作成時間")
    updater = fields.BigIntField(index=True, null=True, description="更新者ID")
    update_time = fields.DatetimeField(auto_now=True, description="更新時間")
    deleted = fields.BooleanField(default=False, description="削除フラグ")

    class Meta:
        table = "infra_file"
