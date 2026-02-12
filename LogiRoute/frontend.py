#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
前端界面用于辅助数据库录入
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入database.py中的函数
from database import (
    create_database_and_tables,
    insert_article,
    insert_title,
    insert_plain_text,
    delete_article_by_title,
    get_all_articles,
    get_article_id_by_title,
    get_titles_by_article_id,
    delete_title_by_id,
    update_title,
    update_plain_text_by_title_id,
    get_titles_by_article,
    get_all_articles_with_details
)

def display_menu():
    """显示主菜单"""
    print("\n" + "="*50)
    print("文档数据库管理系统")
    print("="*50)
    print("1. 创建数据库和表")
    print("2. 录入新文章")
    print("3. 查看所有文章")
    print("4. 管理文章内容")
    print("5. 删除文章")
    print("6. 显示文章内容")
    print("7. 查看文章摘要")
    print("0. 退出")
    print("="*50)

def create_tables():
    """创建数据库和表"""
    print("正在创建数据库和表...")
    create_database_and_tables()
    print("数据库和表创建完成!")

def input_article():
    """录入新文章"""
    print("\n录入新文章")
    print("-"*30)
    
    article_title = input("请输入文章题目: ").strip()
    # 严格去除所有空白字符
    article_title = article_title.replace(" ", "").replace("\t", "").replace("\r", "").replace("\n", "")
    if not article_title:
        print("文章题目不能为空!")
        return
    
    # 检查文章是否已存在
    article_id = get_article_id_by_title(article_title)
    if article_id:
        print(f"文章 '{article_title}' 已存在!")
        return
    
    # 插入文章
    article_id = insert_article(article_title)
    if not article_id:
        print("文章录入失败!")
        return
    
    print(f"文章 '{article_title}' 录入成功!")
    
    # 询问是否继续录入标题
    while True:
        choice = input("\n是否现在录入标题? (y/n): ").strip().lower()
        if choice == 'y':
            input_titles(article_id, article_title)
            break
        elif choice == 'n':
            break
        else:
            print("请输入 y 或 n")

def input_titles(article_id, article_title):
    """录入文章标题和正文"""
    print(f"\n为文章 '{article_title}' 录入标题")
    print("-"*30)
    
    while True:
        print("\n录入标题:")
        title = input("标题名称 (输入 'q' 返回上级菜单): ").strip()
        if title.lower() == 'q':
            break
        
        if not title:
            print("标题名称不能为空!")
            continue
        
        # 选择标题级别
        while True:
            try:
                level = int(input("标题级别 (1-4): "))
                if 1 <= level <= 4:
                    break
                else:
                    print("标题级别必须在 1-4 之间!")
            except ValueError:
                print("请输入有效的数字!")
        
        # 插入标题
        title_id = insert_title(article_id, title, level)
        if not title_id:
            print("标题录入失败!")
            continue
        
        print(f"标题 '{title}' 录入成功!")
        
        # 录入正文
        print("\n录入正文 (可为空，直接按回车跳过):")
        content = input("正文内容: ")
        
        # 插入正文
        text_id = insert_plain_text(title_id, content)
        if text_id:
            print("正文录入成功!")
        else:
            print("正文录入失败!")

def view_all_articles():
    """查看所有文章"""
    print("\n所有文章:")
    print("-"*30)
    
    articles = get_all_articles()
    if not articles:
        print("暂无文章")
        return
    
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article}")

def manage_article():
    """管理文章内容"""
    print("\n管理文章内容")
    print("-"*30)
    
    articles = get_all_articles()
    if not articles:
        print("暂无文章可管理")
        return
    
    print("请选择文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article}")
    
    try:
        choice = int(input("请输入文章编号 (0 返回上级菜单): "))
        if choice == 0:
            return
        
        if 1 <= choice <= len(articles):
            article_title = articles[choice-1]
            article_id = get_article_id_by_title(article_title)
            
            if article_id:
                manage_article_content(article_id, article_title)
            else:
                print("获取文章ID失败!")
        else:
            print("无效的文章编号!")
    except ValueError:
        print("请输入有效的数字!")

def manage_article_content(article_id, article_title):
    """管理文章内容（标题和正文）"""
    while True:
        print(f"\n管理文章 '{article_title}' 的内容")
        print("-"*40)
        
        # 显示文章的所有标题
        titles = get_titles_by_article_id(article_id)
        if not titles:
            print("该文章暂无标题")
        else:
            print("标题列表:")
            for i, (title_id, title, level, _) in enumerate(titles, 1):
                print(f"{i}. [{level}级] {title}")
        
        print("\n操作选项:")
        print("1. 添加新标题")
        print("2. 修改标题")
        print("3. 删除标题")
        print("4. 修改标题正文")
        print("0. 返回上级菜单")
        
        try:
            choice = int(input("请选择操作: "))
            if choice == 0:
                break
            elif choice == 1:
                input_titles(article_id, article_title)
            elif choice == 2:
                modify_title(titles)
            elif choice == 3:
                delete_title(titles)
            elif choice == 4:
                modify_title_content(titles)
            else:
                print("无效的操作选项!")
        except ValueError:
            print("请输入有效的数字!")

def modify_title(titles):
    """修改标题"""
    if not titles:
        print("暂无标题可修改")
        return
    
    try:
        choice = int(input("请选择要修改的标题编号: "))
        if 1 <= choice <= len(titles):
            title_id, old_title, old_level, _ = titles[choice-1]
            
            print(f"当前标题: {old_title} (级别: {old_level})")
            new_title = input("新标题名称 (直接回车保持不变): ").strip()
            if not new_title:
                new_title = old_title
            
            while True:
                try:
                    new_level_input = input("新标题级别 (1-4, 直接回车保持不变): ").strip()
                    if not new_level_input:
                        new_level = old_level
                        break
                    new_level = int(new_level_input)
                    if 1 <= new_level <= 4:
                        break
                    else:
                        print("标题级别必须在 1-4 之间!")
                except ValueError:
                    print("请输入有效的数字!")
            
            if update_title(title_id, new_title, new_level):
                print("标题更新成功!")
            else:
                print("标题更新失败!")
        else:
            print("无效的标题编号!")
    except ValueError:
        print("请输入有效的数字!")

def delete_title(titles):
    """删除标题"""
    if not titles:
        print("暂无标题可删除")
        return
    
    try:
        choice = int(input("请选择要删除的标题编号: "))
        if 1 <= choice <= len(titles):
            title_id, title, level, _ = titles[choice-1]
            
            confirm = input(f"确定要删除标题 '{title}' 吗? 这将同时删除其正文内容 (y/n): ").strip().lower()
            if confirm == 'y':
                if delete_title_by_id(title_id):
                    print("标题删除成功!")
                else:
                    print("标题删除失败!")
            else:
                print("取消删除操作")
        else:
            print("无效的标题编号!")
    except ValueError:
        print("请输入有效的数字!")

def modify_title_content(titles):
    """修改标题正文"""
    if not titles:
        print("暂无标题可修改正文")
        return
    
    try:
        choice = int(input("请选择要修改正文的标题编号: "))
        if 1 <= choice <= len(titles):
            title_id, title, level, _ = titles[choice-1]
            
            print(f"修改标题 '{title}' 的正文")
            new_content = input("新正文内容 (可为空): ")
            
            if update_plain_text_by_title_id(title_id, new_content):
                print("正文更新成功!")
            else:
                print("正文更新失败!")
        else:
            print("无效的标题编号!")
    except ValueError:
        print("请输入有效的数字!")

def delete_article():
    """删除文章 (支持批量)"""
    print("\n删除文章")
    print("-"*30)
    
    articles = get_all_articles()
    if not articles:
        print("暂无文章可删除")
        return
    
    print("请选择要删除的文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article}")
    
    print("\n请输入文章编号 (支持多选，用逗号分隔，例如 1,3,5; 输入 0 返回): ")
    user_input = input("编号: ").strip()
    
    if user_input == '0':
        return

    try:
        # 支持中文逗号和英文逗号
        user_input = user_input.replace('，', ',')
        choices_str = user_input.split(',')
        choices = []
        for s in choices_str:
            s = s.strip()
            if s:
                choices.append(int(s))
        
        valid_articles = []
        for choice in choices:
            if 1 <= choice <= len(articles):
                valid_articles.append(articles[choice-1])
            else:
                print(f"警告: 编号 {choice} 无效，已忽略")
        
        if not valid_articles:
            print("未选择有效的文章编号!")
            return

        print(f"\n即将删除以下 {len(valid_articles)} 篇文章:")
        for article in valid_articles:
            print(f"- {article}")
            
        confirm = input(f"\n确定要删除以上文章吗? 这将同时删除其所有标题和正文内容 (y/n): ").strip().lower()
        if confirm == 'y':
            success_count = 0
            for article_title in valid_articles:
                if delete_article_by_title(article_title):
                    print(f"文章 '{article_title}' 删除成功!")
                    success_count += 1
                else:
                    print(f"文章 '{article_title}' 删除失败!")
            print(f"\n共成功删除 {success_count} 篇文章")
        else:
            print("取消删除操作")
            
    except ValueError:
        print("输入格式错误! 请输入有效的数字。")


def display_article_content():
    """显示文章内容"""
    print("\n显示文章内容")
    print("-"*30)
    
    articles = get_all_articles()
    if not articles:
        print("暂无文章可显示")
        return
    
    print("请选择要查看的文章:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article}")
    
    try:
        choice = int(input("请输入文章编号 (0 返回上级菜单): "))
        if choice == 0:
            return
        
        if 1 <= choice <= len(articles):
            article_title = articles[choice-1]
            article_id = get_article_id_by_title(article_title)
            
            if article_id:
                # 获取文章的所有标题和正文
                titles = get_titles_by_article_id(article_id)
                if not titles:
                    print(f"文章 '{article_title}' 暂无内容")
                    return
                
                print(f"\n文章: {article_title}")
                print("="*50)
                
                # 显示每个标题及其正文
                for i, (title_id, title, level, _) in enumerate(titles, 1):
                    # 根据标题级别添加缩进
                    indent = "  " * (level - 1)
                    
                    # 获取标题对应的正文
                    try:
                        from database import get_plain_text_by_title_id
                        content = get_plain_text_by_title_id(title_id)
                    except ImportError:
                        content = "无法获取正文内容"
                    
                    print(f"{indent}[{level}级] {title}")
                    if content:
                        # 对正文进行适当的格式化
                        formatted_content = "\n".join([f"{indent}  {line}" for line in content.split("\n") if line.strip()])
                        print(f"{formatted_content}")
                    print()  # 添加空行分隔
            else:
                print("获取文章ID失败!")
        else:
            print("无效的文章编号!")
    except ValueError:
        print("请输入有效的数字!")


def view_article_summaries():
    """查看文章及其章节的摘要"""
    print("\n查看文章摘要")
    print("-" * 30)

    # 获取所有文章详情 (id, title, summary)
    articles = get_all_articles_with_details()
    if not articles:
        print("暂无文章")
        return

    print("请选择文章:")
    # 格式化输出文章列表，带摘要状态标记
    for i, (art_id, art_title, art_summary) in enumerate(articles, 1):
        status = "[已生成摘要]" if art_summary and art_summary.strip() else "[未生成摘要]"
        print(f"{i}. {art_title} {status}")

    try:
        choice = int(input("\n请输入文章编号 (0 返回上级菜单): "))
        if choice == 0:
            return

        if 1 <= choice <= len(articles):
            article_id, article_title, article_summary = articles[choice - 1]

            print(f"\n{'='*20} 文章摘要详情 {'='*20}")
            print(f"文章标题: {article_title}")
            print(f"摘要状态: {'已生成' if article_summary and article_summary.strip() else '未生成'}")
            
            if article_summary and article_summary.strip():
                print("-" * 50)
                print("【文章总摘要】")
                print(article_summary.strip())
                print("-" * 50)
            else:
                print("\n(该文章暂无总摘要)")

            # 获取章节标题和摘要
            titles = get_titles_by_article_id(article_id)
            if not titles:
                print("\n该文章暂无章节信息")
            else:
                print("\n【章节摘要列表】")
                for i, (title_id, title_name, level, title_summary) in enumerate(titles, 1):
                    # 根据级别缩进
                    indent = "  " * (level - 1)
                    print(f"\n{indent}├─ [{level}级] {title_name}")
                    
                    if title_summary and title_summary.strip():
                        # 摘要内容缩进显示，增加可读性
                        summary_indent = indent + "   │ "
                        formatted_summary = "\n".join([f"{summary_indent}{line}" for line in title_summary.strip().split('\n')])
                        print(f"{formatted_summary}")
                    else:
                        print(f"{indent}   (无摘要)")
                print("\n" + "="*56)

        else:
            print("无效的文章编号!")
    except ValueError:
        print("请输入有效的数字!")


def main():
    """主函数"""
    while True:
        display_menu()
        try:
            choice = int(input("请选择操作: "))
            if choice == 0:
                print("感谢使用，再见!")
                break
            elif choice == 1:
                create_tables()
            elif choice == 2:
                input_article()
            elif choice == 3:
                view_all_articles()
            elif choice == 4:
                manage_article()
            elif choice == 5:
                delete_article()
            elif choice == 6:
                display_article_content()
            elif choice == 7:
                view_article_summaries()
            else:
                print("无效的操作选项!")
        except ValueError:
            print("请输入有效的数字!")

if __name__ == "__main__":
    main()