[English Version](README_en.md) | [中文版本](README.md)

# LogiRoute - Structured Document RAG System

This is a structured document retrieval and question-answering system based on MySQL database and RAG (Retrieval-Augmented Generation) technology. It covers the complete workflow from PDF parsing to database storage, retrieval, and evaluation.

## Features

- **Document Processing**:
  - PDF OCR to Markdown (based on Marker).
  - DOCX parsing.
  - Automatic article summary generation.
- **Database Storage**: Uses MySQL to store article metadata, section titles, and plain text content.
- **Advanced Retrieval**:
  - Initial screening based on titles and summaries.
  - Deep retrieval based on content.
- **Evaluation System**: Integrated Ragas framework to evaluate Faithfulness, Answer Relevancy, and Context Precision/Recall of the RAG system.

## Project Structure

- `pdf_input/`: Directory for input PDF thesis files.
- `markdown_output/`: Directory for converted Markdown files.
- `database.py`: Core module for database connection and operations.
- `ocr_pdf_to_markdown.py`: Tool for converting PDF to Markdown.
- `import_markdown_to_db.py`: Script to import Markdown data into MySQL.
- `query_data.py`: Data query module.
- `article_retriever_*.py`: Article retrieval implementations for various models.
- `evaluate_*.py`: Scripts for evaluating RAG performance.
- `generate_summaries.py`: Script for generating article summaries.
- `frontend/`: Directory for knowledge base frontend management.

## Quick Start

### 1. Prerequisites

Ensure you have Python 3.8+ and MySQL installed.

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and fill in your configuration details:

```bash
cp .env.example .env
```

Configure the database connection and API Keys in `.env`:
```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...
```

### 3. Data Processing Workflow

1.  Place PDF files into the `pdf_input/` directory.
2.  Run PDF to Markdown conversion:
    ```bash
    python ocr_pdf_to_markdown.py
    ```
3.  Initialize the database:
    ```bash
    python database.py
    ```
4.  Import data into the database:
    ```bash
    python import_markdown_to_db.py
    ```
5.  Generate article summaries:
    ```bash
    python generate_summaries.py
    ```

### 4. Running Retrieval

Run advanced retrieval using the DeepSeek model (summary-based retrieval):
```bash
python advanced_article_retriever_deepseek.py
```

Run normal retrieval using the DeepSeek model (without generating summaries for each section):
```bash
python article_retriever_deepseek.py
```

## Notes

- This project involves processing PDF and Markdown data. Please ensure compliance with relevant data privacy regulations.
- The first run of the PDF conversion tool may trigger the download of OCR model weights.

## License

[MIT License](LICENSE)
