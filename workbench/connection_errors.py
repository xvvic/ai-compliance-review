"""Only fixed, public diagnostics cross the worker boundary."""

MESSAGES = {
    "authentication_failed": "密钥或登录状态无效，请检查密钥与鉴权方式。",
    "billing_error": "模型账户余额不足或计费不可用，请检查服务商账户。",
    "rate_limit": "模型服务限流，请稍后重试或检查账户配额。",
    "invalid_request": "模型服务拒绝了请求，请检查模型名称和 Anthropic 兼容地址。",
    "server_error": "模型服务暂时不可用，请稍后重试。",
    "timeout": "连接超过 60 秒未完成，请检查服务状态、密钥或网络；使用系统代理时可尝试切换为直连。",
    "proxy": "当前系统代理使用 SOCKS 协议，审查引擎不支持此配置。请选择直连，或将系统代理改为 HTTP(S)。",
    "runtime": "审查引擎未能启动或中途退出，请检查本机运行环境。",
    "unknown": "模型未返回有效响应，请检查服务地址、模型名称与网络连接。",
}


class ConnectionFailure(ValueError):
    def __init__(self, code="unknown"):
        super().__init__(MESSAGES.get(code, MESSAGES["unknown"]))


def failure_code(message):
    error = getattr(message, "error", None)
    if error in MESSAGES and error != "unknown":
        return error
    status = getattr(message, "api_error_status", None)
    if status in (401, 403):
        return "authentication_failed"
    if status == 402:
        return "billing_error"
    if status == 429:
        return "rate_limit"
    if status in (400, 404, 422):
        return "invalid_request"
    if status and status >= 500:
        return "server_error"
    return "unknown"
