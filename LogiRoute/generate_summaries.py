#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
该脚本用于根据文章内容生成文章摘要。
"""
import sys
import requests
import json
import os
from openai import OpenAI
from mysql.connector import Error
from dotenv import load_dotenv
from database import (
    create_connection,
    get_all_articles,
    get_article_id_by_title,
    get_titles_by_article_id,
    get_plain_text_by_title_id
)

# 加载环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL_NAME = "deepseek-chat"

def get_deepseek_summary(text, context_type="section"):
    """
    调用DeepSeek API获取总结
    """
    if not text:
        return ""
        
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    if context_type == "section":
        system_prompt = f"""
        Role: 你是一位学术论文分析专家。
        Task: 请阅读下方提供的论文章节内容，生成一份结构化的章节摘要。
        Requirements:
        关键词: 提取 3-5 个反映本章核心技术的术语。
        内容简介: 用 150 字左右的内容概括本章讨论的核心观点、提出的方法或得出的实验结论。
        数据/公式点: 如果文中包含关键公式或实验数据，请务必在简介中提及。
        逻辑定位: 说明本章在全文逻辑结构中扮演的角色（如：背景引入、算法核心、结果验证）。
        待处理内容:
        {text}
        """
    else:
        system_prompt = f"""
        Role: 你是一位学术期刊主编。 
        Task: 我将提供一篇论文各章节的摘要汇总，以及可能包含作者信息的原文片段。请你据此撰写一份完整的全文综合总结。 
        Content Requirements:
        基本信息: 请优先从提供的“原文片段”中提取并标注：作者姓名、学号、班级、学校、指导老师。如果未找到，请标注“未在文中找到”。
        全文关键词: 总结全篇最核心的5-10个关键词。
        全文内容摘要: 撰写一段300字左右的摘要，需包含：研究背景、解决的痛点、核心算法逻辑、实验验证结果及最终贡献。
        各章节摘要汇总如下:
        {text}
        """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt}
            ],
            stream=False
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"调用DeepSeek API时出错: {e}")
        return None

# Ollama API配置 (已注释)
# OLLAMA_API_URL = "http://localhost:11434/api/generate"
# MODEL_NAME_OLLAMA = "qwen3:latest"

# def get_ollama_summary(text, context_type="section"):
#     """
#     调用Ollama API获取总结
#     
#     Args:
#         text (str): 需要总结的文本
#         context_type (str): 上下文类型 ("section" 或 "article")
#     
#     Returns:
#         str: 模型的总结结果
#     """
#     if not text:
#         return ""
# 
#     if context_type == "section":
#         system_prompt = "你是一个助手，请简要总结以下章节的内容，要求总结的内容尽量精简："
#     else:
#         system_prompt = "你是一个助手，请根据以下各章节的摘要，总结整篇文章的内容，要求总结的内容尽量精简："
# 
#     data = {
#         "model": MODEL_NAME_OLLAMA,
#         "prompt": f"{system_prompt}\n\n{text}",
#         "stream": False
#     }
# 
#     try:
#         response = requests.post(OLLAMA_API_URL, json=data, timeout=120)
#         response.raise_for_status()
#         
#         result = response.json()
#         response_text = result.get("response", "")
#         
#         # 处理 <think> 标签
#         if "<think" in response_text:
#             if "</think>" in response_text:
#                 end_think_index = response_text.rfind("</think>") + len("</think>")
#                 final_response = response_text[end_think_index:].strip()
#                 return final_response
#             else:
#                 lines = response_text.strip().split("\n")
#                 return lines[-1].strip() if lines else response_text.strip()
#         
#         return response_text.strip()
#         
#     except Exception as e:
#         print(f"调用Ollama API时出错: {e}")
#         return None

def update_title_summary(title_id, summary):
    """更新title表中的summary字段"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE title SET summary = %s WHERE id = %s",
                (summary, title_id)
            )
            connection.commit()
            return True
        except Error as e:
            print(f"更新章节摘要时出错: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

def update_article_summary(article_id, summary):
    """更新article表中的summary字段"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE article SET summary = %s WHERE id = %s",
                (summary, article_id)
            )
            connection.commit()
            return True
        except Error as e:
            print(f"更新文章摘要时出错: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

def get_title_summaries(article_id):
    """获取指定文章的所有章节摘要"""
    connection = create_connection()
    summaries = []
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT title, summary FROM title WHERE article_id = %s ORDER BY id",
                (article_id,)
            )
            results = cursor.fetchall()
            for title, summary in results:
                if summary:
                    summaries.append(f"章节标题: {title}\n摘要: {summary}")
        except Error as e:
            print(f"获取章节摘要列表时出错: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return summaries

def generate_summary_for_article(article_title):
    """
    为指定文章生成章节摘要和全文摘要
    """
    print(f"\n开始处理文章: {article_title}")
    article_id = get_article_id_by_title(article_title)
    
    if not article_id:
        print("未找到文章ID。")
        return False

    # 2. 获取文章的所有标题
    titles = get_titles_by_article_id(article_id)
    if not titles:
        print("该文章没有章节标题。")
        return False

    print(f"找到 {len(titles)} 个章节，开始生成章节摘要...")

    # 3. 遍历标题，生成并保存摘要
    for title_row in titles:
        title_id = title_row[0]
        title_text = title_row[1]
        
        print(f"\n正在处理章节: {title_text}")
        
        # 获取正文内容
        content = get_plain_text_by_title_id(title_id)
        if not content:
            print(f"  - 章节 '{title_text}' 没有正文内容，跳过。")
            continue
            
        # 生成摘要
        print("  - 正在调用模型生成摘要...")
        summary = get_deepseek_summary(content, context_type="section")
        
        if summary:
            # 保存摘要
            if update_title_summary(title_id, summary):
                print("  - 摘要已保存。")
                print(f"  - 摘要预览: {summary[:50]}...")
            else:
                print("  - 保存摘要失败。")
        else:
            print("  - 模型生成摘要失败。")

    # 4. 生成整篇文章的摘要
    print("\n正在生成整篇文章的摘要...")
    section_summaries = get_title_summaries(article_id)
    
    if not section_summaries:
        print("没有可用的章节摘要来生成文章总结。")
        return False

    # --- 新增逻辑：扫描全文以获取作者及元数据信息 ---
    print("正在扫描全文以获取作者及元数据信息...")
    metadata_content_list = []
    found_metadata = False
    # 常见的元数据关键词
    metadata_keywords = ["作者", "姓名", "学号", "班级", "学校", "指导老师", "导师", "学院", "专业"]
    
    # 遍历章节 (titles 变量在前面已获取)
    # 为了避免上下文过长，且元数据通常在前几个章节，我们主要关注前5个章节，或者直到找到足够的信息
    for i, title_row in enumerate(titles):
        # 限制只扫描前10个章节，通常元数据不会在很后面
        if i >= 10: 
            break
            
        t_id = title_row[0]
        t_text = title_row[1]
        
        # 获取正文
        t_content = get_plain_text_by_title_id(t_id)
        if not t_content:
            continue
            
        # 检查是否包含关键词
        if any(kw in t_content for kw in metadata_keywords):
             print(f"  - 在章节 '{t_text}' 中发现潜在的元数据信息，将纳入全文摘要生成的上下文中。")
             metadata_content_list.append(f"--- 章节 '{t_text}' 原文片段 (可能包含作者信息) ---\n{t_content}")
             found_metadata = True
             
             # 如果已经收集了3个片段，就停止，避免上下文过长
             if len(metadata_content_list) >= 3:
                 print("  - 已提取足够的元数据参考片段，停止继续扫描。")
                 break
    
    if not found_metadata:
        print("【提示】在文章的前几个章节中未找到明显的作者、学号或指导老师等信息。生成的摘要可能缺少这些基本信息。")
    
    # 拼接上下文
    combined_input = ""
    if metadata_content_list:
        combined_input += "\n\n".join(metadata_content_list) + "\n\n"
    
    combined_input += "--- 各章节摘要汇总 ---\n" + "\n\n".join(section_summaries)

    article_summary = get_deepseek_summary(combined_input, context_type="article")

    if article_summary:
        if update_article_summary(article_id, article_summary):
            print("\n文章摘要已保存成功！")
            print(f"文章摘要预览:\n{article_summary}")
            return True
        else:
            print("\n保存文章摘要失败。")
            return False
    else:
        print("\n模型生成文章摘要失败。")
        return False

def main():
    # 1. 获取所有文章并让用户选择
    articles_details = []
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT title, summary FROM article")
            articles_details = cursor.fetchall()
        except Error as e:
            print(f"获取文章列表时出错: {e}")
            return
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    if not articles_details:
        print("数据库中没有文章。")
        return

    print("可用文章列表:")
    for i, (title, summary) in enumerate(articles_details):
        status = "[已生成摘要]" if summary else "[未生成摘要]"
        print(f"{i + 1}. {title} {status}")

    while True:
        try:
            print("\n操作选项:")
            print("输入数字: 选择单篇文章生成摘要")
            print("输入 batch: 批量为所有[未生成摘要]的文章生成摘要")
            print("输入 q: 退出")
            choice = input("请输入指令: ").strip()
            
            if choice.lower() == 'q':
                return
            
            elif choice.lower() == 'batch':
                # 批量处理逻辑
                pending_articles = [t for t, s in articles_details if not s]
                if not pending_articles:
                    print("所有文章都已生成摘要，无需批量处理。")
                    continue
                
                print(f"\n准备批量处理 {len(pending_articles)} 篇文章...")
                for i, title in enumerate(pending_articles, 1):
                    print(f"\n{'='*20} 正在处理 [{i}/{len(pending_articles)}] {title} {'='*20}")
                    generate_summary_for_article(title)
                print("\n批量处理完成！")
                
            else:
                # 单个文章处理逻辑
                idx = int(choice) - 1
                if 0 <= idx < len(articles_details):
                    selected_article_title, existing_summary = articles_details[idx]
                    
                    # 检查是否已生成摘要
                    if existing_summary:
                        print(f"\n文章 '{selected_article_title}' 已经包含摘要。")
                        confirm = input("是否重新生成摘要？这将覆盖原有摘要 (y/n): ")
                        if confirm.lower() != 'y':
                            print("操作已取消。")
                            continue
                        
                        # 清空旧摘要
                        article_id = get_article_id_by_title(selected_article_title)
                        if article_id:
                            update_article_summary(article_id, None)
                            # 同时清空所有章节的摘要
                            connection = create_connection()
                            if connection:
                                try:
                                    cursor = connection.cursor()
                                    cursor.execute("UPDATE title SET summary = NULL WHERE article_id = %s", (article_id,))
                                    connection.commit()
                                    print("旧摘要已清空。")
                                except Error as e:
                                    print(f"清空旧摘要时出错: {e}")
                                finally:
                                    if connection.is_connected():
                                        cursor.close()
                                        connection.close()
                    
                    generate_summary_for_article(selected_article_title)
                else:
                    print("无效的文章编号，请重试。")
        except ValueError:
            print("请输入有效的数字或指令。")

if __name__ == "__main__":
    main()
