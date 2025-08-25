#!/usr/bin/env python3
"""
統一人材管理システム ロールバックスクリプト

移行に問題があった場合、Personnelテーブルのデータを削除し、
元の状態に戻すためのスクリプトです。

注意: 元のテーブル（Employee、Freelancer、BPEmployee）は
削除されませんので、安全にロールバックできます。
"""

import asyncio
import sys
import os
from datetime import datetime
from tortoise import Tortoise
from tortoise.transactions import in_transaction

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.personnel import Personnel, EmployeeDetail, FreelancerDetail, BPEmployeeDetail, PersonnelSkill
from app.settings.config import settings


class MigrationRollback:
    """移行ロールバック管理クラス"""
    
    def __init__(self):
        self.settings = settings
        self.log_entries = []
        
    def log(self, message: str, level: str = "INFO"):
        """ログ出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_entries.append(log_entry)
        print(log_entry)
    
    async def init_db(self):
        """データベース接続初期化"""
        await Tortoise.init(config=self.settings.TORTOISE_ORM)
        self.log("データベース接続を初期化しました")
    
    async def close_db(self):
        """データベース接続終了"""
        await Tortoise.close_connections()
        self.log("データベース接続を終了しました")
    
    async def rollback_personnel_data(self) -> dict:
        """Personnelデータの完全削除"""
        self.log("=== Personnelデータロールバック開始 ===")
        
        results = {
            'personnel_skills': 0,
            'employee_details': 0,
            'freelancer_details': 0,
            'bp_employee_details': 0,
            'personnel': 0
        }
        
        try:
            async with in_transaction():
                # 1. PersonnelSkillを削除（外部キー制約のため先に削除）
                deleted_skills = await PersonnelSkill.all().count()
                await PersonnelSkill.all().delete()
                results['personnel_skills'] = deleted_skills
                self.log(f"PersonnelSkill削除: {deleted_skills}件")
                
                # 2. 詳細テーブルを削除
                deleted_emp_details = await EmployeeDetail.all().count()
                await EmployeeDetail.all().delete()
                results['employee_details'] = deleted_emp_details
                self.log(f"EmployeeDetail削除: {deleted_emp_details}件")
                
                deleted_freelancer_details = await FreelancerDetail.all().count()
                await FreelancerDetail.all().delete()
                results['freelancer_details'] = deleted_freelancer_details
                self.log(f"FreelancerDetail削除: {deleted_freelancer_details}件")
                
                deleted_bp_details = await BPEmployeeDetail.all().count()
                await BPEmployeeDetail.all().delete()
                results['bp_employee_details'] = deleted_bp_details
                self.log(f"BPEmployeeDetail削除: {deleted_bp_details}件")
                
                # 3. Personnelを削除
                deleted_personnel = await Personnel.all().count()
                await Personnel.all().delete()
                results['personnel'] = deleted_personnel
                self.log(f"Personnel削除: {deleted_personnel}件")
                
        except Exception as e:
            self.log(f"ロールバック中にエラーが発生しました: {str(e)}", "ERROR")
            raise
        
        self.log("=== Personnelデータロールバック完了 ===")
        return results
    
    async def reset_evaluation_references(self) -> int:
        """評価データのpersonnel_id参照をクリア"""
        self.log("=== 評価データ参照リセット開始 ===")
        
        try:
            from app.models.evaluation import PersonEvaluation
            
            # personnel_idをNullに設定
            evaluations_with_personnel_id = await PersonEvaluation.filter(
                personnel_id__isnull=False
            ).count()
            
            await PersonEvaluation.filter(personnel_id__isnull=False).update(
                personnel_id=None
            )
            
            self.log(f"評価データのpersonnel_id参照をリセット: {evaluations_with_personnel_id}件")
            return evaluations_with_personnel_id
            
        except Exception as e:
            self.log(f"評価データリセット中にエラー: {str(e)}", "ERROR")
            return 0
    
    async def verify_original_data(self):
        """元のデータが残っているかチェック"""
        self.log("=== 元データ確認 ===")
        
        try:
            from app.models.employee import Employee
            from app.models.freelancer import Freelancer
            from app.models.bp import BPEmployee
            
            employee_count = await Employee.all().count()
            freelancer_count = await Freelancer.all().count()
            bp_employee_count = await BPEmployee.all().count()
            
            self.log(f"Employee: {employee_count}件")
            self.log(f"Freelancer: {freelancer_count}件")
            self.log(f"BPEmployee: {bp_employee_count}件")
            
            total = employee_count + freelancer_count + bp_employee_count
            if total > 0:
                self.log(f"元データ確認完了: 合計 {total}件のデータが保持されています")
            else:
                self.log("警告: 元データが見つかりません", "WARNING")
                
        except Exception as e:
            self.log(f"元データ確認でエラー: {str(e)}", "ERROR")
    
    async def generate_rollback_report(self, personnel_results: dict, evaluation_count: int):
        """ロールバックレポート生成"""
        self.log("=== ロールバックレポート ===")
        
        for table, count in personnel_results.items():
            self.log(f"{table}削除: {count}件")
        
        self.log(f"評価データ参照リセット: {evaluation_count}件")
        
        total_deleted = sum(personnel_results.values())
        self.log(f"削除総計: {total_deleted}件")
        
        # ログファイル出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"rollback_log_{timestamp}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            for log_entry in self.log_entries:
                f.write(log_entry + '\n')
        
        self.log(f"ロールバックログを出力しました: {log_file}")
    
    async def run_rollback(self):
        """メインロールバックプロセス実行"""
        try:
            await self.init_db()
            
            self.log("統一人材管理システム移行のロールバックを開始します")
            
            # 元データ確認
            await self.verify_original_data()
            
            # 評価データ参照リセット
            evaluation_count = await self.reset_evaluation_references()
            
            # Personnelデータ削除
            personnel_results = await self.rollback_personnel_data()
            
            # レポート生成
            await self.generate_rollback_report(personnel_results, evaluation_count)
            
            self.log("ロールバックが正常に完了しました")
            
        except Exception as e:
            self.log(f"ロールバック中にエラーが発生しました: {str(e)}", "ERROR")
            raise
        finally:
            await self.close_db()


async def main():
    """メイン実行関数"""
    rollback = MigrationRollback()
    await rollback.run_rollback()


if __name__ == "__main__":
    print("=== 統一人材管理システム 移行ロールバックスクリプト ===")
    print("Personnelテーブルのデータを削除し、元の状態に戻します")
    print("注意: 元のテーブル（Employee、Freelancer、BPEmployee）は削除されません")
    print()
    
    confirm = input("ロールバックを実行しますか? (y/N): ")
    if confirm.lower() != 'y':
        print("ロールバックをキャンセルしました")
        sys.exit(0)
    
    confirm2 = input("本当によろしいですか？ Personnelデータは完全に削除されます (y/N): ")
    if confirm2.lower() != 'y':
        print("ロールバックをキャンセルしました")
        sys.exit(0)
    
    try:
        asyncio.run(main())
        print("ロールバックが完了しました！")
    except KeyboardInterrupt:
        print("\nロールバックが中断されました")
    except Exception as e:
        print(f"ロールバックでエラーが発生しました: {e}")
        sys.exit(1)