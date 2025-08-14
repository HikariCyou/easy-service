from typing import List
from datetime import date, datetime
from decimal import Decimal

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.freelancer import Freelancer, FreelancerSkill, FreelancerEvaluation
from app.models.skill import Skill
from app.utils.common import clean_dict


class FreelancerController:
    """フリーランサー管理コントローラー"""

    def __init__(self):
        pass

    # ===== 基本CRUD =====
    async def list_freelancers(self, page: int = 1, page_size: int = 10, search: Q = None, order: list = [],
                             include_skills: bool = False):
        """フリーランサー一覧取得"""
        if search is None:
            search = Q()
            
        query = Freelancer.filter(search)
        if include_skills:
            query = query.prefetch_related('skills__skill')

        total = await query.count()
        freelancers = await query.order_by(*order).limit(page_size).offset((page - 1) * page_size).all()
        return freelancers, total

    async def search_freelancers(self, search_params: dict, page: int = 1, page_size: int = 10):
        """高度検索"""
        query = Q()
        
        # 基本情報検索
        if search_params.get('name'):
            query &= Q(name__icontains=search_params['name'])
        if search_params.get('code'):
            query &= Q(code__icontains=search_params['code'])
        if search_params.get('employment_status'):
            query &= Q(employment_status=search_params['employment_status'])
        if search_params.get('nationality'):
            query &= Q(nationality__icontains=search_params['nationality'])
        if search_params.get('business_name'):
            query &= Q(business_name__icontains=search_params['business_name'])
        if search_params.get('preferred_location'):
            query &= Q(preferred_location__icontains=search_params['preferred_location'])
            
        # 日付範囲検索
        if search_params.get('available_from'):
            query &= Q(available_start_date__gte=search_params['available_from'])
        if search_params.get('available_to'):
            query &= Q(available_start_date__lte=search_params['available_to'])
            
        # 経験年数検索
        if search_params.get('min_experience_years'):
            query &= Q(it_experience_years__gte=search_params['min_experience_years'])
        
        # 単価検索
        if search_params.get('min_unit_price'):
            query &= Q(standard_unit_price__gte=search_params['min_unit_price'])
        if search_params.get('max_unit_price'):
            query &= Q(standard_unit_price__lte=search_params['max_unit_price'])
        
        # スキル検索
        if search_params.get('skill_name'):
            query &= Q(skills__skill__name__icontains=search_params['skill_name'])
            
        return await self.list_freelancers(page, page_size, query, ['-updated_at'], include_skills=True)

    async def get_freelancer_by_id(self, freelancer_id: int, include_relations: bool = False):
        """IDでフリーランサー取得"""
        query = Freelancer.filter(id=freelancer_id)
        if include_relations:
            query = query.prefetch_related('skills__skill', 'contracts', 'evaluations', 'case_candidates')
        freelancer = await query.first()
        return freelancer

    async def create_freelancer(self, freelancer_data: dict):
        """フリーランサー作成"""
        async with in_transaction():
            # コード自動生成（もし指定されていない場合）
            if not freelancer_data.get('code'):
                freelancer_data['code'] = await self._generate_freelancer_code()
            
            freelancer = await Freelancer.create(**clean_dict(freelancer_data))
            
            # 作成後に関連データを含めて再取得
            freelancer = await self.get_freelancer_by_id(freelancer.id, include_relations=True)
            return freelancer

    async def update_freelancer(self, freelancer_id: int, freelancer_data: dict):
        """フリーランサー更新"""
        freelancer = await Freelancer.get_or_none(id=freelancer_id)
        if freelancer:
            async with in_transaction():
                data_dict = clean_dict(freelancer_data)
                await freelancer.update_from_dict(data_dict)
                await freelancer.save()
                
                # 更新後に関連データを含めて再取得
                freelancer = await self.get_freelancer_by_id(freelancer_id, include_relations=True)
        return freelancer

    async def delete_freelancer(self, freelancer_id: int):
        """フリーランサー削除（論理削除）"""
        freelancer = await Freelancer.get_or_none(id=freelancer_id)
        if freelancer:
            async with in_transaction():
                freelancer.is_active = False
                await freelancer.save()
        return freelancer

    async def _generate_freelancer_code(self) -> str:
        """フリーランサーコード自動生成"""
        today = datetime.now().strftime("%y%m%d")
        prefix = f"FL{today}"
        
        # 今日作成された最後の番号を取得
        latest = await Freelancer.filter(
            code__startswith=prefix
        ).order_by("-code").first()
        
        if latest:
            last_number = int(latest.code[-3:])
            next_number = last_number + 1
        else:
            next_number = 1
        
        return f"{prefix}{next_number:03d}"

    # ===== スキル管理 =====
    async def get_freelancer_skills(self, freelancer: Freelancer, page: int = 1, page_size: int = 10):
        """フリーランサースキル一覧取得"""
        query = FreelancerSkill.filter(freelancer=freelancer).select_related("skill")

        total = await query.count()
        skills = (
            await query.order_by("-is_primary_skill", "-proficiency", "-years_of_experience")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )
        return skills, total

    async def add_freelancer_skill(self, freelancer: Freelancer, skill_data: dict):
        """フリーランサースキル追加"""
        skill_name = skill_data.get("skill_name")
        category = skill_data.get("category")

        if not skill_name:
            raise ValueError("スキル名称は必須です")

        async with in_transaction():
            # スキル検索または作成
            skill, created = await Skill.get_or_create(name=skill_name, defaults={"category": category})

            # 既存チェック
            existing = await FreelancerSkill.get_or_none(freelancer=freelancer, skill=skill)
            if existing:
                raise ValueError(f"スキル「{skill_name}」は既に登録されています")

            # フリーランサースキル作成
            freelancer_skill = await FreelancerSkill.create(
                freelancer=freelancer,
                skill=skill,
                proficiency=skill_data.get("proficiency", 1),
                years_of_experience=skill_data.get("years_of_experience"),
                last_used_date=skill_data.get("last_used_date"),
                is_primary_skill=skill_data.get("is_primary_skill", False),
                remark=skill_data.get("remark"),
            )
            return freelancer_skill

    async def update_freelancer_skill(self, skill_id: int, skill_data: dict):
        """フリーランサースキル更新"""
        freelancer_skill = await FreelancerSkill.get_or_none(id=skill_id)
        if not freelancer_skill:
            raise ValueError("スキル記録が見つかりません")

        async with in_transaction():
            skill_name = skill_data.get("skill_name")
            category = skill_data.get("category")

            if skill_name:
                skill, created = await Skill.get_or_create(name=skill_name, defaults={"category": category})
                freelancer_skill.skill = skill

            # その他フィールド更新
            update_fields = ["proficiency", "years_of_experience", "last_used_date", "is_primary_skill", "remark"]
            for field in update_fields:
                if field in skill_data:
                    setattr(freelancer_skill, field, skill_data[field])

            await freelancer_skill.save()
            return freelancer_skill

    async def delete_freelancer_skill(self, skill_id: int):
        """フリーランサースキル削除"""
        freelancer_skill = await FreelancerSkill.get_or_none(id=skill_id)
        if freelancer_skill:
            async with in_transaction():
                await freelancer_skill.delete()
        return freelancer_skill

    async def batch_update_freelancer_skills(self, freelancer: Freelancer, skills_data: List[dict]):
        """フリーランサースキル一括更新"""
        async with in_transaction():
            # 既存スキル削除
            await FreelancerSkill.filter(freelancer=freelancer).delete()

            # 新しいスキル追加
            if skills_data:
                for skill_item in skills_data:
                    try:
                        await self.add_freelancer_skill(freelancer, skill_item)
                    except ValueError:
                        # 重複エラーは無視して続行
                        continue

    # ===== 評価管理 =====
    async def get_freelancer_evaluations(self, freelancer: Freelancer, page: int = 1, page_size: int = 10):
        """フリーランサー評価一覧取得"""
        query = FreelancerEvaluation.filter(freelancer=freelancer).select_related("case", "contract")
        
        total = await query.count()
        evaluations = (
            await query.order_by("-evaluation_date", "-created_at")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )
        return evaluations, total

    async def create_freelancer_evaluation(self, freelancer: Freelancer, evaluation_data: dict, evaluator_id: int):
        """フリーランサー評価作成"""
        async with in_transaction():
            evaluation_data['freelancer'] = freelancer
            evaluation_data['evaluator_id'] = evaluator_id
            evaluation = await FreelancerEvaluation.create(**evaluation_data)
            return evaluation

    async def get_freelancer_evaluation_summary(self, freelancer: Freelancer):
        """フリーランサー評価サマリー取得"""
        evaluations = await FreelancerEvaluation.filter(freelancer=freelancer).all()
        
        if not evaluations:
            return {
                "total_evaluations": 0,
                "average_overall_rating": 0,
                "average_technical_skill": 0,
                "average_communication": 0,
                "average_reliability": 0,
                "average_independence": 0,
                "average_delivery_quality": 0,
                "recommendation_rate": 0,
            }

        total = len(evaluations)
        return {
            "total_evaluations": total,
            "average_overall_rating": round(sum(e.overall_rating for e in evaluations) / total, 2),
            "average_technical_skill": round(sum(e.technical_skill for e in evaluations) / total, 2),
            "average_communication": round(sum(e.communication for e in evaluations) / total, 2),
            "average_reliability": round(sum(e.reliability for e in evaluations) / total, 2),
            "average_independence": round(sum(e.independence for e in evaluations) / total, 2),
            "average_delivery_quality": round(sum(e.delivery_quality for e in evaluations) / total, 2),
            "recommendation_rate": round(sum(1 for e in evaluations if e.recommendation) / total * 100, 1),
        }

    # ===== 業務ロジック =====
    async def get_available_freelancers(self, project_start_date: date = None, required_skills: List[str] = None,
                                      min_experience_years: Decimal = None, budget_range: tuple = None,
                                      location: str = None, page: int = 1, page_size: int = 10):
        """利用可能なフリーランサー取得（プロジェクト要件マッチング）"""
        query = Q(is_active=True, employment_status="available")
        
        # プロジェクト開始日フィルター
        if project_start_date:
            query &= Q(available_start_date__lte=project_start_date) | Q(available_start_date__isnull=True)
        
        # スキル要件フィルター
        if required_skills:
            for skill in required_skills:
                query &= Q(skills__skill__name__icontains=skill)
        
        # 経験年数フィルター
        if min_experience_years:
            query &= Q(it_experience_years__gte=min_experience_years)
        
        # 予算範囲フィルター
        if budget_range:
            min_budget, max_budget = budget_range
            if min_budget:
                query &= Q(min_unit_price__lte=min_budget)
            if max_budget:
                query &= Q(standard_unit_price__lte=max_budget)
        
        # 勤務地フィルター
        if location:
            query &= Q(preferred_location__icontains=location)
        
        return await self.list_freelancers(page, page_size, query, ['-it_experience_years', '-updated_at'], 
                                         include_skills=True)

    async def project_matching_search(self, matching_params: dict, page: int = 1, page_size: int = 10):
        """案件マッチング検索"""
        return await self.get_available_freelancers(
            project_start_date=matching_params.get('project_start_date'),
            required_skills=matching_params.get('required_skills'),
            min_experience_years=matching_params.get('min_experience_years'),
            budget_range=(matching_params.get('budget_min'), matching_params.get('budget_max')),
            location=matching_params.get('location'),
            page=page,
            page_size=page_size
        )

    async def check_visa_expiring_soon(self, days: int = 90):
        """ビザ期限切れ警告"""
        from datetime import timedelta
        
        expiry_date = date.today() + timedelta(days=days)
        freelancers = await Freelancer.filter(
            visa_expire_date__lte=expiry_date,
            visa_expire_date__gte=date.today(),
            is_active=True
        ).all()
        
        return freelancers

    async def get_freelancer_dashboard_stats(self, freelancer: Freelancer):
        """フリーランサーダッシュボード統計"""
        # スキル統計
        skills_count = await FreelancerSkill.filter(freelancer=freelancer).count()
        primary_skills_count = await FreelancerSkill.filter(freelancer=freelancer, is_primary_skill=True).count()
        
        # プロジェクト/契約統計
        try:
            total_contracts = await freelancer.contracts.all().count()
            active_contracts = await freelancer.contracts.filter(status="active").count()
        except Exception:
            # 関連データが利用できない場合は直接クエリ
            from app.models.contract import Contract
            total_contracts = await Contract.filter(freelancer=freelancer).count()
            active_contracts = await Contract.filter(freelancer=freelancer, status="active").count()
        
        # 評価統計
        evaluation_summary = await self.get_freelancer_evaluation_summary(freelancer)
        
        # 事業統計
        business_years = freelancer.business_years if hasattr(freelancer, 'business_years') else 0
        
        return {
            "basic_info": {
                "name": freelancer.name,
                "code": freelancer.code,
                "business_name": freelancer.business_name,
                "current_age": freelancer.current_age if hasattr(freelancer, 'current_age') else freelancer.age,
                "employment_status": freelancer.employment_status,
                "business_years": business_years,
                "is_visa_expiring": freelancer.is_visa_expiring_soon() if hasattr(freelancer, 'is_visa_expiring_soon') else False,
            },
            "skills_stats": {
                "total_skills": skills_count,
                "primary_skills": primary_skills_count,
            },
            "contract_stats": {
                "total_contracts": total_contracts,
                "active_contracts": active_contracts,
            },
            "evaluation_stats": evaluation_summary,
        }

    async def get_freelancer_business_stats(self, freelancer: Freelancer, year: int = None, 
                                          month_from: int = 1, month_to: int = 12):
        """フリーランサー事業統計（収入、契約数など）"""
        if year is None:
            year = datetime.now().year
            
        # 指定期間のアクティブな契約を取得
        from datetime import datetime as dt
        start_date = dt(year, month_from, 1).date()
        end_date = dt(year, month_to, 28).date()  # 簡略化
        
        contracts = await freelancer.contracts.filter(
            contract_start_date__lte=end_date,
            contract_end_date__gte=start_date
        ).all()
        
        total_revenue = sum(contract.unit_price or 0 for contract in contracts)
        
        return {
            "period": f"{year}年{month_from}月～{month_to}月",
            "total_contracts": len(contracts),
            "total_revenue": total_revenue,
            "average_unit_price": total_revenue / len(contracts) if contracts else 0,
            "business_years": freelancer.business_years if hasattr(freelancer, 'business_years') else 0,
            "tax_number": freelancer.tax_number,
            "has_invoice_number": bool(freelancer.tax_number),
        }

    async def get_top_rated_freelancers(self, limit: int = 10, min_evaluations: int = 3):
        """高評価フリーランサー取得"""
        # SQLでの複雑な集計が必要な場合は、生のクエリーを使用
        query = """
        SELECT f.*, AVG(e.overall_rating) as avg_rating, COUNT(e.id) as eval_count
        FROM ses_freelancer f
        LEFT JOIN ses_freelancer_evaluation e ON f.id = e.freelancer_id
        WHERE f.is_active = true
        GROUP BY f.id
        HAVING COUNT(e.id) >= %s
        ORDER BY AVG(e.overall_rating) DESC, COUNT(e.id) DESC
        LIMIT %s
        """
        
        # 簡易実装（実際の実装では生のSQLかORMの高度な機能を使用）
        freelancers = await Freelancer.filter(is_active=True).all()
        freelancer_ratings = []
        
        for freelancer in freelancers:
            evaluations = await FreelancerEvaluation.filter(freelancer=freelancer).all()
            if len(evaluations) >= min_evaluations:
                avg_rating = sum(e.overall_rating for e in evaluations) / len(evaluations)
                freelancer_ratings.append((freelancer, avg_rating, len(evaluations)))
        
        # 評価順でソート
        freelancer_ratings.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        return [item[0] for item in freelancer_ratings[:limit]]

    # ===== データ変換 =====
    async def freelancers_to_dict(self, freelancers: List[Freelancer], include_relations: bool = False):
        """フリーランサーリスト辞書変換"""
        result = []
        for freelancer in freelancers:
            freelancer_dict = await freelancer.to_dict()
            
            if include_relations:
                # スキル情報追加
                skills = []
                try:
                    # 関連データが利用可能かチェック
                    if hasattr(freelancer, '_prefetched_objects') and 'skills' in freelancer._prefetched_objects:
                        for skill_relation in freelancer.skills:
                            skill_dict = await skill_relation.to_dict()
                            if hasattr(skill_relation, 'skill') and skill_relation.skill:
                                skill_dict['skill'] = await skill_relation.skill.to_dict()
                            skills.append(skill_dict)
                except Exception:
                    # 関連データが利用できない場合は空のリスト
                    skills = []
                freelancer_dict['skills'] = skills
                
                # 計算属性追加
                freelancer_dict['current_age'] = freelancer.current_age if hasattr(freelancer, 'current_age') else freelancer.age
                freelancer_dict['business_years'] = freelancer.business_years if hasattr(freelancer, 'business_years') else 0
                if hasattr(freelancer, 'is_visa_expiring_soon'):
                    freelancer_dict['is_visa_expiring_soon'] = freelancer.is_visa_expiring_soon()
            
            result.append(freelancer_dict)
        return result

    async def freelancer_to_dict(self, freelancer: Freelancer, include_relations: bool = False):
        """単一フリーランサー辞書変換"""
        if not freelancer:
            return None
        return (await self.freelancers_to_dict([freelancer], include_relations))[0]


freelancer_controller = FreelancerController()