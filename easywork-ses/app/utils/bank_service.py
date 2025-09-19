import asyncio
from typing import Dict, List, Optional

import httpx
from tortoise.transactions import in_transaction

from app.models.bank import Bank, BankBranch


class BankService:
    """
    銀行情報管理サービス
    外部APIから銀行・支店情報を取得してローカルDBに保存
    """

    BASE_URL = "https://bank.teraren.com"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """HTTPクライアントを閉じる"""
        await self.client.aclose()

    async def fetch_banks(self) -> List[Dict]:
        """外部APIから銀行一覧を取得"""
        try:
            response = await self.client.get(f"{self.BASE_URL}/banks.json")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"銀行一覧の取得に失敗しました: {e}")

    async def fetch_branches(self, bank_code: str) -> List[Dict]:
        """外部APIから指定銀行の支店一覧を取得"""
        try:
            response = await self.client.get(f"{self.BASE_URL}/banks/{bank_code}/branches.json")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise Exception(f"支店一覧の取得に失敗しました (銀行コード: {bank_code}): {e}")

    async def sync_banks(self) -> int:
        """
        外部APIから銀行情報を取得してローカルDBに同期
        Returns: 更新された銀行数
        """
        banks_data = await self.fetch_banks()
        updated_count = 0

        async with in_transaction():
            for bank_data in banks_data:
                bank, created = await Bank.get_or_create(
                    code=bank_data.get("code"),
                    defaults={
                        "name": bank_data.get("name", ""),
                        "name_kana": bank_data.get("kana", ""),
                    },
                )

                if not created:
                    # 既存の場合は名前を更新
                    bank.name = bank_data.get("name", bank.name)
                    bank.name_kana = bank_data.get("kana", bank.name_kana)
                    await bank.save()

                updated_count += 1

        return updated_count

    async def sync_branches(self, bank_code: str) -> int:
        """
        指定銀行の支店情報を外部APIから取得してローカルDBに同期
        Returns: 更新された支店数
        """
        bank = await Bank.get_or_none(code=bank_code)
        if not bank:
            raise ValueError(f"銀行コード {bank_code} が見つかりません")

        branches_data = await self.fetch_branches(bank_code)
        updated_count = 0

        async with in_transaction():
            for branch_data in branches_data:
                branch, created = await BankBranch.get_or_create(
                    bank=bank,
                    code=branch_data.get("code"),
                    defaults={
                        "name": branch_data.get("name", ""),
                        "name_kana": branch_data.get("kana", ""),
                    },
                )

                if not created:
                    # 既存の場合は名前を更新
                    branch.name = branch_data.get("name", branch.name)
                    branch.name_kana = branch_data.get("kana", branch.name_kana)
                    await branch.save()

                updated_count += 1

        return updated_count

    async def sync_all_branches(self, limit_banks: Optional[int] = None) -> Dict[str, int]:
        """
        全銀行の支店情報を同期
        Args:
            limit_banks: 処理する銀行数の制限（None = 全て）
        Returns: {"banks": 処理した銀行数, "branches": 更新した支店数}
        """
        banks = await Bank.all().limit(limit_banks) if limit_banks else await Bank.all()

        total_branches = 0
        processed_banks = 0

        for bank in banks:
            try:
                branch_count = await self.sync_branches(bank.code)
                total_branches += branch_count
                processed_banks += 1

                # APIに負荷をかけないよう少し待機
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"銀行 {bank.code} ({bank.name}) の支店同期でエラー: {e}")
                continue

        return {"banks": processed_banks, "branches": total_branches}

    async def get_banks(self) -> List[Bank]:
        """ローカルDBから銀行一覧を取得"""
        return await Bank.all().order_by("code")

    async def get_branches(self, bank_code: str) -> List[BankBranch]:
        """ローカルDBから指定銀行の支店一覧を取得"""
        return await BankBranch.filter(bank__code=bank_code).prefetch_related("bank").order_by("code")

    async def search_banks(self, keyword: str) -> List[Bank]:
        """銀行名で検索"""
        return await Bank.filter(name__icontains=keyword).order_by("code")

    async def search_branches(self, bank_code: str, keyword: str) -> List[BankBranch]:
        """支店名で検索"""
        return (
            await BankBranch.filter(bank__code=bank_code, name__icontains=keyword)
            .prefetch_related("bank")
            .order_by("code")
        )

    async def is_bank_data_exists(self) -> bool:
        """銀行データが存在するかチェック"""
        count = await Bank.all().count()
        return count > 0

    async def is_branch_data_exists(self, bank_code: str) -> bool:
        """指定銀行の支店データが存在するかチェック"""
        count = await BankBranch.filter(bank__code=bank_code).count()
        return count > 0


# グローバルインスタンス
bank_service = BankService()
