import os
import requests
import time
from fastmcp import FastMCP
from pypdf import PdfReader
from playwright.sync_api import sync_playwright
from ratelimit import limits, sleep_and_retry

# --- 1. 프로젝트 경로 및 서버 설정 ---
# 현재 main.py가 있는 폴더 위치를 찾습니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdf")
HTML_DIR = os.path.join(BASE_DIR, "html")

# MCP 서버 생성
mcp = FastMCP("SEC EDGAR Filings MCP")

# --- 2. SEC API 호출 도우미 (속도 제한 및 헤더 설정) ---
SEC_API_BASE_URL = "https://data.sec.gov/submissions"
SEC_ARCHIVE_BASE_URL = "https://www.sec.gov/Archives/edgar/data"


# [중요] SEC는 1초에 10회 요청 제한이 있습니다. 이를 자동으로 지켜주는 장치입니다.
@sleep_and_retry
@limits(calls=10, period=1)
def call_sec_api(url: str):
    # [수정 필요] 아래 이메일 주소를 본인 이메일로 변경해주세요!
    headers = {"User-Agent": "HanyangStudent my-email@example.com"}

    response = requests.get(url, headers=headers)
    # 요청이 실패하면(404 등) 에러를 띄웁니다.
    response.raise_for_status()
    return response


# --- 3. 과제 1: PDF -> Markdown 변환 툴 ---
@mcp.tool()
def read_as_markdown(input_file_path: str) -> str:
    """
    pdf 폴더에 있는 PDF 파일을 읽어서 텍스트(Markdown)로 변환해줍니다.
    """
    # 파일 이름만 추출해서 경로를 만듭니다 (보안상 안전)
    safe_name = os.path.basename(input_file_path)
    file_path = os.path.join(PDF_DIR, safe_name)

    if not os.path.exists(file_path):
        return f"Error: 파일을 찾을 수 없습니다 -> {file_path}"

    try:
        reader = PdfReader(file_path)
        text_content = f"# Content of {safe_name}\n\n"

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_content += f"## Page {i + 1}\n{text}\n\n"

        return text_content
    except Exception as e:
        return f"Error PDF 읽기 실패: {str(e)}"


# --- 4. 과제 2: HTML -> PDF 변환 툴 ---
@mcp.tool()
def html_to_pdf(input_file_path: str, output_file_path: str) -> str:
    """
    html 폴더의 파일을 읽어 pdf 폴더에 PDF로 저장합니다.
    """
    # 1. 입력 파일 경로 확인 (html 폴더 안)
    input_full_path = os.path.join(HTML_DIR, input_file_path)  # 예: html/folder/file.htm
    if not os.path.exists(input_full_path):
        return f"Error: 입력 파일을 찾을 수 없습니다 -> {input_full_path}"

    # 2. 출력 파일 경로 설정 (pdf 폴더 안)
    output_safe_name = os.path.basename(output_file_path)
    output_full_path = os.path.join(PDF_DIR, output_safe_name)

    try:
        # Playwright(가상 브라우저) 실행
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            # 로컬 파일을 브라우저로 열기 (file:// 프로토콜 사용)
            file_url = f"file://{input_full_path}"
            page.goto(file_url)

            # PDF로 저장
            page.pdf(path=output_full_path)
            browser.close()

        return f"Success: PDF 변환 완료! 저장 위치 -> {output_full_path}"
    except Exception as e:
        return f"Error PDF 변환 실패: {str(e)}"


# --- 5. 과제 3: SEC 공시 다운로드 툴 ---
@mcp.tool()
def download_sec_filing(cik: str, year: int, filing_type: str, output_dir_path: str) -> str:
    """
    SEC에서 특정 회사의 공시 자료를 다운로드합니다.
    예: cik="0001018724", year=2024, filing_type="10-K"
    """
    # 1. 입력값 검증
    if not (2021 <= year <= 2025):
        return "Error: 연도는 2021~2025년 사이만 가능합니다."

    # 2. 저장할 폴더 만들기
    save_dir_name = os.path.basename(output_dir_path)
    full_save_path = os.path.join(HTML_DIR, save_dir_name)
    os.makedirs(full_save_path, exist_ok=True)

    try:
        # 3. 회사의 전체 공시 목록 가져오기
        # CIK는 10자리 숫자여야 함 (예: 123 -> 0000000123)
        padded_cik = f"{int(cik):0>10}"
        json_url = f"{SEC_API_BASE_URL}/CIK{padded_cik}.json"

        response = call_sec_api(json_url)
        data = response.json()

        # 4. 원하는 조건(연도, 타입)에 맞는 최신 파일 찾기
        recent = data['filings']['recent']
        target_idx = -1

        # 목록을 하나씩 훑어봅니다.
        for i in range(len(recent['accessionNumber'])):
            form = recent['form'][i]  # 10-K, 8-K 등
            f_date = recent['filingDate'][i]  # 2024-01-01

            if form == filing_type and f_date.startswith(str(year)):
                target_idx = i
                break  # 찾았다! (가장 최신 것이 먼저 나오므로 break)

        if target_idx == -1:
            return f"Error: {year}년도 {filing_type} 문서를 찾을 수 없습니다."

        # 5. 파일 다운로드 링크 만들기
        accession_num = recent['accessionNumber'][target_idx]  # 예: 000-111-222
        doc_name = recent['primaryDocument'][target_idx]  # 예: report.htm

        # URL에서는 하이픈(-)을 빼야 함
        accession_no_dash = accession_num.replace("-", "")

        # 최종 다운로드 URL
        # https://www.sec.gov/Archives/edgar/data/{CIK}/{Accession}/{FileName}
        download_url = f"{SEC_ARCHIVE_BASE_URL}/{int(cik)}/{accession_no_dash}/{doc_name}"

        # 6. 실제 파일 다운로드 및 저장
        file_res = call_sec_api(download_url)
        local_file_path = os.path.join(full_save_path, doc_name)

        with open(local_file_path, "wb") as f:
            f.write(file_res.content)

        # 다음 단계(html_to_pdf)에서 쓰기 편하게 상대 경로 반환
        # 예: html/amzn_2024_10k/report.htm
        relative_path = os.path.join(save_dir_name, doc_name).replace("\\", "/")

        return f"Success: 다운로드 완료! 대표 파일 경로 -> {relative_path}"

    except Exception as e:
        return f"Error 다운로드 중 오류 발생: {str(e)}"


# --- 6. 서버 실행 ---
if __name__ == "__main__":
    mcp.run()