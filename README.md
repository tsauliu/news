# AI 新闻摘要生成器

这个项目是一个自动化的新闻摘要生成工具，可以从微信公众号文章生成AI摘要，并最终生成结构化的文档报告。

## 项目功能

该项目包含以下主要组件：

1. **数据获取** (`1_sql_to_urls.py`)
   - 从 SQLite 数据库中提取 WeWeRSS 抓取的公众号文章
   - 处理文章发布时间和URL
   - 筛选最近15天的文章
   - 输出文章基本信息到 CSV 文件

2. **原始内容提取** (`2_urls_to_raw_mds.py`)
   - 从URL中提取微信公众号文章内容
   - 将原始内容保存为Markdown文件
   - 按日期组织文件结构

3. **内容摘要生成** (`3_raw_mds_to_summaries.py`)
   - 使用AI模型（基于OpenAI API）分析原始文章内容
   - 为每篇文章生成结构化摘要
   - 提取关键信息和主要观点
   - 将摘要保存为独立的Markdown文件

4. **行业分类整理** (`4_summaries_to_sectors.py`)
   - 对生成的摘要进行行业分类
   - 按照预设的行业类别组织内容
   - 生成分类后的结构化数据

5. **文档生成** (`5_sectors_to_docx.py`)
   - 将分类整理后的摘要合并成Word文档
   - 使用预设模板生成结构化报告
   - 包含行业总结和详细新闻两个部分
   - 生成最终的新闻简报文档

## 文件结构

```
project/
├── data/
│   ├── urls/
│   │   └── article_urls.csv
│   ├── raw_mds/
│   │   └── YYYY-MM-DD/
│   └── wewe-rss.db
├── 1_sql_to_urls.py
├── 2_screen_urls.py
├── 3_url_to_md.py
├── 4_md_to_summary.py
├── 5_combined_to_docx.py
└── monthly_news_template.docx
```

## 使用说明

1. 确保已安装所需的Python包：
   ```bash
   pip install pandas openai python-docx selenium beautifulsoup4
   ```

2. 设置Chrome驱动（用于网页抓取）：
   ```bash
   bash crawler/setup_steps.sh
   ```

3. 配置 API 密钥：
   - 在项目根目录创建 `apikey.py` 文件
   - 设置 `api_key`、`model_id_url_to_summary` 和 `model_id_md_to_summary` 变量

4. 按顺序运行脚本：
   ```bash
   python 1_sql_to_urls.py
   python 2_url_to_md.py
   python 3_md_to_article_summary.py
   python 4_article_to_overall_summary.py
   python 5_combined_to_docx.py
   ```

## 参数配置

在 `parameters.py` 文件中可以配置以下参数：
- `friday_date`: 自动计算当周周五的日期（用于文件命名）
- `errorkeywords`: 用于过滤无关内容的关键词列表
- `sector_list`: 新闻分类列表

## 注意事项

- 需要确保 WeWeRSS 数据库正常更新
- API 调用可能需要考虑限流和错误处理
- 建议定期检查生成的摘要质量
- 确保Chrome驱动版本与您的Chrome浏览器版本兼容