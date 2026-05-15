############################################################
# TP OPTIX — FINAL STABLE VERSION
# STEP 1 -> PYTHON EXTRACTION
# STEP 2 -> CHATPDF FINANCIAL JSON
# STEP 3 -> CHATPDF TP ANALYSIS JSON
# STEP 4 -> DISPLAY ONLY
############################################################

import streamlit as st
import os
import json
import re
import requests
import pdfplumber

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

st.title("TP OPTIX")

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)

balanceSheetPages = st.text_input(
    "Balance Sheet Pages"
)

plStatementPages = st.text_input(
    "P&L Pages"
)

otherIncomePages = st.text_input(
    "Other Income Pages"
)

otherExpensePages = st.text_input(
    "Other Expense Pages"
)

rptPages = st.text_input(
    "RPT Pages"
)

run_button = st.button(
    "RUN TP OPTIX"
)
############################################################
# FLASK
############################################################


UPLOAD_FOLDER = "uploads"
GENERATED_FOLDER = "generated"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

############################################################
# CHATPDF API
############################################################

CHATPDF_API_KEY = st.secrets["CHATPDF_API_KEY"]

############################################################
# PAGE PARSER
############################################################

def parse_pages(page_string):

    pages = []

    if not page_string:
        return pages

    parts = str(page_string).split(",")

    for part in parts:

        part = part.strip()

        if "-" in part:

            start, end = part.split("-")

            pages.extend(
                list(
                    range(
                        int(start),
                        int(end) + 1
                    )
                )
            )

        else:

            try:
                pages.append(int(part))
            except:
                pass

    return pages

############################################################
# CLEAN CELL
############################################################

def clean_cell(text):

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\n", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()

############################################################
# RAW PAGE EXTRACTION
############################################################

def extract_full_page_content(pdf_path, page_numbers):

    extracted_text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for p in page_numbers:

            try:

                page = pdf.pages[p - 1]

                extracted_text += "\n\n"
                extracted_text += "=" * 80
                extracted_text += f"\nPAGE {p}\n"
                extracted_text += "=" * 80
                extracted_text += "\n\n"

                ####################################################
                # FULL RAW TEXT
                ####################################################

                raw_text = page.extract_text()

                if raw_text:

                    extracted_text += "FULL PAGE TEXT\n\n"
                    extracted_text += raw_text
                    extracted_text += "\n\n"

                ####################################################
                # TABLES
                ####################################################

                tables = page.extract_tables()

                if tables:

                    extracted_text += "TABLE DATA\n\n"

                    table_counter = 1

                    for table in tables:

                        extracted_text += f"TABLE {table_counter}\n\n"

                        for row in table:

                            if row:

                                cleaned = [

                                    clean_cell(x)

                                    for x in row

                                ]

                                extracted_text += " | ".join(cleaned)
                                extracted_text += "\n"

                        extracted_text += "\n\n"

                        table_counter += 1

            except Exception as e:

                extracted_text += f"\nERROR ON PAGE {p}: {str(e)}\n"

    return extracted_text

############################################################
# BUILD STEP1 TEXT
############################################################

def build_step1_text(

    bs_text,
    pl_text,
    oi_text,
    oe_text,
    rpt_text

):

    final_text = ""

    final_text += "\n\n"
    final_text += "#" * 100
    final_text += "\nBALANCE SHEET EXTRACTION\n"
    final_text += "#" * 100
    final_text += "\n\n"

    final_text += bs_text

    final_text += "\n\n"
    final_text += "#" * 100
    final_text += "\nPROFIT AND LOSS EXTRACTION\n"
    final_text += "#" * 100
    final_text += "\n\n"

    final_text += pl_text

    final_text += "\n\n"
    final_text += "#" * 100
    final_text += "\nOTHER INCOME EXTRACTION\n"
    final_text += "#" * 100
    final_text += "\n\n"

    final_text += oi_text

    final_text += "\n\n"
    final_text += "#" * 100
    final_text += "\nOTHER EXPENSE EXTRACTION\n"
    final_text += "#" * 100
    final_text += "\n\n"

    final_text += oe_text

    final_text += "\n\n"
    final_text += "#" * 100
    final_text += "\nRELATED PARTY DISCLOSURE EXTRACTION\n"
    final_text += "#" * 100
    final_text += "\n\n"

    final_text += rpt_text

    return final_text

############################################################
# CREATE STEP1 PDF
############################################################

def create_step1_pdf(text, output_path):

    doc = SimpleDocTemplate(output_path)

    styles = getSampleStyleSheet()

    story = []

    story.append(

        Paragraph(
            "<b>STEP 1 — FULL FINANCIAL EXTRACTION</b>",
            styles["Heading1"]
        )

    )

    story.append(Spacer(1, 20))

    for line in text.split("\n"):

        line = line.strip()

        if not line:
            continue

        story.append(

            Paragraph(
                line,
                styles["BodyText"]
            )

        )

        story.append(Spacer(1, 5))

    doc.build(story)

############################################################
# CHATPDF UPLOAD
############################################################

def upload_pdf_to_chatpdf(pdf_path):

    url = "https://api.chatpdf.com/v1/sources/add-file"

    headers = {
        "x-api-key": CHATPDF_API_KEY
    }

    with open(pdf_path, "rb") as f:

        files = {

            "file": (
                os.path.basename(pdf_path),
                f,
                "application/pdf"
            )

        }

        response = requests.post(
            url,
            headers=headers,
            files=files,
            timeout=300
        )

    return response.json()

############################################################
# CHATPDF ASK
############################################################

def ask_chatpdf(source_id, prompt):

    url = "https://api.chatpdf.com/v1/chats/message"

    headers = {

        "x-api-key": CHATPDF_API_KEY,
        "Content-Type": "application/json"

    }

    data = {

        "sourceId": source_id,

        "messages": [

            {
                "role": "user",
                "content": prompt
            }

        ]

    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=300
    )

    return response.json()

############################################################
# SAFE JSON
############################################################

def safe_json_load(raw):

    if not raw:
        return {}

    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")

    try:
        return json.loads(raw)
    except:
        return {}

############################################################
# STEP 2 PROMPT
############################################################

############################################################
# STEP 2A — PLI PROMPT
############################################################

def build_prompt_pli():

    return """

You are a Senior Transfer Pricing Consultant and Financial Statement Analyst specializing in:

- Indian Income Tax Act, 1961
- OECD Transfer Pricing Guidelines
- Indian Schedule III Financial Statements
- XBRL Financial Statements
- TP benchmarking
- FAR analysis
- APA
- Safe Harbour Rules

IMPORTANT:

Use ONLY the extracted financial data from uploaded PDF.

Do NOT estimate.
Do NOT infer.
Do NOT create your own values.

====================================================
OBJECTIVE
====================================================

Generate ONLY FINAL PLI JSON.

se ONLY the extracted financial table data shared in the uploaded PDF.

Do NOT estimate.
Do NOT infer missing values.
Do NOT create your own financial figures.

====================================================
OBJECTIVE
====================================================

Prepare the FINAL TRANSFER PRICING PLI.

====================================================
OPERATING VS NON OPERATING RULES
====================================================

Treat the following as NON OPERATING:

- Interest Income
- Dividend Income
- Finance Cost
- Gain/Loss on Investments
- Gain/Loss on Sale of Assets
- Loss on discard of PPE
- Impairment Loss
- Exceptional Items
- Prior Period Items
- Donations
- CSR
- Penalties
- Provisions
- Bad Debts
- Miscellaneous expenditure written off
- Any similar amount

IMPORTANT:

Show ALL such non operating expenses and income items and write whether it was operating or non operating. Also in the result under "Nature as opearting or non opearting" give the nature of the transaction.
Under "final_pli" always give all the Profit and Loss items whatever is available before the Profit Before Tax in the P/L Statement. (e.g - Revenue From Operations to Other Expenses but exclue the Total Income or Total Revenue or Total Expenses or Total Cost type total values just give lineitem wise data)
====================================================
RETURN FORMAT
====================================================

Return ONLY VALID JSON.

{
  "final_pli": [
    {
      "particular": "",
      "amount_current_year": "",
      "amount_previous_year": ""
    }
  ],

  "non_operating_income": [
    {
      "nature_of_income": "",
      "current_year": "",
      "previous_year": "",
      "Nature as opearting or non opearting": "",\
    }
  ],

  "non_operating_expense": [
    {
      "nature_of_expense": "",
      "current_year": "",
      "previous_year": "",
      "Nature as opearting or non opearting": ""
    }
  ]
}

IMPORTANT:
- Preserve ALL rows
- Preserve BOTH years
- Return ONLY JSON

"""
############################################################
# STEP 2B — RPT PROMPT
############################################################

def build_prompt_rpt():

    return """

You are a Senior Transfer Pricing Consultant.

Extract ONLY Related Party Transactions.

STRICTLY extract ONLY from:
RELATED PARTY DISCLOSURE EXTRACTION

DO NOT extract:
- ratios
- KPI
- turnover ratios
- debt equity ratio
- analysis tables

Important - Under "domestic_or_international" field, place the transction as domestic or internation based on this logic as if the Related party is a Indian Company (if mainly have "Limited", "Private Limited", "Pvt Ltd") then tell Domestic other wise International. Only apply on company names, not on indivisuals.
====================================================
RETURN FORMAT
====================================================

Return ONLY VALID JSON.

{
  "rpt_table": [
    {
      "related_party": "",
      "nature_of_transaction": "",
      "current_year": "",
      "previous_year": "",
      "domestic_or_international": ""
    }
  ]
}

IMPORTANT:
- Return ONLY JSON

"""
############################################################
# STEP 3 PROMPT
############################################################

def build_prompt_2():

    return """

You are a Senior Transfer Pricing Consultant and Financial Statement Analyst specializing in:
- Indian Income Tax Act, 1961
- OECD Transfer Pricing Guidelines
- Indian Schedule III Financial Statements
- XBRL Financial Statements
- TP benchmarking
- FAR analysis
- APA
- Safe Harbour Rules
====================================================
VERY IMPORTANT INSTRUCTIONS
====================================================

3. Ignore:
- Chairman report
- ESG section
- CSR report
- Sustainability report
- Director report
- Management discussion
- Consolidated financial statements

4. ONLY use:
- Standalone Balance Sheet
- Standalone Statement of Profit and Loss
- Notes to Accounts
- Related Party disclosures
- Other Income notes
- Other Expense notes
- Segment notes
- Contingent liability notes
- independent Auditors report
- Directors report
Then identify the output of the company’s basic details
Extract:

2. Business overview - (You will get with an language as “engaged in the business” or “incorporated” or something similar paragraphs. So, go through the full Notes to Account and give the 2 to 3 line Business description Max)
4. Registered office – You will get near to the business overview
5. Holding company – see the shareholding structure in the notes to account the recent holding is the holding company
6. Ultimate holding company - see the shareholding structure in the notes to account the recent holding is the holding company whereas the holding company of the holding company is the ultimate holding company
7. Shareholding structure – you will get in the holding company notes to account
8. Main operating segments – You will get in the segment reporting Notes to account or in the business description
9. Main source of revenue – This is the one you will get in the “revenue recognition” note in notes to account
10. Countries involved in international transactions – It is optional, you get then add otherwise remove from output
11. Functional characterization: whether the entity is (Captive Service Provider or Contract  Manufacturer, Licensed Manufacturer, Full Risk Distributor, Limited Risk Distributor, Entrepreneur) etc.
12. Basis of characterization – if you get any clue

Then provide the - TP findings

such as

| Opportunity / Finding | Why Relevant | Risk Level | Suggested Action |

Analyze:

1. APA feasibility
2. Safe Harbour applicability
3. TP policy restructuring
4. Margin optimization
5. Royalty benchmarking
6. AMP exposure
7. Cost allocation redesign
8. Captive characterization review
9. Working capital adjustment opportunity
10. Risk adjustment opportunity
11. Loss-making concerns
12. High RPT dependency
13. Significant related party concentration
14. Abnormal margins
15. Litigation exposure
16. Tax risk areas

IMPORTANT:

Risk Level MUST ONLY be one of the following exact values:

- Low
- Medium
- High

Never generate:
- Low to Medium
- Medium to High
- Moderate
- Critical

Use ONLY:
Low, Medium or High.

SECTION 12 — LITIGATION & CONTINGENT LIABILITY ANALYSIS
====================================================

Generate ONE TABLE with:

| Issue | Amount | Financial Year | Status | TP Relevance | Page No |

Identify:
- TP litigation
- Income tax disputes
- APA references
- DRP references
- MAP references
- Contingent liabilities
- Significant audit qualifications

====================================================
SECTION 13 — WARNINGS & EXTRACTION ISSUES
====================================================

Generate ONE TABLE with:

| Issue | Explanation | Recommended Review |

Identify:
- Missing disclosures
- Ambiguous values
- Inconsistent classifications
- Extraction uncertainty
- Manual review areas

====================================================
RETURN FORMAT
====================================================

Return ONLY VALID JSON.

{
  "basic_information": {
    "business_overview": "",
    "registered_office": "",
    "holding_company": "",
    "ultimate_holding_company": "",
    "shareholding_structure": "",
    "main_operating_segments": "",
    "main_source_of_revenue": "",
    "countries_involved_in_international_transactions": "",
    "functional_characterization": "",
    "basis_of_characterization": ""
  },

  "tp_findings": [
    {
      "opportunity_or_finding": "",
      "why_relevant": "",
      "risk_level": "",
      "suggested_action": ""
    }
  ],

  "litigation_and_contingent_liability_analysis": [
    {
      "issue": "",
      "amount": "",
      "financial_year": "",
      "status": "",
      "tp_relevance": "",
      "page_no": ""
    }
  ],

  "warnings_and_extraction_issues": [
    {
      "issue": "",
      "explanation": "",
      "recommended_review": ""
    }
  ]
}

IMPORTANT:
- Return ONLY JSON
- No markdown
- No explanation
- No tables
- No HTML

"""

############################################################
# STREAMLIT MAIN
############################################################

if run_button:

    try:

        ####################################################
        # PAGE INPUTS
        ####################################################

        bs_pages = parse_pages(balanceSheetPages)

        pl_pages = parse_pages(plStatementPages)

        oi_pages = parse_pages(otherIncomePages)

        oe_pages = parse_pages(otherExpensePages)

        rpt_pages = parse_pages(rptPages)

        ####################################################
        # SAVE PDF
        ####################################################

        if uploaded_file is None:

            st.error("Please upload PDF")

            st.stop()

        pdf_path = os.path.join(
            UPLOAD_FOLDER,
            uploaded_file.name
        )

        with open(pdf_path, "wb") as f:

            f.write(uploaded_file.getbuffer())

        ####################################################
        # STEP 1 EXTRACTION
        ####################################################

        st.info("Running STEP 1 Extraction...")

        bs_text = extract_full_page_content(
            pdf_path,
            bs_pages
        )

        pl_text = extract_full_page_content(
            pdf_path,
            pl_pages
        )

        oi_text = extract_full_page_content(
            pdf_path,
            oi_pages
        )

        oe_text = extract_full_page_content(
            pdf_path,
            oe_pages
        )

        rpt_text = extract_full_page_content(
            pdf_path,
            rpt_pages
        )

        final_step1_text = build_step1_text(

            bs_text,
            pl_text,
            oi_text,
            oe_text,
            rpt_text

        )

        step1 = final_step1_text

        ####################################################
        # DISPLAY STEP 1
        ####################################################

        st.subheader("STEP 1 — EXTRACTION")

        st.text(step1)

        ####################################################
        # CREATE STEP1 PDF
        ####################################################

        st.info("Creating Step 1 PDF...")

        step1_pdf_path = os.path.join(
            GENERATED_FOLDER,
            "step1_extraction.pdf"
        )

        create_step1_pdf(
            final_step1_text,
            step1_pdf_path
        )

        ####################################################
        # STEP 2A — PLI JSON
        ####################################################

        st.info("Running STEP 2A — PLI JSON...")

        upload_1 = upload_pdf_to_chatpdf(
            step1_pdf_path
        )

        print(upload_1)

        source_id_1 = upload_1.get("sourceId")

        if not source_id_1:

            st.error(upload_1)

            st.stop()

        response_pli = ask_chatpdf(
            source_id_1,
            build_prompt_pli()
        )

        ####################################################
        # STEP 2B — RPT JSON
        ####################################################

        st.info("Running STEP 2B — RPT JSON...")

        response_rpt = ask_chatpdf(
            source_id_1,
            build_prompt_rpt()
        )

        ####################################################
        # DISPLAY STEP 2
        ####################################################

        st.subheader("STEP 2A — PLI JSON")

        st.json(response_pli)

        st.subheader("STEP 2B — RPT JSON")

        st.json(response_rpt)

        ####################################################
        # STEP 3 — TP ANALYSIS
        ####################################################

        st.info("Running STEP 3 — TP ANALYSIS...")

        upload_2 = upload_pdf_to_chatpdf(
            pdf_path
        )

        print(upload_2)

        source_id_2 = upload_2.get("sourceId")

        if not source_id_2:

            st.error(upload_2)

            st.stop()

        response_2 = ask_chatpdf(
            source_id_2,
            build_prompt_2()
        )

        ####################################################
        # DISPLAY STEP 3
        ####################################################

        st.subheader("STEP 3 — TP ANALYSIS JSON")

        st.json(response_2)

        ####################################################
        # SAFE PLI JSON
        ####################################################

        raw_pli = response_pli.get("content", "")

        if isinstance(raw_pli, str):

            raw_pli = raw_pli.strip()

            financial_json = safe_json_load(raw_pli)

        else:

            financial_json = raw_pli

        ####################################################
        # SAFE RPT JSON
        ####################################################

        raw_rpt = response_rpt.get("content", "")

        if isinstance(raw_rpt, str):

            raw_rpt = raw_rpt.strip()

            rpt_json = safe_json_load(raw_rpt)

        else:

            rpt_json = raw_rpt

        ####################################################
        # SAFE TP JSON
        ####################################################

        raw_tp = response_2.get("content", "")

        if isinstance(raw_tp, str):

            raw_tp = raw_tp.strip()

            tp_json = safe_json_load(raw_tp)

        else:

            tp_json = raw_tp

        ####################################################
        # FINAL JSON DISPLAY
        ####################################################

        st.subheader("FINAL JSON OUTPUT")

        st.write("STEP 2A — PLI JSON")

        st.json(financial_json)

        st.write("STEP 2B — RPT JSON")

        st.json(rpt_json)

        st.write("STEP 3 — TP ANALYSIS JSON")

        st.json(tp_json)

        ####################################################
        # CLEANUP FILES
        ####################################################

        import os

        try:

            if os.path.exists(pdf_path):

                os.remove(pdf_path)

            if os.path.exists(step1_pdf_path):

                os.remove(step1_pdf_path)

        except Exception as cleanup_error:

            print("Cleanup Error:", cleanup_error)
    except Exception as e:

        import traceback

        st.error(str(e))

        st.code(traceback.format_exc())