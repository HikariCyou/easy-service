from enum import Enum, IntEnum, StrEnum


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


class BPCompanyStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLIST = "blacklist"


class PaymentSite(StrEnum):
    EMPTY = "未設定"  # 未設定
    THIS_MONTH = "今月"  # 今月
    NEXT_MONTH = "翌月"  # 次月
    TWO_MONTHS_LATER = "翌々月"  # 次次月
    THREE_MONTHS = "3月"  # 3月
    FOUR_MONTHS = "4月"  # 4月
    FIVE_MONTHS = "5月"  # 5月
    SIX_MONTHS = "6月"  # 6月


class PaymentDay(StrEnum):
    EMPTY = "未設定"  # 未設定
    DAY_1 = "1"
    DAY_2 = "2"
    DAY_3 = "3"
    DAY_4 = "4"
    DAY_5 = "5"
    DAY_6 = "6"
    DAY_7 = "7"
    DAY_8 = "8"
    DAY_9 = "9"
    DAY_10 = "10"
    DAY_11 = "11"
    DAY_12 = "12"
    DAY_13 = "13"
    DAY_14 = "14"
    DAY_15 = "15"
    DAY_16 = "16"
    DAY_17 = "17"
    DAY_18 = "18"
    DAY_19 = "19"
    DAY_20 = "20"
    DAY_21 = "21"
    DAY_22 = "22"
    DAY_23 = "23"
    DAY_24 = "24"
    DAY_25 = "25"
    DAY_26 = "26"
    DAY_27 = "27"
    DAY_28 = "28"
    DAY_29 = "29"
    DAY_30 = "30"
    END_OF_MONTH = "月末"  # 月末


class AttendanceCalcType(IntEnum):
    EMPTY = 0  # 未設定
    FIFTEEN_MINUTES = 15  # 15分ごと
    THIRTY_MINUTES = 30  # 30分ごと
    ONE_HOUR = 60  # 1時間ごと
    SIX_MINUTES = 6  # 6分ごと


class DecimalProcessingType(StrEnum):
    EMPTY = ""  # 未設定
    ROUND = "四捨五入"  # 四捨五入
    FLOOR = "切り捨て"  # 切り捨て
    CEIL = "切り上げ"  # 切り上げ


class DecimalProcessingPosition(StrEnum):
    EMPTY = ""  # 未設定
    ALL_DECIMAL = "小数全て"  # 小数全て
    ONE_DIGIT = "1桁まで"  # 1桁まで
    TWO_DIGITS = "2桁まで"  # 2桁まで
    THREE_DIGITS = "3桁まで"  # 3桁まで


# 必要なenumの定義例
class CaseStatus(StrEnum):
    OPEN = "open"  # 募集中
    IN_PROGRESS = "in_progress"  # 選考中
    FILLED = "filled"  # 決定済み
    CLOSED = "closed"  # 終了
    CANCELLED = "cancelled"  # キャンセル


class CandidateStatus(StrEnum):
    PENDING = "pending"  # 推薦中
    INTERVIEW_SCHEDULED = "interview_scheduled"  # 面談予定
    INTERVIEWED = "interviewed"  # 面談済み
    OFFER = "offer"  # 内定
    ACCEPTED = "accepted"  # 承諾
    REJECTED = "rejected"  # 不採用
    WITHDRAWN = "withdrawn"  # 辞退


class MarriageStatus(StrEnum):
    SINGLE = "独身"  # 結婚していない
    MARRIED = "既婚"  # 結婚している
    DIVORCED = "離婚"  # 結婚を解消している
    WIDOWED = "死別"  # 死別
    OTHER = "その他"  # その他


# Enum定義
class ContractStatus(StrEnum):
    ACTIVE = "有効"  # 有効
    SUSPENDED = "一時中断"  # 一時中断
    TERMINATED = "終了"  # 終了
    CANCELLED = "キャンセル"  # キャンセル


class ContractType(StrEnum):
    BP_EMPLOYEE = "BP社員"  # BP社員
    EMPLOYEE = "自社社員"  # 自社社員
    FREELANCER = "フリーランス"  # フリーランス


class ContractChangeType(StrEnum):
    """契約変更種別"""

    CONTRACT_RENEWAL = "契約更新"  # 契約更新
    EARLY_TERMINATION = "早期解約"  # 早期解約
    CONDITION_CHANGE = "条件変更"  # 条件変更（単価、時間等）
    PERIOD_EXTENSION = "期間延長"  # 期間延長
    PERIOD_SHORTENING = "期間短縮"  # 期間短縮
    STATUS_CHANGE = "ステータス変更"  # ステータス変更
    AMENDMENT = "契約修正"  # 契約修正
    SUSPENSION = "一時停止"  # 一時停止
    RESUMPTION = "再開"  # 再開


class ContractChangeReason(StrEnum):
    """契約変更理由"""

    CLIENT_REQUEST = "クライアント要望"  # クライアント要望
    PERSONNEL_REQUEST = "人材要望"  # 人材要望
    PROJECT_CHANGE = "プロジェクト変更"  # プロジェクト変更
    PERFORMANCE_ISSUE = "パフォーマンス問題"  # パフォーマンス問題
    BUDGET_CHANGE = "予算変更"  # 予算変更
    SCHEDULE_CHANGE = "スケジュール変更"  # スケジュール変更
    MARKET_CONDITION = "市場状況"  # 市場状況
    COMPANY_POLICY = "会社方針"  # 会社方針
    LEGAL_REQUIREMENT = "法的要件"  # 法的要件
    OTHER = "その他"  # その他


class ContractItemType(StrEnum):
    """契約項目種別"""

    BASIC_SALARY = "基本給"  # 基本給
    OVERTIME_FEE = "残業代"  # 残業代
    ABSENCE_DEDUCTION = "欠勤控除"  # 欠勤控除
    ALLOWANCE = "手当"  # 手当
    OTHER_FEE = "その他費用"  # その他費用
    BONUS = "賞与"  # 賞与
    TRANSPORTATION = "交通費"  # 交通費
    WELFARE = "福利厚生費"  # 福利厚生費
    OTHER_DEDUCTION = "その他控除"  # その他控除


class PaymentUnit(StrEnum):
    """支払い単位"""

    YEN_PER_MONTH = "円/月"  # 円/月
    YEN_PER_HOUR = "円/時間"  # 円/時間
    YEN_PER_DAY = "円/日"  # 円/日
    YEN_PER_MINUTE = "円/分"  # 円/分
    TEN_THOUSAND_YEN_PER_MONTH = "万円/月"  # 万円/月
    PERCENTAGE = "％"  # パーセンテージ
    FIXED_AMOUNT = "固定額"  # 固定額


class AttendanceType(StrEnum):
    NORMAL = "通常出勤"  # 通常出勤
    PAID_LEAVE = "有給休暇"  # 有給休暇
    PAID_LEAVE_HALF = "有給休暇（半休）"  # 有給休暇（半休）
    SICK_LEAVE = "病気休暇"  # 病気休暇
    ABSENCE = "欠勤"  # 欠勤
    HOLIDAY_WORK = "休日出勤"  # 休日出勤
    COMPENSATORY_LEAVE = "振休"  # 振休


# 追加のEnum定義
class VisaStatus(StrEnum):
    CITIZEN = "日本国籍"  # 日本国籍
    PERMANENT_RESIDENT = "永住者"  # 永住者
    ENGINEER = "技術・人文知識・国際業務"  # 技術・人文知識・国際業務
    SKILLED_WORKER = "技能実習"  # 技能実習
    STUDENT = "留学"  # 留学
    WORKING_HOLIDAY = "ワーキングホリデー"  # ワーキングホリデー
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


class ChangeType(StrEnum):
    CREATE = "create"  # 作成
    UPDATE = "update"  # 更新
    DELETE = "delete"  # 削除
    STATUS_CHANGE = "status_change"  # ステータス変更
    CANDIDATE_ADD = "candidate_add"  # 候補者追加
    CANDIDATE_REMOVE = "candidate_remove"  # 候補者削除
    CANDIDATE_UPDATE = "candidate_update"  # 候補者更新


class ApproveStatus(StrEnum):
    """审批状态枚举"""

    DRAFT = "draft"  # 草稿状态（未提交）
    PENDING = "pending"  # 等待审批
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    WITHDRAWN = "withdrawn"  # 已撤回


class OrderStatus(StrEnum):
    """注文書状态枚举"""

    DRAFT = "draft"  # 草稿状态
    GENERATED = "generated"  # 已生成注文书
    SENT = "sent"  # 已发送邮件
    COLLECTED = "collected"  # 已回收


class RequestStatus(StrEnum):
    """請求書状态枚举"""

    DRAFT = "draft"  # 草稿状态
    GENERATED = "generated"  # 已生成请求书
    SENT = "sent"  # 已发送
    PAID = "paid"  # 已支付


class WeeklyMoodStatus(StrEnum):
    """週間心情状态枚举"""

    EXCELLENT = "excellent"  # 😄 优秀/非常好
    GOOD = "good"  # 😊 良好
    NORMAL = "normal"  # 😐 一般
    STRESSED = "stressed"  # 😰 有压力
    TIRED = "tired"  # 😴 疲劳
    DIFFICULT = "difficult"  # 😞 困难/不好


# MonthlySubmissionStatus 已合并到 ApproveStatus，不再单独定义


class BPContractStatus(StrEnum):
    """BP会社契約ステータス"""

    DRAFT = "草案"  # 草案
    ACTIVE = "有効"  # 有効
    SUSPENDED = "一時停止"  # 一時停止
    TERMINATED = "終了"  # 終了
    EXPIRED = "期限切れ"  # 期限切れ


class SESContractForm(StrEnum):
    """SES契約形態"""

    GYOMU_ITAKU = "業務委託"  # 業務委託
    HAN_ITAKU = "半委託"  # 半委託
    HAKEN = "派遣"  # 派遣
    IKKATSU = "一括"  # 一括
    OTHER = "その他"  # その他


class ContractCompanyType(StrEnum):
    """契約会社種別"""

    CLIENT_COMPANY = "取引会社"  # 取引会社
    COMPANY_INFO = "会社情報"  # 会社情報


class BusinessClassification(StrEnum):
    """事業分類"""

    FINANCE_BANK = "金融（銀行）"  # 金融（銀行）
    FINANCE_INSURANCE = "金融（保険）"  # 金融（保険）
    FINANCE_SECURITIES = "金融（証券）"  # 金融（証券）
    MANUFACTURING = "制造"  # 制造
    SERVICE = "サービス"  # サービス
    OTHER = "その他"  # その他


class WorkRoleClassification(StrEnum):
    """作業区分（職責）"""

    OP = "オペレーター"  # オペレーター
    PG = "プログラマー"  # プログラマー
    SP = "システムプログラマー"  # システムプログラマー
    SE = "システムエンジニア"  # システムエンジニア
    SL = "サブリーダー"  # サブリーダー
    L = "リーダー"  # リーダー
    PM = "マネージャー"  # マネージャー


class TimeCalculationType(StrEnum):
    """時間計算種類"""

    FIXED_160 = "固定160時間"  # 毎月固定160時間で計算（実働時間に関係なく固定）
    BUSINESS_DAYS_8 = "営業日数×8"  # 営業日数×8時間で月間工時計算
    BUSINESS_DAYS_7_9 = "営業日数×7.9"  # 営業日数×7.9時間で月間工時計算（休憩時間調整）
    BUSINESS_DAYS_7_75 = "営業日数×7.75"  # 営業日数×7.75時間で月間工時計算（標準休憩時間除く）
    FIXED_AMOUNT = "固定金額"  # 工時に関係なく完全固定金額
    HOURLY_RATE = "時給"  # 実働時間×時給での純粋時給制
    CUSTOM_CALCULATION = "自定義計算"  # プロジェクト固有の計算方式
    OTHER = "その他"  # 上記以外の特殊な計算方式
