#%%
import os
from openai import OpenAI
from apikey import api_key

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Openai客户端，从环境变量中读取您的API Key
client = OpenAI(
    # 此为默认路径，您可根据业务所在地域进行配置
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # 从环境变量中获取您的 API Key
    api_key=api_key,
)

with open('context.txt', 'r', encoding='utf-8') as file:
    content = file.read()


def clean_data(input):
    completion = client.chat.completions.create(
        # 指定您创建的方舟推理接入点 ID，此处已帮您修改为您的推理接入点 ID
        model="doubao-1-5-pro-32k-250115", #doubao-1-5-pro-32k-250115，deepseek-v3-241226
        messages=[
            # {"role": "system", "content": "你是清洗数据助手,只给我答案，不要给任何说明，如果有多个答案，用逗号隔开"},
            # {"role": "user", "content": f"以下表格里面，哪个是<{input}>，以<品牌>列为标准，帮我查找最符合的一个<整车厂/品牌 (中)>，尽量只给一个答案，没有就回答没有\n----\n"+content},
        ],
    )
    return completion.choices[0].message.content

