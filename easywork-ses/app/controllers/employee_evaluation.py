from typing import List, Dict, Any, Optional, Tuple
from datetime import date

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.personnel import Personnel
from app.models.evaluation import PersonEvaluation
from app.models.case import Case
from app.models.contract import Contract
from app.models.enums import PersonType
from app.utils.common import clean_dict


class EmployeeEvaluationController:
    """自社社員評価コントローラー（Personnel統一システム対応）"""

    def __init__(self):
        pass

    # ===== 基本CRUD =====
    async def list_evaluations(self, page: int = 1, page_size: int = 10, search_params: Dict = None) -> Tuple[List[PersonEvaluation], int]:
        """評価一覧取得"""
        if search_params is None:
            search_params = {}
        
        # 社員評価のみにフィルタ
        query = Q(person_type=PersonType.EMPLOYEE)
        
        # 検索条件構築
        if search_params.get('employee_id'):
            query &= Q(person_id=search_params['employee_id'])
        if search_params.get('case_id'):
            query &= Q(case_id=search_params['case_id'])
        if search_params.get('contract_id'):
            query &= Q(contract_id=search_params['contract_id'])
        if search_params.get('evaluator_id'):
            query &= Q(evaluator_id=search_params['evaluator_id'])
        if search_params.get('min_overall_rating'):
            query &= Q(overall_rating__gte=search_params['min_overall_rating'])
        if search_params.get('max_overall_rating'):
            query &= Q(overall_rating__lte=search_params['max_overall_rating'])
        if search_params.get('recommendation') is not None:
            query &= Q(recommendation=search_params['recommendation'])
        if search_params.get('evaluation_date_from'):
            query &= Q(evaluation_date__gte=search_params['evaluation_date_from'])
        if search_params.get('evaluation_date_to'):
            query &= Q(evaluation_date__lte=search_params['evaluation_date_to'])
        
        # 総件数取得
        total = await PersonEvaluation.filter(query).count()
        
        # データ取得
        evaluations = await PersonEvaluation.filter(query).prefetch_related(
            'case', 'contract'
        ).order_by('-evaluation_date', '-created_at').limit(page_size).offset((page - 1) * page_size).all()
        
        return evaluations, total

    async def get_evaluation_by_id(self, evaluation_id: int, include_relations: bool = False) -> Optional[PersonEvaluation]:
        """ID で評価取得"""
        query = PersonEvaluation.filter(id=evaluation_id, person_type=PersonType.EMPLOYEE)
        if include_relations:
            query = query.prefetch_related('case', 'contract')
        return await query.first()

    async def create_evaluation(self, evaluation_data: Dict[str, Any], evaluator_id: int) -> PersonEvaluation:
        """評価作成"""
        async with in_transaction():
            # 社員存在確認
            employee = await Personnel.get_or_none(id=evaluation_data.get('employee_id'), person_type=PersonType.EMPLOYEE)
            if not employee:
                raise ValueError("指定された社員が見つかりません")
            
            # 案件・契約の存在確認（指定されている場合）
            if evaluation_data.get('case_id'):
                case = await Case.get_or_none(id=evaluation_data['case_id'])
                if not case:
                    raise ValueError("指定された案件が見つかりません")
            
            if evaluation_data.get('contract_id'):
                contract = await Contract.get_or_none(id=evaluation_data['contract_id'])
                if not contract:
                    raise ValueError("指定された契約が見つかりません")
            
            # PersonEvaluation作成
            evaluation_data['person_type'] = PersonType.EMPLOYEE
            evaluation_data['person_id'] = evaluation_data.pop('employee_id')  # employee_id -> person_id
            evaluation_data['evaluator_id'] = evaluator_id
            
            evaluation = await PersonEvaluation.create(**clean_dict(evaluation_data))
            return evaluation

    async def update_evaluation(self, evaluation_id: int, evaluation_data: Dict[str, Any]) -> Optional[PersonEvaluation]:
        """評価更新"""
        evaluation = await PersonEvaluation.get_or_none(id=evaluation_id, person_type=PersonType.EMPLOYEE)
        if not evaluation:
            return None

        async with in_transaction():
            # 案件・契約の存在確認（指定されている場合）
            if evaluation_data.get('case_id'):
                case = await Case.get_or_none(id=evaluation_data['case_id'])
                if not case:
                    raise ValueError("指定された案件が見つかりません")
            
            if evaluation_data.get('contract_id'):
                contract = await Contract.get_or_none(id=evaluation_data['contract_id'])
                if not contract:
                    raise ValueError("指定された契約が見つかりません")
            
            # employee_idは更新不可（person_idは固定）
            if 'employee_id' in evaluation_data:
                evaluation_data.pop('employee_id')
            
            await evaluation.update_from_dict(clean_dict(evaluation_data))
            await evaluation.save()
            
            return evaluation

    async def delete_evaluation(self, evaluation_id: int) -> bool:
        """評価削除"""
        evaluation = await PersonEvaluation.get_or_none(id=evaluation_id, person_type=PersonType.EMPLOYEE)
        if evaluation:
            async with in_transaction():
                await evaluation.delete()
            return True
        return False

    # ===== 業務ロジック =====
    async def get_employee_evaluations(self, employee: Personnel, page: int = 1, page_size: int = 10) -> Tuple[List[PersonEvaluation], int]:
        """特定社員の評価一覧取得"""
        query = Q(person_type=PersonType.EMPLOYEE, person_id=employee.id)
        
        total = await PersonEvaluation.filter(query).count()
        evaluations = await PersonEvaluation.filter(query).prefetch_related(
            'case', 'contract'
        ).order_by('-evaluation_date', '-created_at').limit(page_size).offset((page - 1) * page_size).all()
        
        return evaluations, total

    async def create_employee_evaluation(self, employee: Personnel, evaluation_data: Dict[str, Any], evaluator_id: int) -> PersonEvaluation:
        """特定社員の評価作成"""
        evaluation_data['employee_id'] = employee.id
        return await self.create_evaluation(evaluation_data, evaluator_id)

    async def get_employee_evaluation_summary(self, employee: Personnel) -> Dict[str, Any]:
        """特定社員の評価サマリー取得"""
        evaluations = await PersonEvaluation.filter(
            person_type=PersonType.EMPLOYEE, 
            person_id=employee.id
        ).all()
        
        if not evaluations:
            return {
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
        
        # 各評価項目の平均計算
        total_overall = sum(e.overall_rating for e in evaluations)
        total_technical = sum(e.technical_skill for e in evaluations)
        total_communication = sum(e.communication for e in evaluations)
        total_reliability = sum(e.reliability for e in evaluations)
        total_proactiveness = sum(e.proactiveness for e in evaluations)
        
        # 拡張項目（社員のみ）の平均
        independence_evals = [e.independence for e in evaluations if e.independence is not None]
        delivery_evals = [e.delivery_quality for e in evaluations if e.delivery_quality is not None]
        
        # 推薦率
        recommendations = sum(1 for e in evaluations if e.recommendation)
        
        return {
            "total_evaluations": total,
            "average_overall_rating": round(total_overall / total, 2),
            "average_technical_skill": round(total_technical / total, 2),
            "average_communication": round(total_communication / total, 2),
            "average_reliability": round(total_reliability / total, 2),
            "average_proactiveness": round(total_proactiveness / total, 2),
            "average_independence": round(sum(independence_evals) / len(independence_evals), 2) if independence_evals else 0.0,
            "average_delivery_quality": round(sum(delivery_evals) / len(delivery_evals), 2) if delivery_evals else 0.0,
            "recommendation_rate": round((recommendations / total) * 100, 1),
            "latest_evaluation_date": max(e.evaluation_date for e in evaluations) if evaluations else None,
        }

    async def get_top_rated_employees(self, limit: int = 10, min_evaluations: int = 3) -> List[Personnel]:
        """高評価社員取得"""
        # 社員の評価平均を計算するサブクエリが複雑なため、Pythonで処理
        employee_ratings = {}
        
        # 全社員の評価を取得
        evaluations = await PersonEvaluation.filter(person_type=PersonType.EMPLOYEE).all()
        
        # 社員IDごとに評価を集計
        for evaluation in evaluations:
            employee_id = evaluation.person_id
            if employee_id not in employee_ratings:
                employee_ratings[employee_id] = []
            employee_ratings[employee_id].append(evaluation.overall_rating)
        
        # 最低評価数を満たす社員のみ対象
        qualified_employees = []
        for employee_id, ratings in employee_ratings.items():
            if len(ratings) >= min_evaluations:
                avg_rating = sum(ratings) / len(ratings)
                qualified_employees.append((employee_id, avg_rating))
        
        # 平均評価でソート
        qualified_employees.sort(key=lambda x: x[1], reverse=True)
        
        # 上位のPersonnelオブジェクトを取得
        top_employee_ids = [emp_id for emp_id, _ in qualified_employees[:limit]]
        employees = await Personnel.filter(
            id__in=top_employee_ids, 
            person_type=PersonType.EMPLOYEE
        ).all()
        
        # 評価順にソート
        employees_dict = {emp.id: emp for emp in employees}
        return [employees_dict[emp_id] for emp_id in top_employee_ids if emp_id in employees_dict]

    async def get_evaluation_stats_by_period(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """期間別評価統計取得"""
        evaluations = await PersonEvaluation.filter(
            person_type=PersonType.EMPLOYEE,
            evaluation_date__gte=start_date,
            evaluation_date__lte=end_date
        ).all()
        
        if not evaluations:
            return {
                "total_evaluations": 0,
                "average_overall_rating": 0.0,
                "average_technical_skill": 0.0,
                "average_communication": 0.0,
                "average_reliability": 0.0,
                "average_proactiveness": 0.0,
                "recommendation_rate": 0.0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
        
        total = len(evaluations)
        
        # 各項目平均
        avg_overall = sum(e.overall_rating for e in evaluations) / total
        avg_technical = sum(e.technical_skill for e in evaluations) / total
        avg_communication = sum(e.communication for e in evaluations) / total
        avg_reliability = sum(e.reliability for e in evaluations) / total
        avg_proactiveness = sum(e.proactiveness for e in evaluations) / total
        
        # 推薦率
        recommendations = sum(1 for e in evaluations if e.recommendation)
        recommendation_rate = (recommendations / total) * 100
        
        # 評価分布
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for evaluation in evaluations:
            rating_distribution[evaluation.overall_rating] += 1
        
        return {
            "total_evaluations": total,
            "average_overall_rating": round(avg_overall, 2),
            "average_technical_skill": round(avg_technical, 2),
            "average_communication": round(avg_communication, 2),
            "average_reliability": round(avg_reliability, 2),
            "average_proactiveness": round(avg_proactiveness, 2),
            "recommendation_rate": round(recommendation_rate, 1),
            "rating_distribution": rating_distribution
        }

    # ===== ヘルパーメソッド =====
    async def evaluations_to_dict(self, evaluations: List[PersonEvaluation], include_relations: bool = False) -> List[Dict[str, Any]]:
        """評価リストを辞書形式に変換"""
        result = []
        for evaluation in evaluations:
            eval_dict = await evaluation.to_dict()
            
            # person_idをemployee_idとして返す（API互換性のため）
            eval_dict['employee_id'] = eval_dict.pop('person_id')
            
            if include_relations:
                # Personnel情報を追加
                employee = await Personnel.get_or_none(id=evaluation.person_id)
                if employee:
                    eval_dict['employee'] = await employee.to_dict()
            
            result.append(eval_dict)
        
        return result

    async def evaluation_to_dict(self, evaluation: PersonEvaluation, include_relations: bool = False) -> Dict[str, Any]:
        """評価を辞書形式に変換"""
        eval_dict = await evaluation.to_dict()
        
        # person_idをemployee_idとして返す（API互換性のため）
        eval_dict['employee_id'] = eval_dict.pop('person_id')
        
        if include_relations:
            # Personnel情報を追加
            employee = await Personnel.get_or_none(id=evaluation.person_id)
            if employee:
                eval_dict['employee'] = await employee.to_dict()
        
        return eval_dict


# グローバルインスタンス
employee_evaluation_controller = EmployeeEvaluationController()