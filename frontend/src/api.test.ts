import { describe, it, expect } from "vitest";
import { readEvents } from "./api";

describe("SSE framing", () => {
  it("decodes UTF-8 split across arbitrary chunks, CRLF and heartbeat", async () => {
    const bytes = new TextEncoder().encode(
      ': heartbeat\r\n\r\ndata: {"type":"final","content":"中文报告"}\r\n\r\ndata: {"type":"done"}\n\n',
    );
    const stream = new ReadableStream({
      start(controller) {
        for (let i = 0; i < bytes.length; i++)
          controller.enqueue(bytes.slice(i, i + 1));
        controller.close();
      },
    });
    const events: unknown[] = [];
    await readEvents(new Response(stream), (e) => events.push(e));
    expect(events).toEqual([
      { type: "final", content: "中文报告" },
      { type: "done" },
    ]);
  });
  it("does not treat an interrupted stream as completed", async () => {
    await expect(
      readEvents(
        new Response('data: {"type":"final","content":"partial"}\n\n'),
        () => {},
      ),
    ).rejects.toThrow("实时连接已断开");
  });
});
