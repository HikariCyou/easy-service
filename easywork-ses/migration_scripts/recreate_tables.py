#!/usr/bin/env python3
"""
重建缺失的数据库表

当easywork-hr的迁移影响到共享数据库时，
使用此脚本重建easywork-ses的表结构
"""

import asyncio
import os
import sys
from datetime import datetime

from tortoise import Tortoise

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.settings.config import settings


class TableRecreator:
    """表重建管理类"""

    def __init__(self):
        self.settings = settings
        self.log_entries = []

    def log(self, message: str, level: str = "INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_entries.append(log_entry)
        print(log_entry)

    async def init_db(self):
        """初始化数据库连接"""
        await Tortoise.init(config=self.settings.TORTOISE_ORM)
        self.log("数据库连接初始化完成")

    async def close_db(self):
        """关闭数据库连接"""
        await Tortoise.close_connections()
        self.log("数据库连接已关闭")

    async def recreate_tables(self):
        """重建所有表"""
        self.log("=== 开始重建表结构 ===")

        try:
            # 生成数据库表
            await Tortoise.generate_schemas()
            self.log("所有表结构重建成功")

        except Exception as e:
            self.log(f"表重建失败: {str(e)}", "ERROR")
            raise

    async def verify_tables(self):
        """验证表是否存在"""
        self.log("=== 验证表结构 ===")

        try:
            # 获取数据库连接
            db = Tortoise.get_connection("mysql")

            # 检查关键表
            tables_to_check = [
                "ses_personnel",
                "ses_employee_detail",
                "ses_freelancer_detail",
                "ses_bp_employee_detail",
                "ses_personnel_skill",
                "ses_case",
                "ses_contract",
                "ses_attendance",
            ]

            existing_tables = []
            for table in tables_to_check:
                try:
                    await db.execute_query(f"SELECT 1 FROM {table} LIMIT 1")
                    existing_tables.append(table)
                    self.log(f"✓ 表存在: {table}")
                except:
                    self.log(f"✗ 表不存在: {table}", "WARNING")

            self.log(f"验证完成: {len(existing_tables)}/{len(tables_to_check)} 表存在")

        except Exception as e:
            self.log(f"表验证失败: {str(e)}", "ERROR")

    async def run_recreation(self):
        """执行重建过程"""
        try:
            await self.init_db()

            self.log("开始重建easywork-ses数据库表")

            # 重建表
            await self.recreate_tables()

            # 验证表
            await self.verify_tables()

            self.log("表重建过程完成")

        except Exception as e:
            self.log(f"重建过程中发生错误: {str(e)}", "ERROR")
            raise
        finally:
            await self.close_db()


async def main():
    """主函数"""
    recreator = TableRecreator()
    await recreator.run_recreation()


if __name__ == "__main__":
    print("=== easywork-ses 数据库表重建工具 ===")
    print("此工具将重建所有缺失的数据库表")

    confirm = input("是否继续？ (y/N): ")
    if confirm.lower() != "y":
        print("操作已取消")
        sys.exit(0)

    try:
        asyncio.run(main())
        print("表重建完成！")
    except KeyboardInterrupt:
        print("\n操作被中断")
    except Exception as e:
        print(f"重建失败: {e}")
        sys.exit(1)
