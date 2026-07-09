"""
AI 合规审查系统 - 前端界面(改版)
============================================
功能:
- 支持txt/docx/pdf文件上传解析
- SSE流式对接后端,实时展示思考过程、工具调用轨迹
- 左侧:Task 任务面板 + 执行过程(精简工具展示、最新置顶自动刷新)
- 右侧:最终审查报告(只在生成后显示,过程中的中间输出归到左侧)
- 支持Markdown报告下载

运行方式:
    pip install streamlit python-docx pypdf requests
    streamlit run app.py
"""

import os
import re
import json
import requests
import streamlit as st

st.set_page_config(page_title="AI 合规审查系统", page_icon="⚖️", layout="wide")
st.title("⚖️ AI 初创企业合规审查系统")
st.caption("上传企业材料,自动识别合规风险 · 展示 AI 审查全过程")

# ---------------- 会话状态 ----------------
DEFAULTS = {
    "trace_items": [],   # 执行过程条目:[{step, label, count}],连续相同操作聚合计数
    "tasks": [],         # 任务清单(Task面板)
    "report_text": "",   # 最终报告
    "review_finished": False,
    "running": False,    # 审查进行中?进行时禁用"开始"按钮,防重复触发
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

with st.sidebar:
    st.header("设置")
    backend_url = st.text_input(
        "后端接口地址",
        value="http://127.0.0.1:8000/review/stream",
        help="后端SSE接口地址,同WiFi下填队友局域网IP,ngrok穿透填公网地址",
    )
    st.divider()
    st.markdown(
        "**使用说明**\n\n1. 上传待审查文件 → 2. 点击开始审查 → "
        "3. 左侧看任务清单和执行过程,右侧看最终报告"
    )


# ---------------- 工具函数 ----------------
def parse_file(uploaded_file):
    """把上传的文件解析成纯文本"""
    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")
    elif name.endswith(".docx"):
        import docx
        doc = docx.Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs)
    elif name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(uploaded_file)
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        return None


def real_stream(url, text):
    """对接后端SSE流,逐事件yield"""
    resp = requests.post(url, json={"document_text": text}, stream=True, timeout=600)
    resp.raise_for_status()
    for line in resp.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                yield json.loads(decoded[6:])


def _short(text, n=140):
    """压成一行、截断,给执行过程用"""
    s = " ".join(str(text).split())
    return s[:n] + ("…" if len(s) > n else "")


def _base(path):
    return os.path.basename(str(path)) if path else ""


def _clean_pattern(p):
    """把 Grep 的正则压成人能看懂的关键词:去掉量词/元字符,| 变成顿号"""
    if not p:
        return ""
    s = str(p)
    s = re.sub(r"\.?\{[\d,]*\}", " ", s)      # .{0,10} / {0,10} -> 空格(中间隔若干字)
    s = re.sub(r"\.[*+?]", " ", s)             # .* .+ .? -> 空格
    s = s.replace("|", "、")                   # 或 -> 顿号
    s = re.sub(r"[()\[\]{}^$\\+*?]", "", s)    # 去掉残余正则元字符
    s = re.sub(r"\s+", " ", s).strip()
    return s


INPUT_FILE = "待审查材料.txt"    # 用户上传的待审材料
REPORT_FILE = "合规审查报告.md"  # agent 最终产出的报告


def classify_tool(name, args):
    """归类工具调用 -> (分类标签, 明细)。同类聚合计数,明细可展开查看;内部动作返回 (None, None)。"""
    args = args or {}
    if name == "Read":
        f = _base(args.get("file_path"))
        if f == INPUT_FILE:
            return ("📄 读取待审查材料", "")
        if f == REPORT_FILE:
            return ("📄 查看报告草稿", "")
        return ("📚 查阅法规知识库", f)       # 其余是 skill 内部参考/语料/脚本,明细=文件名
    if name == "Write":
        f = _base(args.get("file_path"))
        return ("✏️ 撰写审查报告", "") if f == REPORT_FILE else ("✏️ 写入文件", f)
    if name in ("Edit", "MultiEdit"):
        return ("✏️ 修订报告", "")
    if name == "Grep":
        return ("🔍 检索法条", _clean_pattern(args.get("pattern", "")))
    if name == "Glob":
        return ("🔍 匹配文件", str(args.get("pattern", "")))
    if name == "WebSearch":
        return ("🌐 联网检索法规", _clean_pattern(str(args.get("query", ""))))
    if name == "WebFetch":
        url = str(args.get("url", ""))
        return ("🌐 抓取网页", _base(url) or url)
    if name and name.startswith("mcp__"):
        return ("⚖️ 检索法条", name.split("__")[-1])
    if name in ("ToolSearch", "Skill", "TodoWrite"):
        return (None, None)                  # 纯内部动作,不展示
    return (f"🔧 {name}", "")


STATUS_ICON = {"completed": "✅", "in_progress": "🔄", "pending": "⬜"}

# 对用户无意义的内部管道操作,不在"具体操作"里展示
HIDE_TOOLS = {"Bash", "ToolSearch", "Skill", "TodoWrite"}


def render_steps(placeholder, tasks):
    """审查步骤清单:第N步 + ⬜待办/🔄进行中/✅完成,当前步骤加粗"""
    with placeholder.container():
        if not tasks:
            st.caption("📋 审查步骤(AI 规划后在此显示)")
            return
        done = sum(1 for t in tasks if t.get("status") == "completed")
        st.markdown(f"**📋 审查步骤**  ·  {done}/{len(tasks)} 完成")
        for i, t in enumerate(tasks, 1):
            status = t.get("status", "pending")
            icon = STATUS_ICON.get(status, "⬜")
            label = t.get("content", "")
            if status == "in_progress":
                st.markdown(f"{icon} **第 {i} 步:{label}**")  # 当前步骤加粗
            else:
                st.markdown(f"{icon} 第 {i} 步:{label}")


def render_status(placeholder, tasks, running, finished):
    """方框上方的当前状态行:正式措辞,取自进行中的任务(activeForm 优先)"""
    with placeholder.container():
        cur = next((t for t in tasks if t.get("status") == "in_progress"), None)
        if finished:
            st.success("✅ 审查完成,报告见右侧")
        elif cur:
            txt = cur.get("activeForm") or cur.get("content") or "处理中"
            st.info(f"⏳ 当前:{txt}")
        elif running:
            st.info("⏳ 正在规划审查步骤…")


def render_trace(placeholder, items):
    """具体操作:固定高度滚动框,最新置顶;同类聚合成 ×N,有明细的可点 > 展开看具体内容"""
    with placeholder.container(height=440):
        if not items:
            st.info("等待 AI 开始执行…")
            return
        for it in reversed(items):  # 最新的排最上面
            step = it.get("step")
            prefix = f"`第{step}步` " if step else ""
            count = it.get("count", 1)
            details = [d for d in it.get("details", []) if d]
            header = prefix + it.get("label", "") + (f"  ×{count}" if count > 1 else "")
            if details and count > 1:
                with st.expander(header, expanded=False):   # 点 > 展开明细
                    for d in details:
                        st.markdown(f"- {d}")
            elif details:                                    # 单条带明细,内联显示
                st.markdown(f"{header}:{details[0]}")
            else:
                st.markdown(header)


# ---------------- 主流程 ----------------
uploaded = st.file_uploader("上传企业材料(txt / docx / pdf)", type=["txt", "docx", "pdf"])

if not uploaded:
    st.info("请先上传一份企业材料文件开始审查。")
else:
    text = parse_file(uploaded)
    if not text or not text.strip():
        st.error("文件解析为空,请检查文件(扫描版PDF可能无法提取文字)。")
    else:
        with st.expander("查看解析出的文本", expanded=False):
            st.text(text[:2000] + ("..." if len(text) > 2000 else ""))

        col_left, col_right = st.columns([1, 1])
        col_left.subheader("AI 执行过程")
        col_right.subheader("审查报告")

        steps_placeholder = col_left.empty()      # 审查步骤清单
        status_placeholder = col_left.empty()     # 当前状态行
        col_left.caption("具体操作")
        trace_placeholder = col_left.empty()      # 滚动明细框
        result_placeholder = col_right.empty()    # 最终报告

        render_steps(steps_placeholder, st.session_state.tasks)
        render_status(status_placeholder, st.session_state.tasks, st.session_state.running, st.session_state.review_finished)
        render_trace(trace_placeholder, st.session_state.trace_items)
        if st.session_state.report_text:
            result_placeholder.markdown(st.session_state.report_text)
        elif st.session_state.running:
            result_placeholder.info("审查进行中,报告生成后显示在这里…")
        else:
            result_placeholder.info("点击「开始合规审查」后,报告将显示在这里。")

        # 完成提示+下载按钮放进占位符:开始新审查(running)时立即清空,
        # 否则长时间运行期间 Streamlit 不会清掉上一轮的残留提示。
        footer_placeholder = st.empty()
        if (
            st.session_state.review_finished
            and st.session_state.report_text
            and not st.session_state.running
        ):
            with footer_placeholder.container():
                st.success("审查完成!")
                st.download_button(
                    "下载审查报告",
                    data=st.session_state.report_text,
                    file_name="compliance_report.md",
                    mime="text/markdown",
                    key="download_report",
                )
        else:
            footer_placeholder.empty()

        # 两段式,保证审查进行时按钮真正禁用(先 rerun 成禁用态,再干活):
        #   闲置 -> 点击设 running=True 并 rerun
        #   运行 -> 按钮禁用 + 执行审查,结束后解除并 rerun
        if st.session_state.running:
            st.button("⏳ 审查进行中…", type="primary", disabled=True)
            cur_step = None  # 当前步骤号;只向前推进,空档期操作沿用上一步,避免"无步骤"
            try:
                for ev in real_stream(backend_url, text):
                    t = ev.get("type")

                    if t == "tool_start":
                        name = ev.get("tool_name", "")
                        if name in HIDE_TOOLS:
                            continue  # 内部管道操作(运行脚本/检索工具等),对用户无意义,不展示
                        label, detail = classify_tool(name, ev.get("args", {}))
                        if label is None:
                            continue
                        items = st.session_state.trace_items
                        # 连续同类(同步骤+同标签)则计数+1并收集明细,否则新起一条
                        if items and items[-1].get("step") == cur_step and items[-1].get("label") == label:
                            items[-1]["count"] += 1
                            if detail:
                                items[-1]["details"].append(detail)
                        else:
                            items.append({
                                "step": cur_step, "label": label, "count": 1,
                                "details": [detail] if detail else [],
                            })
                        render_trace(trace_placeholder, st.session_state.trace_items)

                    elif t == "todos":
                        st.session_state.tasks = ev.get("items", [])
                        ip = next(
                            (i for i, tk in enumerate(st.session_state.tasks, 1)
                             if tk.get("status") == "in_progress"),
                            None,
                        )
                        if ip:
                            cur_step = ip  # 步骤只前进;过渡期(无进行中步骤)的操作归到上一步
                        render_steps(steps_placeholder, st.session_state.tasks)
                        render_status(status_placeholder, st.session_state.tasks, True, False)

                    elif t == "final":
                        st.session_state.report_text = ev.get("content", "")
                        result_placeholder.markdown(st.session_state.report_text)
                        render_status(status_placeholder, st.session_state.tasks, False, True)

                    # thinking / assistant / tool_end 不展示:
                    #   前两者是模型口语化的自述("太好了、让我…"),太啰嗦不正式;
                    #   左侧只保留正式动作(读取/检索/命令数)与任务清单。

                st.session_state.review_finished = bool(st.session_state.report_text)
            except requests.exceptions.RequestException as e:
                result_placeholder.error(f"连接后端失败:{e}\n\n检查后端是否启动、地址是否正确。")
                st.session_state.report_text = ""
                st.session_state.review_finished = False
            finally:
                st.session_state.running = False
            st.rerun()  # 结束后刷新:按钮恢复可点、结果落定
        else:
            if st.button("开始合规审查", type="primary"):
                # 清空上一轮 + 进入运行态;rerun 后按钮会渲染成禁用态再开始
                st.session_state.trace_items = []
                st.session_state.tasks = []
                st.session_state.report_text = ""
                st.session_state.review_finished = False
                st.session_state.running = True
                st.rerun()
