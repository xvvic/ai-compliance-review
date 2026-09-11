"""Build a public example from the repository's synthetic evaluation fixture."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workbench.rag import CORPUS, normalize_chunks, report_citations


def example_rag():
    recorded = ROOT / "assets/knowledge/example-rag.json"
    if recorded.exists():
        rag = json.loads(recorded.read_text(encoding="utf-8"))
        appendix = "\n\n## RAG 引用示例\n\n预先生成的检索示例，未实时调用报告模型。下列原文片段可在检索依据中查看。\n\n"
        for fragment in rag["fragments"]:
            appendix += f"- {fragment['filename']} {fragment['tag']} [RAG:{fragment['id']}]\n"
        rag["cited_ids"] = report_citations(appendix, rag)
        return rag, appendix
    # Curated source excerpts for an offline UI example, not a claimed engine run.
    sources = [
        ("案例/国家网信办网络安全、数据安全、个人信息保护执法典型案例.txt", "8.", "App 超出必要范围收集个人信息的执法案例，可用于说明信息收集范围的核查事项。"),
        ("案例/国家网信办网络安全、数据安全、个人信息保护执法典型案例.txt", "10.", "深度合成服务未开展安全评估、未作显著标识的执法案例，可用于说明上线前核查事项。"),
        ("论文/TTAF 309—2025 生成式人工智能产品和服务风险分类分级指南.txt", "6.1 分级方法", "该参考指南按应用领域和潜在危害划分风险，并列出风险要素识别、影响分析等步骤；其分级不直接替代本系统 L1–L4 规则。"),
    ]
    chunks = []
    for path, anchor, _ in sources:
        text = (CORPUS / path).read_text(encoding="utf-8-sig")
        # Select the body occurrence, not an earlier table-of-contents entry.
        start = text.rindex(anchor)
        end = text.find("\n\n", start + len(anchor))
        if end < 0:
            end = len(text)
        if anchor.startswith("6.1"):
            end = text.index("6.2 风险要素", start)
        chunks.append({"file_path": path, "content": text[start:end].strip(), "chunk_id": f"example-{len(chunks) + 1}"})
    rag = {"provider": "本地 BM25", "mode": "lexical", "status": "retrieved", "example": True,
           "queries": ["个人信息收集范围", "深度合成服务安全评估与标识", "生成式人工智能风险分级"],
           "elapsed_ms": 0, "injected": False, "cited_ids": [], "fragments": normalize_chunks({"chunks": chunks})}
    assert len(rag["fragments"]) == len(sources)
    appendix = "\n\n## RAG 引用示例\n\n以下为固定原文节选对应的演示引用，未实时调用报告模型。\n\n"
    for fragment, (_, _, description) in zip(rag["fragments"], sources):
        appendix += f"- {description} {fragment['tag']} [RAG:{fragment['id']}]\n"
    rag["cited_ids"] = report_citations(appendix, rag)
    return rag, appendix


def main():
    source = ROOT / "eval" / "sample1_星云智算_risk_report.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    data["report_markdown"] = (ROOT / "eval" / "sample1_星云智算_report_r2.md").read_text(encoding="utf-8")
    data["review_id"] = "example-synthetic-001"
    data["example"] = True
    data["model"] = ""
    data["rag"], appendix = example_rag()
    data["report_markdown"] += appendix
    data["schema_version"] = "1.2"
    data["material"] = {"chars": data["material"]["chars"]}
    output = ROOT / "assets"
    output.mkdir(exist_ok=True)
    (output / "example-report.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
