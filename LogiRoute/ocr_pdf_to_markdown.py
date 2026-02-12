#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF 转 Markdown 转换工具 (基于 Marker)

功能：
1. 遍历指定文件夹中的 PDF 文件。
2. 使用 Marker 本地模型将 PDF 转换为 Markdown。
3. 将生成的 Markdown 保存到指定输出文件夹。

注意：
- 首次运行会自动下载必要的模型权重，请保持网络连接。
- 转换过程在本地进行，速度取决于计算机性能 (推荐使用 GPU)。
"""

import os
import time
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# ================= 配置区域 =================

# 输入和输出文件夹
INPUT_FOLDER = "pdf_input"
OUTPUT_FOLDER = "markdown_output"

# ===========================================

def process_pdf(pdf_path, output_path, converter):
    """处理单个 PDF 文件"""
    print(f"正在处理: {os.path.basename(pdf_path)}...")
    
    try:
        # 调用 Marker 进行转换
        rendered = converter(pdf_path)
        
        # 获取纯文本内容 (rendered 可能包含其他信息，或者本身就是字符串，视版本而定)
        # 根据源码 PdfConverter.__call__ 返回 rendered，这是 MarkdownRenderer 的结果
        # MarkdownRenderer 通常返回一个 RenderResult 对象或字符串
        
        # 为了稳健性，我们尝试从 rendered 中提取文本，或者直接使用它
        if hasattr(rendered, 'text'):
            full_text = rendered.text
        elif isinstance(rendered, str):
            full_text = rendered
        else:
            # 尝试使用 marker.output.text_from_rendered (如果存在)
            try:
                # text_from_rendered 返回 (text, ext, images)
                text_content, _, _ = text_from_rendered(rendered)
                full_text = text_content
            except Exception as e:
                # 如果 text_from_rendered 失败，回退到 str()
                print(f"  [WARNING] text_from_rendered 解析失败: {e}，尝试直接转换。")
                full_text = str(rendered)

        # 保存 Markdown 文件
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"  [SUCCESS] 转换完成，已保存至: {output_path}")
        
    except Exception as e:
        print(f"  [ERROR] 处理文件 {os.path.basename(pdf_path)} 时出错: {e}")
        import traceback
        traceback.print_exc()

def main():
    # 1. 创建输入输出目录
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"已创建输入文件夹 '{INPUT_FOLDER}'，请将 PDF 文件放入其中。")
        with open(os.path.join(INPUT_FOLDER, "put_pdfs_here.txt"), "w") as f:
            f.write("请将需要转换的 PDF 文件放入此文件夹。")
        return

    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"已创建输出文件夹 '{OUTPUT_FOLDER}'。")

    # 2. 获取 PDF 列表
    pdf_files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"输入文件夹 '{INPUT_FOLDER}' 中没有找到 PDF 文件。")
        return

    print("正在加载 Marker 模型 (首次运行可能需要下载模型)...")
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {device}")
        
        # 加载模型
        model_dict = create_model_dict(device=device)
        # 初始化转换器
        converter = PdfConverter(artifact_dict=model_dict)
        print("模型加载完成。")
    except Exception as e:
        print(f"模型加载失败: {e}")
        print("请检查网络连接或 PyTorch 安装。")
        import traceback
        traceback.print_exc()
        return

    print(f"找到 {len(pdf_files)} 个 PDF 文件，准备开始转换...")

    # 3. 批量处理
    for pdf_file in pdf_files:
        input_path = os.path.join(INPUT_FOLDER, pdf_file)
        # 输出文件名：原文件名.md
        output_filename = os.path.splitext(pdf_file)[0] + ".md"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        process_pdf(input_path, output_path, converter)
        print("-" * 50)

    print("\n所有任务完成！")

if __name__ == "__main__":
    main()
