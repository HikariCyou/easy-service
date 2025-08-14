from typing import List, Dict, Any, Optional
from datetime import date

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.employee import Employee, EmployeeEvaluation
from app.models.case import Case
from app.models.contract import Contract
from app.utils.common import clean_dict


class EmployeeEvaluationController:
    """自社社員評価コントローラー"""

    def __init__(self):
        pass

    # ===== 基本CRUD =====
    async def list_evaluations(self, page: int = 1, page_size: int = 10, search_params: Dict = None) -> tuple:
        """評価一覧取得"""
        if search_params is None:
            search_params = {}
        
        # 検索条件構築
        query = self._build_search_query(search_params)
        
        # 総件数取得
        total = await EmployeeEvaluation.filter(query).count()
        
        # データ取得
        evaluations = await EmployeeEvaluation.filter(query).prefetch_related(
            'freelancer', 'case', 'contract'
        ).order_by('-evaluation_date', '-created_at').limit(page_size).offset((page - 1) * page_size).all()
        
        return evaluations, total

    async def get_evaluation_by_id(self, evaluation_id: int, include_relations: bool = False) -> Optional[EmployeeEvaluation]:
        """ID で評価取得"""
        query = EmployeeEvaluation.filter(id=evaluation_id)
        if include_relations:
            query = query.prefetch_related('freelancer', 'case', 'contract')
        return await query.first()

    async def create_evaluation(self, evaluation_data: Dict[str, Any], evaluator_id: int) -> EmployeeEvaluation:
        """評価作成"""
        async with in_transaction():
            # 社員存在確認
            employee = await Employee.get_or_none(id=evaluation_data.get('employee_id'))
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
            
            # 評価データ作成
            evaluation_data['evaluator_id'] = evaluator_id
            evaluation_data['freelancer'] = employee  # Model の field 名に合わせる
            evaluation_data.pop('employee_id', None)  # employee_id を削除
            
            evaluation = await EmployeeEvaluation.create(**clean_dict(evaluation_data))
            
            # 関連データを含めて再取得
            return await self.get_evaluation_by_id(evaluation.id, include_relations=True)

    async def update_evaluation(self, evaluation_id: int, evaluation_data: Dict[str, Any]) -> Optional[EmployeeEvaluation]:
        """評価更新"""
        evaluation = await EmployeeEvaluation.get_or_none(id=evaluation_id)
        if not evaluation:
            return None

        async with in_transaction():
            # 案件・契約の存在確認（更新される場合）
            if evaluation_data.get('case_id'):
                case = await Case.get_or_none(id=evaluation_data['case_id'])
                if not case:
                    raise ValueError("指定された案件が見つかりません")
            
            if evaluation_data.get('contract_id'):
                contract = await Contract.get_or_none(id=evaluation_data['contract_id'])
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
        evaluation = await EmployeeEvaluation.get_or_none(id=evaluation_id)
        if evaluation:
            async with in_transaction():
                await evaluation.delete()
            return True
        return False

    # ===== 特定社員の評価管理 =====
    async def get_employee_evaluations(self, employee: Employee, page: int = 1, page_size: int = 10) -> tuple:
        """特定社員の評価一覧取得"""
        query = EmployeeEvaluation.filter(freelancer=employee).prefetch_related('case', 'contract')
        
        total = await query.count()
        evaluations = await query.order_by('-evaluation_date', '-created_at').limit(page_size).offset((page - 1) * page_size).all()
        
        return evaluations, total

    async def create_employee_evaluation(self, employee: Employee, evaluation_data: Dict[str, Any], evaluator_id: int) -> EmployeeEvaluation:
        """特定社員の評価作成"""
        # employee は create_evaluation内で設定されるので、ここでは employee_id を設定
        evaluation_data['employee_id'] = employee.id
        return await self.create_evaluation(evaluation_data, evaluator_id)

    async def get_employee_evaluation_summary(self, employee: Employee) -> Dict[str, Any]:
        """特定社員の評価サマリー取得"""
        evaluations = await EmployeeEvaluation.filter(freelancer=employee).all()
        
        if not evaluations:
            return {
                "total_evaluations": 0,
                "average_overall_rating": 0,
                "average_technical_skill": 0,
                "average_communication": 0,
                "average_reliability": 0,
                "average_proactiveness": 0,
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
            "average_proactiveness": round(sum(e.proactiveness for e in evaluations) / total, 2),
            "average_independence": round(sum(e.independence for e in evaluations) / total, 2),
            "average_delivery_quality": round(sum(e.delivery_quality for e in evaluations) / total, 2),
            "recommendation_rate": round(sum(1 for e in evaluations if e.recommendation) / total * 100, 1),
        }

    # ===== 業務ロジック =====
    async def get_top_rated_employees(self, limit: int = 10, min_evaluations: int = 3) -> List[Employee]:
        """高評価社員取得"""
        # 簡易実装（実際の実装では生のSQLかORMの高度な機能を使用）
        employees = await Employee.filter(is_active=True).all()
        employee_ratings = []
        
        for employee in employees:
            evaluations = await EmployeeEvaluation.filter(freelancer=employee).all()
            if len(evaluations) >= min_evaluations:
                avg_rating = sum(e.overall_rating for e in evaluations) / len(evaluations)
                employee_ratings.append((employee, avg_rating, len(evaluations)))
        
        # 評価順でソート
        employee_ratings.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        return [item[0] for item in employee_ratings[:limit]]

    async def get_evaluation_stats_by_period(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """期間別評価統計取得"""
        evaluations = await EmployeeEvaluation.filter(
            evaluation_date__gte=start_date,
            evaluation_date__lte=end_date
        ).all()
        
        if not evaluations:
            return {
                "period": f"{start_date} ~ {end_date}",
                "total_evaluations": 0,
                "average_overall_rating": 0,
                "recommendation_rate": 0,
                "top_rated_count": 0,
            }

        total = len(evaluations)
        avg_rating = sum(e.overall_rating for e in evaluations) / total
        recommendation_rate = sum(1 for e in evaluations if e.recommendation) / total * 100
        top_rated_count = sum(1 for e in evaluations if e.overall_rating >= 4)

        return {
            "period": f"{start_date} ~ {end_date}",
            "total_evaluations": total,
            "average_overall_rating": round(avg_rating, 2),
            "recommendation_rate": round(recommendation_rate, 1),
            "top_rated_count": top_rated_count,
        }

    # ===== データ変換 =====
    async def evaluations_to_dict(self, evaluations: List[EmployeeEvaluation], include_relations: bool = False) -> List[Dict[str, Any]]:
        """評価リスト辞書変換"""
        result = []
        for evaluation in evaluations:
            evaluation_dict = await evaluation.to_dict()
            
            if include_relations:
                # 関連データ追加
                if hasattr(evaluation, 'freelancer') and evaluation.freelancer:
                    evaluation_dict['employee'] = await evaluation.freelancer.to_dict()
                    evaluation_dict['employee_name'] = evaluation.freelancer.name
                
                if hasattr(evaluation, 'case') and evaluation.case:
                    evaluation_dict['case'] = await evaluation.case.to_dict()
                    evaluation_dict['case_name'] = evaluation.case.title
                
                if hasattr(evaluation, 'contract') and evaluation.contract:
                    evaluation_dict['contract'] = await evaluation.contract.to_dict()
                    evaluation_dict['contract_number'] = evaluation.contract.contract_number
            
            result.append(evaluation_dict)
        return result

    async def evaluation_to_dict(self, evaluation: EmployeeEvaluation, include_relations: bool = False) -> Optional[Dict[str, Any]]:
        """単一評価辞書変換"""
        if not evaluation:
            return None
        return (await self.evaluations_to_dict([evaluation], include_relations))[0]

    # ===== 内部辅助メソッド =====
    def _build_search_query(self, search_params: Dict) -> Q:
        """検索クエリ構築"""
        query = Q()
        
        # 社員IDで絞り込み
        if search_params.get('employee_id'):
            query &= Q(freelancer__id=search_params['employee_id'])
        
        # 案件IDで絞り込み
        if search_params.get('case_id'):
            query &= Q(case_id=search_params['case_id'])
        
        # 契約IDで絞り込み
        if search_params.get('contract_id'):
            query &= Q(contract_id=search_params['contract_id'])
        
        # 評価者IDで絞り込み
        if search_params.get('evaluator_id'):
            query &= Q(evaluator_id=search_params['evaluator_id'])
        
        # 評価レンジ
        if search_params.get('min_overall_rating'):
            query &= Q(overall_rating__gte=search_params['min_overall_rating'])
        if search_params.get('max_overall_rating'):
            query &= Q(overall_rating__lte=search_params['max_overall_rating'])
        
        # 推薦可能かどうか
        if search_params.get('recommendation') is not None:
            query &= Q(recommendation=search_params['recommendation'])
        
        # 評価日期間
        if search_params.get('evaluation_date_from'):
            query &= Q(evaluation_date__gte=search_params['evaluation_date_from'])
        if search_params.get('evaluation_date_to'):
            query &= Q(evaluation_date__lte=search_params['evaluation_date_to'])
        
        # キーワード検索
        if search_params.get('good_points_keyword'):
            query &= Q(good_points__icontains=search_params['good_points_keyword'])
        if search_params.get('improvement_points_keyword'):
            query &= Q(improvement_points__icontains=search_params['improvement_points_keyword'])
        
        return query


# 创建全局实例
employee_evaluation_controller = EmployeeEvaluationController()