# AI 新闻摘要生成器

这个项目是一个自动化的新闻摘要生成工具，可以从微信公众号文章生成AI摘要，并最终生成结构化的文档报告。

## 项目功能

该项目包含以下主要组件：

1. **数据获取** (`1_sql_to_urls.py`)
   - 从 SQLite 数据库中提取 WeWeRSS 抓取的公众号文章
   - 处理文章发布时间和URL
   - 筛选最近15天的文章
   - 输出文章基本信息到 CSV 文件

2. **URL筛选** (`2_screen_urls.py`)
   - 对文章URL进行智能筛选
   - 保留最相关的新闻内容

3. **内容摘要生成** (`3_url_to_md.py`)
   - 使用 AI 接口（基于 OpenAI API）读取网页内容
   - 为每篇文章生成摘要
   - 将摘要保存为 Markdown 文件
   - 按日期和来源组织文件结构

4. **高层次总结** (`4_md_to_summary.py`)
   - 对生成的 Markdown 文件进行二次处理
   - 生成更高层次的新闻摘要

5. **文档生成** (`5_combined_to_docx.py`)
   - 将摘要和详细新闻合并成 Word 文档
   - 使用预设模板生成结构化报告
   - 包含新闻总结和详细内容两个部分

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
   pip install pandas openai python-docx
   ```

2. 配置 API 密钥：
   - 在项目根目录创建 `apikey.py` 文件
   - 设置 `api_key` 和 `model_id` 变量

3. 按顺序运行脚本：
   ```bash
   python 1_sql_to_urls.py
   python 2_screen_urls.py
   python 3_url_to_md.py
   python 4_md_to_summary.py
   python 5_combined_to_docx.py
   ```

## 注意事项

- 需要确保 WeWeRSS 数据库正常更新
- API 调用可能需要考虑限流和错误处理
- 建议定期检查生成的摘要质量