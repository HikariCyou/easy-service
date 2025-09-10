from typing import Optional, Dict, Any, List
from datetime import datetime, date

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.core.ctx import CTX_USER_ID, CTX_USER_INFO
from app.models.case import Case, CaseCandidate, CaseHistory
from app.models.enums import ChangeType
from app.schemas.case import (AddCaseCandidateSchema, AddCaseSchema,
                              UpdateCaseCandidateSchema, UpdateCaseSchema,
                              CreateCaseHistorySchema, CaseHistorySearchSchema)
from app.utils.common import clean_dict


class CaseController:
    def __init__(self):
        pass
    
    def _get_current_user_info(self):
        """現在のユーザー情報を取得"""
        user_id = CTX_USER_ID.get()
        user_info = CTX_USER_INFO.get()
        user_name = user_info.get("nickname") if user_info else None
        return user_id, user_name

    async def list_cases(self, page: int = 1, page_size: int = 10, search: Q = None, order: list = []):
        query = Case.filter(search)
        total = await query.count()
        cases = await query.select_related("client_company", "client_sales_representative", "company_sales_representative").order_by(*order).limit(page_size).offset((page - 1) * page_size).all()
        return cases, total

    async def get_cases_with_filters(
        self,
        page: Optional[int] = 1,
        page_size: Optional[int] = 10,
        title: Optional[str] = None,
        status: Optional[str] = None,
        client_company_id: Optional[int] = None,
    ):
        q = Q()
        if title:
            q &= Q(title__icontains=title)
        if status:
            q &= Q(status=status)
        if client_company_id:
            q &= Q(client_company_id=client_company_id)

        cases, total = await self.list_cases(page=page, page_size=page_size, search=q)
        data = []
        for case in cases:
            case_dict = await case.to_dict()
            if case.client_company:
                case_dict['client_company'] = await case.client_company.to_dict()
            if case.client_sales_representative:
                case_dict['client_sales_representative'] = await case.client_sales_representative.to_dict()
            if case.company_sales_representative:
                case_dict['company_sales_representative'] = await case.company_sales_representative.to_dict()
            data.append(case_dict)
        return data, total

    async def get_case_by_id(self, case_id: int):
        case = await Case.get_or_none(id=case_id).select_related("client_company", "client_sales_representative", "company_sales_representative")
        return case

    async def get_case_dict_by_id(self, case_id: int):
        case = await self.get_case_by_id(case_id)
        if case:
            case_dict = await case.to_dict()
            # 添加关联信息
            if case.client_company:
                case_dict['client_company'] = await case.client_company.to_dict()
            if case.client_sales_representative:
                case_dict['client_sales_representative'] = await case.client_sales_representative.to_dict()
            if case.company_sales_representative:
                case_dict['company_sales_representative'] = await case.company_sales_representative.to_dict()
            return case_dict
        return None

    async def validate_sales_representatives(self, case_data, existing_case=None):
        """営業担当の妥当性検証"""
        # 取引先担当営業の検証
        if case_data.client_sales_representative_id:
            from app.models.client import ClientContact
            client_rep = await ClientContact.get_or_none(id=case_data.client_sales_representative_id)
            if not client_rep:
                raise ValueError(f"取引先担当営業ID {case_data.client_sales_representative_id} が見つかりません")
            
            # 同じ取引先会社かチェック
            client_company_id = None
            if hasattr(case_data, 'client_company_id') and case_data.client_company_id:
                client_company_id = case_data.client_company_id
            elif existing_case:
                client_company_id = existing_case.client_company_id
            
            if client_company_id and client_rep.client_company_id != client_company_id:
                raise ValueError("取引先担当営業は同じ取引先会社の担当者である必要があります")
        
        # 自社担当営業の検証
        if case_data.company_sales_representative_id:
            from app.models.personnel import Personnel
            from app.models.enums import PersonType
            company_rep = await Personnel.get_or_none(id=case_data.company_sales_representative_id)
            if not company_rep:
                raise ValueError(f"自社担当営業ID {case_data.company_sales_representative_id} が見つかりません")
            # 自社員工かチェック
            if company_rep.person_type != PersonType.EMPLOYEE:
                raise ValueError("自社担当営業は自社員工である必要があります")

    async def create_case(self, case_data: AddCaseSchema):
        # 営業担当の妥当性検証
        await self.validate_sales_representatives(case_data)
        
        async with in_transaction():
            data_dict = clean_dict(case_data.model_dump(exclude_unset=True))
            case = await Case.create(**data_dict)
            return case

    async def create_case_dict(self, case_data: AddCaseSchema):
        case = await self.create_case(case_data)
        case_dict = await case.to_dict()
        
        # 作成履歴を記録
        try:
            user_id, user_name = self._get_current_user_info()
            if user_id and user_id > 0:
                from app.controllers.case import case_history_controller
                await case_history_controller.create_simple_history(
                    case_id=case.id,
                    change_type=ChangeType.CREATE,
                    changed_by=user_id,
                    changed_by_name=user_name,
                    comment=f"案件「{case.title}」を作成",
                    change_details={"created_data": case_dict}
                )
        except Exception as e:
            # 履歴記録のエラーは本処理に影響させない
            print(f"Failed to create case history: {e}")
        
        return case_dict

    async def update_case(self, case_data: UpdateCaseSchema):
        case = await Case.get_or_none(id=case_data.id)
        if not case:
            return None
            
        # 営業担当の妥当性検証
        await self.validate_sales_representatives(case_data, existing_case=case)
        
        async with in_transaction():
            data_dict = clean_dict(case_data.model_dump(exclude_unset=True))
            await case.update_from_dict(data_dict)
            await case.save()
        return case

    async def update_case_dict(self, case_data: UpdateCaseSchema):
        # 更新前のデータを取得
        case = await Case.get_or_none(id=case_data.id)
        if not case:
            return None
            
        old_data = await case.to_dict()
        
        # 更新実行
        case = await self.update_case(case_data)
        if case:
            new_data = await case.to_dict()
            
            # 変更履歴を記録
            try:
                user_id, user_name = self._get_current_user_info()
                if user_id and user_id > 0:
                    from app.controllers.case import case_history_controller
                    update_dict = clean_dict(case_data.model_dump(exclude_unset=True))
                    
                    # ステータス変更の場合は特別な履歴を作成
                    if 'status' in update_dict and update_dict['status'] != old_data.get('status'):
                        await case_history_controller.create_simple_history(
                            case_id=case.id,
                            change_type=ChangeType.STATUS_CHANGE,
                            changed_by=user_id,
                            changed_by_name=user_name,
                            comment=f"案件ステータスを「{old_data.get('status')}」から「{update_dict['status']}」に変更",
                            change_details={
                                "old_status": old_data.get('status'),
                                "new_status": update_dict['status']
                            }
                        )
                    
                    # 一般的な更新履歴を作成
                    await case_history_controller.create_history_from_changes(
                        case_id=case.id,
                        old_data=old_data,
                        new_data=update_dict,
                        changed_by=user_id,
                        changed_by_name=user_name,
                        comment=f"案件「{case.title}」を更新"
                    )
            except Exception as e:
                # 履歴記録のエラーは本処理に影響させない
                print(f"Failed to create case update history: {e}")
            
            return new_data
        return None

    async def delete_case(self, case_id: int):
        case = await Case.get_or_none(id=case_id)
        if case:
            case_data = await case.to_dict()
            
            async with in_transaction():
                # 削除履歴を記録
                try:
                    user_id, user_name = self._get_current_user_info()
                    if user_id and user_id > 0:
                        from app.controllers.case import case_history_controller
                        await case_history_controller.create_simple_history(
                            case_id=case.id,
                            change_type=ChangeType.DELETE,
                            changed_by=user_id,
                            changed_by_name=user_name,
                            comment=f"案件「{case.title}」を削除",
                            change_details={"deleted_data": case_data}
                        )
                except Exception as e:
                    # 履歴記録のエラーは本処理に影響させない
                    print(f"Failed to create case delete history: {e}")
                
                await case.delete()
        return case


class CaseCandidateController:
    def __init__(self):
        pass
    
    def _get_current_user_info(self):
        """現在のユーザー情報を取得"""
        user_id = CTX_USER_ID.get()
        user_info = CTX_USER_INFO.get()
        user_name = user_info.get("nickname") if user_info else None
        return user_id, user_name

    async def list_candidates(self, page: int = 1, page_size: int = 10, search: Q = None, order: list = []):
        query = CaseCandidate.filter(search)
        total = await query.count()
        candidates = (
            await query.order_by(*order)
            .limit(page_size)
            .offset((page - 1) * page_size)
            .select_related("case", "bp_employee", "employee", "freelancer")
            .all()
        )
        return candidates, total

    async def get_candidates_by_case_id(self, case_id: int, page: int = 1, page_size: int = 10):
        q = Q(case_id=case_id)
        candidates, total = await self.list_candidates(page=page, page_size=page_size, search=q)
        data = []
        for candidate in candidates:
            candidate_dict = await candidate.to_dict()
            candidate_dict["candidate_name"] = candidate.candidate_name
            candidate_dict["candidate_type"] = candidate.candidate_type
            data.append(candidate_dict)
        return data, total

    async def get_candidate_by_id(self, candidate_id: int):
        candidate = await CaseCandidate.get_or_none(id=candidate_id).select_related(
            "case", "bp_employee", "employee", "freelancer"
        )
        return candidate

    async def get_candidate_dict_by_id(self, candidate_id: int):
        candidate = await self.get_candidate_by_id(candidate_id)
        if candidate:
            candidate_dict = await candidate.to_dict()
            candidate_dict["candidate_name"] = candidate.candidate_name
            candidate_dict["candidate_type"] = candidate.candidate_type
            return candidate_dict
        return None

    async def add_candidate(self, candidate_data: AddCaseCandidateSchema):
        async with in_transaction():
            data_dict = clean_dict(candidate_data.model_dump(exclude_unset=True))
            candidate = await CaseCandidate.create(**data_dict)
            return candidate

    async def add_candidate_dict(self, candidate_data: AddCaseCandidateSchema):
        candidate = await self.add_candidate(candidate_data)
        candidate_dict = await candidate.to_dict()
        candidate_dict["candidate_name"] = candidate.candidate_name
        candidate_dict["candidate_type"] = candidate.candidate_type
        
        # 候補者追加履歴を記録
        try:
            user_id, user_name = self._get_current_user_info()
            if user_id and user_id > 0:
                from app.controllers.case import case_history_controller
                await case_history_controller.create_simple_history(
                    case_id=candidate.case_id,
                    change_type=ChangeType.CANDIDATE_ADD,
                    changed_by=user_id,
                    changed_by_name=user_name,
                    comment=f"候補者「{candidate.candidate_name}」({candidate.candidate_type})を追加",
                    change_details={"candidate_data": candidate_dict}
                )
        except Exception as e:
            # 履歴記録のエラーは本処理に影響させない
            print(f"Failed to create candidate add history: {e}")
        
        return candidate_dict

    async def update_candidate(self, candidate_data: UpdateCaseCandidateSchema):
        candidate = await CaseCandidate.get_or_none(id=candidate_data.id)
        if candidate:
            async with in_transaction():
                data_dict = clean_dict(candidate_data.model_dump(exclude_unset=True))
                await candidate.update_from_dict(data_dict)
                await candidate.save()
        return candidate

    async def update_candidate_dict(self, candidate_data: UpdateCaseCandidateSchema):
        # 更新前のデータを取得
        candidate = await CaseCandidate.get_or_none(id=candidate_data.id)
        if not candidate:
            return None
            
        old_data = await candidate.to_dict()
        
        # 更新実行
        candidate = await self.update_candidate(candidate_data)
        if candidate:
            candidate_dict = await candidate.to_dict()
            candidate_dict["candidate_name"] = candidate.candidate_name
            candidate_dict["candidate_type"] = candidate.candidate_type
            
            # 候補者更新履歴を記録
            try:
                user_id, user_name = self._get_current_user_info()
                if user_id and user_id > 0:
                    from app.controllers.case import case_history_controller
                    update_dict = clean_dict(candidate_data.model_dump(exclude_unset=True))
                    
                    # 候補者更新履歴を作成
                    await case_history_controller.create_history_from_changes(
                        case_id=candidate.case_id,
                        old_data=old_data,
                        new_data=update_dict,
                        changed_by=user_id,
                        changed_by_name=user_name,
                        comment=f"候補者「{candidate.candidate_name}」({candidate.candidate_type})を更新"
                    )
                    
                    # ステータス変更の場合は特別な履歴も作成
                    if 'status' in update_dict and update_dict['status'] != old_data.get('status'):
                        await case_history_controller.create_simple_history(
                            case_id=candidate.case_id,
                            change_type=ChangeType.CANDIDATE_UPDATE,
                            changed_by=user_id,
                            changed_by_name=user_name,
                            comment=f"候補者「{candidate.candidate_name}」のステータスを「{old_data.get('status')}」から「{update_dict['status']}」に変更",
                            change_details={
                                "candidate_name": candidate.candidate_name,
                                "old_status": old_data.get('status'),
                                "new_status": update_dict['status']
                            }
                        )
            except Exception as e:
                # 履歴記録のエラーは本処理に影響させない
                print(f"Failed to create candidate update history: {e}")
            
            return candidate_dict
        return None

    async def delete_candidate(self, candidate_id: int):
        candidate = await CaseCandidate.get_or_none(id=candidate_id)
        if candidate:
            candidate_data = await candidate.to_dict()
            candidate_data["candidate_name"] = candidate.candidate_name
            candidate_data["candidate_type"] = candidate.candidate_type
            
            async with in_transaction():
                # 候補者削除履歴を記録
                try:
                    user_id, user_name = self._get_current_user_info()
                    if user_id and user_id > 0:
                        from app.controllers.case import case_history_controller
                        await case_history_controller.create_simple_history(
                            case_id=candidate.case_id,
                            change_type=ChangeType.CANDIDATE_REMOVE,
                            changed_by=user_id,
                            changed_by_name=user_name,
                            comment=f"候補者「{candidate.candidate_name}」({candidate.candidate_type})を削除",
                            change_details={"deleted_candidate_data": candidate_data}
                        )
                except Exception as e:
                    # 履歴記録のエラーは本処理に影響させない
                    print(f"Failed to create candidate delete history: {e}")
                
                await candidate.delete()
        return candidate


class CaseHistoryController:
    """案件変更履歴コントローラー"""
    
    def __init__(self):
        pass
    
    async def create_history(self, history_data: CreateCaseHistorySchema) -> CaseHistory:
        """変更履歴を作成"""
        async with in_transaction():
            data_dict = clean_dict(history_data.model_dump(exclude_unset=True))
            history = await CaseHistory.create(**data_dict)
            return history
    
    async def create_history_from_changes(
        self, 
        case_id: int,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        changed_by: int,
        changed_by_name: str = None,
        comment: str = None,
        ip_address: str = None
    ) -> List[CaseHistory]:
        """変更内容から履歴を自動作成"""
        histories = []
        
        async with in_transaction():
            for field, new_value in new_data.items():
                if field in old_data:
                    old_value = old_data[field]
                    if old_value != new_value:
                        history = await CaseHistory.create(
                            case_id=case_id,
                            change_type=ChangeType.UPDATE,
                            changed_by=changed_by,
                            changed_by_name=changed_by_name,
                            field_name=field,
                            old_value=str(old_value) if old_value is not None else None,
                            new_value=str(new_value) if new_value is not None else None,
                            comment=comment,
                            ip_address=ip_address
                        )
                        histories.append(history)
        
        return histories
    
    async def create_simple_history(
        self,
        case_id: int,
        change_type: ChangeType,
        changed_by: int,
        changed_by_name: str = None,
        comment: str = None,
        change_details: Dict[str, Any] = None,
        ip_address: str = None
    ) -> CaseHistory:
        """シンプルな履歴を作成"""
        async with in_transaction():
            history = await CaseHistory.create(
                case_id=case_id,
                change_type=change_type,
                changed_by=changed_by,
                changed_by_name=changed_by_name,
                change_details=change_details,
                comment=comment,
                ip_address=ip_address
            )
            return history
    
    async def get_case_history_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search_params: CaseHistorySearchSchema = None
    ) -> Dict[str, Any]:
        """案件変更履歴一覧取得"""
        
        query = Q()
        
        if search_params:
            if search_params.case_id:
                query &= Q(case_id=search_params.case_id)
            if search_params.change_type:
                query &= Q(change_type=search_params.change_type)
            if search_params.changed_by:
                query &= Q(changed_by=search_params.changed_by)
            if search_params.field_name:
                query &= Q(field_name__icontains=search_params.field_name)
            if search_params.start_date:
                query &= Q(created_at__gte=search_params.start_date)
            if search_params.end_date:
                query &= Q(created_at__lte=search_params.end_date)
        
        # 総数取得
        total = await CaseHistory.filter(query).count()
        
        # データ取得
        histories = await CaseHistory.filter(query).select_related(
            'case'
        ).order_by('-created_at').limit(page_size).offset((page - 1) * page_size).all()
        
        # 変換
        items = []
        for history in histories:
            history_dict = await history.to_dict()
            if history.case:
                history_dict['case'] = {
                    'id': history.case.id,
                    'title': history.case.title,
                    'status': history.case.status
                }
            items.append(history_dict)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def get_history_by_id(self, history_id: int) -> Optional[Dict[str, Any]]:
        """変更履歴詳細取得"""
        history = await CaseHistory.get_or_none(id=history_id).select_related('case')
        if not history:
            return None
        
        history_dict = await history.to_dict()
        if history.case:
            history_dict['case'] = await history.case.to_dict()
        
        return history_dict
    
    async def get_history_by_case(self, case_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """特定案件の変更履歴取得"""
        search_params = CaseHistorySearchSchema(case_id=case_id)
        return await self.get_case_history_list(page=page, page_size=page_size, search_params=search_params)
    
    async def get_history_stats(self, search_params: CaseHistorySearchSchema = None) -> Dict[str, Any]:
        """変更履歴統計取得"""
        query = Q()
        
        if search_params:
            if search_params.case_id:
                query &= Q(case_id=search_params.case_id)
            if search_params.change_type:
                query &= Q(change_type=search_params.change_type)
            if search_params.changed_by:
                query &= Q(changed_by=search_params.changed_by)
            if search_params.start_date:
                query &= Q(created_at__gte=search_params.start_date)
            if search_params.end_date:
                query &= Q(created_at__lte=search_params.end_date)
        
        # 基本統計
        all_histories = await CaseHistory.filter(query).all()
        total_changes = len(all_histories)
        
        # 変更タイプ別集計
        change_type_counts = {}
        case_change_counts = {}
        user_change_counts = {}
        
        for history in all_histories:
            # 変更タイプ別
            change_type = history.change_type.value
            change_type_counts[change_type] = change_type_counts.get(change_type, 0) + 1
            
            # 案件別
            case_id = history.case_id
            case_change_counts[case_id] = case_change_counts.get(case_id, 0) + 1
            
            # ユーザー別
            user_id = history.changed_by
            user_change_counts[user_id] = user_change_counts.get(user_id, 0) + 1
        
        # Top 10案件（変更回数順）
        most_changed_cases = []
        for case_id, count in sorted(case_change_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            case = await Case.get_or_none(id=case_id)
            if case:
                most_changed_cases.append({
                    "case_id": case_id,
                    "case_title": case.title,
                    "change_count": count
                })
        
        # Top 10ユーザー（変更回数順）
        most_active_users = []
        for user_id, count in sorted(user_change_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            most_active_users.append({
                "user_id": user_id,
                "change_count": count
            })
        
        # 最近の変更履歴（最新10件）
        recent_changes = []
        recent_histories = await CaseHistory.filter(query).select_related('case').order_by('-created_at').limit(10).all()
        for history in recent_histories:
            history_dict = await history.to_dict()
            if history.case:
                history_dict['case_title'] = history.case.title
            recent_changes.append(history_dict)
        
        # 期間設定
        period = "全期間"
        if search_params and search_params.start_date and search_params.end_date:
            period = f"{search_params.start_date} - {search_params.end_date}"
        elif search_params and search_params.start_date:
            period = f"{search_params.start_date} 以降"
        elif search_params and search_params.end_date:
            period = f"{search_params.end_date} 以前"
        
        return {
            "total_changes": total_changes,
            "change_type_counts": change_type_counts,
            "most_changed_cases": most_changed_cases,
            "most_active_users": most_active_users,
            "recent_changes": recent_changes,
            "period": period
        }
    
    async def delete_history(self, history_id: int) -> bool:
        """変更履歴削除"""
        history = await CaseHistory.get_or_none(id=history_id)
        if not history:
            return False
        
        async with in_transaction():
            await history.delete()
        
        return True


case_controller = CaseController()
case_candidate_controller = CaseCandidateController()
case_history_controller = CaseHistoryController()
