import dashscope
import os
from dotenv import load_dotenv

# 加载 .env 文件里的环境变量
load_dotenv()

# 从环境变量读取 API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")


def ask(prompt, system_prompt="你是一个 helpful 的助手。", temperature=0.7):
    """
    调用通义千问大模型
    
    Args:
        prompt: 用户问题/输入内容
        system_prompt: 系统提示词，用来设定AI身份和规则
        temperature: 创造性，0-1，越低越保守，法律场景建议0.3-0.5
    
    Returns:
        大模型的回复文本
    """
    try:
        resp = dashscope.Generation.call(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            result_format='message',
        )
        
        if resp.status_code == 200:
            return resp.output.choices[0].message.content
        else:
            return f"调用失败，错误码：{resp.status_code}，错误信息：{resp.message}"
            
    except Exception as e:
        return f"调用大模型出错：{str(e)}"


def chat(messages, temperature=0.7):
    """
    多轮对话版本，传入完整的消息历史
    
    Args:
        messages: 消息列表，格式 [{"role": "user"/"assistant"/"system", "content": "..."}]
        temperature: 创造性
    
    Returns:
        大模型的回复文本
    """
    try:
        resp = dashscope.Generation.call(
            model="qwen-plus",
            messages=messages,
            temperature=temperature,
            result_format='message',
        )
        
        if resp.status_code == 200:
            return resp.output.choices[0].message.content
        else:
            return f"调用失败，错误码：{resp.status_code}，错误信息：{resp.message}"
            
    except Exception as e:
        return f"调用大模型出错：{str(e)}"


# 测试
if __name__ == "__main__":
    result = ask("你好，介绍一下你自己")
    print("测试结果：", result)