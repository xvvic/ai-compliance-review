# Output Template

Use this structure for full reports. For quick answers, preserve the same order in compressed form.

```markdown
# AI 初创公司合规审查报告

## 1. 一页结论
- 审查事项：
- 业务场景：
- 总体风险等级：
- 建议结论：推进 / 附条件推进 / 暂缓 / 停止并重构
- 关键理由：
- 最先处理的三项事项：

## 2. 场景画像
| 项目 | 内容 |
|---|---|
| 公司角色 | |
| 产品/交易阶段 | |
| AI 系统类型 | |
| 数据类型 | |
| 用户/影响对象 | |
| 目标市场 | |
| 关键假设 | |

## 3. 风险矩阵
| 风险 | 领域 | 等级 | 置信度 | 触发事实 | 来源/依据 | 处理建议 |
|---|---|---|---|---|---|---|

矩阵一致性要求：矩阵须是本报告风险条目的**完整清单**——每行在"风险"列标注规则 ID（预扫描命中项，如 `BIO-001`）或 `[语义识别]`（规则未覆盖、模型新发现项）；报告中任何风险等级统计（如"L3 共 N 项"）必须与矩阵行数一致，禁止矩阵与正文各说各话。

**机器可读条目文件（硬性要求）**：完成报告的同时，把风险矩阵逐行写入工作目录下的《风险条目.json》（UTF-8，严格 JSON，字段如下），行数与矩阵一致：

```json
{
  "risks": [
    {
      "rule_id": "BIO-001",
      "risk": "敏感个人信息与生物识别风险：面向公安场景部署人脸识别",
      "category": "个人信息与敏感个人信息风险",
      "level": "L4",
      "confidence": "高",
      "trigger_fact": "材料第2节：向公安部门提供实时人脸识别",
      "evidence": "《个人信息保护法》第28-29条；本地语料 案例/Clearview AI 案",
      "recommendation": "开展PIA并取得单独同意；暂缓公安场景上线"
    }
  ]
}
```

字段规则：`rule_id` 为预扫描命中的规则号；规则未覆盖的新发现风险填 `null`；`level` 只能是 "L1"/"L2"/"L3"/"L4"；`evidence` 必须注明法条或语料来源，纯模型推断标注 `[模型推理-待核验]`。

## 4. 审查路径
说明是否需要 PIA/DPIA、AIA、算法/生成式 AI 审查、数据出境评估、供应商审查、外部律师复核、董事会或投资披露。

## 5. 整改清单
| 优先级 | 整改项 | 负责人 | 验收标准 | 建议期限 |
|---|---|---|---|---|

## 6. 来源与待核验清单
### 已使用来源
- 
- 例如：`[北大法宝MCP: pkulaw-law-search/search_article | 生成式人工智能 服务管理暂行办法 | 检索日期 YYYY-MM-DD]`

### 待核验
-

## 7. 残余风险与复查触发条件
- 残余风险：
- 复查触发条件：
- 人工复核建议：
```

## Short Answer Form

When the user wants a fast pass, include:

1. Overall level and recommendation.
2. Top risks in a table.
3. Missing facts.
4. Next actions with acceptance criteria.
5. Source and verification notes.
