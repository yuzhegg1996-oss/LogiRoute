#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
高级文章检索系统
使用DeepSeek模型，结合文章和章节的摘要信息，提供更精准的检索功能
"""

import sys
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库函数
from database import get_all_articles_with_details, get_plain_text_by_title_id
from query_data import query_article_titles

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

if not DEEPSEEK_API_KEY:
    print("Warning: DEEPSEEK_API_KEY environment variable not set.")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
MODEL_NAME = "deepseek-chat"

def get_enhanced_deepseek_response_article(prompt, articles_details):
    """
    调用DeepSeek API获取模型响应，基于文章标题和摘要判断最相关文章
    
    Args:
        prompt (str): 用户的问题
        articles_details (list): 包含(id, title, summary)的元组列表
    
    Returns:
        str: 最相关文章的标题
    """
    # 构建包含摘要的文章上下文
    articles_context = []
    for id, title, summary in articles_details:
        summary_text = summary if summary else "暂无摘要"
        articles_context.append(f"文章标题: {title}\n文章摘要: {summary_text}\n-------------------")
    
    context_str = "\n".join(articles_context)
    
    # 构建系统提示词
    system_prompt = f"""
    你是一个智能文章检索助手。你的任务是根据用户提出的问题，在提供的文章列表中找出最相关的一篇文章。
    
    以下是候选文章列表，每项包含文章标题和内容摘要：
    {context_str}

    请仔细分析每篇文章的【文章摘要】，判断哪篇文章的核心内容与用户问题最匹配。
    只返回最相关的那一篇的文章标题。
    
    要求：
    1. 必须返回一个文章标题。
    2. 不要使用<thinking>标签或其他推理标签。
    3. 不要包含任何编号、解释或说明文字，只返回纯净的文章标题。
    """

    # 构建请求数据
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=False
        )
        response_text = response.choices[0].message.content.strip()
        
        # 处理可能的<think>标签
        if "<think" in response_text:
            if "</think>" in response_text:
                end_think_index = response_text.rfind("</think>") + len("</think>")
                final_response = response_text[end_think_index:].strip()
                if "\n" in final_response:
                    final_response = final_response.split("\n")[0].strip()
                return final_response
            else:
                lines = response_text.strip().split("\n")
                return lines[-1].strip() if lines else response_text.strip()
        else:
            if "\n" in response_text:
                return response_text.split("\n")[0].strip()
            return response_text.strip()
            
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        return None

def get_enhanced_deepseek_response_title(prompt, response_article):
    """
    调用DeepSeek API获取模型响应，基于章节标题和摘要判断问题可能出现在哪些章节
    
    Args:
        prompt (str): 用户的问题
        response_article (str): 文章标题
    
    Returns:
        tuple: (相关的章节ID列表字符串, 章节列表)
    """
    # 获取文章的所有标题 (id, title, level, summary)
    titles_json = query_article_titles(response_article)
    titles = json.loads(titles_json)
    
    if not titles:
        print(f"文章 '{response_article}' 没有找到任何章节")
        return None, None
        
    # 直接使用JSON格式作为上下文，更加简洁且利于模型结构化理解
    context_str = json.dumps(titles, ensure_ascii=False, indent=2)
    print(f"文章章节信息已构建，共 {len(titles)} 个章节")
    
    # 构建系统提示词
    system_prompt = f"""
    你是一个智能检索助手。
    任务：基于提供的JSON格式章节列表，找出与用户问题最相关的2个章节。
    
    候选章节数据（JSON格式）：
    {context_str}

    请分析上述JSON数据中每个章节的 'title' (标题) 和 'summary' (摘要)，判断其与用户问题的相关性。
    请输出一个标准的JSON对象，包含一个字段 "ids"，值为最相关章节的 'id' (数字ID) 列表。
    
    注意：
    1. 请不要返回为{context_str}中title值为"目录"的章节ID。
    2. 必须返回最相关的2个章节ID。
    3. 严禁输出任何解释性文字，只输出JSON对象。
    
    示例：{{"ids": [3496,3498]}}
    """

    # 打印提示词长度以便调试
    print(f"提示词长度: {len(system_prompt)} 字符")

    # 构建请求数据
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=False,
            response_format={"type": "json_object"}
        )
        response_text = response.choices[0].message.content.strip()
        
        # 处理可能的<think>标签
        final_text = response_text
        if "<think" in response_text:
            if "</think>" in response_text:
                end_think_index = response_text.rfind("</think>") + len("</think>")
                final_text = response_text[end_think_index:].strip()
            else:
                lines = response_text.strip().split("\n")
                final_text = lines[-1].strip() if lines else response_text.strip()
        
        # 尝试解析JSON
        try:
            # 清理Markdown代码块
            json_text = final_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            
            data_json = json.loads(json_text)
            if "ids" in data_json and isinstance(data_json["ids"], list):
                return ", ".join(map(str, data_json["ids"])), titles
        except Exception as e:
            print(f"JSON解析失败，尝试直接返回文本: {e}")
            
        return final_text, titles
            
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        return None, None

def get_deepseek_response_rag(prompt, response_title_ids):
    """
    调用DeepSeek API获取模型响应，基于文章正文内容回答用户问题
    
    Args:
        prompt (str): 用户的问题
        response_title_ids (list): 章节ID列表
    
    Returns:
        str: 模型的回答
    """
    all_contents = []
    for title_id in response_title_ids:
        # 获取正文内容
        contents = get_plain_text_by_title_id(title_id)
        
        # 简单的容错逻辑：如果当前ID没内容，尝试找下一个ID（仅尝试一次）
        if contents is None:
            print(f"标题ID {title_id} 对应的正文为None，尝试下一个ID...")
            contents = get_plain_text_by_title_id(title_id + 1)
            
        if contents:
            all_contents.append(contents)
        else:
            print(f"无法获取章节ID {title_id} (或 {title_id+1}) 的内容")
    
    if not all_contents:
        return "很抱歉，我无法获取到相关章节的具体内容，无法回答您的问题。"

    # 将正文内容列表转换为文本上下文
    content_context = "\n\n".join(all_contents)
    
    # 打印最终送给大模型的上下文信息
    print("\n" + "="*50)
    print("【DEBUG】送给大模型的上下文信息 (content_context):")
    print("-" * 50)
    print(content_context)
    print("="*50 + "\n")
    
    # 构建系统提示词
    system_prompt = f"""
    你是一个智能问答助手。你的任务是根据用户提出的问题和提供的文章正文内容，
    准确回答用户的问题。
    注意：
    1. 请直接回答问题，不要啰嗦。
    2. 严格基于提供的上下文回答，不要使用外部知识、如果上下文中没有答案，请直接说不知道
    3. 请基于提供的文章正文内容回答用户问题，如果内容中没有相关信息，请说明无法基于提供的内容回答问题。
    4. 回答要简洁明了，尽量用一句话高度概括。
    文章正文内容:
    {content_context}

    
    """

    # 构建请求数据
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        return None

def main():
    print("="*50)
    print("高级文章检索系统 (DeepSeek版)")
    print("="*50)
    
    # 1. 获取所有文章详情 (ID, Title, Summary)
    articles_details = get_all_articles_with_details()
    
    if not articles_details:
        print("数据库中没有文章，无法进行检索")
        return
        
    # user_question = "在柯泽正的论文中，系统持久化数据使用了哪种数据库？"
    user_question = "在汪啸宇设计的基于 SSM 框架的校园自动售货系统中，SSM 框架具体指哪三个技术栈？"
    print(f"用户问题: {user_question}")
    print("-" * 50)

    # 2. Level 1: 确定文章
    print("正在定位最相关文章...")
    response_article = get_enhanced_deepseek_response_article(user_question, articles_details)
    print(f"模型定位文章: {response_article}")
    
    if not response_article:
        print("无法定位相关文章。")
        return

    # 3. Level 2: 确定章节
    print("-" * 50)
    print("正在定位最相关章节...")
    response_titles, all_titles = get_enhanced_deepseek_response_title(user_question, response_article)
    print(f"模型定位章节ID: {response_titles}")
    
    if not response_titles:
        print("无法定位相关章节。")
        return

    try:
        # 清理和转换ID列表
        # 处理可能的非数字字符，只保留数字和逗号
        clean_ids = "".join([c for c in response_titles if c.isdigit() or c == ','])
        title_id_list = [int(num) for num in clean_ids.split(',') if num.strip()]
        print(f"解析后的章节ID列表: {title_id_list}")
        
        # 打印对应的章节标题
        if title_id_list and all_titles:
            print("\n对应的章节标题:")
            id_to_title = {t['id']: t['title'] for t in all_titles}
            for tid in title_id_list:
                title_name = id_to_title.get(tid, "未找到标题")
                print(f"- ID {tid}: {title_name}")
        
        if title_id_list:
            # 4. Level 3: 生成回答
            print("-" * 50)
            print("正在生成最终回答...")
            response_rag = get_deepseek_response_rag(user_question, title_id_list)
            
            # 注释掉最终回答的打印，只保留上面的上下文打印
            print("\n基于文章内容的回答:")
            print(response_rag)
            
    except ValueError as e:
        print(f"解析章节ID时出错: {e}")

if __name__ == "__main__":
    main()
