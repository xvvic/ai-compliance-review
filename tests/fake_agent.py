"""Deterministic subprocess used only by the browser integration fixture."""
import json
import sys
import time
from pathlib import Path

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
payload = json.load(sys.stdin)
text = (Path(payload['work_dir']) / '待审查材料.txt').read_text(encoding='utf-8')
print(json.dumps({'type': 'todos', 'items': [{'content': '核查数据处理活动', 'status': 'in_progress'}]}), flush=True)
print(json.dumps({'type': 'tool_start', 'tool_name': '检索相关依据'}), flush=True)
time.sleep(30 if 'SLOW' in text else 2)
if 'FAIL' in text:
    print(json.dumps({'type': 'error', 'content': '模拟模型连接失败'}), flush=True)
else:
    print(json.dumps({'type': 'todos', 'items': [{'content': '核查数据处理活动', 'status': 'completed'}]}), flush=True)
    print(json.dumps({'type': 'final', 'content': '# 企业合规审查报告\n\n## 审查结论\n\n这是自动化测试报告。\n\n## 风险核查\n\n| 事项 | 状态 |\n| --- | --- |\n| 数据跨境 | 待复核 |\n\n## 整改建议\n\n补充授权与数据流向证明。'}), flush=True)
