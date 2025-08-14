from typing import Optional

from fastapi import APIRouter, Query

from app.controllers.case import case_candidate_controller, case_controller
from app.schemas import Fail, Success
from app.schemas.case import (AddCaseCandidateSchema, AddCaseSchema,
                              UpdateCaseCandidateSchema, UpdateCaseSchema)

router = APIRouter()


@router.get("/list", summary="案件一覧取得")
async def get_case_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    title: Optional[str] = Query(None, description="案件タイトル検索"),
    status: Optional[str] = Query(None, description="ステータス検索"),
    client_company_id: Optional[int] = Query(None, description="取引先会社ID検索"),
):
    try:
        data, total = await case_controller.get_cases_with_filters(
            page=page, page_size=pageSize, title=title, status=status, client_company_id=client_company_id
        )
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="IDで案件取得")
async def get_case(id: int = Query(..., description="案件ID")):
    try:
        data = await case_controller.get_case_dict_by_id(case_id=id)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="案件が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/add", summary="案件新規作成")
async def add_case(case_data: AddCaseSchema):
    try:
        data = await case_controller.create_case_dict(case_data=case_data)
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/update", summary="案件更新")
async def update_case(case_data: UpdateCaseSchema):
    try:
        data = await case_controller.update_case_dict(case_data=case_data)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="案件が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="案件削除")
async def delete_case(id: int = Query(..., description="案件ID")):
    try:
        await case_controller.delete_case(case_id=id)
        return Success()
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/candidates", summary="案件候補者一覧取得")
async def get_case_candidates(
    case_id: int = Query(..., description="案件ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    try:
        data, total = await case_candidate_controller.get_candidates_by_case_id(
            case_id=case_id, page=page, page_size=pageSize
        )
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/candidate/get", summary="IDで候補者取得")
async def get_candidate(id: int = Query(..., description="候補者ID")):
    try:
        data = await case_candidate_controller.get_candidate_dict_by_id(candidate_id=id)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="候補者が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/candidate/add", summary="案件候補者追加")
async def add_candidate(candidate_data: AddCaseCandidateSchema):
    try:
        data = await case_candidate_controller.add_candidate_dict(candidate_data=candidate_data)
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/candidate/update", summary="候補者情報更新")
async def update_candidate(candidate_data: UpdateCaseCandidateSchema):
    try:
        data = await case_candidate_controller.update_candidate_dict(candidate_data=candidate_data)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="候補者が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/candidate/delete", summary="候補者削除")
async def delete_candidate(id: int = Query(..., description="候補者ID")):
    try:
        await case_candidate_controller.delete_candidate(candidate_id=id)
        return Success()
    except Exception as e:
        return Fail(msg=str(e))
