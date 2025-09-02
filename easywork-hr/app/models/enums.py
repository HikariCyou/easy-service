from enum import Enum, StrEnum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class EmployeeType(StrEnum):
    # 正社員
    FULL_TIME = "正社員"
    # 契約社員
    CONTRACT = "契約社員"
    # 派遣社員
    TEMPORARY = "派遣社員"
    # 役員
    EXECUTIVE = "役員"
    # アルバイト　パート
    PART_TIME = "アルバイト・パート"
    # 業務委託
    OUTSOURCED = "業務委託"
    # その他
    OTHER = "その他"

class SalaryPaymentType(StrEnum):
    # 月給制
    MONTHLY = "月給制"
    # 時給制
    HOURLY = "時給制"
    # 日給制
    DAILY = "日給制"
    # 年俸制
    ANNUAL = "年俸制"
    # 歩合制
    COMMISSION = "歩合制"
    # その他
    OTHER = "その他"

class HeadOfHouseholdRelationship(StrEnum):
    # 世帯主
    HEAD = "本人"
    # 配偶者
    SPOUSE = "配偶者"
    # 子供
    CHILD = "子供"
    # 親
    PARENT = "親"
    # 兄弟姉妹
    SIBLING = "兄弟姉妹"
    # その他
    OTHER = "その他"

# 在留資格の種類
class ResidenceStatus(StrEnum):
    # 永住者
    PERMANENT_RESIDENT = "永住者"
    # 特別永住者
    SPECIAL_PERMANENT_RESIDENT = "特別永住者"
    # 定住者
    LONG_TERM_RESIDENT = "定住者"
    # 技術・人文知識・国際業務
    ENGINEERING_HUMANITIES_INTERNATIONAL = "技術・人文知識・国際業務"
    # 経営・管理
    BUSINESS_MANAGER = "経営・管理"
    # 介護
    NURSING_CARE = "介護"
    # 留学
    STUDENT = "留学"
    # 家族滞在
    FAMILY_STAY = "家族滞在"
    # その他
    OTHER = "その他"

class DocumentType(StrEnum):
    # 身分証明書
    IDENTITY_PROOF = "身分証明書"
    # 住民票
    RESIDENT_RECORD = "住民票の写し"
    # 健康保険証
    HEALTH_INSURANCE_CARD = "健康保険証"
    # 雇用契約書
    EMPLOYMENT_CONTRACT = "雇用契約書"
    # 給与明細
    PAYSLIP = "給与明細"
    # マイナンバーのコピー
    MY_NUMBER_COPY = "マイナンバー"
    # LICENSE
    LICENSE = "資格証明書"
    # PASSPORT
    PASSPORT = "パスポート"
    # 口座情報
    BANK_ACCOUNT = "口座情報"
    # 在留カード
    RESIDENCE_CARD = "在留カード"
    # 雇用保険
    EMPLOYMENT_INSURANCE = "雇用保険被保険者証"
    # その他
    OTHER = "その他"


# === SES統合用追加Enum ===

class PersonType(StrEnum):
    BP_EMPLOYEE = "bp_employee"  # BP社員
    FREELANCER = "freelancer"  # フリーランス
    EMPLOYEE = "employee"  # 自社社員
    @classmethod
    def get_label(cls, value: str) -> str:
        return _PERSON_TYPE_LABELS.get(value, value)

_PERSON_TYPE_LABELS = {
    PersonType.BP_EMPLOYEE: "BP社員",
    PersonType.FREELANCER: "個人事業主",
    PersonType.EMPLOYEE: "自社社員",
}


class MarriageStatus(StrEnum):
    SINGLE = "独身"  # 結婚していない
    MARRIED = "既婚"  # 結婚している
    DIVORCED = "離婚"  # 結婚を解消している
    WIDOWED = "死別"  # 死別
    OTHER = "その他"  # その他


class JapaneseLevel(StrEnum):
    NATIVE = "native"  # ネイティブ
    N1 = "N1"  # JLPT N1
    N2 = "N2"  # JLPT N2
    N3 = "N3"  # JLPT N3
    N4 = "N4"  # JLPT N4
    N5 = "N5"  # JLPT N5
    BEGINNER = "Beginner"  # 初級


class EmploymentStatus(StrEnum):
    AVAILABLE = "稼働可能"  # 稼働可能
    WORKING = "稼働中"  # 稼働中
    VACATION = "休暇中"  # 休暇中
    UNAVAILABLE = "稼働不可"  # 稼働不可
    RETIRED = "退職"  # 退職


class DecimalProcessingType(StrEnum):
    ROUND = "四捨五入"  # 四捨五入
    FLOOR = "切り捨て"  # 切り捨て
    CEIL = "切り上げ"  # 切り上げ

