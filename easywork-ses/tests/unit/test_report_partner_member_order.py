import os

import pytest
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.settings import settings


def test_report_partner_member_order():
    template_dir = os.path.join(settings.BASE_DIR, "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("partner_member_order.html")

    html = template.render(
        order_number="ODR24080006",
        order_date="2024-07-31",
        recipient_company="株式会社創益",
        issuer_company="株式会社TOB",
        issuer_address_line1="東京都千代田区神田神保町3-2-28",
        issuer_address_line2="ACN神保町ビル9階",
        issuer_tel="03-4500-9760",
        issuer_fax="",
        creator="張 智南",
        work_name="みずほ情報系の開発",
        work_period="2024年8月1日〜2024年8月31日",
        responsibility_ko="王 団傑",
        contact_ko="王 団傑",
        responsibility_ot="黎 穎",
        contact_ot="",
        work_responsible="田 彦宇",
        base_fee="340,000",
        shortage_fee="2,125",
        excess_fee="1,700",
        standard_time="160.0h〜200.0h/月",
        work_place="弊社指定場所",
        deliverable="月別作業報告書",
        payment_terms="作業報告書査収による毎月末締め、翌々月末に現金振込\n① 時間単位30分。\n② 休憩時間は顧客就業時間に準ずる。\n③ 請求は株式会社TOBからメール配信の『御請求書』に押印、郵送する。\n④ 延長/中止の場合には、両者協議の上、継続検討を行う。\n⑤ 著しく勤怠不良の場合は、協議の上で減額する。\n⑥ 振込手数料は受託者負担。\n⑦ 注文請書は毎月15日までに必着。",
        contract_terms="1. 本作業に関わる著作権は、甲に一切帰属する。\n2. 乙は、本作業にて知り得た知識・企業秘密・ノウハウその他の情報を外部に漏洩しない。\n3. 顧客の都合により本注文書の業務が中断または終了した場合、その時点で注文は解除され効力を失う。",
        company_seal_url="inkan.png",
    )

    HTML(string=html).write_pdf("注文書.pdf")

    assert True
