
build a macos desktop pet app that captures & analyze the screenshot every 5 minuts, 
the analyze is conducted using Qwen LLM (reference codes is below),
the desktop pet should be a cute cat with a cute friendly personality
after analyze, the cat display the analysis result like a short friendly warmly catchup (in chinese) according to the analysis result (do not be typical explanatory AI, image ur girlfriend or boyfriend is sitting next to you watching you work, and she/he causally say something about your job)

give me the detailed steps and codes for each file




reference codes:

api_key="sk-1a28c3fcc7e044cbacd6faf47dc89755"


import os
from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-1a28c3fcc7e044cbacd6faf47dc89755",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen-vl-plus",  # 此处以qwen-vl-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    messages=[{"role": "user","content": [
            {"type": "text","text": "这是什么"},
            {"type": "image_url",
             "image_url": {"url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"}}
            ]}]
    )
print(completion.model_dump_json())


or
```nodejs
import OpenAI from "openai";

const openai = new OpenAI(
    {
        // 若没有配置环境变量，请用百炼API Key将下行替换为：apiKey: "sk-xxx",
        apiKey: process.env.DASHSCOPE_API_KEY,
        baseURL: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    }
);

async function main() {
    const response = await openai.chat.completions.create({
        model: "qwen-vl-max", // 此处以qwen-vl-max为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages: [{role: "user",content: [
            { type: "text", text: "这是什么？" },
            { type: "image_url",image_url: {"url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"}}
        ]}]
    });
    console.log(JSON.stringify(response));
}

main();
```


or
```curl
curl -X POST https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
-H "Authorization: Bearer $DASHSCOPE_API_KEY" \
-H 'Content-Type: application/json' \
-d '{
  "model": "qwen-vl-plus",
  "messages": [{
      "role": "user",
      "content": 
      [{"type": "text","text": "这是什么"},
       {"type": "image_url","image_url": {"url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"}}]
    }]
}'
```