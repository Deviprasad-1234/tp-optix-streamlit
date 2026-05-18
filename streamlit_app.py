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
import gspread

from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

####################################################
# GOOGLE SHEET CONNECTION
####################################################

scope = [

    "https://spreadsheets.google.com/feeds",

    "https://www.googleapis.com/auth/drive"

]

creds = ServiceAccountCredentials.from_json_keyfile_dict(

    dict(st.secrets["gcp_service_account"]),

    scope

)

client = gspread.authorize(creds)

sheet = client.open(

    "TP_OPTIX_RESULTS"

).sheet1

st.title("TP OPTIX")

####################################################
# QUERY PARAMS
####################################################

query_params = st.query_params

auto_pdf_link = query_params.get(

    "pdf_link",

    ""

)

auto_job = query_params.get(

    "job_id",

    ""

)

auto_bs = query_params.get(

    "bs",

    ""

)

auto_pl = query_params.get(

    "pl",

    ""

)

auto_oi = query_params.get(

    "oi",

    ""

)

auto_oe = query_params.get(

    "oe",

    ""

)

auto_rpt = query_params.get(

    "rpt",

    ""

)

auto_run = query_params.get(

    "run",

    "false"

)

####################################################
# GOOGLE DRIVE LINK
####################################################

google_drive_link = st.text_input(

    "OR Paste Google Drive PDF Link",

    value=auto_pdf_link

)
####################################################
# UNIQUE JOB ID
####################################################

job_id = st.text_input(

    "Unique Job ID",

    value=auto_job,

    placeholder="TPX_20260515_001"

)
balanceSheetPages = st.text_input(

    "Balance Sheet Pages",

    value=auto_bs

)

plStatementPages = st.text_input(

    "P&L Pages",

    value=auto_pl

)

otherIncomePages = st.text_input(

    "Other Income Pages",

    value=auto_oi

)

otherExpensePages = st.text_input(

    "Other Expense Pages",

    value=auto_oe

)

rptPages = st.text_input(

    "RPT Pages",

    value=auto_rpt

)

run_button = st.button(
    "RUN TP OPTIX"
)

if auto_run == "true":

    run_button = True
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
# DOWNLOAD GOOGLE DRIVE PDF
############################################################

def download_drive_pdf(drive_link, output_path):

    try:

        ####################################################
        # EXTRACT FILE ID
        ####################################################

        file_id = None

        if "/file/d/" in drive_link:

            file_id = drive_link.split("/file/d/")[1].split("/")[0]

        elif "id=" in drive_link:

            file_id = drive_link.split("id=")[1].split("&")[0]

        ####################################################
        # INVALID
        ####################################################

        if not file_id:

            return False

        ####################################################
        # DIRECT DOWNLOAD URL
        ####################################################

        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        ####################################################
        # DOWNLOAD
        ####################################################

        response = requests.get(

            download_url,

            timeout=300

        )

        ####################################################
        # SAVE FILE
        ####################################################

        with open(output_path, "wb") as f:

            f.write(response.content)

        return True

    except Exception as e:

        print(e)

        return False
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

############################################################
# CREATE FOCUSED PLI PDF
############################################################

def create_pli_retry_pdf(

    pl_text,

    oi_text,

    oe_text,

    output_path

):

    doc = SimpleDocTemplate(output_path)

    styles = getSampleStyleSheet()

    story = []

    ####################################################
    # TITLE
    ####################################################

    story.append(

        Paragraph(

            "<b>PLI RETRY EXTRACTION PDF</b>",

            styles["Heading1"]

        )

    )

    story.append(Spacer(1, 20))

    ####################################################
    # P&L
    ####################################################

    story.append(

        Paragraph(

            "<b>PROFIT AND LOSS EXTRACTION</b>",

            styles["Heading2"]

        )

    )

    story.append(Spacer(1, 10))

    for line in pl_text.split("\\n"):

        if line.strip():

            story.append(

                Paragraph(

                    line,

                    styles["BodyText"]

                )

            )

    ####################################################
    # OTHER INCOME
    ####################################################

    story.append(Spacer(1, 20))

    story.append(

        Paragraph(

            "<b>OTHER INCOME EXTRACTION</b>",

            styles["Heading2"]

        )

    )

    for line in oi_text.split("\\n"):

        if line.strip():

            story.append(

                Paragraph(

                    line,

                    styles["BodyText"]

                )

            )

    ####################################################
    # OTHER EXPENSE
    ####################################################

    story.append(Spacer(1, 20))

    story.append(

        Paragraph(

            "<b>OTHER EXPENSE EXTRACTION</b>",

            styles["Heading2"]

        )

    )

    for line in oe_text.split("\\n"):

        if line.strip():

            story.append(

                Paragraph(

                    line,

                    styles["BodyText"]

                )

            )

    doc.build(story)

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
# CHECK MISSING PLI KEYWORDS
############################################################

def check_missing_pli_keywords(

    financial_json,

    pl_text

):

    try:

        ####################################################
        # NO JSON
        ####################################################

        if not financial_json:

            return True, ["JSON EMPTY"]

        ####################################################
        # NO final_pli
        ####################################################

        if "final_pli" not in financial_json:

            return True, ["final_pli missing"]

        ####################################################
        # FINAL PLI TEXT
        ####################################################

        combined_text = json.dumps(

            financial_json["final_pli"]

        ).lower()

        ####################################################
        # REQUIRED KEYWORDS
        ####################################################

        required_keywords = [

            "Revenue",

            "Purchase",

            "Employee",

            "Depreciation",

            "Other expenses"

        ]

        ####################################################
        # CHECK ONLY IF EXISTS IN P&L
        ####################################################

        missing_keywords = []

        for keyword in required_keywords:

            if keyword.lower() in pl_text.lower():

                if keyword.lower() not in combined_text:

                    missing_keywords.append(keyword)

        ####################################################
        # RESULT
        ####################################################

        if len(missing_keywords) > 0:

            return True, missing_keywords

        return False, []

    except Exception as e:

        return True, [str(e)]

############################################################
# SMART PLI VALIDATION
############################################################


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

STRICT EXTRACTION SOURCE RULES:

1. "final_pli" MUST be created STRICTLY and ONLY from:
PROFIT AND LOSS EXTRACTION section. (include all items from Revenue or Revenue from Operation to Other expenses all strictly everytime. Don't skip please)

2. "non_operating_income" MUST be created STRICTLY and ONLY from:
OTHER INCOME EXTRACTION section.

3. "non_operating_expense" MUST be created STRICTLY and ONLY from:
OTHER EXPENSE EXTRACTION section.

4. Do NOT move items from P&L into non_operating_income.

5. Do NOT move items from P&L into non_operating_expense.

6. Do NOT deduct non-operating items from final_pli.

7. final_pli should preserve the ORIGINAL Profit & Loss structure exactly as disclosed in the P&L before Profit Before Tax.

8. Exclude:
- Profit Before Tax
- Profit After Tax
- EPS
- OCI
- Comprehensive Income

9. Preserve ONLY line-item level data.

10. AI dashboard calculations and PLI adjustments will happen later externally. Do NOT perform any adjustment calculations here.

11. Under:
"Nature as opearting or non opearting"

ONLY use:
- Operating
- Non operating

No other values allowed.

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
        # VERIFY JOB ID IN GOOGLE SHEET
        ####################################################

        if not job_id:

            st.error("Please enter Unique Job ID")

            st.stop()

        all_values = sheet.get_all_values()

        job_found = False

        job_row = None

        for idx, row in enumerate(all_values, start=1):

            if len(row) > 0 and row[0].strip() == job_id.strip():

                job_found = True

                job_row = idx

                break

        ####################################################
        # INVALID JOB ID
        ####################################################

        if not job_found:

            st.error(

                "Code is not matching. Request has been rejected."

            )

            st.stop()
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

        ####################################################
        # PDF SOURCE
        ####################################################

        pdf_path = os.path.join(

            UPLOAD_FOLDER,

            f"{job_id}.pdf"

        )

        ####################################################
        # GOOGLE DRIVE LINK
        ####################################################

        if google_drive_link:

            st.info("Downloading PDF from Google Drive...")

            success = download_drive_pdf(

                google_drive_link,

                pdf_path

            )

            if not success:

                st.error("Unable to download Google Drive PDF")

                st.stop()

        ####################################################
        # NO INPUT
        ####################################################

        else:

            st.error(

                "Please upload PDF or provide Google Drive Link"

            )

            st.stop()

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

        st.success(

            "STEP 1 Extraction Completed"

        )

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

        ####################################################
        # STEP 2A — STRONG RETRY LOGIC
        ####################################################

        ####################################################
        # STEP 2A — SMART RETRY LOGIC
        ####################################################

        ####################################################
        # STEP 2A — NORMAL GENERATION
        ####################################################

        response_pli = ask_chatpdf(

            source_id_1,

            build_prompt_pli()

        )

        financial_json = safe_json_load(

            response_pli.get("content", "")

        )

        ####################################################
        # CHECK MISSING KEYWORDS
        ####################################################

        rerun_required, missing_keywords = check_missing_pli_keywords(

            financial_json,

            pl_text

        )

        ####################################################
        # RERUN ONLY IF MISSING
        ####################################################

        if rerun_required:

            st.warning(

                f"Re-running PLI Extraction. Missing: {missing_keywords}"

            )

            ####################################################
            # SECOND ATTEMPT
            ####################################################

            response_pli_retry = ask_chatpdf(

                source_id_1,

                build_prompt_pli()

            )

            retry_json = safe_json_load(

                response_pli_retry.get("content", "")

            )

            ####################################################
            # CHECK AGAIN
            ####################################################

            rerun_required_again, missing_keywords_again = check_missing_pli_keywords(

                retry_json,

                pl_text

            )

            ####################################################
            # SUCCESS
            ####################################################

            if not rerun_required_again:

                financial_json = retry_json

            ####################################################
            # FINAL FAILURE
            ####################################################

            else:

                financial_json = {

                    "status": "AI_STUDIO_REPROCESS_REQUIRED",

                    "reason": "Missing mandatory PLI items after retry",

                    "missing_keywords": missing_keywords_again,

                    ####################################################
                    # IMPORTANT
                    ####################################################

                    "chatpdf_generated_json": retry_json,

                    ####################################################
                    # STEP 2 RAW RESPONSES
                    ####################################################

                    "raw_step2a_response": response_pli_retry.get(

                        "content",

                        ""

                    ),

                    ####################################################
                    # CLEAN EXTRACTIONS
                    ####################################################

                    "step1_pl_extraction": pl_text,

                    "step1_other_income_extraction": oi_text,

                    "step1_other_expense_extraction": oe_text,

                    ####################################################
                    # AI STUDIO ACTION
                    ####################################################

                    "ai_studio_instruction": (

                        "Use chatpdf_generated_json first. "

                        "If incomplete, reprocess using "

                        "step1_pl_extraction + "

                        "step1_other_income_extraction + "

                        "step1_other_expense_extraction"

                    )

                }
        ####################################################
        # STEP 2B — RPT JSON
        ####################################################

        st.info("Running STEP 2B — RPT JSON...")

        ####################################################
        # STEP 2B RETRY LOGIC
        ####################################################

        ####################################################
        # STEP 2B RETRY LOGIC
        ####################################################

        rpt_json = {}

        rpt_retry = 0

        max_rpt_retry = 2

        while rpt_retry < max_rpt_retry:

            response_rpt = ask_chatpdf(

                source_id_1,

                build_prompt_rpt()

            )

            rpt_json = safe_json_load(

                response_rpt.get("content", "")

            )

            ################################################
            # VALID
            ################################################

            if rpt_json and "rpt_table" in rpt_json:

                break

            rpt_retry += 1

        ####################################################
        # FINAL FALLBACK
        ####################################################

        if not rpt_json:

            rpt_json = {

                "status": "AI_STUDIO_REPROCESS_REQUIRED",

                "reason": "RPT JSON FAILED",

                "raw_response": response_rpt,

                "raw_rpt_text": rpt_text[:25000]

            }
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

        ####################################################
        # STEP 3 — STRONG RETRY
        ####################################################

        tp_json = {}

        tp_retry = 0

        max_tp_retry = 2

        while tp_retry < max_tp_retry:

            response_2 = ask_chatpdf(

                source_id_2,

                build_prompt_2()

            )

            tp_json = safe_json_load(

                response_2.get("content", "")

            )

            ####################################################
            # VALID TP JSON
            ####################################################

            if tp_json and "basic_information" in tp_json:

                break

            tp_retry += 1

        ####################################################
        # FINAL FALLBACK
        ####################################################

        if not tp_json:

            tp_json = {

                "status": "AI_STUDIO_REPROCESS_REQUIRED",

                "reason": "TP JSON FAILED",

                "raw_response": response_2,

                "raw_pdf_data": final_step1_text[:25000]

            }

        ####################################################
        # FINAL PLI RECOVERY STEP
        ####################################################

        if (

            isinstance(financial_json, dict)

            and financial_json.get(

                "status"

            ) == "AI_STUDIO_REPROCESS_REQUIRED"

        ):

            st.warning(

                "FINAL PLI RECOVERY STEP RUNNING..."

            )

            ################################################
            # CREATE SMALL FOCUSED PDF
            ################################################

            pli_retry_pdf_path = os.path.join(

                GENERATED_FOLDER,

                "pli_retry.pdf"

            )

            create_pli_retry_pdf(

                pl_text,

                oi_text,

                oe_text,

                pli_retry_pdf_path

            )

            ################################################
            # UPLOAD NEW PDF
            ################################################

            upload_retry = upload_pdf_to_chatpdf(

                pli_retry_pdf_path

            )

            retry_source_id = upload_retry.get(

                "sourceId"

            )

            ################################################
            # DOUBLE RETRY
            ################################################

            if retry_source_id:

                retry_count = 0

                while retry_count < 2:

                    retry_response = ask_chatpdf(

                        retry_source_id,

                        build_prompt_pli()

                    )

                    retry_json = safe_json_load(

                        retry_response.get(

                            "content",

                            ""

                        )

                    )

                    ################################################
                    # VALIDATE AGAIN
                    ################################################

                    retry_failed, retry_missing = check_missing_pli_keywords(

                        retry_json,

                        pl_text

                    )

                    ################################################
                    # SUCCESS
                    ################################################

                    if not retry_failed:

                        financial_json = retry_json

                        st.success(

                            "FINAL PLI RECOVERY SUCCESSFUL"

                        )

                        break

                    retry_count += 1

            sheet.update_cell(
                job_row,
                10,
                "COMPLETED"
            )
        ####################################################
        # CLEANUP FILES
        ####################################################
                
        try:

            if os.path.exists(pdf_path):

                os.remove(pdf_path)

            if os.path.exists(step1_pdf_path):

                os.remove(step1_pdf_path)

        except Exception as cleanup_error:

            print("Cleanup Error:", cleanup_error)

        ####################################################
        # DONE MESSAGE
        ####################################################

        st.success(

            "DONE — Task Finished Successfully"

        )

        st.balloons()

        st.info(

            "Task completed successfully. "

            "Please return to AI Studio "

            "and refresh the results page."

        )

    except Exception as e:

        import traceback

        st.error(str(e))

        st.code(traceback.format_exc())