#%%
import sys,os
sys.path.append(os.path.abspath(".."))
from parameters import friday_date
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def clean_single_markdown(raw_path, output_path, file):
    """清理单个markdown文件的函数"""
    output_file = os.path.join(output_path, file)
    if os.path.exists(output_file):
        print(f"跳过已存在的文件: {file}")
        return f"跳过: {file}"

    print(f"开始清理: {file}")
    
    try:
        with open(os.path.join(raw_path, file), 'r') as f:
            content = f.read()
        
        # Find lines with "Disclosures" but not "see"
        lines = content.split('\n')
        
        with open(output_file, 'w') as f:
            for line in lines:
                if "disclosures" in line.lower() and "see" not in line.lower():
                    f.write(line + '\n')
                    break
                elif "免责声明" in line.lower() and "阅读" not in line.lower():
                    f.write(line + '\n')
                    break
                else:
                    f.write(line + '\n')
        
        print(f"完成清理: {file}")
        return f"成功: {file}"
    
    except Exception as e:
        print(f"清理文件 {file} 时出错: {str(e)}")
        return f"错误: {file} - {str(e)}"

def clean_markdown(friday_date, max_workers=8):
    raw_path = f'pdfreport/02 markdown/{friday_date}'
    output_path = f'pdfreport/03 cleaned_markdown/{friday_date}'
    os.makedirs(output_path, exist_ok=True)
    os.makedirs(raw_path, exist_ok=True)

    # 获取所有需要处理的文件
    files = [f for f in os.listdir(raw_path) if os.path.isfile(os.path.join(raw_path, f))]
    
    if not files:
        print("没有找到需要清理的markdown文件")
        return
    
    print(f"找到 {len(files)} 个markdown文件，开始并行清理 (最大并发数: {max_workers})")
    
    # 使用ThreadPoolExecutor进行并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(clean_single_markdown, raw_path, output_path, file): file
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
                print(f"清理文件 {file} 时发生未预期的错误: {str(e)}")
                results.append(f"异常: {file} - {str(e)}")
    
    print("\n=== 清理结果汇总 ===")
    for result in results:
        print(result)
    print(f"总共清理完成 {len(results)} 个markdown文件")

# 如果直接运行此脚本
if __name__ == "__main__":
    clean_markdown(friday_date)