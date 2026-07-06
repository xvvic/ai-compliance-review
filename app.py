"""
AI 合规审查系统 - 前端界面
============================================
功能:
- 支持txt/docx/pdf文件上传解析
- SSE流式对接后端，实时展示思考过程、工具调用轨迹
- 双栏布局：左侧执行过程，右侧审查结果
- 支持Markdown报告下载

运行方式:
    pip install streamlit python-docx pypdf requests
    streamlit run app.py
"""

import streamlit as st
import json
import requests


# ============================================================
# 页面基础配置
# ============================================================
st.set_page_config(page_title="AI 合规审查系统", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 初创企业合规审查系统")
st.caption("上传企业材料,自动识别合规风险 · 展示 AI 审查全过程")

# 侧边栏:后端地址配置
with st.sidebar:
    st.header("设置")
    backend_url = st.text_input(
        "后端接口地址",
        value="http://127.0.0.1:8000/review/stream",
        help="后端SSE接口地址，同WiFi下填队友局域网IP，ngrok穿透填公网地址",
    )
    st.divider()
    st.markdown("**使用说明**\n\n1. 上传待审查文件 → 2. 点击开始审查 → 3. 左侧查看AI执行过程，右侧查看最终报告")


# ============================================================
# 文件解析
# ============================================================
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


# ============================================================
# 后端SSE流对接
# ============================================================
def real_stream(url, text):
    """对接后端SSE流，逐事件yield"""
    resp = requests.post(url, json={"document_text": text}, stream=True, timeout=300)
    resp.raise_for_status()
    for line in resp.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                yield json.loads(decoded[6:])


# ============================================================
# 主界面
# ============================================================
uploaded = st.file_uploader("上传企业材料(txt / docx / pdf)", type=["txt", "docx", "pdf"])

if uploaded:
    text = parse_file(uploaded)
    if not text or not text.strip():
        st.error("文件解析为空,请检查文件(扫描版PDF可能无法提取文字)。")
    else:
        with st.expander("查看解析出的文本", expanded=False):
            st.text(text[:2000] + ("..." if len(text) > 2000 else ""))

        if st.button("🚀 开始合规审查", type="primary"):
            # 双栏布局
            col_trace, col_result = st.columns([1, 1])
            trace_box = col_trace.container()
            result_box = col_result.container()

            col_trace.subheader("🔍 AI 执行过程")
            col_result.subheader("📋 审查结果")

            trace_items = []     # 存储过程轨迹
            final_text = ""      # 存储最终报告

            trace_placeholder = trace_box.empty()
            result_placeholder = result_box.empty()

            # 流式接收事件并渲染
            for ev in real_stream(backend_url, text):
                t = ev.get("type")

                if t == "thinking":
                    trace_items.append(("💭 思考", ev.get("content", "")))
                elif t == "tool_start":
                    trace_items.append(("🔧 调用工具", f"**{ev.get('tool_name','')}**  \n入参: `{json.dumps(ev.get('args',{}), ensure_ascii=False)}`"))
                elif t == "tool_end":
                    res = ev.get('result','')
                    show_res = res[:500] + "..." if len(res) > 500 else res
                    trace_items.append(("✅ 工具返回", f"**{ev.get('tool_name','')}**  \n{show_res}"))
                elif t == "final":
                    final_text += ev.get("content", "")

                # 刷新轨迹区
                with trace_placeholder.container():
                    for label, content in trace_items:
                        st.markdown(f"**{label}**")
                        st.caption(content)
                        st.divider()

                # 刷新结果区
                with result_placeholder.container():
                    if final_text:
                        st.markdown(final_text)
                    else:
                        st.info("审查进行中,结果生成后显示在这里...")

            # 审查完成后提供下载
            if final_text:
                st.success("审查完成！")
                st.download_button(
                    "⬇️ 下载审查报告",
                    data=final_text,
                    file_name="合规审查报告.md",
                    mime="text/markdown",
                )
else:
    st.info("👆 请先上传一份企业材料文件开始审查。")