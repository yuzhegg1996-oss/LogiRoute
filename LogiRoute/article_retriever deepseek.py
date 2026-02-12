#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文章检索系统
使用DeepSeek API，根据用户问题和数据库中的文章标题，找出最相关文章
"""

import json
import os
import re
import sys
from openai import OpenAI

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入查询文章的函数
from database import get_all_articles, get_plain_text_by_title, get_plain_text_by_title_id
from query_data import query_title_content, query_article_titles

# DeepSeek API配置
DEEPSEEK_API_KEY = "sk-bfcb1cfdb6c74b869263a3bd4d974b1b"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

def get_deepseek_response_article(prompt, articles_context):
    """
    调用DeepSeek API获取模型响应
    
    Args:
        prompt (str): 用户的问题
        articles_context (str): 文章标题作为上下文
    
    Returns:
        str: 模型的响应结果
    """
    # 构建系统提示词
    system_prompt = f"""
    你是一个智能文章检索助手。你的任务是根据用户提出的问题和提供的文章标题列表，
    判断这个问题最有可能出现在哪一篇文章中。

    可参考的文章标题列表:
    {articles_context}

    请分析用户问题与文章标题的相关性，只返回最相关的一篇文章标题。
    并且你必须返回一个文章标题。
    返回的标题内容要与{articles_context}中的标题内容完全一致，不能有任何差异。
    不要使用<thinking>标签或其他推理标签，
    不要包含任何编号、解释或说明文字，只返回纯净的文章标题
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # 如果响应中包含<thinking>标签，只提取标签外的内容
        if "<think" in response_text:
            # 提取最终答案，去除思考过程
            if "</think>" in response_text:
                # 找到最后一个</think>标签的位置
                end_think_index = response_text.rfind("</think>") + len("</think>")
                # 提取</think>标签后的内容作为最终答案
                final_response = response_text[end_think_index:].strip()
                # 如果还有换行符，提取第一行作为答案
                if "\n" in final_response:
                    final_response = final_response.split("\n")[0].strip()
                return final_response
            else:
                # 如果没有找到结束标签，尝试提取最后一行
                lines = response_text.strip().split("\n")
                return lines[-1].strip() if lines else response_text.strip()
        else:
            # 没有<thinking>标签，直接返回响应内容
            # 如果有多行，只返回第一行
            if "\n" in response_text:
                return response_text.split("\n")[0].strip()
            return response_text.strip()
            
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        return None

def get_deepseek_response_title(prompt, response_article):
    """
    调用DeepSeek API获取模型响应，判断问题可能出现在文章的哪些章节中
    
    Args:
        prompt (str): 用户的问题
        response_article (str): 文章标题
    
    Returns:
        str: 模型的响应结果，包含可能的章节标题
    """
    # 获取文章的所有标题
    full_titles = json.loads(query_article_titles(response_article))
    titles = [{"id": item["id"], "title": item["title"]} for item in full_titles]
    # print(f"文章章节标题列表: {titles}")
    
    # 构建系统提示词
    system_prompt = f"""
    你是一个智能文章检索助手。你的任务是根据用户提出的问题和提供的文章章节标题列表，
    判断这个问题最有可能出现在哪些章节中。

    文章章节标题列表:
    {titles}

    请分析用户问题与章节标题的相关性，返回最相关的3个章节的ID。
    不要使用<thinking>标签或其他推理标签，
    至少要返回3个章节ID。
    不要包含任何编号、解释或说明文字，只返回章节ID数字，多个ID用逗号分隔
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # 如果响应中包含<thinking>标签，只提取标签外的内容
        if "<think" in response_text:
            # 提取最终答案，去除思考过程
            if "</think>" in response_text:
                # 找到最后一个</think>标签的位置
                end_think_index = response_text.rfind("</think>") + len("</think>")
                # 提取</think>标签后的内容作为最终答案
                final_response = response_text[end_think_index:].strip()
                # 如果还有换行符，提取第一行作为答案
                if "\n" in final_response:
                    final_response = final_response.split("\n")[0].strip()
                return final_response
            else:
                # 如果没有找到结束标签，尝试提取最后一行
                lines = response_text.strip().split("\n")
                return lines[-1].strip() if lines else response_text.strip()
        else:
            # 没有<thinking>标签，直接返回响应内容
            # 如果有多行，只返回第一行
            if "\n" in response_text:
                return response_text.split("\n")[0].strip()
            return response_text.strip()
            
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        return None

def get_deepseek_response_rag(prompt, response_title):
    """
    调用DeepSeek API获取模型响应，基于文章正文内容回答用户问题
    
    Args:
        prompt (str): 用户的问题
        response_title (str): 章节标题，可能包含多个标题，用逗号分隔
    
    Returns:
        str: 模型的响应结果，基于文章内容回答问题
    """
    # 根据标题数量调用query_title_content方法
    all_contents = []
    for title_id in response_title:
        contents = get_plain_text_by_title_id(title_id)
        # 如果获取到的正文为None，则对title_id加1并继续查询，直到获取到非None的正文内容
        while contents is None:
            print(f"标题ID {title_id} 对应的正文为None，尝试下一个ID...")
            title_id += 1
            contents = get_plain_text_by_title_id(title_id)
        # print(contents)
        if contents:
            all_contents.extend(contents)
    
    # 将正文内容列表转换为文本上下文
    content_context = "\n".join([content for content, in all_contents]) if all_contents else "无正文内容"
    
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

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        response_text = response.choices[0].message.content.strip()
        return response_text
            
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        return None

def main(): 
    # 获取所有文章标题
    articles = get_all_articles()
    
    if not articles:
        print("数据库中没有文章，无法进行检索")
        return
    # 将文章标题转换为文本上下文（不带编号）
    articles_context = "\n".join(articles)
    
    user_question = "在滕国坤设计的停车场管理系统中，车辆信息表的字段结构是怎样的？"
    # user_question="在张扬编写的《基于数据挖掘的个性化影视作品推荐系统设计与实现》中，该系统主要采用什么服务器来防止兼容性及稳定性问题？"
    
    print(f"正在处理问题: {user_question}")
    
    response_article = get_deepseek_response_article(user_question, articles_context)
    print(f"模型定位到的文章: {response_article}")
    
    # 使用新添加的方法获取可能的章节标题
    if response_article:
        # 【新增】熔断机制：先检查该文章是否有章节
        titles_json = query_article_titles(response_article)
        titles = json.loads(titles_json)
        if not titles:
            print(f"警告: 找到文章 '{response_article}' 但该文章没有任何章节信息。")
            print("可能是文章导入不完整或数据库中缺少title记录。流程结束。")
            return

        response_titles = get_deepseek_response_title(user_question, response_article)
        print(f"问题可能出现在以下章节: {response_titles}")
        
        # 【新增】容错解析：使用正则提取数字ID
        raw_ids = [int(num) for num in re.findall(r'\d+', response_titles)]
        valid_ids = {item['id'] for item in titles}
        title_id_list = [tid for tid in raw_ids if tid in valid_ids]
        
        print(f"提取到的章节ID列表: {title_id_list}")
        
        # 调用get_deepseek_response_rag方法，基于章节内容回答问题
        if title_id_list:
            response_rag = get_deepseek_response_rag(user_question, title_id_list)
            print(f"基于文章内容的回答: {response_rag}")
        else:
            print("未能提取到有效的章节ID，无法进行正文检索。")
      
if __name__ == "__main__":
    main()
