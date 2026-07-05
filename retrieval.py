import dashscope
import numpy as np

# 简版"法条库":先手写几条占位,之后换成MCP或自建库
LAWS = [
    "个人信息保护法第29条:处理敏感个人信息,应当取得个人的单独同意。",
    "个人信息保护法第39条:向境外提供个人信息,应当向个人告知并取得单独同意。",
    "数据安全法第21条:国家建立数据分类分级保护制度。",
    "网络安全法第41条:网络运营者收集使用个人信息应遵循合法正当必要原则。",
]

def _embed(text):
    """把文字变成向量(复用你学过的embedding)"""
    resp = dashscope.TextEmbedding.call(model="text-embedding-v3", input=text)
    return np.array(resp.output['embeddings'][0]['embedding'])

def _cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 预先把法条都向量化(建索引)
_LAW_VECTORS = [_embed(law) for law in LAWS]

def search(query, top_k=2):
    """输入查询,返回最相关的top_k条法条。这就是对外的检索接口。"""
    qv = _embed(query)
    scored = [(_cosine(qv, _LAW_VECTORS[i]), LAWS[i]) for i in range(len(LAWS))]
    scored.sort(reverse=True)
    return [law for score, law in scored[:top_k]]