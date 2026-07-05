from llm import ask
# from pkulaw_mcp import search_law_articles, search_cases  # 等 MCP 能用了再打开注释


# ========== 各个 Skill 的系统提示词 ==========

# 合规审查 Skill 的系统提示词
REVIEW_SYSTEM_PROMPT = """
你是一名专业的企业合规律师，擅长数据合规、劳动合规、知识产权合规等领域。

请严格按照以下要求回答用户的问题：
1. 只能基于提供的参考资料进行回答，不要编造法条和案例
2. 如果参考资料中没有相关信息，请明确说明
3. 回答必须包含：风险等级、风险点、法律依据、相似案例、整改建议
4. 风险等级分为三级：🟢低风险、🟡中风险、🔴高风险
5. 语言要专业、严谨，符合法律文书规范
6. 最后必须加上免责声明：以上分析仅供参考，最终结论请咨询专业律师
"""

# 法条检索 Skill 的系统提示词
LAW_SEARCH_SYSTEM_PROMPT = """
你是法律检索助手，负责整理和展示检索到的法律法规。

请将检索到的法条按照以下格式整理：
1. 每条法条标明法律名称和条款号
2. 引用法条原文
3. 按照相关性从高到低排序
4. 语言简洁、清晰
"""

# 案例查询 Skill 的系统提示词
CASE_SEARCH_SYSTEM_PROMPT = """
你是案例检索助手，负责整理和展示检索到的司法案例。

请将检索到的案例按照以下格式整理：
1. 每个案例标明案例名称、处罚机关、处罚时间
2. 简要说明违法事实和处罚结果
3. 按照相关性从高到低排序
4. 语言简洁、清晰
"""

# 风险分级 Skill 的系统提示词
RISK_GRADE_SYSTEM_PROMPT = """
你是风险评估专家，负责对企业合规风险进行分级。

风险等级分为三级：
- 🟢 L1 低风险：规则明确、法条清晰、可模板化处理的问题
- 🟡 L2 中风险：需要法律判断、依赖案例参考的问题
- 🔴 L3 高风险：涉及监管、国家安全、重大决策的问题

请根据用户描述的内容，判断风险等级，并说明分级理由。
"""


# ========== 各个 Skill 的实现 ==========

def compliance_review(user_input):
    """
    完整合规审查 Skill
    流程：检索法条 → 检索案例 → 组装 Prompt → 大模型生成结论
    """
    
    # ===== 第一步：检索法条和案例（MCP 能用了再打开注释） =====
    # print("正在检索法律法规...")
    # law_articles = search_law_articles(user_input)
    # 
    # print("正在检索相似案例...")
    # cases = search_cases(user_input)
    
    # 临时：MCP 还没通的时候，用演示数据（后面删掉）
    law_articles = """
    1. 《中华人民共和国个人信息保护法》第六条
       处理个人信息应当具有明确、合理的目的，并应当与处理目的直接相关，采取对个人权益影响最小的方式。
       收集个人信息，应当限于实现处理目的的最小范围，不得过度收集个人信息。
    
    2. 《中华人民共和国个人信息保护法》第十三条
       符合下列情形之一的，个人信息处理者方可处理个人信息：
       （一）取得个人的同意；
       （二）为订立、履行个人作为一方当事人的合同所必需...
    """
    
    cases = """
    1. 某科技有限公司个人信息保护行政处罚案
       处罚机关：XX市市场监督管理局
       处罚时间：2024年3月
       违法事实：过度收集用户位置信息，超出业务必要范围
       处罚结果：责令改正，警告，罚款人民币50万元
    """
    
    # ===== 第二步：组装 Prompt =====
    reference_material = f"""
【相关法律法规】
{law_articles}

【相似案例】
{cases}
"""
    
    user_prompt = f"""
【用户问题】
{user_input}

【参考资料】
{reference_material}

请根据以上参考资料，对用户的问题进行合规风险分析，按照以下格式输出：

## 风险等级
（🟢低风险 / 🟡中风险 / 🔴高风险）

## 风险点识别
（列出具体的风险点）

## 法律依据
（列出相关的法条）

## 相似案例
（列出相关的案例）

## 整改建议
（给出具体的整改建议）

---
*注：以上分析仅供参考，最终结论请咨询专业律师。*
"""
    
    # ===== 第三步：调用大模型 =====
    print("正在生成合规分析报告...")
    result = ask(user_prompt, system_prompt=REVIEW_SYSTEM_PROMPT, temperature=0.3)
    
    return result


def law_search(user_input):
    """法条检索 Skill"""
    
    # 检索法条（MCP 能用了再打开注释）
    # law_articles = search_law_articles(user_input)
    
    # 临时演示数据
    law_articles = f"""
    1. 《中华人民共和国个人信息保护法》第六条
       处理个人信息应当具有明确、合理的目的，并应当与处理目的直接相关，采取对个人权益影响最小的方式。
       收集个人信息，应当限于实现处理目的的最小范围，不得过度收集个人信息。
    
    2. 《中华人民共和国个人信息保护法》第十三条
       符合下列情形之一的，个人信息处理者方可处理个人信息：
       （一）取得个人的同意；
       （二）为订立、履行个人作为一方当事人的合同所必需...
    
    3. 《中华人民共和国网络安全法》第四十一条
       网络运营者收集、使用个人信息，应当遵循合法、正当、必要的原则...
    """
    
    # 让大模型整理格式
    prompt = f"""
查询关键词：{user_input}

检索结果：
{law_articles}

请按照规范格式整理以上检索结果。
"""
    
    result = ask(prompt, system_prompt=LAW_SEARCH_SYSTEM_PROMPT, temperature=0.2)
    return result


def case_search(user_input):
    """案例查询 Skill"""
    
    # 检索案例（MCP 能用了再打开注释）
    # cases = search_cases(user_input)
    
    # 临时演示数据
    cases = f"""
    1. 某科技有限公司个人信息保护行政处罚案
       处罚机关：XX市市场监督管理局
       处罚时间：2024年3月
       违法事实：过度收集用户位置信息，超出业务必要范围
       处罚结果：责令改正，警告，罚款人民币50万元
    
    2. 某移动应用程序违法违规收集使用个人信息案
       处罚机关：国家互联网信息办公室
       处罚时间：2023年11月
       违法事实：违反必要原则，收集与服务无关的个人信息
       处罚结果：责令限期整改，公开通报，下架处理
    """
    
    # 让大模型整理格式
    prompt = f"""
查询关键词：{user_input}

检索结果：
{cases}

请按照规范格式整理以上检索结果。
"""
    
    result = ask(prompt, system_prompt=CASE_SEARCH_SYSTEM_PROMPT, temperature=0.2)
    return result


def risk_grade(user_input):
    """风险分级 Skill"""
    
    prompt = f"""
请对以下内容进行合规风险分级：

{user_input}
"""
    
    result = ask(prompt, system_prompt=RISK_GRADE_SYSTEM_PROMPT, temperature=0.3)
    return result


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("测试：合规审查")
    print("=" * 60)
    result = compliance_review("我们APP收集用户位置信息，合规吗？")
    print(result)
    
    print("\n" + "=" * 60)
    print("测试：法条检索")
    print("=" * 60)
    result = law_search("个人信息最小必要原则")
    print(result)
    
    print("\n" + "=" * 60)
    print("测试：案例查询")
    print("=" * 60)
    result = case_search("过度收集个人信息 处罚")
    print(result)
    
    print("\n" + "=" * 60)
    print("测试：风险分级")
    print("=" * 60)
    result = risk_grade("我们公司要把用户数据传到海外")
    print(result)