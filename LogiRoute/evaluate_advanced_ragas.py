
import os
import sys
import json
import re
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from langchain_openai import ChatOpenAI
# from langchain_ollama import OllamaEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import RAG functions
try:
    from advanced_article_retriever_deepseek import (
        get_all_articles_with_details,
        get_enhanced_deepseek_response_article,
        get_enhanced_deepseek_response_title,
        get_deepseek_response_rag,
        get_plain_text_by_title_id,
        DEEPSEEK_API_KEY,
        DEEPSEEK_BASE_URL,
        MODEL_NAME
    )
except ImportError as e:
    print(f"Error importing RAG module: {e}")
    # Define fallback constants if import fails
    DEEPSEEK_API_KEY = "sk-bfcb1cfdb6c74b869263a3bd4d974b1b"
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    MODEL_NAME = "deepseek-chat"

# ChatGPT (GPT-4o) Configuration for RAGAS
OPENAI_API_KEY = "sk-vBR7rq8Z7sXK8JpQlb94V4IjhWBhalBIbogfKMBGu7aX7oMn"
OPENAI_BASE_URL = "https://api.shubiaobiao.com/v1"

evaluator_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    temperature=0,
    request_timeout=120,
    max_retries=3
)

# Embeddings for metrics that need them (like answer_relevancy)
# We use HuggingFace embeddings model as requested by user.
# Model: BAAI/bge-large-zh-v1.5
print("Loading embeddings model (BAAI/bge-large-zh-v1.5)...")
try:
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-zh-v1.5"
    )
except Exception as e:
    print(f"Error loading HuggingFace embeddings: {e}")
    # Raise error because user specifically requested this model and not Ollama
    raise e

def run_rag_pipeline(question, articles_details):
    """
    Runs the full RAG pipeline for a given question.
    Returns:
        answer (str): The generated answer.
        contexts (list[str]): The retrieved context texts.
    """
    # Level 1: Article Retrieval
    try:
        article_title = get_enhanced_deepseek_response_article(question, articles_details)
    except Exception as e:
        print(f"Error in article retrieval: {e}")
        return "Error in article retrieval", []
        
    if not article_title:
        return "无法找到相关文章", []

    # Level 2: Chapter Retrieval
    try:
        ids_str, all_titles = get_enhanced_deepseek_response_title(question, article_title)
    except Exception as e:
        print(f"Error in chapter retrieval: {e}")
        return "Error in chapter retrieval", []
        
    if not ids_str:
        return "无法找到相关章节", []

    # Parse IDs
    clean_ids = "".join([c for c in ids_str if c.isdigit() or c == ','])
    title_id_list = [int(num) for num in clean_ids.split(',') if num.strip()]
    
    if not title_id_list:
        return "无法解析章节ID", []

    # Level 3: Context Retrieval
    contexts = []
    for tid in title_id_list:
        try:
            content = get_plain_text_by_title_id(tid)
            if content:
                contexts.append(content)
            else:
                # Retry next ID logic from original script
                 content = get_plain_text_by_title_id(tid + 1)
                 if content:
                     contexts.append(content)
        except Exception as e:
            print(f"Error fetching content for ID {tid}: {e}")
    
    if not contexts:
        # If no context found, we return empty list. 
        # RAGAS might penalize this, which is correct.
        return "无法获取章节内容", []

    # Level 4: Generation
    try:
        answer = get_deepseek_response_rag(question, title_id_list)
    except Exception as e:
        print(f"Error in generation: {e}")
        answer = "生成回答失败"
        
    if not answer:
        answer = "生成回答失败"
        
    return answer, contexts

def main():
    print("Starting RAGAS Evaluation...")
    
    # Load dataset
    dataset_path = "dataset.json"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize RAG resources
    print("Initializing RAG resources...")
    articles_details = get_all_articles_with_details()
    if not articles_details:
        print("No articles found in database.")
        return

    # Prepare data for RAGAS
    questions = []
    ground_truths = []
    answers = []
    contexts_list = []
    types = []
    reference_contents = []

    # Process items
    # For demonstration/testing, we might want to limit the number if it takes too long
    # But let's process all for now.
    total_items = len(data)
    print(f"Processing {total_items} items from dataset...")
    
    for i, item in enumerate(data):
        q = item["question"]
        gt = item["answer"]
        q_type = item.get("type", "unknown") # Get type, default to unknown
        ref_content = item.get("content", "") # Get reference content (evidence)
        
        print(f"\n[{i+1}/{total_items}] Processing Question: {q}")
        
        # Run RAG
        ans, ctxs = run_rag_pipeline(q, articles_details)
        
        # Ensure contexts is a list of strings
        if not ctxs:
            ctxs = [""] # Empty context
            
        questions.append(q)
        ground_truths.append(gt) # RAGAS expects string or list[str]. Usually string is fine for 'ground_truth' column in newer versions, but 'ground_truths' (plural) is list. Let's use 'ground_truth' column with string.
        answers.append(ans)
        contexts_list.append(ctxs)
        types.append(q_type)
        reference_contents.append(ref_content)

    # Create HF Dataset
    # Note: RAGAS expects 'question', 'answer', 'contexts', 'ground_truth'
    ragas_data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
        "type": types,
        "reference_content": reference_contents
    }
    dataset = Dataset.from_dict(ragas_data)

    # Run Evaluation
    print("\nRunning RAGAS metrics...")
    
    # We need to pass the llm and embeddings explicitly
    try:
        results = evaluate(
            dataset=dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
            llm=evaluator_llm,
            embeddings=embeddings
        )

        print("\nEvaluation Results:")
        print(results)
        
        # Save results
        df = results.to_pandas()
        output_file = "ragas_evaluation_results.csv"
        df.to_csv(output_file, index=False)
        print(f"Results saved to {output_file}")
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
