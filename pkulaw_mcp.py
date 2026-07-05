import requests
import json

# 配置你的北大法宝 API Key
PKULAW_API_KEY = "你的北大法宝API_KEY"  # 等你拿到了填进去

# MCP 服务地址
MCP_URL = "https://apim-gateway.pkulaw.com/mcp-law-search-service"


def _call_mcp_tool(tool_name, arguments):
    """
    通用的 MCP 工具调用函数（内部用，外部不用直接调）
    """
    headers = {
        "Authorization": f"Bearer {PKULAW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        response = requests.post(MCP_URL, json=data, headers=headers)
        result = response.json()
        
        if "result" in result:
            # MCP 返回的 content 是一个列表，取第一个的文本
            content_list = result["result"].get("content", [])
            if content_list:
                return content_list[0].get("text", "")
            return ""
        else:
            error_msg = result.get("error", {}).get("message", "未知错误")
            return f"MCP调用失败：{error_msg}"
            
    except Exception as e:
        return f"MCP调用出错：{str(e)}"


def search_law_articles(query, max_results=5):
    """
    语义检索法律法规
    
    Args:
        query: 查询内容，比如"个人信息最小必要原则"
        max_results: 返回结果数量
    
    Returns:
        检索到的法条文本（字符串，格式化好的）
    """
    # 工具名可能需要根据实际文档调整，这里是常见命名
    result = _call_mcp_tool("search_article", {"query": query, "limit": max_results})
    return result


def search_cases(query, max_results=3):
    """
    语义检索司法案例
    
    Args:
        query: 查询内容，比如"过度收集个人信息 处罚"
        max_results: 返回结果数量
    
    Returns:
        检索到的案例文本（字符串，格式化好的）
    """
    result = _call_mcp_tool("search_case", {"query": query, "limit": max_results})
    return result


def get_article_by_id(article_id):
    """
    根据法条ID获取精确法条内容
    """
    result = _call_mcp_tool("get_article", {"id": article_id})
    return result


# 测试（等你有 API Key 了再测）
if __name__ == "__main__":
    print("测试法条检索...")
    laws = search_law_articles("个人信息保护 最小必要原则")
    print(laws)
    print("-" * 50)
    
    print("测试案例检索...")
    cases = search_cases("过度收集个人信息 处罚")
    print(cases)