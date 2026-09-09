let token = "";
export async function initialize() {
  const response = await fetch("/api/session");
  if (!response.ok) throw new Error("本机服务连接失败，请重新启动应用。");
  token = (await response.json()).token;
}
export async function request(path: string, method = "GET", body?: unknown) {
  const response = await fetch(path, {
    method,
    headers: {
      "x-session-token": token,
      ...(body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
    },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === "string" ? error.detail : "请求失败，请重试。",
    );
  }
  return response;
}
export async function api(path: string, method = "GET", body?: unknown) {
  return (await request(path, method, body)).json();
}
export async function readEvents(
  response: Response,
  onEvent: (event: Record<string, any>) => void,
) {
  if (!response.body) throw new Error("审查连接未建立。");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "",
    doneEvent = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let boundary: RegExpExecArray | null;
      while ((boundary = /\r?\n\r?\n/.exec(buffer))) {
        const block = buffer.slice(0, boundary.index);
        buffer = buffer.slice(boundary.index + boundary[0].length);
        const data = block
          .split(/\r?\n/)
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trimStart())
          .join("\n");
        if (data) {
          const event = JSON.parse(data);
          onEvent(event);
          if (event.type === "done") doneEvent = true;
        }
      }
      if (done) break;
    }
    if (!doneEvent)
      throw new Error("实时连接已断开，审查可能仍在运行。请刷新页面恢复状态。");
  } finally {
    reader.releaseLock();
  }
}
