#%%
import sys,os
sys.path.append(os.path.abspath(".."))
from parameters import friday_date
import os
from models import deepseek_model,count_tokens,gemini_model
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def process_single_file(raw_path, output_path_ds, file, prompt, max_retries=3):
    """处理单个文件的函数，包含重试机制"""
    output_file = os.path.join(output_path_ds, file)
    if os.path.exists(output_file):
        print(f"跳过已存在的文件: {file}")
        return f"跳过: {file}"

    print(f"开始处理: {file}")
    
    # 读取文件内容
    try:
        with open(os.path.join(raw_path, file), 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 {file} 失败: {str(e)}")
        return f"读取错误: {file} - {str(e)}"
            
    print(f'{file} - total tokens: {count_tokens(prompt+"\n -- \n"+content)}')
    
    # 重试机制
    for attempt in range(max_retries):
        try:
            print(f"尝试生成摘要 (第 {attempt + 1}/{max_retries} 次): {file}")
            summary_ds = deepseek_model(prompt, content)
            
            # 检查生成的摘要是否有效（不为空且有最少内容）
            if not summary_ds or len(summary_ds.strip()) < 10:
                raise ValueError("生成的摘要为空或内容过短")
            
            with open(output_file, 'w') as f:
                f.write(summary_ds)
            
            print(f"完成处理: {file}")
            return f"成功: {file}"
        
        except Exception as e:
            print(f"第 {attempt + 1} 次尝试失败: {file} - {str(e)}")
            if attempt == max_retries - 1:  # 最后一次尝试
                print(f"处理文件 {file} 最终失败，已重试 {max_retries} 次")
                return f"最终失败: {file} - {str(e)}"
            else:
                print(f"等待重试...")
                import time
                time.sleep(2)  # 等待2秒后重试

def md_to_summary(friday_date, max_workers=8, max_retries=3):
    raw_path = f'pdfreport/03 cleaned_markdown/{friday_date}'
    output_path_ds = f'pdfreport/04 summary/{friday_date}_ds'
    # output_path_gemini=f'./04 summary/{friday_date}_gemini'
    os.makedirs(output_path_ds, exist_ok=True)
    # os.makedirs(output_path_gemini, exist_ok=True)
    os.makedirs(raw_path, exist_ok=True)

    # 读取prompt文件一次，避免重复读取
    prompt = open('pdfreport/prompt.txt','r').read()
    
    # 获取所有需要处理的文件
    files = [f for f in os.listdir(raw_path) if os.path.isfile(os.path.join(raw_path, f))]
    
    if not files:
        print("没有找到需要处理的文件")
        return
    
    print(f"找到 {len(files)} 个文件，开始并行处理 (最大并发数: {max_workers}, 最大重试次数: {max_retries})")
    
    # 使用ThreadPoolExecutor进行并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(process_single_file, raw_path, output_path_ds, file, prompt, max_retries): file
            for file in files
        }
        
        # 等待所有任务完成并收集结果
        results = []
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"处理文件 {file} 时发生未预期的错误: {str(e)}")
                results.append(f"异常: {file} - {str(e)}")
    
    print("\n=== 处理结果汇总 ===")
    for result in results:
        print(result)
    print(f"总共处理完成 {len(results)} 个文件")

# 如果直接运行此脚本
if __name__ == "__main__":
    md_to_summary(friday_date)