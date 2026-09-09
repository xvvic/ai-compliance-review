import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Alert,
  App as AntApp,
  Button,
  Checkbox,
  Collapse,
  ConfigProvider,
  Drawer,
  Dropdown,
  Empty,
  Form,
  Input,
  Modal,
  Select,
  Spin,
  Table,
  Tabs,
  Tag,
  Tooltip,
  Upload,
} from "antd";
import zhCN from "antd/locale/zh_CN";
import {
  ArrowDownToLine,
  ArrowRight,
  Check,
  CheckCheck,
  ChevronRight,
  CircleHelp,
  Clock3,
  FileCheck2,
  FileText,
  FolderOpen,
  Layers3,
  ListChecks,
  LoaderCircle,
  PanelLeftClose,
  Plus,
  Search,
  Settings2,
  ShieldCheck,
  Square,
  UploadCloud,
  X,
} from "lucide-react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, initialize, readEvents, request } from "./api";
import "./styles.css";

type Rule = {
  id: string;
  category: string;
  risk_type: string;
  final_level: string;
  human_review_required: boolean;
  matched_keywords: Record<string, number>;
  evidence_needed: string[];
  remediation_hint: string;
  semantic_cues: string;
};
type Report = {
  generated_at: string;
  model: string;
  report_markdown: string;
  risk_scan: { matched_rules: Rule[]; error?: string };
  material: { chars: number };
  review_id: string;
};
type Job = {
  id: string;
  status: string;
  filename: string;
  started_at: string;
  report: Report | null;
  tasks: { content: string; status: string }[];
  activities: { label: string; at: string }[];
  error?: string;
  save_error?: string;
  saved: boolean;
  reviewed: boolean;
  decisions?: Decision[];
};
type Decision = {
  rule_id: string;
  action: string;
  review_level: string;
  evidence_note: string;
};
const levels = ["L4", "L3", "L2", "L1"];
const levelNames: Record<string, string> = {
  L4: "重大",
  L3: "高风险",
  L2: "中风险",
  L1: "低风险",
};
const statusNames: Record<string, string> = {
  running: "审查进行中",
  completed: "审查完成",
  failed: "审查失败",
  cancelled: "已取消",
};
const badge = (level: string) => (
  <span className={`risk-badge ${level}`}>
    {level} · {levelNames[level]}
  </span>
);
function download(data: string, filename: string, type: string) {
  const url = URL.createObjectURL(new Blob([data], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Workbench() {
  const { message, modal } = AntApp.useApp();
  const [ready, setReady] = useState(false),
    [config, setConfig] = useState<any>(null),
    [settingsOpen, setSettingsOpen] = useState(false);
  const [job, setJob] = useState<Job | null>(null),
    [example, setExample] = useState<Report | null>(null);
  const [doc, setDoc] = useState<{
    filename: string;
    text: string;
    chars: number;
    bytes: number;
  } | null>(null);
  const [loading, setLoading] = useState(false),
    [starting, setStarting] = useState(false),
    [error, setError] = useState("");
  const [tab, setTab] = useState("report"),
    [filter, setFilter] = useState("all"),
    [search, setSearch] = useState("");
  const [detail, setDetail] = useState<Rule | null>(null),
    [decisions, setDecisions] = useState<Record<string, Decision>>({}),
    [submitting, setSubmitting] = useState(false);
  const [processOpen, setProcessOpen] = useState(true),
    [tick, setTick] = useState(Date.now()),
    [settingsForm] = Form.useForm();
  const [saving, setSaving] = useState(false),
    [testing, setTesting] = useState(false),
    [testResult, setTestResult] = useState<{
      ok: boolean;
      text: string;
    } | null>(null);
  const consuming = useRef(false);
  const report = example || job?.report;
  const running = starting || job?.status === "running";
  const rules = report?.risk_scan.matched_rules || [];
  const must = rules.filter(
    (r) => r.human_review_required || ["L3", "L4"].includes(r.final_level),
  ).length;
  const refresh = async () => {
    const current = await api("/api/review/current");
    setJob(current);
    return current;
  };
  const showError = (e: unknown) =>
    setError(e instanceof Error ? e.message : "操作失败，请重试。");
  const consume = async (response: Response) => {
    consuming.current = true;
    try {
      await readEvents(response, () => {});
      await refresh();
    } finally {
      consuming.current = false;
    }
  };
  useEffect(() => {
    initialize()
      .then(async () => {
        const initialConfig = await api("/api/config");
        setConfig(initialConfig);
        if (initialConfig.config_error) setError(initialConfig.config_error);
        const current = await refresh();
        setReady(true);
        if (current?.status === "running")
          consume(await request(`/api/review/${current.id}/events`)).catch(
            showError,
          );
      })
      .catch(showError);
  }, []);
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => {
      setTick(Date.now());
      refresh().catch(showError);
    }, 1000);
    return () => clearInterval(id);
  }, [running]);
  useEffect(() => {
    if (job?.decisions)
      setDecisions(
        Object.fromEntries(job.decisions.map((d) => [d.rule_id, d])),
      );
  }, [job?.id, job?.reviewed]);

  const upload = async (file: File) => {
    if (file.size > 20 * 1024 * 1024) {
      setError("文件不能超过 20MB。");
      return false;
    }
    setLoading(true);
    setError("");
    try {
      const data = new FormData();
      data.append("file", file);
      setDoc(await api("/api/documents/parse", "POST", data));
    } catch (e) {
      showError(e);
    } finally {
      setLoading(false);
    }
    return false;
  };
  const newReview = () => {
    const reset = () => {
      setJob(null);
      setExample(null);
      setDoc(null);
      setDecisions({});
      setError("");
      setTab("report");
      setFilter("all");
      setSearch("");
    };
    if (report && !example)
      modal.confirm({
        title: "开始新的审查？",
        content: "当前页面将清空，请确认所需报告已下载。",
        okText: "新建审查",
        cancelText: "返回",
        onOk: reset,
      });
    else reset();
  };
  const start = async () => {
    if (!doc) return;
    if (!config?.configured) {
      openSettings();
      return;
    }
    setError("");
    setStarting(true);
    setExample(null);
    setDecisions({});
    setTab("report");
    try {
      const response = await request("/review/stream", "POST", {
        document_text: doc.text,
        filename: doc.filename,
      });
      await refresh();
      setStarting(false);
      await consume(response);
    } catch (e) {
      showError(e);
    } finally {
      setStarting(false);
    }
  };
  const openExample = async () => {
    try {
      setExample(await api("/api/example"));
      setTab("report");
      setError("");
      setDecisions({});
    } catch (e) {
      showError(e);
    }
  };
  const openSettings = () => {
    settingsForm.setFieldsValue({
      ...config,
      secret: "",
      mcp_token: "",
      clear_secret: false,
      clear_mcp_token: false,
    });
    setTestResult(null);
    setSettingsOpen(true);
  };
  const saveSettings = async (test: boolean) => {
    try {
      const data = await settingsForm.validateFields();
      test ? setTesting(true) : setSaving(true);
      const result = await api(
        test ? "/api/config/test" : "/api/config",
        test ? "POST" : "PUT",
        data,
      );
      if (test) setTestResult({ ok: true, text: result.message });
      else {
        setConfig(result);
        setSettingsOpen(false);
        message.success("设置已保存");
      }
    } catch (e) {
      if (e instanceof Error) setTestResult({ ok: false, text: e.message });
    } finally {
      setSaving(false);
      setTesting(false);
    }
  };
  const choose = (rule: Rule, patch: Partial<Decision>) =>
    setDecisions((old) => ({
      ...old,
      [rule.id]: {
        ...(old[rule.id] || {
          rule_id: rule.id,
          action: "",
          review_level: rule.final_level,
          evidence_note: "",
        }),
        ...patch,
      },
    }));
  const submit = async () => {
    setSubmitting(true);
    try {
      await api(`/api/review/${job!.id}/decisions`, "POST", {
        items: rules.map((r) => decisions[r.id]),
      });
      await refresh();
      message.success("复核记录已保存");
    } catch (e) {
      showError(e);
    } finally {
      setSubmitting(false);
    }
  };
  const completeDecisions =
    rules.length > 0 &&
    rules.every(
      (r) =>
        decisions[r.id]?.action &&
        (decisions[r.id].action === "认可初评" ||
          decisions[r.id].evidence_note.trim()),
    );
  const visibleRules = rules.filter(
    (r) =>
      (filter === "all" || r.final_level === filter) &&
      `${r.id}${r.category}${r.risk_type}`.includes(search),
  );
  const headings = report?.report_markdown.match(/^#{1,3}\s+.+$/gm) || [];
  const reportPane = report ? (
    <div className="report-layout">
      <article className="report-paper">
        <div className="paper-meta">
          <span>COMPLIANCE REVIEW</span>
          <span>
            {example ? "合成案例 · 示例" : report.generated_at.slice(0, 10)}
          </span>
        </div>
        <Markdown
          remarkPlugins={[remarkGfm]}
          skipHtml
          components={{
            h1: ({ children }) => <h1 id={String(children)}>{children}</h1>,
            h2: ({ children }) => <h2 id={String(children)}>{children}</h2>,
            h3: ({ children }) => <h3 id={String(children)}>{children}</h3>,
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noreferrer">
                {children}
              </a>
            ),
            table: ({ children }) => (
              <div className="markdown-table">
                <table>{children}</table>
              </div>
            ),
          }}
        >
          {report.report_markdown}
        </Markdown>
      </article>
      <aside className="report-toc">
        <span className="small-title">报告目录</span>
        {headings.slice(0, 18).map((h, i) => (
          <a key={i} href={`#${encodeURIComponent(h.replace(/^#+\s+/, ""))}`}>
            {h.replace(/^#+\s+/, "")}
          </a>
        ))}
        <div className="toc-note">
          <ShieldCheck size={18} />
          <span>
            合规审查工作底稿
            <br />
            结论需经人工复核
          </span>
        </div>
      </aside>
    </div>
  ) : null;

  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand-symbol">
          <ShieldCheck size={24} />
        </div>
        <div className="rail-links">
          <Tooltip title="审查工作台" placement="right">
            <button className="rail-button active" aria-label="审查工作台">
              <Layers3 size={22} />
            </button>
          </Tooltip>
        </div>
        <Tooltip title="连接设置" placement="right">
          <button
            className="rail-button"
            aria-label="连接设置"
            onClick={openSettings}
            disabled={!ready}
          >
            <Settings2 size={21} />
          </button>
        </Tooltip>
        <span className="rail-version">1.0</span>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="brand-name">
            AI 初创企业合规审查系统 <span className="edition">WORKBENCH</span>
          </div>
          <div className="top-actions">
            <span
              className={`connection ${config?.configured ? "connected" : ""}`}
            >
              <i />
              {config?.configured ? "模型已配置" : "模型未配置"}
            </span>
            <Button
              icon={<Settings2 size={16} />}
              onClick={openSettings}
              disabled={!ready}
            >
              设置
            </Button>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="breadcrumb">
                合规管理 <ChevronRight size={12} /> 审查工作台
              </div>
              <h1>
                合规审查<span className="heading-mark">工作台</span>
              </h1>
              <p>企业材料评估与风险复核</p>
            </div>
            <Button
              icon={<Plus size={16} />}
              onClick={newReview}
              disabled={!!running}
            >
              新建审查
            </Button>
          </div>
          {error && (
            <Alert
              className="page-alert"
              type="error"
              showIcon
              message={error}
              closable
              onClose={() => setError("")}
            />
          )}
          {!ready && !error && (
            <div className="loading-surface">
              <Spin />
            </div>
          )}
          {ready && !report && !running && !job && (
            <>
              <div className="workflow-strip">
                <span className="selected">
                  <b>01</b> 材料准备
                </span>
                <ChevronRight size={15} />
                <span>
                  <b>02</b> 智能审查
                </span>
                <ChevronRight size={15} />
                <span>
                  <b>03</b> 人工复核
                </span>
              </div>
              <div className="intake-grid">
                <section className="intake">
                  <div className="section-title">
                    <div>
                      <h2>待审查材料</h2>
                      <span className="muted">
                        企业方案、数据清单或产品上线材料
                      </span>
                    </div>
                    <span className="section-number">01 / 03</span>
                  </div>
                  <Upload.Dragger
                    accept=".txt,.docx,.pdf"
                    multiple={false}
                    showUploadList={false}
                    beforeUpload={upload}
                    disabled={loading}
                  >
                    <div className="upload-icon">
                      {loading ? (
                        <LoaderCircle className="spin" size={30} />
                      ) : (
                        <UploadCloud size={30} />
                      )}
                    </div>
                    <h3>
                      {loading
                        ? "正在解析材料"
                        : doc
                          ? "替换审查材料"
                          : "选择或拖入企业材料"}
                    </h3>
                    <p>
                      TXT、DOCX、PDF<span>单份不超过 20MB</span>
                    </p>
                    <span className="upload-action">
                      选择文件 <ArrowRight size={15} />
                    </span>
                  </Upload.Dragger>
                  {doc && (
                    <div className="file-row">
                      <FileText size={22} />
                      <div>
                        <strong>{doc.filename}</strong>
                        <span>{doc.chars.toLocaleString()} 字符 · 已解析</span>
                      </div>
                      <Check size={17} />
                      <Tooltip title="移除材料">
                        <Button
                          type="text"
                          aria-label="移除材料"
                          icon={<X size={16} />}
                          onClick={() => setDoc(null)}
                        />
                      </Tooltip>
                    </div>
                  )}
                  {doc && (
                    <Collapse
                      ghost
                      items={[
                        {
                          key: "preview",
                          label: "材料预览",
                          children: (
                            <pre className="text-preview">{doc.text}</pre>
                          ),
                        },
                      ]}
                    />
                  )}
                  <div className="intake-footer">
                    <span>
                      <ShieldCheck size={16} /> 材料在本机解析
                    </span>
                    <Button
                      type="primary"
                      size="large"
                      disabled={!doc || loading}
                      onClick={start}
                      icon={<ArrowRight size={17} />}
                      iconPosition="end"
                    >
                      {config?.configured ? "开始审查" : "配置模型并审查"}
                    </Button>
                  </div>
                </section>
                <aside className="sample-panel">
                  <div className="section-title">
                    <h2>审查示例</h2>
                    <Tag bordered={false}>合成案例</Tag>
                  </div>
                  <div className="sample-preview">
                    <img
                      src="/report-preview.png"
                      alt="星云智算合成案例的审查报告预览"
                    />
                  </div>
                  <div className="sample-caption">
                    <FileCheck2 size={19} />
                    <div>
                      <strong>星云智算 · 产品上线方案</strong>
                      <span>审查报告与规则预扫描结果</span>
                    </div>
                  </div>
                  <Button
                    block
                    onClick={openExample}
                    icon={<ArrowRight size={16} />}
                    iconPosition="end"
                  >
                    查看示例报告
                  </Button>
                </aside>
              </div>
              <div className="scope-band">
                <div>
                  <span className="small-title">审查领域</span>
                  <h3>企业业务与合规风险</h3>
                </div>
                <div className="scope-labels">
                  {[
                    "数据与隐私",
                    "AI 治理",
                    "知识产权",
                    "网络安全",
                    "跨境业务",
                    "消费者权益",
                  ].map((x) => (
                    <span key={x}>{x}</span>
                  ))}
                </div>
              </div>
            </>
          )}
          {(running || (job && !report)) && (
            <section className="run-surface">
              <div className="run-title">
                <div>
                  <span className="small-title">
                    {job?.filename || doc?.filename}
                  </span>
                  <h2>
                    {starting
                      ? "正在建立审查任务"
                      : statusNames[job?.status || "running"]}
                  </h2>
                </div>
                {running && job?.id && (
                  <Button
                    danger
                    icon={<Square size={14} />}
                    onClick={() =>
                      api(`/api/review/${job.id}/cancel`, "POST")
                        .then(setJob)
                        .catch(showError)
                    }
                  >
                    取消审查
                  </Button>
                )}
              </div>
              {running ? (
                <>
                  <div className="run-center">
                    <div className="scan-symbol">
                      <ShieldCheck size={36} />
                    </div>
                    <h3>
                      {job?.tasks.find((t) => t.status === "in_progress")
                        ?.content || "正在规划审查步骤"}
                    </h3>
                    <p>
                      <Clock3 size={14} />{" "}
                      {Math.max(
                        0,
                        Math.floor(
                          (tick -
                            new Date(job?.started_at || Date.now()).getTime()) /
                            1000,
                        ),
                      )}{" "}
                      秒
                    </p>
                  </div>
                  <div className="process-toolbar">
                    <span>审查过程</span>
                    <Button
                      type="text"
                      icon={<PanelLeftClose size={15} />}
                      onClick={() => setProcessOpen(!processOpen)}
                    >
                      {processOpen ? "收起" : "展开"}
                    </Button>
                  </div>
                  {processOpen && (
                    <div className="process-grid">
                      <div>
                        {job?.tasks.map((t, i) => (
                          <div className={`task-row ${t.status}`} key={i}>
                            <span>
                              {t.status === "completed" ? (
                                <Check size={14} />
                              ) : (
                                i + 1
                              )}
                            </span>
                            {t.content}
                          </div>
                        ))}
                      </div>
                      <div className="activity-list">
                        {job?.activities
                          .slice(-8)
                          .reverse()
                          .map((a, i) => (
                            <div key={i}>
                              <span>{a.label}</span>
                              <time>
                                {new Date(a.at).toLocaleTimeString("zh-CN")}
                              </time>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <Alert
                    type={job?.status === "failed" ? "error" : "info"}
                    showIcon
                    message={job?.error || "本次审查已取消，未生成正式报告。"}
                  />
                  <Button
                    className="retry-button"
                    type="primary"
                    onClick={doc ? start : newReview}
                  >
                    {doc ? "重新审查" : "上传材料"}
                  </Button>
                </>
              )}
            </section>
          )}
          {report && (
            <>
              <div className="result-heading">
                <div>
                  <span className="result-status">
                    <CheckCheck size={16} />
                    {example ? "示例报告" : "审查完成"}
                  </span>
                  <span className="result-filename">
                    {example ? "星云智算 · 产品上线方案" : job?.filename}
                  </span>
                </div>
              <Dropdown
                trigger={["click"]}
                  menu={{
                    items: [
                      {
                        key: "md",
                        label: "Markdown 报告",
                        onClick: () =>
                          download(
                            report.report_markdown,
                            "compliance_report.md",
                            "text/markdown",
                          ),
                      },
                      {
                        key: "json",
                        label: "结构化 JSON",
                        onClick: () =>
                          download(
                            JSON.stringify(report, null, 2),
                            "risk_report.json",
                            "application/json",
                          ),
                      },
                    ],
                  }}
                >
                  <Button icon={<ArrowDownToLine size={16} />}>下载报告</Button>
                </Dropdown>
              </div>
              {example && (
                <Alert
                  className="page-alert"
                  type="info"
                  message="当前为合成案例示例，未调用模型，不提交正式复核记录。"
                />
              )}
              {job?.save_error && !example && (
                <Alert
                  className="page-alert"
                  type="warning"
                  message={job.save_error}
                />
              )}
              {report.risk_scan.error && (
                <Alert
                  className="page-alert"
                  type="warning"
                  message={report.risk_scan.error}
                />
              )}
              <div className="risk-summary">
                <div className="summary-total">
                  <span>规则预扫描命中</span>
                  <strong>
                    {report.risk_scan.error ? "未完成" : rules.length}
                    <small>{!report.risk_scan.error && "项"}</small>
                  </strong>
                </div>
                {levels.map((l) => (
                  <button
                    key={l}
                    onClick={() => {
                      setFilter(l);
                      setTab("risks");
                    }}
                  >
                    <span>
                      <i className={`dot ${l}`} />
                      {l} {levelNames[l]}
                    </span>
                    <strong>
                      {rules.filter((r) => r.final_level === l).length}
                    </strong>
                  </button>
                ))}
                <div className="summary-review">
                  <span>需人工复核</span>
                  <strong>
                    {must}
                    <small>项</small>
                  </strong>
                </div>
              </div>
              <Tabs
                activeKey={tab}
                onChange={setTab}
                items={[
                  {
                    key: "report",
                    label: (
                      <span className="tab-label">
                        <FileText size={16} />
                        审查报告
                      </span>
                    ),
                    children: reportPane,
                  },
                  {
                    key: "risks",
                    label: (
                      <span className="tab-label">
                        <ListChecks size={16} />
                        风险清单{" "}
                        <span className="tab-count">{rules.length}</span>
                      </span>
                    ),
                    children: (
                      <div className="risk-list">
                        <div className="table-toolbar">
                          <h2>规则预扫描结果</h2>
                          <div>
                            <Input
                              placeholder="搜索风险或规则编号"
                              prefix={<Search size={15} />}
                              value={search}
                              onChange={(e) => setSearch(e.target.value)}
                            />
                            <Select
                              aria-label="风险等级"
                              value={filter}
                              onChange={setFilter}
                              options={[
                                { value: "all", label: "全部等级" },
                                ...levels.map((l) => ({
                                  value: l,
                                  label: `${l} ${levelNames[l]}`,
                                })),
                              ]}
                            />
                          </div>
                        </div>
                        <Table
                          rowKey="id"
                          dataSource={visibleRules}
                          pagination={false}
                          scroll={{ x: 680 }}
                          columns={[
                            {
                              title: "风险事项",
                              dataIndex: "risk_type",
                              render: (_, r: Rule) => (
                                <button
                                  className="risk-link"
                                  onClick={() => setDetail(r)}
                                >
                                  <strong>{r.risk_type}</strong>
                                  <span>
                                    {r.id} · {r.category}
                                  </span>
                                </button>
                              ),
                            },
                            {
                              title: "初评等级",
                              dataIndex: "final_level",
                              width: 135,
                              render: badge,
                            },
                            {
                              title: "复核要求",
                              width: 135,
                              render: (_, r: Rule) =>
                                r.human_review_required ||
                                ["L3", "L4"].includes(r.final_level) ? (
                                  <span className="required-label">
                                    必须复核
                                  </span>
                                ) : (
                                  "常规复核"
                                ),
                            },
                            {
                              title: "",
                              width: 60,
                              render: (_, r: Rule) => (
                                <Button
                                  aria-label={`查看 ${r.id}`}
                                  type="text"
                                  icon={<ChevronRight size={16} />}
                                  onClick={() => setDetail(r)}
                                />
                              ),
                            },
                          ]}
                        />
                      </div>
                    ),
                  },
                  {
                    key: "review",
                    label: (
                      <span className="tab-label">
                        <FileCheck2 size={16} />
                        人工复核
                      </span>
                    ),
                    children: (
                      <div className="review-area">
                        <div className="table-toolbar">
                          <div>
                            <h2>风险逐项确认</h2>
                            <span className="muted">
                              已确认{" "}
                              {
                                Object.values(decisions).filter((d) => d.action)
                                  .length
                              }{" "}
                              / {rules.length} 项
                            </span>
                          </div>
                          {job?.reviewed && !example && (
                            <Tag color="success">复核已保存</Tag>
                          )}
                        </div>
                        {rules.length === 0 ? (
                          <Empty
                            description={
                              report.risk_scan.error
                                ? "预扫描未完成，请人工核查审查报告。"
                                : "规则预扫描无命中，请结合报告核查。"
                            }
                          />
                        ) : (
                          rules.map((r) => (
                            <div className="decision-row" key={r.id}>
                              <div className="decision-title">
                                <div>
                                  <span className="rule-id">{r.id}</span>
                                  <h3>{r.risk_type}</h3>
                                </div>
                                {badge(r.final_level)}
                              </div>
                              <div className="evidence-note">
                                所需证据：{r.evidence_needed.join("、")}
                              </div>
                              <div className="decision-controls">
                                <Select
                                  aria-label={`${r.id} 复核动作`}
                                  placeholder="选择复核动作"
                                  value={decisions[r.id]?.action || undefined}
                                  disabled={!!example || job?.reviewed}
                                  onChange={(action) => choose(r, { action })}
                                  options={[
                                    "认可初评",
                                    "调整等级",
                                    "补充依据",
                                    "退回重审",
                                  ].map((v) => ({ value: v, label: v }))}
                                />
                                <Select
                                  aria-label={`${r.id} 复核等级`}
                                  value={
                                    decisions[r.id]?.review_level ||
                                    r.final_level
                                  }
                                  disabled={
                                    !!example ||
                                    job?.reviewed ||
                                    decisions[r.id]?.action !== "调整等级"
                                  }
                                  onChange={(review_level) =>
                                    choose(r, { review_level })
                                  }
                                  options={levels.map((v) => ({
                                    value: v,
                                    label: `${v} ${levelNames[v]}`,
                                  }))}
                                />
                              </div>
                              <Input.TextArea
                                aria-label={`${r.id} 复核意见`}
                                placeholder="复核依据与补充意见"
                                autoSize={{ minRows: 2, maxRows: 6 }}
                                maxLength={5000}
                                value={decisions[r.id]?.evidence_note || ""}
                                disabled={!!example || job?.reviewed}
                                onChange={(e) =>
                                  choose(r, { evidence_note: e.target.value })
                                }
                              />
                            </div>
                          ))
                        )}
                        {rules.length > 0 && (
                          <div className="review-submit">
                            <span>
                              {example
                                ? "示例模式"
                                : job?.reviewed
                                  ? "复核记录已存档"
                                  : "调级、补证和退回需填写依据"}
                            </span>
                            <Button
                              type="primary"
                              icon={<CheckCheck size={16} />}
                              disabled={
                                !!example || job?.reviewed || !completeDecisions
                              }
                              loading={submitting}
                              onClick={submit}
                            >
                              提交复核
                            </Button>
                          </div>
                        )}
                      </div>
                    ),
                  },
                ]}
              />
            </>
          )}
          <footer className="page-footer">
            <span>
              <ShieldCheck size={14} /> 本机工作空间
            </span>
            <span>
              AI COMPLIANCE REVIEW <b>·</b> V1.0
            </span>
          </footer>
        </main>
      </div>
      <Drawer
        title="模型与连接设置"
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        width={480}
        extra={<Settings2 size={19} />}
        footer={
          <div className="drawer-footer">
            <Button
              loading={testing}
              disabled={saving}
              onClick={() => saveSettings(true)}
            >
              测试连接
            </Button>
            <Button
              type="primary"
              loading={saving}
              disabled={testing}
              onClick={() => saveSettings(false)}
            >
              保存设置
            </Button>
          </div>
        }
      >
        <Form
          layout="vertical"
          form={settingsForm}
          initialValues={{
            auth_mode: "api_key",
            base_url: "https://api.anthropic.com",
            model: "sonnet",
          }}
        >
          <div className="settings-section">
            <span className="small-title">模型服务</span>
            <Form.Item name="auth_mode" label="鉴权方式">
              <Select
                options={[
                  { value: "api_key", label: "Anthropic API Key" },
                  { value: "auth_token", label: "Anthropic 兼容服务 Token" },
                  { value: "claude_login", label: "使用本机 Claude 登录" },
                ]}
              />
            </Form.Item>
            <Form.Item
              name="base_url"
              label="服务地址"
              rules={[{ required: true }]}
            >
              <Input placeholder="https://api.anthropic.com" />
            </Form.Item>
            <Form.Item
              name="model"
              label="模型名称"
              rules={[{ required: true }]}
            >
              <Input placeholder="sonnet" />
            </Form.Item>
            <Form.Item name="secret" label="模型密钥">
              <Input.Password
                autoComplete="new-password"
                placeholder={
                  config?.has_secret ? "已保存，留空保留当前密钥" : "输入密钥"
                }
              />
            </Form.Item>
            {config?.has_secret && (
              <Form.Item name="clear_secret" valuePropName="checked">
                <Checkbox>清除已保存的模型密钥</Checkbox>
              </Form.Item>
            )}
          </div>
          <Collapse
            ghost
            items={[
              {
                key: "mcp",
                label: "高级设置 · 北大法宝 MCP",
                children: (
                  <>
                    <Form.Item name="mcp_token" label="MCP 访问令牌">
                      <Input.Password
                        placeholder={
                          config?.has_mcp_token ? "已保存，留空保留" : "可选"
                        }
                        autoComplete="new-password"
                      />
                    </Form.Item>
                    {config?.has_mcp_token && (
                      <Form.Item name="clear_mcp_token" valuePropName="checked">
                        <Checkbox>清除 MCP 令牌</Checkbox>
                      </Form.Item>
                    )}
                    {[
                      ["LAW_SEARCH_URL", "法规语义检索"],
                      ["LAW_KEYWORD_URL", "法规关键词检索"],
                      ["CASE_SEMANTIC_URL", "案例语义检索"],
                      ["LAW_ITEM_URL", "法条检索"],
                      ["CITATION_VALIDATOR_URL", "引文核验"],
                    ].map(([key, label]) => (
                      <Form.Item
                        key={key}
                        name={["mcp_urls", key]}
                        label={label}
                      >
                        <Input placeholder="https://" />
                      </Form.Item>
                    ))}
                  </>
                ),
              },
            ]}
          />
          {testResult && (
            <Alert
              type={testResult.ok ? "success" : "error"}
              showIcon
              message={testResult.text}
            />
          )}
        </Form>
      </Drawer>
      <Drawer
        title="风险依据"
        open={!!detail}
        onClose={() => setDetail(null)}
        width={480}
      >
        {detail && (
          <div className="risk-detail">
            <span className="rule-id">{detail.id}</span>
            <h2>{detail.risk_type}</h2>
            {badge(detail.final_level)}
            <h3>命中关键词</h3>
            <div className="keywords">
              {Object.keys(detail.matched_keywords).map((k) => (
                <Tag key={k}>{k}</Tag>
              ))}
            </div>
            <h3>核查线索</h3>
            <p>{detail.semantic_cues}</p>
            <h3>所需证据</h3>
            <ul>
              {detail.evidence_needed.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
            <h3>整改方向</h3>
            <p>{detail.remediation_hint}</p>
          </div>
        )}
      </Drawer>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <ConfigProvider
    locale={zhCN}
    theme={{
      token: {
          colorPrimary: "#117b69",
          motion: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
        colorInfo: "#117b69",
        colorText: "#263431",
        colorTextSecondary: "#78827e",
        colorBorder: "#dce3df",
        borderRadius: 6,
        controlHeight: 36,
        fontFamily:
          '"Workbench Sans", "Segoe UI", "Microsoft YaHei", sans-serif',
        fontSize: 14,
      },
    }}
  >
    <AntApp>
      <Workbench />
    </AntApp>
  </ConfigProvider>,
);
