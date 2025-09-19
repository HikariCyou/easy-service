"""
銀行データ初期化スクリプト
外部APIから銀行・支店データを取得してローカルDBに保存

使用方法:
python -m app.scripts.init_bank_data [--limit-banks 10] [--sync-branches]
"""

import argparse
import asyncio

from tortoise import Tortoise

from app.settings.config import settings
from app.utils.bank_service import bank_service


async def init_bank_data(limit_banks: int = None, sync_branches: bool = True):
    """銀行データを初期化"""

    # DB接続初期化
    await Tortoise.init(config=settings.TORTOISE_ORM)

    try:
        print("🏦 銀行データ初期化を開始します...")

        # 既存のデータをチェック
        if await bank_service.is_bank_data_exists():
            print("⚠️  既に銀行データが存在します。データを更新します。")

        # 銀行データ同期
        print("📥 銀行一覧を取得中...")
        bank_count = await bank_service.sync_banks()
        print(f"✅ {bank_count}件の銀行データを同期しました")

        # 支店データ同期（オプション）
        if sync_branches:
            print("📥 支店データを取得中...")
            if limit_banks:
                print(f"⚠️  最初の{limit_banks}行のみ処理します")

            result = await bank_service.sync_all_branches(limit_banks=limit_banks)
            print(f"✅ {result['banks']}行の銀行で{result['branches']}件の支店データを同期しました")
        else:
            print("ℹ️  支店データの同期はスキップしました（--sync-branchesを指定すると同期されます）")

        print("🎉 銀行データ初期化が完了しました！")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        raise

    finally:
        # HTTPクライアントとDB接続を閉じる
        await bank_service.close()
        await Tortoise.close_connections()


async def main():
    parser = argparse.ArgumentParser(description="銀行データ初期化スクリプト")
    parser.add_argument("--limit-banks", type=int, help="処理する銀行数の制限")
    parser.add_argument("--sync-branches", action="store_true", help="支店データも同期する")

    args = parser.parse_args()

    await init_bank_data(limit_banks=args.limit_banks, sync_branches=True)


if __name__ == "__main__":
    asyncio.run(main())
