import { Drawer, Tag } from "antd";
import { Database, ArrowRight } from "lucide-react";

export type RagFragment = {
  id: string;
  source_id: string;
  filename: string;
  path: string;
  category: string;
  tag: string;
  line_start: number | null;
  line_end: number | null;
  text: string;
  truncated?: boolean;
};
export type RagRecord = {
  provider: string;
  mode: string;
  status: string;
  queries: string[];
  elapsed_ms: number;
  fragments: RagFragment[];
  injected: boolean;
  cited_ids: string[];
  example?: boolean;
  knowledge_version?: string;
  embedding_model?: string;
  example_origin?: string;
};
export function hasRag(rag?: RagRecord): rag is RagRecord {
  return rag?.status === "retrieved" && rag.fragments.length > 0;
}

// Convert only ordinary Markdown text, never code or existing links.
export function ragCitationPlugin(ids: string[]) {
  const valid = new Set(ids);
  return () => (tree: any) => {
    const visit = (node: any) => {
      if (!node.children || ["link", "linkReference", "code", "inlineCode"].includes(node.type)) return;
      node.children = node.children.flatMap((child: any) => {
        if (child.type !== "text") {
          visit(child);
          return [child];
        }
        const parts: any[] = [];
        let offset = 0;
        for (const match of child.value.matchAll(/\[RAG:(S\d{2})\]/g)) {
          if (!valid.has(match[1])) continue;
          parts.push({ type: "text", value: child.value.slice(offset, match.index) });
          parts.push({ type: "link", url: `#rag-${match[1]}`, children: [{ type: "text", value: match[0] }] });
          offset = match.index + match[0].length;
        }
        parts.push({ type: "text", value: child.value.slice(offset) });
        return parts;
      });
    };
    visit(tree);
  };
}

export function RagSummary({ rag, onOpen, example = false }: { rag?: RagRecord; onOpen: () => void; example?: boolean }) {
  if (!hasRag(rag)) return null;
  return (
    <section className="rag-summary" aria-label="RAG 检索增强">
      <Database size={23} />
      <div className="rag-summary-copy">
        <strong>RAG 检索增强{example ? " · 示例" : ` · ${rag.provider}`}</strong>
        <span>{new Set(rag.fragments.map(f => f.path)).size} 份来源 · {rag.fragments.length} 个片段
          {!example && ` · ${rag.injected ? "已加入生成上下文" : "已检索"}`}
        </span>
        {example && <span>{rag.example_origin === "precomputed" ? "预先生成的检索示例，未实时调用报告模型" : "示例引用数据，未实时调用 LightRAG 或模型"}</span>}
      </div>
      <button className="rag-open" onClick={onOpen}>RAG 检索依据 <ArrowRight size={15} /></button>
    </section>
  );
}

export function RagEvidence({ rag, open, selectedId, onClose, example = false }: {
  rag?: RagRecord; open: boolean; selectedId: string | null; onClose: () => void; example?: boolean;
}) {
  if (!hasRag(rag)) return null;
  return (
    <Drawer title="RAG 检索依据" width={660} open={open} onClose={onClose}
      afterOpenChange={(visible) => { if (visible && selectedId) document.getElementById(`evidence-${selectedId}`)?.scrollIntoView({ block: "start" }); }}>
      <div className="rag-evidence">
        <p className="rag-note">{example ? (rag.example_origin === "precomputed" ? "预先生成的检索示例，未实时调用报告模型。" : "示例引用数据，未实时调用 LightRAG 或模型。") : `LightRAG · 向量检索 · ${rag.elapsed_ms} 毫秒`}</p>
        {rag.knowledge_version && <p className="rag-note">知识库版本：{rag.knowledge_version}</p>}
        <h3>{example ? "示例检索主题" : "检索查询"}</h3>
        <ul className="rag-queries">{rag.queries.map((q, i) => <li key={i}>{q}</li>)}</ul>
        {rag.fragments.map(f => (
          <section key={f.id} id={`evidence-${f.id}`} className={`rag-fragment ${f.id === selectedId ? "selected" : ""}`}>
            <div className="rag-fragment-labels"><Tag>{f.id}</Tag><Tag>{f.category}</Tag>
              {rag.cited_ids.includes(f.id) && <Tag color="success">{example ? "示例报告引用" : "报告引用"}</Tag>}
            </div>
            <h3>{f.filename}</h3>
            <p className="rag-source">{f.path}{f.line_start != null ? ` · 第 ${f.line_start}–${f.line_end} 行` : " · 来源未提供可核对行号"}</p>
            <blockquote>{f.text}</blockquote>
            {f.truncated && <small>片段过长，仅展示已加入上下文的节选。</small>}
          </section>
        ))}
      </div>
    </Drawer>
  );
}
