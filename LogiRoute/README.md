[English Version](README_en.md) | [中文版本](README.md)

# LogiRoute - 结构化文档 RAG 系统

这是一个基于 MySQL 数据库和 RAG (Retrieval-Augmented Generation) 技术的结构化文档检索与问答系统。包含从 PDF 解析到数据库存储、检索、评估的完整流程。

## 功能特性

- **文档处理**：
  - PDF OCR 转 Markdown (基于 Marker)。
  - DOCX 解析。
  - 自动生成文章摘要。
- **数据库存储**：使用 MySQL 存储文章元数据、章节标题和正文内容。
- **高级检索**：
  - 基于标题和摘要的初筛。
  - 基于内容的深度检索。
- **评估体系**：集成 Ragas 框架，对 RAG 系统的 Faithfulness, Answer Relevancy, Context Precision/Recall 进行评估。

## 项目结构

- `pdf_input/`: 存放输入的 PDF 论文文件。
- `markdown_output/`: 存放转换后的 Markdown 文件。
- `database.py`: 数据库连接与操作核心模块。
- `ocr_pdf_to_markdown.py`: PDF 转 Markdown 工具。
- `import_markdown_to_db.py`: 将 Markdown 数据导入 MySQL。
- `query_data.py`: 数据查询模块。
- `article_retriever_*.py`: 各种模型的文章检索实现。
- `evaluate_*.py`: RAG 效果评估脚本。
- `generate_summaries.py`: 文章摘要生成脚本。
- `frontend/`: 知识库前端管理目录。

## 快速开始

### 1. 环境准备

确保已安装 Python 3.8+ 和 MySQL。

安装依赖：
```bash
pip install -r requirements.txt
```

### 2. 配置环境

复制 `.env.example` 为 `.env` 并填入你的配置信息：

```bash
cp .env.example .env
```

在 `.env` 中配置数据库连接和 API Key：
```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DEEPSEEK_API_KEY=sk-...
OPENAI_API_KEY=sk-...
```

### 3. 数据处理流程

1.  将 PDF 论文放入 `pdf_input/` 目录。
2.  运行 PDF 转 Markdown：
    ```bash
    python ocr_pdf_to_markdown.py
    ```
3.  创建数据库
    ```bash
    python database.py
    ```
4.  初始化数据库并导入数据：
    ```bash
    python import_markdown_to_db.py
    ```
5.  生成文章摘要：
    ```bash
    python generate_summaries.py
    ```
### 4. 运行检索

使用 DeepSeek 模型进行高级检索（基于summary的检索）：
```bash
python advanced_article_retriever_deepseek.py
```
使用 DeepSeek 模型进行普通检索（不用生成每个章节的summary）：
```bash
python article_retriever_deepseek.py
```

## 注意事项

- 本项目包含大量 PDF 和 Markdown 数据处理逻辑，请确保遵守相关数据隐私规定。
- 首次运行 PDF 转换可能需要下载 OCR 模型权重。

## License

[MIT License](LICENSE)
