import os
import sys
import json

# --- 1. 경로 설정 ---
current_dir = os.getcwd()
# 파이썬 설치 경로 찾기
python_dir = os.path.dirname(sys.executable)
# Scripts 폴더 안의 fastmcp.exe 경로 (이게 정답 실행 도구입니다)
fastmcp_exe = os.path.join(python_dir, "Scripts", "fastmcp.exe")
main_py = os.path.join(current_dir, "main.py")
config_path = os.path.join(os.getenv('APPDATA'), "Claude", "claude_desktop_config.json")

print(f"🔧 수리 시작...")
print(f"👉 실행 도구 위치: {fastmcp_exe}")

# --- 2. main.py 코드 완벽 수정 (헤더 오타 수정됨) ---
# headers 변수가 함수 안에 정확히 들어있는 버전입니다.
correct_main_code = r'''
import os
import requests
from fastmcp import FastMCP
from pypdf import PdfReader
from playwright.sync_api import sync_playwright
from ratelimit import limits, sleep_and_retry

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdf")
HTML_DIR = os.path.join(BASE_DIR, "html")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

mcp = FastMCP("SEC EDGAR Filings MCP")
SEC_API_BASE_URL = "https://data.sec.gov/submissions"
SEC_ARCHIVE_BASE_URL = "https://www.sec.gov/Archives/edgar/data"

@sleep_and_retry
@limits(calls=10, period=1)
def call_sec_api(url: str):
    # [수정됨] 학교/학생 신분을 명시한 헤더 (차단 방지)
    headers = {
        "User-Agent": "HanyangUniversity Student_Project peterjdw@naver.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov"
    }
    # headers 변수명이 소문자로 일치합니다.
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response

@mcp.tool()
def read_as_markdown(input_file_path: str) -> str:
    safe_name = os.path.basename(input_file_path)
    file_path = os.path.join(PDF_DIR, safe_name)
    if not os.path.exists(file_path): return f"Error: File not found: {file_path}"
    try:
        reader = PdfReader(file_path)
        text = f"# Content of {safe_name}\n\n"
        for i, p in enumerate(reader.pages): text += f"## Page {i+1}\n{p.extract_text()}\n\n"
        return text
    except Exception as e: return f"Error: {e}"

@mcp.tool()
def html_to_pdf(input_file_path: str, output_file_path: str) -> str:
    input_path = os.path.join(HTML_DIR, input_file_path)
    output_path = os.path.join(PDF_DIR, os.path.basename(output_file_path))
    if not os.path.exists(input_path): return f"Error: Not found {input_path}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{input_path}")
            page.pdf(path=output_path)
            browser.close()
        return f"Success: Saved to {output_path}"
    except Exception as e: return f"Error: {e}"

@mcp.tool()
def download_sec_filing(cik: str, year: int, filing_type: str, output_dir_path: str) -> str:
    try:
        padded_cik = f"{int(cik):0>10}"
        resp = call_sec_api(f"{SEC_API_BASE_URL}/CIK{padded_cik}.json")
        data = resp.json()
        recent = data['filings']['recent']
        target_idx = -1
        for i in range(len(recent['accessionNumber'])):
            if recent['form'][i] == filing_type and recent['filingDate'][i].startswith(str(year)):
                target_idx = i
                break
        if target_idx == -1: return f"Error: No {filing_type} for {year}"

        acc_num = recent['accessionNumber'][target_idx]
        doc_name = recent['primaryDocument'][target_idx]
        save_path = os.path.join(HTML_DIR, os.path.basename(output_dir_path))
        os.makedirs(save_path, exist_ok=True)

        file_resp = call_sec_api(f"{SEC_ARCHIVE_BASE_URL}/{int(cik)}/{acc_num.replace('-','')}/{doc_name}")
        with open(os.path.join(save_path, doc_name), "wb") as f: f.write(file_resp.content)
        return os.path.join(os.path.basename(output_dir_path), doc_name).replace("\\", "/")
    except Exception as e: return f"Error: {e}"

if __name__ == "__main__":
    mcp.run()
'''

with open(main_py, "w", encoding="utf-8") as f:
    f.write(correct_main_code)
print("✅ main.py 코드 수정 완료 (오타 해결)")

# --- 3. Claude 설정 파일 복구 (fastmcp 직접 연결) ---
# cmd.exe를 빼고, 아까 성공했던 fastmcp.exe 직접 연결 방식으로 돌아갑니다.
config_data = {
    "mcpServers": {
        "sec-edgar-mcp": {
            "command": fastmcp_exe,
            "args": [
                "run",
                main_py,
                "--no-banner"  # 로고 숨김 옵션
            ],
            "env": {
                "PYTHONUTF8": "1"  # 한글 깨짐 방지
            }
        }
    }
}

# 폴더가 없으면 생성
if not os.path.exists(os.path.dirname(config_path)):
    os.makedirs(os.path.dirname(config_path))

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config_data, f, indent=2, ensure_ascii=False)
print("✅ Claude 설정 파일 복구 완료 (cmd 제거, fastmcp 직접 연결)")

print("\n" + "=" * 50)
print("🎉 모든 준비가 끝났습니다!")
print("1. [작업 관리자]에서 Claude를 강제 종료하세요.")
print("2. Claude를 다시 켜세요.")
print("3. 'Amazon 2024 10-K 다운로드해줘' 입력하세요.")
print("=" * 50)