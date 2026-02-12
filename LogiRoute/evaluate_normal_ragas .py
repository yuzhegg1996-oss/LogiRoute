
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

# Import RAG functions from article_retriever deepseek.py
try:
    from database import get_all_articles, get_plain_text_by_title_id
    from query_data import query_article_titles
    # Import functions from article_retriever deepseek.py
    # Note: We import the module as a whole or specific functions. 
    # Since the file name has spaces, we might need to use importlib or rename the file.
    # However, Python import doesn't support spaces directly.
    # Let's check if the file can be imported directly or if we need to use importlib.
    import importlib.util
    spec = importlib.util.spec_from_file_location("article_retriever_deepseek", "article_retriever deepseek.py")
    article_retriever_deepseek = importlib.util.module_from_spec(spec)
    sys.modules["article_retriever_deepseek"] = article_retriever_deepseek
    spec.loader.exec_module(article_retriever_deepseek)
    
    get_deepseek_response_article = article_retriever_deepseek.get_deepseek_response_article
    get_deepseek_response_title = article_retriever_deepseek.get_deepseek_response_title
    get_deepseek_response_rag = article_retriever_deepseek.get_deepseek_response_rag
    
except ImportError as e:
    print(f"Error importing RAG module: {e}")
    sys.exit(1)

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

def run_rag_pipeline(question, articles_context):
    """
    Runs the full RAG pipeline for a given question using article_retriever deepseek.py logic.
    Returns:
        answer (str): The generated answer.
        contexts (list[str]): The retrieved context texts.
    """
    # Level 1: Article Retrieval
    try:
        article_title = get_deepseek_response_article(question, articles_context)
    except Exception as e:
        print(f"Error in article retrieval: {e}")
        return "Error in article retrieval", []
        
    if not article_title:
        return "无法找到相关文章", []

    # Level 2: Chapter Retrieval
    try:
        # Check if article has chapters (from main function logic in article_retriever deepseek.py)
        titles_json = query_article_titles(article_title)
        titles = json.loads(titles_json)
        if not titles:
            return "文章无章节信息", []
            
        response_titles = get_deepseek_response_title(question, article_title)
    except Exception as e:
        print(f"Error in chapter retrieval: {e}")
        return "Error in chapter retrieval", []
        
    if not response_titles:
        return "无法找到相关章节", []

    # Parse IDs (Logic from article_retriever deepseek.py main function)
    raw_ids = [int(num) for num in re.findall(r'\d+', response_titles)]
    valid_ids = {item['id'] for item in titles}
    title_id_list = [tid for tid in raw_ids if tid in valid_ids]
    
    if not title_id_list:
        return "无法解析有效章节ID", []

    # Level 3: Context Retrieval
    contexts = []
    all_contents = []
    for tid in title_id_list:
        try:
            content = get_plain_text_by_title_id(tid)
            # Retry logic from article_retriever deepseek.py
            current_tid = tid
            while content is None:
                # Limit retry to avoid infinite loop, though original script just says "try next ID"
                # Let's try up to 5 next IDs
                current_tid += 1
                if current_tid > tid + 5: 
                    break
                content = get_plain_text_by_title_id(current_tid)
            
            if content:
                contexts.append(content)
                all_contents.extend(content)
        except Exception as e:
            print(f"Error fetching content for ID {tid}: {e}")
    
    if not contexts:
        return "无法获取章节内容", []

    # Level 4: Generation
    try:
        # The original function get_deepseek_response_rag takes title_id_list and does retrieval internally again
        # But we already retrieved contexts. However, to stay true to the script logic, we call it.
        # But wait, get_deepseek_response_rag does retrieval AND generation.
        # So we can just call it.
        answer = get_deepseek_response_rag(question, title_id_list)
    except Exception as e:
        print(f"Error in generation: {e}")
        answer = "生成回答失败"
        
    if not answer:
        answer = "生成回答失败"
        
    # Flatten contexts for RAGAS (list of strings)
    # The get_plain_text_by_title_id returns a list of strings (chunks) or None.
    # We flattened it into all_contents which is a list of strings.
    # But contexts list above is list of lists.
    flat_contexts = []
    for c_list in contexts:
        if isinstance(c_list, list):
            flat_contexts.extend(c_list)
        else:
            flat_contexts.append(str(c_list))
            
    return answer, flat_contexts

def main():
    print("Starting RAGAS Evaluation (Normal RAG)...")
    
    # Load dataset
    dataset_path = "dataset.json"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize RAG resources
    print("Initializing RAG resources...")
    articles = get_all_articles()
    if not articles:
        print("No articles found in database.")
        return
    articles_context = "\n".join(articles)


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
        ans, ctxs = run_rag_pipeline(q, articles_context)
        
        # Display Context and Answer as requested
        print("-" * 50)
        print("【参考上下文 (Contexts)】:")
        if not ctxs:
            print("无上下文")
        else:
            for idx, ctx in enumerate(ctxs):
                print(f"--- Context {idx+1} ---")
                print(ctx.strip())
        print("\n【最终回复 (Answer)】:")
        print(ans)
        print("-" * 50)
        
        # Ensure contexts is a list of strings
        if not ctxs:
            ctxs = [""] # Empty context
            
        questions.append(q)
        ground_truths.append(gt) 
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
