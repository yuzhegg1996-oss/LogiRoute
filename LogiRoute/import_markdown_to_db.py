import os
import re
import database

def parse_markdown_file(file_path):
    """
    解析 Markdown 文件，返回结构化数据。
    返回结构:
    {
        "article_title": "文件名(无后缀)",
        "sections": [
            {
                "title": "标题内容",
                "level": 1,
                "content": "正文内容..."
            },
            ...
        ]
    }
    """
    filename = os.path.basename(file_path)
    # 去除文件名中的多余空格 (包括中间的连续空格)
    article_title = re.sub(r'\s+', ' ', os.path.splitext(filename)[0]).strip()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    sections = []
    current_title = "Introduction" # 默认开头部分的标题
    current_level = 0
    current_content = []
    
    # 正则匹配 Markdown 标题 (例如: # 标题, ## 标题)
    header_pattern = re.compile(r'^(#+)\s+(.*)')
    
    first_header_found = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = header_pattern.match(line)
        if match:
            # 提取标题内容，并去除多余空格
            title_text = re.sub(r'\s+', ' ', match.group(2)).strip()

            # 如果是文档中的第一个标题，将其作为文章题目
            if not first_header_found:
                article_title = title_text
                first_header_found = True

            # 遇到新标题，保存上一个部分（如果有内容）
            if current_content:
                sections.append({
                    "title": current_title,
                    "level": current_level,
                    "content": "\n".join(current_content)
                })
                current_content = []
            
            # 更新当前标题状态
            current_level = len(match.group(1))
            current_title = title_text
        else:
            # 普通文本，追加到当前内容
            current_content.append(line)
            
    # 保存最后一个部分
    if current_content:
        sections.append({
            "title": current_title,
            "level": current_level,
            "content": "\n".join(current_content)
        })
        
    return article_title, sections

def import_to_database(article_title, sections):
    """
    将解析后的数据存入数据库
    """
    print(f"正在处理文章: {article_title}")
    
    # 1. 检查文章是否已存在
    existing_id = database.get_article_id_by_title(article_title)
    if existing_id:
        print(f"  [跳过] 文章 '{article_title}' 已存在 (ID: {existing_id})")
        return
        
    # 2. 插入文章表
    article_id = database.insert_article(article_title)
    if not article_id:
        print(f"  [错误] 无法插入文章 '{article_title}'")
        return
    print(f"  [成功] 插入文章 '{article_title}' (ID: {article_id})")
    
    # 3. 遍历章节插入 title 和 plain_text 表
    count_titles = 0
    count_texts = 0
    
    for section in sections:
        title_text = section['title']
        level = section['level']
        content = section['content']
        
        # 插入 title 表
        title_id = database.insert_title(article_id, title_text, level)
        if title_id:
            count_titles += 1
            # 插入 plain_text 表 (如果有内容)
            if content:
                text_id = database.insert_plain_text(title_id, content)
                if text_id:
                    count_texts += 1
        else:
            print(f"  [警告] 无法插入标题 '{title_text}'")
            
    print(f"  完成: 插入 {count_titles} 个标题, {count_texts} 段正文。")

def main():
    # 定义 markdown_output 文件夹路径
    # 假设它在当前脚本所在目录的 markdown_output 子目录中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    markdown_dir = os.path.join(current_dir, 'markdown_output')
    
    if not os.path.exists(markdown_dir):
        print(f"错误: 找不到文件夹 '{markdown_dir}'")
        return
        
    print(f"开始从 '{markdown_dir}' 导入 Markdown 文件...")
    
    files = [f for f in os.listdir(markdown_dir) if f.lower().endswith('.md')]
    
    if not files:
        print("文件夹中没有找到 .md 文件。")
        return
        
    for filename in files:
        file_path = os.path.join(markdown_dir, filename)
        try:
            article_title, sections = parse_markdown_file(file_path)
            if not sections:
                print(f"警告: 文件 '{filename}' 内容为空或无法解析。")
                continue
            import_to_database(article_title, sections)
        except Exception as e:
            print(f"处理文件 '{filename}' 时发生未知错误: {e}")

    print("\n所有任务完成！")

if __name__ == "__main__":
    main()
