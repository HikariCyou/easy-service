#!/usr/bin/env python3
"""
統一人材管理システム データ移行スクリプト

既存の分離されたテーブルから統一Personnelテーブルへデータを移行します。
- Employee → Personnel + EmployeeDetail
- Freelancer → Personnel + FreelancerDetail  
- BPEmployee → Personnel + BPEmployeeDetail
- 各スキルテーブル → PersonnelSkill
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
from tortoise import Tortoise
from tortoise.transactions import in_transaction

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.models.employee import Employee, EmployeeSkill
from app.models.freelancer import Freelancer, FreelancerSkill
from app.models.bp import BPEmployee, BPEmployeeSkill
from app.models.personnel import Personnel, EmployeeDetail, FreelancerDetail, BPEmployeeDetail, PersonnelSkill
from app.models.enums import PersonType
from app.models.skill import Skill
from app.settings.config import settings


class DataMigrator:
    """データ移行管理クラス"""
    
    def __init__(self):
        self.settings = settings
        self.migration_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """ログ出力"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
    
    async def init_db(self):
        """データベース接続初期化"""
        await Tortoise.init(config=self.settings.TORTOISE_ORM)
        self.log("データベース接続を初期化しました")
    
    async def close_db(self):
        """データベース接続終了"""
        await Tortoise.close_connections()
        self.log("データベース接続を終了しました")
    
    def clean_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """None値を除去した辞書を返す"""
        return {k: v for k, v in data.items() if v is not None}
    
    async def migrate_employees(self) -> int:
        """社員データの移行"""
        self.log("=== 社員データ移行開始 ===")
        
        employees = await Employee.all()
        migrated_count = 0
        error_count = 0
        
        for employee in employees:
            try:
                async with in_transaction():
                    # 既存チェック
                    existing = await Personnel.filter(
                        person_type=PersonType.EMPLOYEE,
                        code=employee.code
                    ).first()
                    
                    if existing:
                        self.log(f"スキップ: 社員 {employee.code} は既に移行済み", "WARNING")
                        continue
                    
                    # Personnel基本データ作成
                    personnel_data = {
                        'person_type': PersonType.EMPLOYEE,
                        'user_id': employee.user_id,
                        'code': employee.code,
                        'name': employee.name,
                        'free_kana_name': employee.free_kana_name,
                        'age': employee.age,
                        'sex': employee.sex,
                        'birthday': employee.birthday,
                        'station': employee.station,
                        'marriage_status': employee.marriage_status,
                        'phone': employee.phone,
                        'email': employee.email,
                        'emergency_contact_name': employee.emergency_contact_name,
                        'emergency_contact_phone': employee.emergency_contact_phone,
                        'emergency_contact_relation': employee.emergency_contact_relation,
                        'zip_code': employee.zip_code,
                        'address': employee.address,
                        'nationality': employee.nationality,
                        'visa_status': employee.visa_status,
                        'visa_expire_date': employee.visa_expire_date,
                        'japanese_level': employee.japanese_level,
                        'total_experience_years': employee.total_experience_years,
                        'it_experience_years': employee.it_experience_years,
                        'education_level': employee.education_level,
                        'major': employee.major,
                        'certifications': employee.certifications,
                        'standard_unit_price': employee.standard_unit_price,
                        'employment_status': employee.employment_status,
                        'available_start_date': employee.available_start_date,
                        'current_project_end_date': employee.current_project_end_date,
                        'preferred_location': employee.preferred_location,
                        'remote_work_available': employee.remote_work_available,
                        'overtime_available': employee.overtime_available,
                        'photo_url': employee.photo_url,
                        'resume_url': employee.resume_url,
                        'portfolio_url': employee.portfolio_url,
                        'remark': employee.remark,
                        'is_active': employee.is_active,
                        'created_at': employee.created_at,
                        'updated_at': employee.updated_at,
                    }
                    
                    personnel = await Personnel.create(**self.clean_dict(personnel_data))
                    self.log(f"Personnel作成: {personnel.code} (ID: {personnel.id})")
                    
                    # EmployeeDetail作成
                    detail_data = {
                        'personnel': personnel,
                        'joining_time': employee.joining_time,
                        'position': employee.position,
                        'employment_type': employee.employment_type,
                        'business_content': employee.business_content,
                        'salary_payment_type': employee.salary_payment_type,
                        'salary': employee.salary,
                        'process_instance_id': employee.process_instance_id,
                    }
                    
                    await EmployeeDetail.create(**self.clean_dict(detail_data))
                    self.log(f"EmployeeDetail作成: {personnel.code}")
                    
                    # スキル移行
                    await self.migrate_employee_skills(employee, personnel)
                    
                    migrated_count += 1
                    
            except Exception as e:
                error_count += 1
                self.log(f"エラー: 社員 {employee.code} の移行に失敗 - {str(e)}", "ERROR")
                continue
        
        self.log(f"=== 社員データ移行完了: 成功 {migrated_count}件, エラー {error_count}件 ===")
        return migrated_count
    
    async def migrate_employee_skills(self, employee: Employee, personnel: Personnel):
        """社員スキルの移行"""
        skills = await EmployeeSkill.filter(employee=employee).prefetch_related('skill')
        
        for emp_skill in skills:
            try:
                # スキル存在確認・作成
                skill = emp_skill.skill
                
                # PersonnelSkill作成
                await PersonnelSkill.create(
                    personnel=personnel,
                    skill=skill,
                    proficiency=emp_skill.proficiency,
                    years_of_experience=emp_skill.years_of_experience,
                    last_used_date=emp_skill.last_used_date,
                    is_primary_skill=emp_skill.is_primary_skill,
                    remark=emp_skill.remark,
                )
                
            except Exception as e:
                self.log(f"スキル移行エラー: 社員 {employee.code}, スキル {skill.name} - {str(e)}", "ERROR")
    
    async def migrate_freelancers(self) -> int:
        """フリーランサーデータの移行"""
        self.log("=== フリーランサーデータ移行開始 ===")
        
        freelancers = await Freelancer.all()
        migrated_count = 0
        error_count = 0
        
        for freelancer in freelancers:
            try:
                async with in_transaction():
                    # 既存チェック
                    existing = await Personnel.filter(
                        person_type=PersonType.FREELANCER,
                        code=freelancer.code
                    ).first()
                    
                    if existing:
                        self.log(f"スキップ: フリーランサー {freelancer.code} は既に移行済み", "WARNING")
                        continue
                    
                    # Personnel基本データ作成
                    personnel_data = {
                        'person_type': PersonType.FREELANCER,
                        'code': freelancer.code,
                        'name': freelancer.name,
                        'free_kana_name': freelancer.free_kana_name,
                        'age': freelancer.age,
                        'sex': freelancer.sex,
                        'birthday': freelancer.birthday,
                        'station': freelancer.station,
                        'marriage_status': freelancer.marriage_status,
                        'phone': freelancer.phone,
                        'email': freelancer.email,
                        'emergency_contact_name': freelancer.emergency_contact_name,
                        'emergency_contact_phone': freelancer.emergency_contact_phone,
                        'emergency_contact_relation': freelancer.emergency_contact_relation,
                        'zip_code': freelancer.zip_code,
                        'address': freelancer.address,
                        'work_address': freelancer.work_address,
                        'nationality': freelancer.nationality,
                        'visa_status': freelancer.visa_status,
                        'visa_expire_date': freelancer.visa_expire_date,
                        'japanese_level': freelancer.japanese_level,
                        'total_experience_years': freelancer.total_experience_years,
                        'it_experience_years': freelancer.it_experience_years,
                        'education_level': freelancer.education_level,
                        'major': freelancer.major,
                        'certifications': freelancer.certifications,
                        'standard_unit_price': freelancer.standard_unit_price,
                        'min_unit_price': freelancer.min_unit_price,
                        'max_unit_price': freelancer.max_unit_price,
                        'hourly_rate': freelancer.hourly_rate,
                        'employment_status': freelancer.employment_status,
                        'is_active': freelancer.is_active,
                        'available_start_date': freelancer.available_start_date,
                        'current_project_end_date': freelancer.current_project_end_date,
                        'preferred_location': freelancer.preferred_location,
                        'photo_url': freelancer.photo_url,
                        'resume_url': freelancer.resume_url,
                        'portfolio_url': freelancer.portfolio_url,
                        'website_url': freelancer.website_url,
                        'remark': freelancer.remark,
                        'created_at': freelancer.created_at,
                        'updated_at': freelancer.updated_at,
                    }
                    
                    personnel = await Personnel.create(**self.clean_dict(personnel_data))
                    self.log(f"Personnel作成: {personnel.code} (ID: {personnel.id})")
                    
                    # FreelancerDetail作成
                    detail_data = {
                        'personnel': personnel,
                        'business_name': freelancer.business_name,
                        'tax_number': freelancer.tax_number,
                        'business_start_date': freelancer.business_start_date,
                        'freelance_experience_years': freelancer.freelance_experience_years,
                        'preferred_project_type': freelancer.preferred_project_type,
                        'preferred_work_style': freelancer.preferred_work_style,
                        'ng_client_companies': freelancer.ng_client_companies,
                        'interview_available': freelancer.interview_available,
                    }
                    
                    await FreelancerDetail.create(**self.clean_dict(detail_data))
                    self.log(f"FreelancerDetail作成: {personnel.code}")
                    
                    # スキル移行
                    await self.migrate_freelancer_skills(freelancer, personnel)
                    
                    migrated_count += 1
                    
            except Exception as e:
                error_count += 1
                self.log(f"エラー: フリーランサー {freelancer.code} の移行に失敗 - {str(e)}", "ERROR")
                continue
        
        self.log(f"=== フリーランサーデータ移行完了: 成功 {migrated_count}件, エラー {error_count}件 ===")
        return migrated_count
    
    async def migrate_freelancer_skills(self, freelancer: Freelancer, personnel: Personnel):
        """フリーランサースキルの移行"""
        skills = await FreelancerSkill.filter(freelancer=freelancer).prefetch_related('skill')
        
        for freelancer_skill in skills:
            try:
                skill = freelancer_skill.skill
                
                await PersonnelSkill.create(
                    personnel=personnel,
                    skill=skill,
                    proficiency=freelancer_skill.proficiency,
                    years_of_experience=freelancer_skill.years_of_experience,
                    last_used_date=freelancer_skill.last_used_date,
                    is_primary_skill=freelancer_skill.is_primary_skill,
                    remark=freelancer_skill.remark,
                )
                
            except Exception as e:
                self.log(f"スキル移行エラー: フリーランサー {freelancer.code}, スキル {skill.name} - {str(e)}", "ERROR")
    
    async def migrate_bp_employees(self) -> int:
        """BP社員データの移行"""
        self.log("=== BP社員データ移行開始 ===")
        
        bp_employees = await BPEmployee.all()
        migrated_count = 0
        error_count = 0
        
        for bp_employee in bp_employees:
            try:
                async with in_transaction():
                    # 既存チェック
                    existing = await Personnel.filter(
                        person_type=PersonType.BP_EMPLOYEE,
                        code=bp_employee.code
                    ).first()
                    
                    if existing:
                        self.log(f"スキップ: BP社員 {bp_employee.code} は既に移行済み", "WARNING")
                        continue
                    
                    # Personnel基本データ作成
                    personnel_data = {
                        'person_type': PersonType.BP_EMPLOYEE,
                        'code': bp_employee.code,
                        'name': bp_employee.name,
                        'free_kana_name': bp_employee.free_kana_name,
                        'age': bp_employee.age,
                        'sex': bp_employee.sex,
                        'birthday': bp_employee.birthday,
                        'station': bp_employee.station,
                        'marriage_status': bp_employee.marriage_status,
                        'phone': bp_employee.phone,
                        'email': bp_employee.email,
                        'emergency_contact_name': bp_employee.emergency_contact_name,
                        'emergency_contact_phone': bp_employee.emergency_contact_phone,
                        'emergency_contact_relation': bp_employee.emergency_contact_relation,
                        'zip_code': bp_employee.zip_code,
                        'address': bp_employee.address,
                        'nationality': bp_employee.nationality,
                        'visa_status': bp_employee.visa_status,
                        'visa_expire_date': bp_employee.visa_expire_date,
                        'japanese_level': bp_employee.japanese_level,
                        'total_experience_years': bp_employee.total_experience_years,
                        'it_experience_years': bp_employee.it_experience_years,
                        'education_level': bp_employee.education_level,
                        'major': bp_employee.major,
                        'certifications': bp_employee.certifications,
                        'standard_unit_price': bp_employee.standard_unit_price,
                        'min_unit_price': bp_employee.min_unit_price,
                        'max_unit_price': bp_employee.max_unit_price,
                        'employment_status': bp_employee.employment_status,
                        'available_start_date': bp_employee.available_start_date,
                        'current_project_end_date': bp_employee.current_project_end_date,
                        'preferred_location': bp_employee.preferred_location,
                        'remote_work_available': bp_employee.remote_work_available,
                        'overtime_available': bp_employee.overtime_available,
                        'photo_url': bp_employee.photo_url,
                        'resume_url': bp_employee.resume_url,
                        'portfolio_url': bp_employee.portfolio_url,
                        'remark': bp_employee.remark,
                        'is_active': bp_employee.is_active,
                        'created_at': bp_employee.created_at,
                        'updated_at': bp_employee.updated_at,
                    }
                    
                    personnel = await Personnel.create(**self.clean_dict(personnel_data))
                    self.log(f"Personnel作成: {personnel.code} (ID: {personnel.id})")
                    
                    # BPEmployeeDetail作成
                    detail_data = {
                        'personnel': personnel,
                        'bp_company_id': bp_employee.bp_company_id,
                        'interview_available': bp_employee.interview_available,
                    }
                    
                    await BPEmployeeDetail.create(**self.clean_dict(detail_data))
                    self.log(f"BPEmployeeDetail作成: {personnel.code}")
                    
                    # スキル移行
                    await self.migrate_bp_employee_skills(bp_employee, personnel)
                    
                    migrated_count += 1
                    
            except Exception as e:
                error_count += 1
                self.log(f"エラー: BP社員 {bp_employee.code} の移行に失敗 - {str(e)}", "ERROR")
                continue
        
        self.log(f"=== BP社員データ移行完了: 成功 {migrated_count}件, エラー {error_count}件 ===")
        return migrated_count
    
    async def migrate_bp_employee_skills(self, bp_employee: BPEmployee, personnel: Personnel):
        """BP社員スキルの移行"""
        skills = await BPEmployeeSkill.filter(bp_employee=bp_employee).prefetch_related('skill')
        
        for bp_skill in skills:
            try:
                skill = bp_skill.skill
                
                await PersonnelSkill.create(
                    personnel=personnel,
                    skill=skill,
                    proficiency=bp_skill.proficiency,
                    years_of_experience=bp_skill.years_of_experience,
                    last_used_date=bp_skill.last_used_date,
                    is_primary_skill=bp_skill.is_primary_skill,
                    remark=bp_skill.remark,
                )
                
            except Exception as e:
                self.log(f"スキル移行エラー: BP社員 {bp_employee.code}, スキル {skill.name} - {str(e)}", "ERROR")
    
    async def update_evaluations(self) -> int:
        """評価データのpersonnel_id更新"""
        self.log("=== 評価データ更新開始 ===")
        
        from app.models.evaluation import PersonEvaluation
        
        updated_count = 0
        error_count = 0
        
        # 全評価レコードを取得
        evaluations = await PersonEvaluation.all()
        
        for evaluation in evaluations:
            try:
                # 既にpersonnel_idが設定されている場合はスキップ
                if evaluation.personnel_id:
                    continue
                
                personnel = None
                
                # 各タイプのIDから対応するPersonnelを検索
                if evaluation.employee_id:
                    old_employee = await Employee.get_or_none(id=evaluation.employee_id)
                    if old_employee:
                        personnel = await Personnel.filter(
                            person_type=PersonType.EMPLOYEE,
                            code=old_employee.code
                        ).first()
                
                elif evaluation.freelancer_id:
                    old_freelancer = await Freelancer.get_or_none(id=evaluation.freelancer_id)
                    if old_freelancer:
                        personnel = await Personnel.filter(
                            person_type=PersonType.FREELANCER,
                            code=old_freelancer.code
                        ).first()
                
                elif evaluation.bp_employee_id:
                    old_bp = await BPEmployee.get_or_none(id=evaluation.bp_employee_id)
                    if old_bp:
                        personnel = await Personnel.filter(
                            person_type=PersonType.BP_EMPLOYEE,
                            code=old_bp.code
                        ).first()
                
                if personnel:
                    evaluation.personnel_id = personnel.id
                    await evaluation.save()
                    updated_count += 1
                    self.log(f"評価更新: ID {evaluation.id} → Personnel {personnel.id}")
                else:
                    self.log(f"対応するPersonnelが見つかりません: 評価ID {evaluation.id}", "WARNING")
                    
            except Exception as e:
                error_count += 1
                self.log(f"評価更新エラー: ID {evaluation.id} - {str(e)}", "ERROR")
        
        self.log(f"=== 評価データ更新完了: 成功 {updated_count}件, エラー {error_count}件 ===")
        return updated_count
    
    async def generate_migration_report(self, results: Dict[str, int]):
        """移行レポート生成"""
        self.log("=== データ移行レポート ===")
        self.log(f"社員移行: {results['employees']}件")
        self.log(f"フリーランサー移行: {results['freelancers']}件") 
        self.log(f"BP社員移行: {results['bp_employees']}件")
        self.log(f"評価データ更新: {results['evaluations']}件")
        self.log(f"総計: {sum(results.values())}件")
        
        # ログファイル出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"migration_log_{timestamp}.txt"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            for log_entry in self.migration_log:
                f.write(log_entry + '\n')
        
        self.log(f"詳細ログを出力しました: {log_file}")
    
    async def run_migration(self):
        """メイン移行プロセス実行"""
        try:
            await self.init_db()
            
            self.log("統一人材管理システム データ移行を開始します")
            
            results = {
                'employees': await self.migrate_employees(),
                'freelancers': await self.migrate_freelancers(),
                'bp_employees': await self.migrate_bp_employees(),
                'evaluations': await self.update_evaluations(),
            }
            
            await self.generate_migration_report(results)
            
            self.log("データ移行が正常に完了しました")
            
        except Exception as e:
            self.log(f"移行プロセスでエラーが発生しました: {str(e)}", "ERROR")
            raise
        finally:
            await self.close_db()


async def main():
    """メイン実行関数"""
    migrator = DataMigrator()
    await migrator.run_migration()


if __name__ == "__main__":
    print("=== 統一人材管理システム データ移行スクリプト ===")
    print("既存データをPersonnelテーブルに移行します...")
    
    confirm = input("続行しますか? (y/N): ")
    if confirm.lower() != 'y':
        print("移行をキャンセルしました")
        sys.exit(0)
    
    try:
        asyncio.run(main())
        print("移行が完了しました！")
    except KeyboardInterrupt:
        print("\n移行が中断されました")
    except Exception as e:
        print(f"移行でエラーが発生しました: {e}")
        sys.exit(1)