from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class CreateEmployeeEvaluationSchema(BaseModel):
    """自社社員評価作成schema"""
    
    employee_id: int = Field(..., description="対象社員ID", example=1)
    case_id: Optional[int] = Field(None, description="評価対象案件ID", example=1)
    contract_id: Optional[int] = Field(None, description="評価対象契約ID", example=1)
    technical_skill: int = Field(..., description="技術力 (1-5)", example=5, ge=1, le=5)
    communication: int = Field(..., description="コミュニケーション力 (1-5)", example=4, ge=1, le=5)
    reliability: int = Field(..., description="信頼性 (1-5)", example=5, ge=1, le=5)
    proactiveness: int = Field(..., description="積極性 (1-5)", example=4, ge=1, le=5)
    independence: int = Field(..., description="自立性 (1-5)", example=5, ge=1, le=5)
    delivery_quality: int = Field(..., description="成果物品質 (1-5)", example=5, ge=1, le=5)
    overall_rating: int = Field(..., description="総合評価 (1-5)", example=5, ge=1, le=5)
    good_points: Optional[str] = Field(None, description="良い点", example="高い技術力と迅速な対応で期待以上の成果を提供した")
    improvement_points: Optional[str] = Field(None, description="改善点", example="定期的な進捗報告があるとより良い")
    recommendation: bool = Field(..., description="次回推薦可能か", example=True)
    evaluation_date: date = Field(..., description="評価日", example="2024-01-31")
    remark: Optional[str] = Field(None, description="備考", example="優秀な社員です")


class UpdateEmployeeEvaluationSchema(BaseModel):
    """自社社員評価更新schema"""
    
    case_id: Optional[int] = Field(None, description="評価対象案件ID", example=1)
    contract_id: Optional[int] = Field(None, description="評価対象契約ID", example=1)
    technical_skill: Optional[int] = Field(None, description="技術力 (1-5)", example=5, ge=1, le=5)
    communication: Optional[int] = Field(None, description="コミュニケーション力 (1-5)", example=4, ge=1, le=5)
    reliability: Optional[int] = Field(None, description="信頼性 (1-5)", example=5, ge=1, le=5)
    proactiveness: Optional[int] = Field(None, description="積極性 (1-5)", example=4, ge=1, le=5)
    independence: Optional[int] = Field(None, description="自立性 (1-5)", example=5, ge=1, le=5)
    delivery_quality: Optional[int] = Field(None, description="成果物品質 (1-5)", example=5, ge=1, le=5)
    overall_rating: Optional[int] = Field(None, description="総合評価 (1-5)", example=5, ge=1, le=5)
    good_points: Optional[str] = Field(None, description="良い点", example="高い技術力と迅速な対応で期待以上の成果を提供した")
    improvement_points: Optional[str] = Field(None, description="改善点", example="定期的な進捗報告があるとより良い")
    recommendation: Optional[bool] = Field(None, description="次回推薦可能か", example=True)
    evaluation_date: Optional[date] = Field(None, description="評価日", example="2024-01-31")
    remark: Optional[str] = Field(None, description="備考", example="優秀な社員です")


class EmployeeEvaluationListSchema(BaseModel):
    """自社社員評価一覧schema"""
    
    id: int = Field(..., description="評価ID")
    employee_id: int = Field(..., description="対象社員ID")
    employee_name: Optional[str] = Field(None, description="対象社員名")
    case_id: Optional[int] = Field(None, description="評価対象案件ID")
    case_name: Optional[str] = Field(None, description="評価対象案件名")
    contract_id: Optional[int] = Field(None, description="評価対象契約ID")
    contract_number: Optional[str] = Field(None, description="評価対象契約番号")
    technical_skill: int = Field(..., description="技術力 (1-5)")
    communication: int = Field(..., description="コミュニケーション力 (1-5)")
    reliability: int = Field(..., description="信頼性 (1-5)")
    proactiveness: int = Field(..., description="積極性 (1-5)")
    independence: int = Field(..., description="自立性 (1-5)")
    delivery_quality: int = Field(..., description="成果物品質 (1-5)")
    overall_rating: int = Field(..., description="総合評価 (1-5)")
    good_points: Optional[str] = Field(None, description="良い点")
    improvement_points: Optional[str] = Field(None, description="改善点")
    recommendation: bool = Field(..., description="次回推薦可能か")
    evaluator_id: int = Field(..., description="評価者ID")
    evaluation_date: date = Field(..., description="評価日")
    remark: Optional[str] = Field(None, description="備考")
    created_at: Optional[date] = Field(None, description="作成日")
    updated_at: Optional[date] = Field(None, description="更新日")


class EmployeeEvaluationDetailSchema(EmployeeEvaluationListSchema):
    """自社社員評価詳細schema"""
    
    # 関連情報
    employee: Optional[dict] = Field(None, description="社員情報")
    case: Optional[dict] = Field(None, description="案件情報")
    contract: Optional[dict] = Field(None, description="契約情報")


class EmployeeEvaluationSummarySchema(BaseModel):
    """自社社員評価統計schema"""
    
    total_evaluations: int = Field(..., description="総評価数")
    average_overall_rating: float = Field(..., description="平均総合評価")
    average_technical_skill: float = Field(..., description="平均技術力")
    average_communication: float = Field(..., description="平均コミュニケーション力")
    average_reliability: float = Field(..., description="平均信頼性")
    average_proactiveness: float = Field(..., description="平均積極性")
    average_independence: float = Field(..., description="平均自立性")
    average_delivery_quality: float = Field(..., description="平均成果物品質")
    recommendation_rate: float = Field(..., description="推薦率(%)")


class EmployeeEvaluationSearchSchema(BaseModel):
    """自社社員評価検索schema"""
    
    employee_id: Optional[int] = Field(None, description="社員IDで絞り込み")
    case_id: Optional[int] = Field(None, description="案件IDで絞り込み")
    contract_id: Optional[int] = Field(None, description="契約IDで絞り込み")
    evaluator_id: Optional[int] = Field(None, description="評価者IDで絞り込み")
    min_overall_rating: Optional[int] = Field(None, description="最低総合評価", ge=1, le=5)
    max_overall_rating: Optional[int] = Field(None, description="最高総合評価", ge=1, le=5)
    recommendation: Optional[bool] = Field(None, description="推薦可能かどうか")
    evaluation_date_from: Optional[date] = Field(None, description="評価日開始")
    evaluation_date_to: Optional[date] = Field(None, description="評価日終了")
    good_points_keyword: Optional[str] = Field(None, description="良い点キーワード検索")
    improvement_points_keyword: Optional[str] = Field(None, description="改善点キーワード検索")