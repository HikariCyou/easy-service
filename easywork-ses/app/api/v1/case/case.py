from typing import Optional

from fastapi import APIRouter, Query

from app.controllers.case import case_candidate_controller, case_controller
from app.schemas import Fail, Success
from app.schemas.case import (
    AddCaseCandidateSchema,
    AddCaseSchema,
    CaseTerminationSchema,
    UpdateCaseCandidateSchema,
    UpdateCaseSchema,
)

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


@router.post("/terminate", summary="案件終了")
async def terminate_case(termination_data: CaseTerminationSchema):
    try:
        case = await case_controller.get_case_by_id(case_id=termination_data.case_id)
        if not case:
            return Fail(msg="案件が見つかりませんでした")

        result = await case.terminate_case(
            termination_date=termination_data.termination_date,
            reason=termination_data.reason,
            terminated_by=termination_data.terminated_by,
        )
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/client-sales-representatives/{client_company_id}", summary="取引先営業担当者一覧取得")
async def get_client_sales_representatives(client_company_id: int):
    """指定した取引先会社の営業担当者一覧を取得"""
    try:
        from app.models.client import ClientContact

        representatives = await ClientContact.filter(client_company_id=client_company_id, is_active=True).all()

        data = []
        for rep in representatives:
            rep_data = await rep.to_dict()
            data.append(
                {
                    "id": rep_data["id"],
                    "name": rep_data["name"],
                    "name_kana": rep_data.get("name_kana"),
                    "email": rep_data["email"],
                    "phone": rep_data.get("phone"),
                    "is_primary": rep_data.get("is_primary", False),
                }
            )

        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/company-sales-representatives", summary="自社営業担当者一覧取得")
async def get_company_sales_representatives():
    """自社の営業担当者（Employee）一覧を取得"""
    try:
        from app.models.enums import PersonType
        from app.models.personnel import Personnel

        representatives = await Personnel.filter(person_type=PersonType.EMPLOYEE, is_active=True).all()

        data = []
        for rep in representatives:
            rep_data = await rep.to_dict()
            data.append(
                {
                    "id": rep_data["id"],
                    "name": rep_data["name"],
                    "code": rep_data.get("code"),
                    "email": rep_data.get("email"),
                    "phone": rep_data.get("phone"),
                }
            )

        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/by-client/{client_id}", summary="取引先会社別案件一覧取得")
async def get_cases_by_client(
    client_id: int,
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    title: Optional[str] = Query(None, description="案件タイトル検索"),
    status: Optional[str] = Query(None, description="ステータス検索"),
):
    """指定した取引先会社の案件一覧を取得する"""
    try:
        data, total = await case_controller.get_cases_with_filters(
            page=page,
            page_size=pageSize,
            title=title,
            status=status,
            client_company_id=client_id
        )
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))
