import streamlit as st
from compliance_agent import compliance_review, law_search, case_search, risk_grade

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AI合规审查助手", 
    page_icon="⚖️", 
    layout="centered"
)

# ==================== 定义 Skill ====================
SKILLS = [
    {
        "id": "review", 
        "name": "📋 合规审查", 
        "desc": "完整风险分析",
        "command": "/review",
        "function": compliance_review
    },
    {
        "id": "law", 
        "name": "📚 查法条", 
        "desc": "检索法律法规",
        "command": "/law",
        "function": law_search
    },
    {
        "id": "case", 
        "name": "🔍 查案例", 
        "desc": "查询司法案例",
        "command": "/case",
        "function": case_search
    },
    {
        "id": "grade", 
        "name": "⚠️ 风险分级", 
        "desc": "判定风险等级",
        "command": "/grade",
        "function": risk_grade
    },
]

# ==================== 辅助函数 ====================
def get_skill_by_id(skill_id):
    return next((s for s in SKILLS if s["id"] == skill_id), None)

def get_skill_by_command(command):
    return next((s for s in SKILLS if s["command"] == command), None)

# ==================== 初始化状态 ====================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的AI合规审查助手。\n\n您可以：\n- 点击下方快捷按钮选择技能\n- 或在输入框输入 `/` 查看命令\n\n请描述您的业务场景或问题，我会为您进行合规分析。"}
    ]

if "current_skill" not in st.session_state:
    st.session_state.current_skill = "review"

# ==================== 侧边栏 ====================
with st.sidebar:
    st.title("⚖️ 合规审查助手")
    st.caption("AI驱动的企业合规审查系统")
    st.markdown("---")
    
    # 技能列表
    st.subheader("🎯 技能列表")
    for skill in SKILLS:
        if st.button(
            f"{skill['name']}", 
            use_container_width=True,
            key=f"sidebar_{skill['id']}",
            type="primary" if st.session_state.current_skill == skill["id"] else "secondary"
        ):
            st.session_state.current_skill = skill["id"]
            st.rerun()
    
    st.markdown("---")
    
    # 当前技能
    current_skill = get_skill_by_id(st.session_state.current_skill)
    st.subheader("📍 当前技能")
    st.info(f"**{current_skill['name']}**\n\n{current_skill['desc']}")
    
    st.markdown("---")
    
    # 斜杠命令说明
    with st.expander("⌨️ 斜杠命令"):
        st.markdown("在输入框输入以下命令：")
        for skill in SKILLS:
            st.markdown(f"- `{skill['command']}`：{skill['name']}")
        st.markdown("- `/help`：查看帮助")
        st.markdown("- `/clear`：清空对话")
    
    st.markdown("---")
    st.caption("挑战杯项目 · AI合规审查工作组")

# ==================== 主界面 ====================
st.title("💬 AI企业合规审查助手")
st.caption("基于 RAG + 大模型的智能合规审查系统")

# ===== 快捷按钮区 =====
st.markdown("---")
cols = st.columns(len(SKILLS))

for i, skill in enumerate(SKILLS):
    with cols[i]:
        is_active = st.session_state.current_skill == skill["id"]
        if st.button(
            skill["name"], 
            use_container_width=True,
            key=f"top_{skill['id']}",
            type="primary" if is_active else "secondary"
        ):
            st.session_state.current_skill = skill["id"]
            st.rerun()

st.markdown("---")

# ==================== 聊天区 ====================
for message in st.session_state.messages:
    with st.chat_message(
        message["role"], 
        avatar="🧑‍💼" if message["role"] == "user" else "⚖️"
    ):
        st.markdown(message["content"])

# ==================== 用户输入处理 ====================
prompt = st.chat_input("输入问题，或输入 / 查看可用命令...")

if prompt:
    # ===== 处理斜杠命令 =====
    if prompt.startswith("/"):
        command = prompt.strip().lower()
        
        # /help 命令
        if command == "/help":
            help_text = """**可用命令：**

| 命令 | 功能 |
|------|------|
"""
            for skill in SKILLS:
                help_text += f"| `{skill['command']}` | {skill['name']} - {skill['desc']} |\n"
            help_text += """
| `/help` | 查看帮助 |
| `/clear` | 清空对话 |

也可以点击上方快捷按钮切换技能。
"""
            with st.chat_message("assistant", avatar="⚖️"):
                st.markdown(help_text)
            st.session_state.messages.append({"role": "assistant", "content": help_text})
        
        # /clear 命令
        elif command == "/clear":
            st.session_state.messages = [
                {"role": "assistant", "content": "对话已清空，请重新开始。"}
            ]
            st.rerun()
        
        # 切换技能的命令
        elif get_skill_by_command(command):
            skill = get_skill_by_command(command)
            st.session_state.current_skill = skill["id"]
            switch_msg = f"✅ 已切换到 **{skill['name']}** 技能\n\n{skill['desc']}\n\n请输入您的问题或业务描述。"
            with st.chat_message("assistant", avatar="⚖️"):
                st.success(switch_msg)
            st.session_state.messages.append({"role": "assistant", "content": switch_msg})
            st.rerun()
        
        # 未知命令
        else:
            error_msg = f"❌ 未知命令：`{prompt}`\n\n输入 `/help` 查看可用命令。"
            with st.chat_message("assistant", avatar="⚖️"):
                st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # ===== 正常对话 =====
    else:
        # 显示用户消息
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 根据当前技能调用对应的函数
        with st.chat_message("assistant", avatar="⚖️"):
            with st.spinner("正在分析，请稍候..."):
                skill = get_skill_by_id(st.session_state.current_skill)
                response = skill["function"](prompt)
        
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})