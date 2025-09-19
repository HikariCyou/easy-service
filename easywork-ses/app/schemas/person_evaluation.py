from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.models.enums import PersonType


class PersonEvaluationBase(BaseModel):
    """人材評価基本スキーマ"""

    person_type: PersonType = Field(..., description="人材タイプ")
    person_id: int = Field(..., description="対象人材ID")
    case_id: Optional[int] = Field(None, description="評価対象案件ID")
    contract_id: Optional[int] = Field(None, description="評価対象契約ID")

    technical_skill: int = Field(..., ge=1, le=5, description="技術力 (1-5)")
    communication: int = Field(..., ge=1, le=5, description="コミュニケーション力 (1-5)")
    reliability: int = Field(..., ge=1, le=5, description="信頼性 (1-5)")
    proactiveness: int = Field(..., ge=1, le=5, description="積極性 (1-5)")
    independence: Optional[int] = Field(None, ge=1, le=5, description="自立性 (1-5)")
    delivery_quality: Optional[int] = Field(None, ge=1, le=5, description="成果物品質 (1-5)")
    overall_rating: int = Field(..., ge=1, le=5, description="総合評価 (1-5)")

    good_points: Optional[str] = Field(None, description="良い点")
    improvement_points: Optional[str] = Field(None, description="改善点")
    recommendation: bool = Field(..., description="次回推薦可能か")

    evaluation_date: date = Field(..., description="評価日")
    remark: Optional[str] = Field(None, description="備考")

    evaluator_id: Optional[int] = Field(None, description="評価者ID")

    @validator("independence", "delivery_quality")
    def validate_extended_fields(cls, v, values):
        """拡張フィールドのバリデーション"""
        person_type = values.get("person_type")
        if person_type == PersonType.BP_EMPLOYEE:
            # BP社員の場合は強制的にNoneに設定
            return None
        # フリーランスと自社社員の場合はそのまま返す
        return v


class CreatePersonEvaluationSchema(PersonEvaluationBase):
    """人材評価作成スキーマ"""

    pass


class UpdatePersonEvaluationSchema(BaseModel):
    """人材評価更新スキーマ"""

    case_id: Optional[int] = Field(None, description="評価対象案件ID")
    contract_id: Optional[int] = Field(None, description="評価対象契約ID")

    technical_skill: Optional[int] = Field(None, ge=1, le=5, description="技術力 (1-5)")
    communication: Optional[int] = Field(None, ge=1, le=5, description="コミュニケーション力 (1-5)")
    reliability: Optional[int] = Field(None, ge=1, le=5, description="信頼性 (1-5)")
    proactiveness: Optional[int] = Field(None, ge=1, le=5, description="積極性 (1-5)")
    independence: Optional[int] = Field(None, ge=1, le=5, description="自立性 (1-5)")
    delivery_quality: Optional[int] = Field(None, ge=1, le=5, description="成果物品質 (1-5)")
    overall_rating: Optional[int] = Field(None, ge=1, le=5, description="総合評価 (1-5)")

    good_points: Optional[str] = Field(None, description="良い点")
    improvement_points: Optional[str] = Field(None, description="改善点")
    recommendation: Optional[bool] = Field(None, description="次回推薦可能か")

    evaluation_date: Optional[date] = Field(None, description="評価日")
    remark: Optional[str] = Field(None, description="備考")


class PersonEvaluationDetailSchema(PersonEvaluationBase):
    """人材評価詳細スキーマ"""

    id: int = Field(..., description="評価ID")
    evaluator_id: int = Field(..., description="評価者ID")
    person_name: Optional[str] = Field(None, description="対象人材名")
    case_name: Optional[str] = Field(None, description="案件名")
    contract_number: Optional[str] = Field(None, description="契約番号")
    created_at: date = Field(..., description="作成日時")
    updated_at: date = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class PersonEvaluationListSchema(BaseModel):
    """人材評価リストスキーマ"""

    id: int = Field(..., description="評価ID")
    person_type: PersonType = Field(..., description="人材タイプ")
    person_id: int = Field(..., description="対象人材ID")
    person_name: Optional[str] = Field(None, description="対象人材名")
    overall_rating: int = Field(..., description="総合評価")
    recommendation: bool = Field(..., description="次回推薦可能か")
    evaluation_date: date = Field(..., description="評価日")
    evaluator_id: int = Field(..., description="評価者ID")
    case_name: Optional[str] = Field(None, description="案件名")

    class Config:
        from_attributes = True


class PersonEvaluationSummarySchema(BaseModel):
    """人材評価サマリースキーマ"""

    person_type: PersonType = Field(..., description="人材タイプ")
    person_id: int = Field(..., description="対象人材ID")
    person_name: Optional[str] = Field(None, description="対象人材名")
    total_evaluations: int = Field(..., description="総評価数")
    average_overall_rating: float = Field(..., description="平均総合評価")
    average_technical_skill: float = Field(..., description="平均技術力")
    average_communication: float = Field(..., description="平均コミュニケーション力")
    average_reliability: float = Field(..., description="平均信頼性")
    average_proactiveness: float = Field(..., description="平均積極性")
    average_independence: Optional[float] = Field(None, description="平均自立性")
    average_delivery_quality: Optional[float] = Field(None, description="平均成果物品質")
    recommendation_rate: float = Field(..., description="推薦率 (%)")
    latest_evaluation_date: Optional[date] = Field(None, description="最新評価日")


class PersonEvaluationSearchSchema(BaseModel):
    """人材評価検索スキーマ"""

    person_type: Optional[PersonType] = Field(None, description="人材タイプ")
    person_id: Optional[int] = Field(None, description="対象人材ID")
    case_id: Optional[int] = Field(None, description="案件ID")
    contract_id: Optional[int] = Field(None, description="契約ID")
    evaluator_id: Optional[int] = Field(None, description="評価者ID")

    min_overall_rating: Optional[int] = Field(None, ge=1, le=5, description="最小総合評価")
    max_overall_rating: Optional[int] = Field(None, ge=1, le=5, description="最大総合評価")

    recommendation: Optional[bool] = Field(None, description="推薦可能かどうか")

    evaluation_date_from: Optional[date] = Field(None, description="評価日開始")
    evaluation_date_to: Optional[date] = Field(None, description="評価日終了")

    good_points_keyword: Optional[str] = Field(None, description="良い点キーワード")
    improvement_points_keyword: Optional[str] = Field(None, description="改善点キーワード")


class PersonEvaluationStatsSchema(BaseModel):
    """人材評価統計スキーマ"""

    period: str = Field(..., description="集計期間")
    total_evaluations: int = Field(..., description="総評価数")
    average_overall_rating: float = Field(..., description="平均総合評価")
    recommendation_rate: float = Field(..., description="推薦率 (%)")
    top_rated_count: int = Field(..., description="高評価件数 (4点以上)")

    # 人材タイプ別統計
    bp_employee_count: int = Field(0, description="BP社員評価数")
    freelancer_count: int = Field(0, description="フリーランス評価数")
    employee_count: int = Field(0, description="自社社員評価数")


class PersonTopRatedSchema(BaseModel):
    """高評価人材スキーマ"""

    person_type: PersonType = Field(..., description="人材タイプ")
    person_id: int = Field(..., description="人材ID")
    person_name: str = Field(..., description="人材名")
    average_rating: float = Field(..., description="平均評価")
    total_evaluations: int = Field(..., description="総評価数")
    recommendation_rate: float = Field(..., description="推薦率 (%)")
    latest_evaluation_date: Optional[date] = Field(None, description="最新評価日")


# レスポンス用のスキーマ
class PersonEvaluationListResponse(BaseModel):
    """人材評価リストレスポンス"""

    evaluations: List[PersonEvaluationListSchema]
    total: int
    page: int
    page_size: int


class PersonEvaluationPaginatedResponse(BaseModel):
    """人材評価ページネーションレスポンス"""

    data: List[PersonEvaluationDetailSchema]
    total: int
    page: int
    page_size: int
    total_pages: int
