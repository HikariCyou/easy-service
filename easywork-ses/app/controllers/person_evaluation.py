from typing import List, Dict, Any, Optional, Tuple
from datetime import date

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.evaluation import PersonEvaluation
from app.models.enums import PersonType
from app.models.case import Case
from app.models.contract import Contract
from app.utils.common import clean_dict


class PersonEvaluationController:
    """統一人材評価コントローラー"""

    def __init__(self):
        pass

    # ===== 基本CRUD =====
    async def list_evaluations(
        self, page: int = 1, page_size: int = 10, search_params: Dict = None
    ) -> Tuple[List[PersonEvaluation], int]:
        """評価一覧取得"""
        if search_params is None:
            search_params = {}

        # 検索条件構築
        query = self._build_search_query(search_params)

        # 総件数取得
        total = await PersonEvaluation.filter(query).count()

        # データ取得
        evaluations = (
            await PersonEvaluation.filter(query)
            .prefetch_related("case", "contract")
            .order_by("-evaluation_date", "-created_at")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        return evaluations, total

    async def get_evaluation_by_id(
        self, evaluation_id: int, include_relations: bool = False
    ) -> Optional[PersonEvaluation]:
        """IDで評価取得"""
        query = PersonEvaluation.filter(id=evaluation_id)
        if include_relations:
            query = query.prefetch_related("case", "contract")
        return await query.first()

    async def create_evaluation(
        self, evaluation_data
    ) -> PersonEvaluation:
        """評価作成"""
        async with in_transaction():
            # Pydanticスキーマを辞書に変換
            if hasattr(evaluation_data, 'model_dump'):
                data_dict = evaluation_data.model_dump(exclude_unset=True)
            elif hasattr(evaluation_data, 'dict'):
                data_dict = evaluation_data.dict()
            else:
                data_dict = evaluation_data
                
            # 人材存在確認
            person = await self._get_person_by_type_and_id(
                data_dict.get("person_type"), data_dict.get("person_id")
            )
            if not person:
                raise ValueError("指定された要員が見つかりません")

            # 案件・契約の存在確認（指定されている場合）
            if data_dict.get("case_id"):
                case = await Case.get_or_none(id=data_dict["case_id"])
                if not case:
                    raise ValueError("指定された案件が見つかりません")

            if data_dict.get("contract_id"):
                contract = await Contract.get_or_none(id=data_dict["contract_id"])
                if not contract:
                    raise ValueError("指定された契約が見つかりません")

            # 評価データ作成
            evaluation = await PersonEvaluation.create(**clean_dict(data_dict))

            # 関連データを含めて再取得
            return await self.get_evaluation_by_id(evaluation.id, include_relations=True)

    async def update_evaluation(
        self, evaluation_id: int, evaluation_data: Dict[str, Any]
    ) -> Optional[PersonEvaluation]:
        """評価更新"""
        evaluation = await PersonEvaluation.get_or_none(id=evaluation_id)
        if not evaluation:
            return None

        async with in_transaction():
            # 案件・契約の存在確認（更新される場合）
            if evaluation_data.get("case_id"):
                case = await Case.get_or_none(id=evaluation_data["case_id"])
                if not case:
                    raise ValueError("指定された案件が見つかりません")

            if evaluation_data.get("contract_id"):
                contract = await Contract.get_or_none(id=evaluation_data["contract_id"])
                if not contract:
                    raise ValueError("指定された契約が見つかりません")

            # 更新
            data_dict = clean_dict(evaluation_data)
            await evaluation.update_from_dict(data_dict)
            await evaluation.save()

            # 関連データを含めて再取得
            return await self.get_evaluation_by_id(evaluation_id, include_relations=True)

    async def delete_evaluation(self, evaluation_id: int) -> bool:
        """評価削除"""
        evaluation = await PersonEvaluation.get_or_none(id=evaluation_id)
        if evaluation:
            async with in_transaction():
                await evaluation.delete()
            return True
        return False

    # ===== 特定人材の評価管理 =====
    async def get_person_evaluations(
        self,
        person_type: PersonType,
        person_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[PersonEvaluation], int]:
        """特定人材の評価一覧取得"""
        query = PersonEvaluation.filter(
            person_type=person_type, person_id=person_id
        ).prefetch_related("case", "contract")

        total = await query.count()
        evaluations = (
            await query.order_by("-evaluation_date", "-created_at")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        return evaluations, total

    async def create_person_evaluation(
        self,
        person_type: PersonType,
        person_id: int,
        evaluation_data: Dict[str, Any],
        evaluator_id: int,
    ) -> PersonEvaluation:
        """特定人材の評価作成"""
        evaluation_data["person_type"] = person_type
        evaluation_data["person_id"] = person_id
        return await self.create_evaluation(evaluation_data, evaluator_id)

    async def get_person_evaluation_summary(
        self, person_type: PersonType, person_id: int
    ) -> Dict[str, Any]:
        """特定人材の評価サマリー取得"""
        evaluations = await PersonEvaluation.filter(
            person_type=person_type, person_id=person_id
        ).all()

        if not evaluations:
            return {
                "person_type": person_type.value,
                "person_id": person_id,
                "total_evaluations": 0,
                "average_overall_rating": 0.0,
                "average_technical_skill": 0.0,
                "average_communication": 0.0,
                "average_reliability": 0.0,
                "average_proactiveness": 0.0,
                "average_independence": 0.0,
                "average_delivery_quality": 0.0,
                "recommendation_rate": 0.0,
                "latest_evaluation_date": None,
            }

        total = len(evaluations)
        
        # 拡張フィールドを持つ評価のみで計算
        extended_evaluations = [e for e in evaluations if e.has_extended_fields()]
        
        return {
            "person_type": person_type.value,
            "person_id": person_id,
            "total_evaluations": total,
            "average_overall_rating": round(
                sum(e.overall_rating for e in evaluations) / total, 2
            ),
            "average_technical_skill": round(
                sum(e.technical_skill for e in evaluations) / total, 2
            ),
            "average_communication": round(
                sum(e.communication for e in evaluations) / total, 2
            ),
            "average_reliability": round(
                sum(e.reliability for e in evaluations) / total, 2
            ),
            "average_proactiveness": round(
                sum(e.proactiveness for e in evaluations) / total, 2
            ),
            "average_independence": round(
                sum(e.independence for e in extended_evaluations if e.independence) 
                / len(extended_evaluations), 2
            ) if extended_evaluations and any(e.independence for e in extended_evaluations) else 0.0,
            "average_delivery_quality": round(
                sum(e.delivery_quality for e in extended_evaluations if e.delivery_quality) 
                / len(extended_evaluations), 2
            ) if extended_evaluations and any(e.delivery_quality for e in extended_evaluations) else 0.0,
            "recommendation_rate": round(
                sum(1 for e in evaluations if e.recommendation) / total * 100, 1
            ),
            "latest_evaluation_date": max(e.evaluation_date for e in evaluations) if evaluations else None,
        }

    # ===== 業務ロジック =====
    async def get_top_rated_persons(
        self,
        person_type: Optional[PersonType] = None,
        limit: int = 10,
        min_evaluations: int = 3,
    ) -> List[Dict[str, Any]]:
        """高評価人材取得"""
        query = Q()
        if person_type:
            query &= Q(person_type=person_type)

        # 人材別に評価を集計
        evaluations = await PersonEvaluation.filter(query).all()
        person_stats = {}

        for evaluation in evaluations:
            key = (evaluation.person_type, evaluation.person_id)
            if key not in person_stats:
                person_stats[key] = {
                    "evaluations": [],
                    "person_type": evaluation.person_type,
                    "person_id": evaluation.person_id,
                }
            person_stats[key]["evaluations"].append(evaluation)

        # 最小評価数を満たす人材をフィルタリングし、評価計算
        top_persons = []
        for (person_type, person_id), stats in person_stats.items():
            evaluations = stats["evaluations"]
            if len(evaluations) >= min_evaluations:
                avg_rating = sum(e.overall_rating for e in evaluations) / len(evaluations)
                recommendation_rate = (
                    sum(1 for e in evaluations if e.recommendation) / len(evaluations) * 100
                )
                
                # 人材名を取得
                person = await self._get_person_by_type_and_id(person_type, person_id)
                person_name = person.name if person else f"Unknown-{person_id}"

                top_persons.append({
                    "person_type": person_type,
                    "person_id": person_id,
                    "person_name": person_name,
                    "average_rating": round(avg_rating, 2),
                    "total_evaluations": len(evaluations),
                    "recommendation_rate": round(recommendation_rate, 1),
                    "latest_evaluation_date": max(e.evaluation_date for e in evaluations),
                })

        # 評価順でソート
        top_persons.sort(key=lambda x: (x["average_rating"], x["total_evaluations"]), reverse=True)
        
        return top_persons[:limit]

    async def get_evaluation_stats_by_period(
        self, start_date: date, end_date: date, person_type: Optional[PersonType] = None
    ) -> Dict[str, Any]:
        """期間別評価統計取得"""
        query = Q(
            evaluation_date__gte=start_date,
            evaluation_date__lte=end_date,
        )
        if person_type:
            query &= Q(person_type=person_type)

        evaluations = await PersonEvaluation.filter(query).all()

        if not evaluations:
            return {
                "period": f"{start_date} ~ {end_date}",
                "total_evaluations": 0,
                "average_overall_rating": 0.0,
                "recommendation_rate": 0.0,
                "top_rated_count": 0,
                "bp_employee_count": 0,
                "freelancer_count": 0,
                "employee_count": 0,
            }

        total = len(evaluations)
        avg_rating = sum(e.overall_rating for e in evaluations) / total
        recommendation_rate = sum(1 for e in evaluations if e.recommendation) / total * 100
        top_rated_count = sum(1 for e in evaluations if e.overall_rating >= 4)

        # 人材タイプ別カウント
        bp_employee_count = sum(1 for e in evaluations if e.person_type == PersonType.BP_EMPLOYEE)
        freelancer_count = sum(1 for e in evaluations if e.person_type == PersonType.FREELANCER)
        employee_count = sum(1 for e in evaluations if e.person_type == PersonType.EMPLOYEE)

        return {
            "period": f"{start_date} ~ {end_date}",
            "total_evaluations": total,
            "average_overall_rating": round(avg_rating, 2),
            "recommendation_rate": round(recommendation_rate, 1),
            "top_rated_count": top_rated_count,
            "bp_employee_count": bp_employee_count,
            "freelancer_count": freelancer_count,
            "employee_count": employee_count,
        }

    # ===== データ変換 =====
    async def evaluations_to_dict(
        self, evaluations: List[PersonEvaluation], include_relations: bool = False
    ) -> List[Dict[str, Any]]:
        """評価リスト辞書変換"""
        result = []
        for evaluation in evaluations:
            evaluation_dict = await evaluation.to_dict()

            if include_relations:
                # 人材名を取得
                person = await self._get_person_by_type_and_id(
                    evaluation.person_type, evaluation.person_id
                )
                if person:
                    evaluation_dict["person_name"] = person.name

                # 案件・契約情報追加
                if hasattr(evaluation, "case") and evaluation.case:
                    evaluation_dict["case"] = await evaluation.case.to_dict()
                    evaluation_dict["case_name"] = evaluation.case.title

                if hasattr(evaluation, "contract") and evaluation.contract:
                    evaluation_dict["contract"] = await evaluation.contract.to_dict()
                    evaluation_dict["contract_number"] = evaluation.contract.contract_number

            result.append(evaluation_dict)
        return result

    async def evaluation_to_dict(
        self, evaluation: PersonEvaluation, include_relations: bool = False
    ) -> Optional[Dict[str, Any]]:
        """単一評価辞書変換"""
        if not evaluation:
            return None
        return (await self.evaluations_to_dict([evaluation], include_relations))[0]

    # ===== 内部补助メソッド =====
    async def _get_person_by_type_and_id(self, person_type: PersonType, person_id: int):
        """人材タイプとIDから人材オブジェクトを取得"""
        if person_type == PersonType.BP_EMPLOYEE:
            from app.models.bp import BPEmployee
            return await BPEmployee.get_or_none(id=person_id)
        elif person_type == PersonType.FREELANCER:
            from app.models.freelancer import Freelancer
            return await Freelancer.get_or_none(id=person_id)
        elif person_type == PersonType.EMPLOYEE:
            from app.models.employee import Employee
            return await Employee.get_or_none(id=person_id)
        return None

    def _build_search_query(self, search_params: Dict) -> Q:
        """検索クエリ構築"""
        query = Q()

        # 人材タイプで絞り込み
        if search_params.get("person_type"):
            query &= Q(person_type=search_params["person_type"])

        # 人材IDで絞り込み
        if search_params.get("person_id"):
            query &= Q(person_id=search_params["person_id"])

        # 案件IDで絞り込み
        if search_params.get("case_id"):
            query &= Q(case_id=search_params["case_id"])

        # 契約IDで絞り込み
        if search_params.get("contract_id"):
            query &= Q(contract_id=search_params["contract_id"])

        # 評価者IDで絞り込み
        if search_params.get("evaluator_id"):
            query &= Q(evaluator_id=search_params["evaluator_id"])

        # 評価レンジ
        if search_params.get("min_overall_rating"):
            query &= Q(overall_rating__gte=search_params["min_overall_rating"])
        if search_params.get("max_overall_rating"):
            query &= Q(overall_rating__lte=search_params["max_overall_rating"])

        # 推薦可能かどうか
        if search_params.get("recommendation") is not None:
            query &= Q(recommendation=search_params["recommendation"])

        # 評価日期間
        if search_params.get("evaluation_date_from"):
            query &= Q(evaluation_date__gte=search_params["evaluation_date_from"])
        if search_params.get("evaluation_date_to"):
            query &= Q(evaluation_date__lte=search_params["evaluation_date_to"])

        # キーワード検索
        if search_params.get("good_points_keyword"):
            query &= Q(good_points__icontains=search_params["good_points_keyword"])
        if search_params.get("improvement_points_keyword"):
            query &= Q(improvement_points__icontains=search_params["improvement_points_keyword"])

        return query


# グローバルインスタンス作成
person_evaluation_controller = PersonEvaluationController()