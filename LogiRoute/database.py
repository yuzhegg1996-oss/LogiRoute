#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
该模块包含数据库操作相关的函数。
创建数据库和表，包括article、title和plain_text表。
"""

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "rag_database")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root123")

def create_connection():
    """创建数据库连接"""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None

def create_database_and_tables():
    """创建数据库和表"""
    # 连接到MySQL服务器（不指定数据库）
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS rag_database")
            cursor.execute("USE rag_database")
            
            # 创建article表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS article (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL UNIQUE,
                    summary TEXT
                )
            """)
            
            # 创建title表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS title (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    article_id INT,
                    title VARCHAR(255) NOT NULL,
                    level INT NOT NULL,
                    summary TEXT,
                    FOREIGN KEY (article_id) REFERENCES article(id) ON DELETE CASCADE
                )
            """)
            
            # 创建plain_text表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plain_text (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title_id INT,
                    text_content TEXT,
                    FOREIGN KEY (title_id) REFERENCES title(id) ON DELETE CASCADE
                )
            """)
            
            print("数据库和表创建成功!")
            
    except Error as e:
        print(f"创建数据库和表时出错: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def insert_article(title):
    """插入新文章并返回文章ID"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO article (title) VALUES (%s)", (title,))
            connection.commit()
            article_id = cursor.lastrowid
            return article_id
        except Error as e:
            print(f"插入文章时出错: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

def insert_title(article_id, title, level):
    """插入标题并返回标题ID"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO title (article_id, title, level) VALUES (%s, %s, %s)",
                (article_id, title, level)
            )
            connection.commit()
            title_id = cursor.lastrowid
            return title_id
        except Error as e:
            print(f"插入标题时出错: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

def insert_plain_text(title_id, text_content):
    """插入正文并返回正文ID"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO plain_text (title_id, text_content) VALUES (%s, %s)",
                (title_id, text_content)
            )
            connection.commit()
            text_id = cursor.lastrowid
            return text_id
        except Error as e:
            print(f"插入正文时出错: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

def get_all_articles():
    """获取所有文章标题"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT title FROM article")
            articles = [row[0] for row in cursor.fetchall()]
            return articles
        except Error as e:
            print(f"获取文章列表时出错: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return []

def get_all_articles_with_details():
    """获取所有文章的ID、标题和摘要"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, title, summary FROM article")
            articles = cursor.fetchall()
            return articles
        except Error as e:
            print(f"获取文章详情列表时出错: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return []

def get_article_id_by_title(title):
    """根据文章标题获取文章ID"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # 1. 尝试精确匹配
            cursor.execute("SELECT id FROM article WHERE title = %s", (title,))
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # 2. 如果精确匹配失败，尝试去除空格后匹配
            # 获取所有文章标题和ID
            cursor.execute("SELECT id, title FROM article")
            all_articles = cursor.fetchall()
            
            # 归一化输入标题 (去除所有空白字符并转小写)
            normalized_input_title = "".join(title.split()).lower()
            
            for article_id, db_title in all_articles:
                if "".join(db_title.split()).lower() == normalized_input_title:
                    print(f"提示: 通过模糊匹配找到文章 '{db_title}' (ID: {article_id})")
                    return article_id
            
            return None
        except Error as e:
            print(f"获取文章ID时出错: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

def get_titles_by_article_id(article_id):
    """根据文章ID获取所有标题"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, title, level, summary FROM title WHERE article_id = %s ORDER BY id",
                (article_id,)
            )
            titles = cursor.fetchall()
            return titles
        except Error as e:
            print(f"获取标题列表时出错: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return []

def get_titles_by_article(title):
    """根据文章标题获取所有标题"""
    article_id = get_article_id_by_title(title)
    if article_id:
        return get_titles_by_article_id(article_id)
    return []

def delete_article_by_title(title):
    """根据文章标题删除文章"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM article WHERE title = %s", (title,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"删除文章时出错: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

def delete_title_by_id(title_id):
    """根据标题ID删除标题"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM title WHERE id = %s", (title_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"删除标题时出错: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

def update_title(title_id, new_title, new_level):
    """更新标题"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE title SET title = %s, level = %s WHERE id = %s",
                (new_title, new_level, title_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"更新标题时出错: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

def update_plain_text_by_title_id(title_id, new_content):
    """根据标题ID更新正文"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # 检查是否存在正文记录
            cursor.execute(
                "SELECT id FROM plain_text WHERE title_id = %s",
                (title_id,)
            )
            result = cursor.fetchone()
            
            if result:
                # 更新现有正文
                text_id = result[0]
                cursor.execute(
                    "UPDATE plain_text SET text_content = %s WHERE id = %s",
                    (new_content, text_id)
                )
            else:
                # 插入新正文
                cursor.execute(
                    "INSERT INTO plain_text (title_id, text_content) VALUES (%s, %s)",
                    (title_id, new_content)
                )
            
            connection.commit()
            return True
        except Error as e:
            print(f"更新正文时出错: {e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

def get_plain_text_by_title(title):
    """根据标题获取正文内容"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # 执行JOIN查询获取正文内容
            cursor.execute("""
                SELECT pt.text_content, t.summary
                FROM plain_text pt
                JOIN title t ON pt.title_id = t.id
                WHERE t.title = %s
            """, (title,))
            
            result = cursor.fetchone()
            # 返回 (text_content, summary)
            return (result[0], result[1]) if result else None
        except Error as e:
            print(f"获取正文内容时出错: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None


def get_plain_text_by_title_id(title_id):
    """根据标题ID获取正文内容"""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # 查询指定标题ID的正文内容
            cursor.execute("""
                SELECT pt.text_content 
                FROM plain_text pt 
                WHERE pt.title_id = %s
            """, (title_id,))
            
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            print(f"获取正文内容时出错: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None


# 以下为测试代码
if __name__ == "__main__":
    # 创建数据库和表
    create_database_and_tables()
    
    # 插入测试文章
    article_id = insert_article("测试文章")
    if article_id:
        print(f"文章ID: {article_id}")
        
        # 插入测试标题
        title_id = insert_title(article_id, "测试标题", 1)
        if title_id:
            print(f"标题ID: {title_id}")
            
            # 插入测试正文
            text_id = insert_plain_text(title_id, "这是测试正文内容。")
            if text_id:
                print(f"正文ID: {text_id}")
                
                # 测试获取正文内容
                content = get_plain_text_by_title_id(title_id)
                print(f"获取到的正文内容: {content}")
