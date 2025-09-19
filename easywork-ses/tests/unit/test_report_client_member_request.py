import os

import pytest
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.settings import settings


def test_report_client_member_request():
    """請求書PDFテンプレートのテスト"""
    template_dir = os.path.join(settings.BASE_DIR, "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("client_member_request.html")

    html = template.render(
        # ヘッダー情報
        company_postal_code="101-0051",
        company_address_line1="東京都千代田区神田神保町3-2-28",
        company_address_line2="ACN神保町ビル9階",
        registration_number="T1010001234567",
        company_tel="03-4500-9760",

        # 請求書基本情報
        invoice_number="REQ24080006",
        issue_date="2024年8月31日",

        # クライアント会社情報
        client_company="株式会社ABC商事",

        # 金額情報
        total_amount="715,000",
        subtotal_amount="650,000",
        tax_amount="65,000",
        tax_rate="10",
        final_total_amount="715,000",

        # 作業期間
        work_start_date="2024年8月1日",
        work_end_date="2024年8月31日",

        # 支払期限
        payment_due_date="2024年9月30日",

        # 請求会社情報
        billing_postal_code="101-0051",
        billing_address="東京都千代田区神田神保町3-2-28 ACN神保町ビル9階",
        billing_company="株式会社TOB",
        billing_tel="03-4500-9760",
        president_title="代表取締役",
        president_name="田中太郎",

        # 明細項目
        detail_items=[
            {
                "number": "1",
                "name": "ECサイト開発プロジェクト",
                "unit_price": "650,000",
                "work_hours": "160",
                "rate": "100%",
                "min_max_hours": "140/180",
                "shortage_rate": "0.6",
                "excess_rate": "1.25",
                "other": "",
                "amount": "650,000",
                "remarks": ""
            }
        ],

        # 調整項目
        deduction_amount="",
        addition_amount="",

        # 銀行情報
        bank_name="三菱UFJ銀行",
        branch_name="神保町支店",
        branch_code="001",
        account_type="普通",
        account_number="1234567",
        account_holder="カ）ティーオービー",
        account_holder_address="東京都千代田区神田神保町3-2-28",
        account_holder_tel="03-4500-9760",

        # その他
        company_seal_url="inkan.png",
        title="御請求書",
    )

    # PDFファイル生成（テスト用）
    HTML(string=html).write_pdf("請求書.pdf")

    assert True


def test_report_client_member_request_minimal():
    """請求書PDFテンプレートの最小テスト（必須項目のみ）"""
    template_dir = os.path.join(settings.BASE_DIR, "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("client_member_request.html")

    html = template.render(
        # ヘッダー情報
        company_postal_code="101-0051",
        company_address_line1="東京都千代田区神田神保町3-2-28",
        company_address_line2="ACN神保町ビル9階",
        registration_number="T1010001234567",
        company_tel="03-4500-9760",

        # 請求書基本情報
        invoice_number="REQ24080007",
        issue_date="2024年8月31日",

        # クライアント会社情報
        client_company="テスト会社",

        # 金額情報
        total_amount="550,000",
        subtotal_amount="500,000",
        tax_amount="50,000",
        tax_rate="10",
        final_total_amount="550,000",

        # 作業期間
        work_start_date="2024年8月1日",
        work_end_date="2024年8月31日",

        # 支払期限
        payment_due_date="2024年9月30日",

        # 請求会社情報
        billing_postal_code="101-0051",
        billing_address="東京都千代田区神田神保町3-2-28 ACN神保町ビル9階",
        billing_company="株式会社TOB",
        billing_tel="03-4500-9760",
        president_title="代表取締役",
        president_name="田中太郎",

        # 明細項目（最小限）
        detail_items=[],

        # 調整項目
        deduction_amount="",
        addition_amount="",

        # 銀行情報
        bank_name="三菱UFJ銀行",
        branch_name="神保町支店",
        branch_code="001",
        account_type="普通",
        account_number="1234567",
        account_holder="カ）ティーオービー",
        account_holder_address="東京都千代田区神田神保町3-2-28",
        account_holder_tel="03-4500-9760",

        # その他
        company_seal_url="inkan.png",
        title="御請求書",
    )

    # HTMLが正常に生成されることを確認
    assert "REQ24080007" in html
    assert "テスト会社" in html
    assert "550,000" in html

    assert True


def test_report_client_member_request_with_long_text():
    """請求書PDFテンプレートの長文テスト"""
    template_dir = os.path.join(settings.BASE_DIR, "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("client_member_request.html")


    html = template.render(
        # ヘッダー情報
        company_postal_code="101-0051",
        company_address_line1="東京都千代田区神田神保町3-2-28",
        company_address_line2="ACN神保町ビル9階",
        registration_number="T1010001234567",
        company_tel="03-4500-9760",

        # 請求書基本情報
        invoice_number="REQ24080008",
        issue_date="2024年8月31日",

        # クライアント会社情報
        client_company="株式会社長い名前のテスト会社サンプル",

        # 金額情報
        total_amount="1,099,999",
        subtotal_amount="999,999",
        tax_amount="100,000",
        tax_rate="10",
        final_total_amount="1,099,999",

        # 作業期間
        work_start_date="2024年8月1日",
        work_end_date="2024年8月31日",

        # 支払期限
        payment_due_date="2024年10月31日",

        # 請求会社情報
        billing_postal_code="101-0051",
        billing_address="東京都千代田区神田神保町3-2-28 ACN神保町ビル9階",
        billing_company="株式会社TOB",
        billing_tel="03-4500-9760",
        president_title="代表取締役",
        president_name="田中太郎",

        # 明細項目
        detail_items=[
            {
                "number": "1",
                "name": "非常に長いプロジェクト名のテストケースシステム開発案件",
                "unit_price": "999,999",
                "work_hours": "200",
                "rate": "100%",
                "min_max_hours": "140/250",
                "shortage_rate": "0.6",
                "excess_rate": "1.25",
                "other": "",
                "amount": "999,999",
                "remarks": "長文テスト"
            }
        ],

        # 調整項目
        deduction_amount="",
        addition_amount="",

        # 銀行情報
        bank_name="三菱UFJ銀行",
        branch_name="神保町支店",
        branch_code="001",
        account_type="普通",
        account_number="1234567",
        account_holder="カ）ティーオービー",
        account_holder_address="東京都千代田区神田神保町3-2-28",
        account_holder_tel="03-4500-9760",

        # その他
        company_seal_url="inkan.png",
        title="御請求書",
    )

    # 長文でもHTMLが正常に生成されることを確認
    assert "REQ24080008" in html
    assert "データベース設計" in html
    assert "1,099,999" in html

    assert True