# AI News Summary Generator

这个项目用于从网络文章链接生成AI新闻摘要，并将其转换为带有目录的PDF文档

## 功能概述

项目包含三个主要组件：

1. **sql_to_url.py**：WeWeRSS 上自动抓取的公众号文章，会存储在Sqlite里；从sqlite 提取文章url
1. **url_to_md.py**: 从文本文件中读取URL列表，调用AI接口生成摘要，并输出为Markdown文件。
2. **md_to_summary.py**: 将Markdown进行summary，挑出来最关键的新闻
