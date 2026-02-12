#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DOCX文档解析并存入数据库的脚本

该脚本将解析DOCX文档，并将内容按照以下规则存入数据库：
1. 字典content_dict中的第一个key作为文章题目存入article表
2. 后续的每个key作为文章标题存入title表
3. 每个key对应的value（正文内容）存入plain_text表
"""

import os
import sys
from typing import Dict, List

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入DOCX解析器
from docx_parser import RAGFlowDocxParser

# 导入数据库操作函数
from database import (
    create_database_and_tables,
    insert_article,
    insert_title,
    insert_plain_text
)

def parse_docx_to_dict(file_path: str) -> Dict[str, List[str]]:
    """
    解析DOCX文档并构建标题与段落内容的映射字典
    
    Args:
        file_path (str): DOCX文件路径
        
    Returns:
        Dict[str, List[str]]: 标题与段落内容的映射字典
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件 {file_path} 不存在")
    
    # 读取文件内容
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    file_name = os.path.basename(file_path)
    
    # 创建解析器并解析文档
    parser = RAGFlowDocxParser()
    doc_content = parser(file_name, binary=file_content)
    
    # 打印解析结果用于调试
    print("解析结果详情:")
    print("-" * 30)
    for i, (content, content_type) in enumerate(doc_content):
        print(f"{i+1:3d}. 类型: {content_type:15s} 内容: {content[:50]}{'...' if len(content) > 50 else ''}")
    print("-" * 30)
    
    # 创建标题与段落内容的映射字典
    content_dict = {}
    current_heading = None
    current_paragraphs = []
    
    # 遍历解析结果，构建标题与段落的映射关系
    for content, content_type in doc_content:
        if content_type.startswith("heading_"):
            # 如果遇到新的标题，将之前收集的段落保存到字典中
            if current_heading is not None:
                content_dict[current_heading] = current_paragraphs
            
            # 更新当前标题，并重置段落列表
            current_heading = content
            current_paragraphs = []
            print(f"发现标题: {content}")
        elif content_type.startswith("paragraph_"):
            # 如果当前有标题，则将段落添加到当前标题下
            if current_heading is not None:
                current_paragraphs.append(content)
            # 如果还没有遇到标题，将段落添加到一个特殊键下（如"无标题段落"）
            else:
                if "无标题段落" not in content_dict:
                    content_dict["无标题段落"] = []
                content_dict["无标题段落"].append(content)
        elif content_type.startswith("table_"):
            # 表格内容可以单独处理或添加到当前标题下
            if current_heading is not None:
                current_paragraphs.append(f"[表格内容]: {content}")
            else:
                if "无标题段落" not in content_dict:
                    content_dict["无标题段落"] = []
                content_dict["无标题段落"].append(f"[表格内容]: {content}")
        elif content_type == "error":
            print(f"解析错误: {content}")
    
    # 保存最后一个标题下的段落
    if current_heading is not None:
        content_dict[current_heading] = current_paragraphs
    
    return content_dict

def save_dict_to_database(content_dict: Dict[str, List[str]], docx_file_path: str) -> bool:
    """
    将解析后的字典内容存入数据库
    
    Args:
        content_dict (Dict[str, List[str]]): 标题与段落内容的映射字典
        docx_file_path (str): 原始DOCX文件路径
        
    Returns:
        bool: 是否成功存入数据库
    """
    try:
        # 获取字典中的所有键
        keys = list(content_dict.keys())
        
        if not keys:
            print("文档内容为空，无法存入数据库")
            return False
        
        # 第一个键作为文章题目
        article_title = keys[0]
        print(f"文章题目: {article_title}")
        
        # 插入文章并获取文章ID
        article_id = insert_article(article_title)
        if not article_id:
            print("插入文章失败")
            return False
        
        print(f"文章ID: {article_id}")
        
        # 如果第一个键是"无标题段落"，说明文档没有标题，需要特殊处理
        start_index = 0
        if article_title == "无标题段落":
            # 将"无标题段落"的内容作为文章正文处理
            paragraphs = content_dict[article_title]
            if paragraphs:
                text_content = "\n\n".join(paragraphs)
                # 为无标题文章创建一个标题记录
                title_id = insert_title(article_id, "文章正文", 1)
                if title_id:
                    text_id = insert_plain_text(title_id, text_content)
                    if text_id:
                        print(f"无标题文章正文插入成功，标题ID: {title_id}, 正文ID: {text_id}")
                    else:
                        print("插入无标题文章正文失败")
                else:
                    print("插入无标题文章标题失败")
            start_index = 1  # 跳过"无标题段落"
        
        # 处理后续的标题和正文内容
        # 标题级别从1开始（如果已经处理了无标题段落，则从2开始）
        level = 1 if article_title != "无标题段落" else 2
        
        for i in range(start_index, len(keys)):
            key = keys[i]
            
            # 如果文章题目就是"无标题段落"，则跳过它
            if key == article_title and article_title == "无标题段落":
                continue
            
            # 插入标题并获取标题ID
            title_id = insert_title(article_id, key, level=1)
            if not title_id:
                print(f"插入标题 '{key}' 失败")
                continue
            
            print(f"标题 '{key}' 插入成功，标题ID: {title_id}")
            
            # 将该标题下的所有段落内容合并为一个字符串
            paragraphs = content_dict[key]
            if paragraphs:
                # 使用两个换行符分隔段落
                text_content = "\n\n".join(paragraphs)
                
                # 插入正文内容
                text_id = insert_plain_text(title_id, text_content)
                if text_id:
                    print(f"正文内容插入成功，正文ID: {text_id}")
                else:
                    print(f"插入标题 '{key}' 的正文内容失败")
            else:
                print(f"标题 '{key}' 下无正文内容")
            
            # 更新标题级别
            # level = 1
        
        print("文档内容已成功存入数据库")
        return True
        
    except Exception as e:
        print(f"存入数据库时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    # 创建数据库和表（如果尚未创建）
    create_database_and_tables()
    
    # DOCX文件路径
    docx_path = "C:\\Users\\woshi\\OneDrive\\桌面\\毕业设计论文何兴翔.docx"
    
    # 检查文件是否存在
    if not os.path.exists(docx_path):
        print(f"错误: 文件 {docx_path} 不存在")
        print("请确保文件路径正确，并且文件未被其他程序占用")
        return
    
    try:
        # 解析DOCX文档并构建字典
        print("开始解析DOCX文档...")
        content_dict = parse_docx_to_dict(docx_path)
        print("DOCX文档解析完成")
        
        # 打印解析结果概览
        print("\n解析结果概览:")
        print("-" * 30)
        for i, (heading, paragraphs) in enumerate(content_dict.items()):
            print(f"{i+1}. 标题: {heading}")
            print(f"   段落数量: {len(paragraphs)}")
        
        # 将内容存入数据库
        print("\n开始将内容存入数据库...")
        success = save_dict_to_database(content_dict, docx_path)
        
        if success:
            print("文档内容已成功存入数据库")
        else:
            print("存入数据库失败")
            
    except PermissionError:
        print(f"权限错误: 无法访问文件 {docx_path}")
        print("请确保文件未被其他程序占用（如Word），然后重新运行脚本")
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()