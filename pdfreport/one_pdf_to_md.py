#%%
import sys,os
sys.path.append(os.path.abspath(".."))
from markitdown import MarkItDown
from parameters import friday_date
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def convert_single_pdf(raw_path, output_path, file):
    """转换单个PDF文件的函数"""
    output_file = os.path.join(output_path, file.replace('.pdf', '.md'))
    if os.path.exists(output_file):
        print(f"跳过已存在的文件: {file}")
        return f"跳过: {file}"

    print(f"开始转换: {file}")
    
    try:
        # 每个线程创建自己的MarkItDown实例，避免线程冲突
        md = MarkItDown()
        result = md.convert(os.path.join(raw_path, file))
        
        with open(output_file, 'w') as f:
            f.write(file + '\n\n')
            f.write(result.text_content)
        
        print(f"完成转换: {file}")
        return f"成功: {file}"
    
    except Exception as e:
        print(f"转换文件 {file} 时出错: {str(e)}")
        return f"错误: {file} - {str(e)}"

def pdf_to_md(friday_date, max_workers=8):
    source_path = os.path.expanduser(f'~/Dropbox/MyServerFiles/AutoWeekly/{friday_date}')
    raw_path = f'pdfreport/01 raw/{friday_date}'

    # Create raw_path if it doesn't exist
    os.makedirs(raw_path, exist_ok=True)
    
    # Copy PDFs from source to raw path if source exists
    if os.path.exists(source_path):
        source_pdfs = [f for f in os.listdir(source_path) if f.lower().endswith('.pdf')]
        if source_pdfs:
            print(f"Found {len(source_pdfs)} PDFs in {source_path}")
            for pdf_file in source_pdfs:
                source_file = os.path.join(source_path, pdf_file)
                dest_file = os.path.join(raw_path, pdf_file)
                if not os.path.exists(dest_file):
                    shutil.copy2(source_file, dest_file)
                    print(f"Copied: {pdf_file}")
                else:
                    print(f"Skipping existing: {pdf_file}")

    output_path = f'pdfreport/02 markdown/{friday_date}'

    if os.path.exists(raw_path):
        os.makedirs(output_path, exist_ok=True)
        
        # 获取所有PDF文件
        pdf_files = [f for f in os.listdir(raw_path) 
                    if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(raw_path, f))]
        
        if not pdf_files:
            print("没有找到需要转换的PDF文件")
            return
        
        print(f"找到 {len(pdf_files)} 个PDF文件，开始并行转换 (最大并发数: {max_workers})")
        
        # 使用ThreadPoolExecutor进行并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(convert_single_pdf, raw_path, output_path, file): file
                for file in pdf_files
            }
            
            # 等待所有任务完成并收集结果
            results = []
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"转换文件 {file} 时发生未预期的错误: {str(e)}")
                    results.append(f"异常: {file} - {str(e)}")
        
        print("\n=== 转换结果汇总 ===")
        for result in results:
            print(result)
        print(f"总共转换完成 {len(results)} 个PDF文件")
        
    else:
        raise FileNotFoundError(f"Raw path {raw_path} does not exist")

# 如果直接运行此脚本
if __name__ == "__main__":
    pdf_to_md(friday_date)

#%%
