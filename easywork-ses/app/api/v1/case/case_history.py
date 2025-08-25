from datetime import date
from typing import Optional
from fastapi import APIRouter, Query, Body, HTTPException

from app.controllers.case import case_history_controller
from app.schemas import Success, Fail
from app.schemas.case import (
    CaseHistorySchema,
    CreateCaseHistorySchema,
    CaseHistorySearchSchema,
    CaseHistoryStatsSchema
)

router = APIRouter()


@router.post("/", summary="案件変更履歴作成")
async def create_case_history(data: CreateCaseHistorySchema):
    """
    案件変更履歴を手動作成
    
    通常は案件の更新時に自動で作成されますが、
    手動でカスタム履歴を作成する場合に使用
    """
    try:
        history = await case_history_controller.create_history(data)
        result = await history.to_dict()
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/list", summary="案件変更履歴一覧取得")
async def get_case_history_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    case_id: Optional[int] = Query(None, description="案件ID"),
    change_type: Optional[str] = Query(None, description="変更タイプ"),
    changed_by: Optional[int] = Query(None, description="変更者ユーザーID"),
    field_name: Optional[str] = Query(None, description="変更フィールド名"),
    start_date: Optional[date] = Query(None, description="検索開始日"),
    end_date: Optional[date] = Query(None, description="検索終了日")
):
    """
    案件変更履歴の一覧を取得
    
    検索条件:
    - 案件ID
    - 変更タイプ（create/update/delete/status_change等）
    - 変更者ユーザーID
    - 変更フィールド名
    - 日付範囲
    """
    try:
        search_params = CaseHistorySearchSchema(
            case_id=case_id,
            change_type=change_type,
            changed_by=changed_by,
            field_name=field_name,
            start_date=start_date,
            end_date=end_date
        )
        
        result = await case_history_controller.get_case_history_list(
            page=page,
            page_size=page_size,
            search_params=search_params
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/{history_id}", summary="案件変更履歴詳細取得")
async def get_case_history(history_id: int):
    """
    指定IDの案件変更履歴詳細を取得
    """
    try:
        history = await case_history_controller.get_history_by_id(history_id)
        if not history:
            return Fail(msg="変更履歴が見つかりません")
        return Success(data=history)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/case/{case_id}/history", summary="特定案件の変更履歴取得")
async def get_case_history_by_case(
    case_id: int,
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ")
):
    """
    指定案件の変更履歴を時系列で取得
    
    案件詳細画面でその案件の履歴を表示する際に使用
    """
    try:
        result = await case_history_controller.get_history_by_case(
            case_id=case_id,
            page=page,
            page_size=page_size
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/stats/summary", summary="案件変更履歴統計取得")
async def get_case_history_stats(
    case_id: Optional[int] = Query(None, description="案件ID"),
    change_type: Optional[str] = Query(None, description="変更タイプ"),
    changed_by: Optional[int] = Query(None, description="変更者ユーザーID"),
    start_date: Optional[date] = Query(None, description="統計開始日"),
    end_date: Optional[date] = Query(None, description="統計終了日")
):
    """
    案件変更履歴の統計情報を取得
    
    含まれる統計:
    - 総変更数
    - 変更タイプ別件数
    - 最も変更回数の多い案件Top10
    - 最もアクティブなユーザーTop10
    - 最近の変更履歴
    """
    try:
        search_params = CaseHistorySearchSchema(
            case_id=case_id,
            change_type=change_type,
            changed_by=changed_by,
            start_date=start_date,
            end_date=end_date
        )
        
        stats = await case_history_controller.get_history_stats(search_params)
        return Success(data=stats)
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/{history_id}", summary="案件変更履歴削除")
async def delete_case_history(history_id: int):
    """
    案件変更履歴を削除
    
    注意: 通常は履歴の削除は推奨されませんが、
    管理者権限での操作や間違った履歴の削除に使用
    """
    try:
        success = await case_history_controller.delete_history(history_id)
        if success:
            return Success(data={"deleted": True})
        else:
            return Fail(msg="変更履歴が見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/export/data", summary="案件変更履歴エクスポート")
async def export_case_history_data(
    format: str = Query("excel", description="エクスポート形式", regex="^(excel|csv)$"),
    case_id: Optional[int] = Query(None, description="案件ID"),
    change_type: Optional[str] = Query(None, description="変更タイプ"),
    changed_by: Optional[int] = Query(None, description="変更者ユーザーID"),
    start_date: Optional[date] = Query(None, description="開始日"),
    end_date: Optional[date] = Query(None, description="終了日")
):
    """
    案件変更履歴データをエクスポート
    
    対応形式: Excel、CSV
    監査レポートや分析用のデータ出力に使用
    
    注意: このエンドポイントは予約済み
    実装時は指定形式のファイルを生成し、ダウンロードURLを返す
    """
    try:
        export_params = {
            "format": format,
            "filters": {
                "case_id": case_id,
                "change_type": change_type,
                "changed_by": changed_by,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
        
        return Success(data={
            "export_params": export_params,
            "download_url": None,
            "note": "案件変更履歴エクスポート機能は今後のバージョンで提供予定です"
        })
    except Exception as e:
        return Fail(msg=str(e))