from retrieval import search   # 检索零件
from llm import ask            # 调大模型零件

def load_skill(name):
    """读取一个skill文件(就是读一个md文本)"""
    with open(f"skills/{name}.md", encoding="utf-8") as f:
        return f.read()

def judge_dimension(维度, 材料):
    """对一个维度做要件判定:读skill → 检索 → 拼prompt → AI判断"""

    # ① 读取判定skill(方法论)
    skill = load_skill("element_judgment")

    # ② 检索相关法条(依据)
    法条列表 = search(材料)

    # ③ 把 skill + 材料 + 法条 拼成给AI的prompt
    法条文本 = "\n".join(f"- {t}" for t in 法条列表)
    prompt = f"""{skill}

【待审维度】
{维度}

【待审材料】
{材料}

【相关法条】
{法条文本}

请严格按技能说明中的"输出格式"输出JSON,只输出JSON,不要有其他文字。"""

    # ④ 调AI做判断
    结果 = ask(prompt)
    return 法条列表, 结果


# ===== 试跑:那个"人脸传美国/收集人脸"的场景 =====
if __name__ == "__main__":
    维度 = "个人信息处理"
    材料 = "我们在用户注册时收集人脸信息用于身份核验,但未单独征得用户同意"

    print("=" * 50)
    print(f"【维度】{维度}")
    print(f"【材料】{材料}\n")

    法条, 判断 = judge_dimension(维度, 材料)

    print("【检索到的法条】")
    for t in 法条:
        print(f"  - {t}")
    print("\n【AI要件判定结果】")
    print(判断)