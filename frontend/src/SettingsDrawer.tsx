import { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Checkbox,
  Collapse,
  Drawer,
  Form,
  Input,
  Select,
  Switch,
  Tabs,
  Tag,
} from "antd";
import { Check, PlugZap, Save } from "lucide-react";
import { api } from "./api";

const services = [
  ["LAW_SEARCH_URL", "法规语义检索"],
  ["LAW_KEYWORD_URL", "法规关键词检索"],
  ["CASE_SEMANTIC_URL", "案例语义检索"],
  ["LAW_ITEM_URL", "法条检索"],
  ["CITATION_VALIDATOR_URL", "引文核验"],
];
const presets: Record<
  string,
  { base_url: string; model: string; auth_mode: string }
> = {
  deepseek: {
    base_url: "https://api.deepseek.com/anthropic",
    model: "deepseek-v4-flash",
    auth_mode: "api_key",
  },
  anthropic: {
    base_url: "https://api.anthropic.com",
    model: "sonnet",
    auth_mode: "api_key",
  },
};
const urlRules = [
  {
    validator: (_: unknown, value: string) => {
      try {
        const url = new URL(value?.trim());
        if (
          !["https:", "http:"].includes(url.protocol) ||
          url.username ||
          url.password ||
          url.search ||
          url.hash
        )
          throw new Error();
        return Promise.resolve();
      } catch {
        return Promise.reject(
          new Error("请输入完整的 HTTP(S) 地址，不含账号、查询参数或片段"),
        );
      }
    },
  },
];

export function SettingsDrawer({
  open,
  config,
  onClose,
  onSaved,
}: {
  open: boolean;
  config: any;
  onClose: () => void;
  onSaved: (config: any) => void;
}) {
  const [form] = Form.useForm();
  const [provider, setProvider] = useState("anthropic");
  const [tab, setTab] = useState("model");
  const [advanced, setAdvanced] = useState<string[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState<"test" | "save" | null>(null);
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(
    null,
  );
  const enabled = Form.useWatch("mcp_enabled", form);
  const auth = Form.useWatch("auth_mode", form);
  const baseUrl = Form.useWatch("base_url", form);
  const canKeepSecret =
    config?.has_secret &&
    auth === config.auth_mode &&
    baseUrl === config.base_url;

  useEffect(() => {
    if (!open) return;
    form.resetFields();
    form.setFieldsValue({
      network_mode: "direct",
      mcp_enabled: false,
      ...config,
      secret: "",
      mcp_token: "",
      clear_secret: false,
      clear_mcp_token: false,
    });
    const preset =
      Object.keys(presets).find(
        (key) => presets[key].base_url === config?.base_url,
      ) || "custom";
    setProvider(preset);
    setAdvanced(preset === "custom" ? ["advanced"] : []);
    setSelected(
      services.filter(([key]) => config?.mcp_urls?.[key]).map(([key]) => key),
    );
    setResult(null);
    setTab("model");
  }, [open, config, form]);

  const changeProvider = (value: string) => {
    setProvider(value);
    setAdvanced(value === "custom" ? ["advanced"] : []);
    setResult(null);
    if (presets[value])
      form.setFieldsValue({
        ...presets[value],
        secret: "",
        clear_secret: false,
      });
  };
  const submit = async (test: boolean) => {
    try {
      await form.validateFields(
        test
          ? ["base_url", "model", "secret", "auth_mode", "network_mode"]
          : undefined,
      );
      const values = form.getFieldsValue(true);
      if (!test && values.mcp_enabled && !selected.length) {
        setTab("retrieval");
        setResult({ ok: false, text: "请至少选择一项在线检索服务。" });
        return;
      }
      setBusy(test ? "test" : "save");
      setResult(null);
      const data = {
        ...values,
        mcp_urls: values.mcp_enabled
          ? Object.fromEntries(
              selected.map((key) => [key, values.mcp_urls?.[key] || ""]),
            )
          : config?.mcp_urls || {},
      };
      const response = await api(
        test ? "/api/config/test" : "/api/config",
        test ? "POST" : "PUT",
        test
          ? { ...data, mcp_enabled: false, mcp_urls: {}, mcp_token: "" }
          : data,
      );
      if (test) setResult({ ok: true, text: response.message });
      else onSaved(response);
    } catch (error) {
      if (error instanceof Error) setResult({ ok: false, text: error.message });
      else if ((error as any)?.errorFields?.length) {
        const field = (error as any).errorFields[0].name[0];
        setTab(
          ["mcp_urls", "mcp_token"].includes(field) ? "retrieval" : "model",
        );
        if (field === "base_url") setAdvanced(["advanced"]);
      }
    } finally {
      setBusy(null);
    }
  };

  return (
    <Drawer
      title="模型与连接设置"
      open={open}
      width={480}
      onClose={onClose}
      closable={!busy}
      maskClosable={!busy}
      keyboard={!busy}
      footer={
        <div className="settings-footer">
          {result && (
            <Alert
              showIcon
              type={result.ok ? "success" : "error"}
              message={result.text}
            />
          )}
          <div className="drawer-footer">
            <Button disabled={!!busy} onClick={onClose}>
              取消
            </Button>
            <Button
              type="primary"
              icon={<Save size={16} />}
              loading={busy === "save"}
              disabled={busy === "test"}
              onClick={() => submit(false)}
            >
              保存设置
            </Button>
          </div>
        </div>
      }
    >
      <Form
        form={form}
        layout="vertical"
        disabled={!!busy}
        onValuesChange={() => setResult(null)}
        initialValues={{
          auth_mode: "api_key",
          base_url: presets.anthropic.base_url,
          model: "sonnet",
          network_mode: "direct",
          mcp_enabled: false,
        }}
      >
        <Tabs
          activeKey={tab}
          onChange={setTab}
          items={[
            {
              key: "model",
              label: "模型服务",
              forceRender: true,
              children: (
                <div className="settings-section">
                  <Form.Item label="服务商">
                    <Select
                      aria-label="服务商"
                      value={provider}
                      onChange={changeProvider}
                      options={[
                        { value: "deepseek", label: "DeepSeek" },
                        { value: "anthropic", label: "Anthropic / Claude" },
                        { value: "custom", label: "自定义兼容服务" },
                      ]}
                    />
                  </Form.Item>
                  <Form.Item
                    name="model"
                    label="模型名称"
                    rules={[
                      {
                        required: true,
                        whitespace: true,
                        message: "请填写模型名称",
                      },
                    ]}
                  >
                    <Input
                      placeholder={
                        presets[provider]?.model || "服务商提供的模型名称"
                      }
                    />
                  </Form.Item>
                  {auth !== "claude_login" && (
                    <>
                      <Form.Item name="secret" label="模型密钥">
                        <Input.Password
                          autoComplete="new-password"
                          placeholder={
                            canKeepSecret
                              ? "已保存，留空保留当前密钥"
                              : "输入服务商提供的 API Key"
                          }
                        />
                      </Form.Item>
                      {canKeepSecret && (
                        <Form.Item name="clear_secret" valuePropName="checked">
                          <Checkbox>清除已保存的模型密钥</Checkbox>
                        </Form.Item>
                      )}
                    </>
                  )}
                  <Form.Item name="network_mode" label="网络连接">
                    <Select
                      options={[
                        { value: "direct", label: "直连" },
                        {
                          value: "system",
                          label: "使用系统代理（HTTP / HTTPS）",
                        },
                      ]}
                    />
                  </Form.Item>
                  <Collapse
                    ghost
                    activeKey={advanced}
                    onChange={(keys) =>
                      setAdvanced(typeof keys === "string" ? [keys] : keys)
                    }
                    items={[
                      {
                        key: "advanced",
                        label: "服务地址与鉴权",
                        forceRender: true,
                        children: (
                          <>
                            <Form.Item
                              name="base_url"
                              label="服务地址"
                              rules={urlRules}
                            >
                              <Input
                                placeholder="https://api.deepseek.com/anthropic"
                                onChange={() => setProvider("custom")}
                              />
                            </Form.Item>
                            <Form.Item name="auth_mode" label="鉴权方式">
                              <Select
                                options={[
                                  {
                                    value: "api_key",
                                    label: "API Key（x-api-key）",
                                  },
                                  {
                                    value: "auth_token",
                                    label: "Bearer Token",
                                  },
                                  {
                                    value: "claude_login",
                                    label: "使用本机 Claude 登录",
                                  },
                                ]}
                              />
                            </Form.Item>
                          </>
                        ),
                      },
                    ]}
                  />
                  <Button
                    className="model-test-button"
                    icon={<PlugZap size={16} />}
                    loading={busy === "test"}
                    disabled={busy === "save"}
                    onClick={() => submit(true)}
                  >
                    测试模型连接
                  </Button>
                </div>
              ),
            },
            {
              key: "retrieval",
              label: "法规检索",
              forceRender: true,
              children: (
                <div className="settings-section retrieval-settings">
                  <div className="retrieval-source">
                    <div>
                      <strong>本地法规与案例</strong>
                      <span>随应用内置的参考资料</span>
                    </div>
                    <Tag icon={<Check size={13} />} color="success">
                      已启用
                    </Tag>
                  </div>
                  <div className="retrieval-heading">
                    <div>
                      <strong>北大法宝在线检索</strong>
                      <span>可选外部数据源</span>
                    </div>
                    <Form.Item
                      name="mcp_enabled"
                      valuePropName="checked"
                      noStyle
                    >
                      <Switch aria-label="启用北大法宝在线检索" />
                    </Form.Item>
                  </div>
                  {enabled && (
                    <>
                      <Form.Item label="检索服务" required>
                        <Select
                          aria-label="检索服务"
                          mode="multiple"
                          value={selected}
                          placeholder="选择已开通的服务"
                          onChange={(keys) => {
                            setSelected(keys);
                            setResult(null);
                          }}
                          options={services.map(([value, label]) => ({
                            value,
                            label,
                          }))}
                        />
                      </Form.Item>
                      {services
                        .filter(([key]) => selected.includes(key))
                        .map(([key, label]) => (
                          <Form.Item
                            key={key}
                            name={["mcp_urls", key]}
                            label={`${label}地址`}
                            rules={urlRules}
                          >
                            <Input placeholder="北大法宝提供的服务 URL" />
                          </Form.Item>
                        ))}
                      <Form.Item name="mcp_token" label="访问令牌（可选）">
                        <Input.Password
                          autoComplete="new-password"
                          placeholder={
                            config?.has_mcp_token
                              ? "已保存，留空保留"
                              : "服务商提供的访问令牌"
                          }
                        />
                      </Form.Item>
                      {config?.has_mcp_token && (
                        <Form.Item
                          name="clear_mcp_token"
                          valuePropName="checked"
                        >
                          <Checkbox>清除已保存的访问令牌</Checkbox>
                        </Form.Item>
                      )}
                    </>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Form>
    </Drawer>
  );
}
