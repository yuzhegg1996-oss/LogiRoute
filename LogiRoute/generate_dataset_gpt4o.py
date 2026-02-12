import os
import json
import glob
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MARKDOWN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markdown_output")
DATASET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.json")

def initialize_llm():
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.7, # Slightly higher temperature for diversity, or 0 for consistency? User said "diversity" in distribution. 0.7 is safe.
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        request_timeout=120,
        max_retries=3
    )

def generate_qa_pairs(llm, file_content, filename):
    prompt_text = f"""Role: 你是一名顶尖的 AI 研究员与数据标注专家，擅长从学术论文中提取高质量的 RAG（检索增强生成）测试数据。

Task: 请深入阅读提供的学术论文，并严格按照以下要求生成 15 个中文问答对，用于测试 RAG 系统的检索与生成性能。

核心约束：

显式主语（Context Anchor）： 为了防止 RAG 系统检索时产生歧义，每个问题必须包含论文的具体研究对象或系统名称作为主语。

错误示例： “系统的评估指标是什么？”

正确示例： “在张扬（替换为论文作者）设计的 [具体系统名称] 中，其核心评估指标主要包含了哪些参数？”
正确示例： 在某某（用文章中做的系统来替代某某）系统中.其核心评估指标主要包含了哪些参数？
内容回溯（Evidence Retrieval）： content 字段必须包含支撑该答案的原始段落全文（证据文本），而非简单的答案复读。

难度分布（Diversity）：

6个【细节定位】问题： 针对论文中的特定版本号、硬件环境、模型超参数（如 Learning Rate）、具体工具栈等。

6个【逻辑推理】问题： 考察“为什么这样设计”、“对比其他方法的优劣”、“某个算法模块的运作逻辑”等需跨段落总结的内容。

3个【结构化/表格】问题： 专门针对论文中的表格（Table）、数据库 Schema 或具体的测试用例数据进行提问。

输出格式（严格执行 JSON 列表格式）：

JSON
[
  {{
    "question": "在[论文系统/研究对象名称]中，[具体问题描述]？",
    "answer": "基于论文内容的详尽回答...",
    "type": "detail | logic | structure",
    "content": "此处填入论文中支撑该问题的原始段落文本，确保引用完整。"
  }}
]

待处理的论文内容（文件名：{filename}）：
{file_content[:50000]}  # Limit content length to avoid token limits if files are huge, though GPT-4o has large context.
"""
    
    messages = [
        ("system", "You are a helpful assistant that generates synthetic dataset in JSON format."),
        ("user", prompt_text)
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        # Remove Markdown code block formatting if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return []

def main():
    llm = initialize_llm()
    
    # Initialize or load dataset
    if os.path.exists(DATASET_FILE):
        try:
            with open(DATASET_FILE, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
                if not isinstance(dataset, list):
                    dataset = []
        except:
            dataset = []
    else:
        dataset = []
    
    # Get list of md files
    md_files = glob.glob(os.path.join(MARKDOWN_DIR, "*.md"))
    print(f"Found {len(md_files)} Markdown files.")
    
    processed_files = set() 
    # Optional: Logic to skip already processed files could be added here if we had a way to track them.
    # For now, we append. But if we want to avoid duplicates, we might want to check if the file was processed.
    # However, the user said "iterate... append...". I'll assume I should process all or maybe checking if we already have questions for this file?
    # Simpler to just process.
    
    for i, file_path in enumerate(md_files):
        filename = os.path.basename(file_path)
        print(f"Processing [{i+1}/{len(md_files)}]: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            qa_pairs = generate_qa_pairs(llm, content, filename)
            
            if qa_pairs:
                print(f"Generated {len(qa_pairs)} QA pairs for {filename}")
                dataset.extend(qa_pairs)
                
                # Save immediately
                with open(DATASET_FILE, 'w', encoding='utf-8') as f:
                    json.dump(dataset, f, ensure_ascii=False, indent=2)
            else:
                print(f"No QA pairs generated for {filename}")
                
        except Exception as e:
            print(f"Failed to process file {filename}: {e}")

    print("All done!")

if __name__ == "__main__":
    main()
