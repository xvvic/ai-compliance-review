# AI 初创企业合规审查系统

上传企业材料，生成合规审查报告并完成人工复核。

适用于 **Windows 10 / 11，64 位（x64）**。使用便携包，无需安装 Python、Node.js 或 Git。

## 1. 下载应用

1. 打开 **[软件下载页](https://github.com/xvvic/ai-compliance-review/releases)**，找到最新版本，展开 **Assets（附件）**。
2. 下载 **`AI-Compliance-Workbench-Windows-x64.zip`**，不要选择 `Source code` 源码包。
3. 找到下载的 ZIP 文件，右键选择 **全部解压**，解压到方便找到的位置。

## 2. 打开应用

打开解压后的 **AI-Compliance-Workbench** 文件夹，双击 **启动应用.vbs**，等待浏览器自动打开工作台。

请从解压后的文件夹启动，并保留其中的其他文件。下次使用时，再次双击 **启动应用.vbs** 即可。

## 3. 配置模型与检索

打开工作台“设置”，填写报告生成模型的连接信息。使用内置知识库时，在“知识库与本地检索”页启用检索增强。无需 Embedding API 或额外服务。

检索完全在本机运行，无需远程 API、LightRAG 服务或 embedding 模型。上传材料只用于审查，不会加入知识库。有检索结果时，可在报告中打开“RAG 检索依据”查看原文与来源。

## 4. 关闭应用

回到同一文件夹，双击 **停止应用.vbs**，然后关闭浏览器页面。

**仅关闭浏览器页面不会停止应用。**

---

源码运行、测试和打包发布见 [开发指南](https://github.com/xvvic/ai-compliance-review/blob/HEAD/docs/开发指南.md)。
