import { describe, expect, it } from "vitest";
import { hasRag, ragCitationPlugin, type RagRecord } from "./RagEvidence";

describe("RAG display and citations", () => {
  it("requires actual fragments and a successful retrieval", () => {
    expect(hasRag()).toBe(false);
    for (const status of ["empty", "failed", "disabled", "retrieved"])
      expect(hasRag({ status, fragments: [] } as unknown as RagRecord)).toBe(false);
    expect(hasRag({ status: "failed", fragments: [{}] } as RagRecord)).toBe(false);
    expect(hasRag({ status: "retrieved", fragments: [{}] } as RagRecord)).toBe(true);
  });
  it("links known citations in text but leaves unknown IDs and code unchanged", () => {
    const tree: any = { type: "root", children: [
      { type: "paragraph", children: [{ type: "text", value: "依据 [RAG:S01]，未知 [RAG:S99]。" }] },
      { type: "inlineCode", value: "[RAG:S01]" },
      { type: "link", url: "https://example.com", children: [{ type: "text", value: "[RAG:S01]" }] },
    ] };
    ragCitationPlugin(["S01"])()(tree);
    expect(tree.children[0].children[1].url).toBe("#rag-S01");
    expect(tree.children[0].children[2].value).toContain("[RAG:S99]");
    expect(tree.children[1].value).toBe("[RAG:S01]");
    expect(tree.children[2].children[0].type).toBe("text");
  });
});
