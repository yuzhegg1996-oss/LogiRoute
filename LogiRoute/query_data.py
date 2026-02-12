#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查询文档数据的脚本
通过文章题目查询所有标题，然后通过标题查询正文内容
"""

import sys
import os
import json
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_plain_text_by_title, 
    get_titles_by_article, 
    get_all_articles_with_details,
    get_plain_text_by_title_id
)

def list_articles_with_summary():
    """
    列出所有文章及其摘要
    """
    print("=" * 50)
    print("文章列表及摘要")
    print("=" * 50)
    
    articles = get_all_articles_with_details()
    
    if not articles:
        print("数据库中暂无文章")
        return
    
    for i, (id, title, summary) in enumerate(articles, 1):
        print(f"{i}. [ID:{id}] {title}")
        print(f"   摘要: {summary if summary else '暂无摘要'}")
        print("-" * 30)

def query_article_titles(article_title):
    """
    根据文章题目查询该文章中的所有标题
    
    Args:
        article_title (str): 文章题目
    
    Returns:
        str: JSON格式的标题列表，每个元素是包含id, title, level, summary的字典
    """
    print(f"正在查询文章 '{article_title}' 的所有标题...")
    titles_with_id = get_titles_by_article(article_title)
    
    if not titles_with_id:
        print(f"未找到文章 '{article_title}' 的任何标题")
        return json.dumps([], ensure_ascii=False)
    
    # 将元组列表转换为字典列表
    titles_list = []
    for id, title, level, summary in titles_with_id:
        titles_list.append({
            "id": id,
            "title": title,
            "level": level,
            "summary": summary
        })
    
    return json.dumps(titles_list, ensure_ascii=False, indent=4)

def query_title_content(title_name):
    """
    根据标题名称查询该标题下的正文内容
    
    Args:
        title_name (str): 标题名称
    
    Returns:
        tuple: (正文内容, 摘要)
    """
    print(f"\n正在查询标题 '{title_name}' 下的正文内容...")
    result = get_plain_text_by_title(title_name)
    
    if not result:
        print(f"未找到标题 '{title_name}' 下的正文内容")
        return None
    
    content, summary = result
    print(f"正文内容预览: {content[:100] if content else '无内容'}...")
    print(f"摘要: {summary if summary else '无摘要'}")
    
    return result

def query_article_and_content(article_title):
    """
    查询文章的所有标题及其对应的正文内容
    
    Args:
        article_title (str): 文章题目
    """
    print("=" * 50)
    print(f"查询文章: {article_title}")
    print("=" * 50)
    
    # 查询文章的所有标题
    titles_json = query_article_titles(article_title)
    titles = json.loads(titles_json)
    
    if not titles:
        return
    
    # 查询每个标题下的正文内容
    for item in titles:
        title = item['title']
        query_title_content(title)
        print("-" * 30)

def main():
    """主函数"""
    # 列出所有文章及其摘要
    # list_articles_with_summary()

    # 示例文章标题，请根据实际情况修改
    # article_title = "基于OpenCV的实时物体尺寸测量系统"
    article_title = "基于 WebSocket 的即时通讯软件设计与实现"
    # title_name="虚拟现实技术课程内容与特征分析"
    # 查询文章及其内容
    titles=query_article_titles(article_title)
    print(titles)
    # content=get_plain_text_by_title_id(168)
    # print(content)
    # contents=query_title_content(title_name)
    # print(contents)
    
    # 也可以单独查询特定标题的正文
    # print("\n" + "=" * 50)
    # print("单独查询标题正文示例:")
    # print("=" * 50)
    # query_title_content("摘要")

if __name__ == "__main__":
    main()