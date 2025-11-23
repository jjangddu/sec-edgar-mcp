# SEC EDGAR Filings MCP Server

This project is an MCP (Model Context Protocol) server implementation designed to interact with the SEC EDGAR database. It allows AI agents (like Claude) to search, download, and parse corporate filings automatically.

## Features

1.  **Download SEC Filings**: Fetches specific filings (8-K, 10-Q, 10-K, DEF 14A) directly from SEC EDGAR based on CIK and Year.
2.  **HTML to PDF**: Converts the downloaded HTML filing documents into PDF format using Playwright.
3.  **PDF to Markdown**: Parses PDF files into Markdown text to allow LLMs to read and analyze the content.

## Prerequisites

* **Python**: 3.10 or higher
* **Package Manager**: pip
* **Playwright**: Required for HTML to PDF conversion

## Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/jjangddu/sec-edgar-mcp.git
    cd sec-edgar-mcp
    ```

2.  **Create and Activate Virtual Environment**
    ```bash
    # Windows
    python -m venv .venv
    .\.venv\Scripts\activate
    
    # Mac/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    playwright install
    ```

4.  **Prepare Directories**
    Ensure the `html` and `pdf` directories exist in the root folder.
    ```bash
    mkdir html pdf
    ```

## How to Run

### Option 1: Local Execution (STDIO)
Run the server directly using Python. This is used for connecting with Claude Desktop.
```bash
python main.py