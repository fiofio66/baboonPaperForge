# 论文智能排版与模板适配 Agent 平台 - 开发需求说明书 (PRD)

## 1. 核心目标
开发一款面向科研人员的“本地 Web 应用（Local Web App）”，旨在自动化解决学术论文（LaTeX/Word）的期刊模板搜索、解析与一键排版适配问题。要求后端基于 Python 现代技术栈构建高可用、安全隔离的 Agentic 工作流，解决真实业务场景中高并发、状态管理和数据隐私的痛点。

## 2. 技术栈选型 (严格遵守)
* **后端框架**：Python + FastAPI (提供 RESTful API，处理并发任务)。
* **Agent 编排**：LangChain + LangGraph (构建多节点的 Agent 工作流，如搜索、下载、解析、校验)。
* **知识库与检索**：RAG 架构 + Milvus 向量数据库 (用于处理和检索期刊的 Author Guidelines/排版规范)。
* **关系型数据库**：PostgreSQL (存储模板元数据、解析占位符 JSON、用户配置和历史任务记录)。
* **前端**：轻量级 Web 框架 (如 Vue3 或 Streamlit)，需包含支持 Markdown 的富文本编辑器和多表单输入交互。

## 3. 核心功能模块与系统流转

### 3.1 模板获取与元数据存储 (Search Agent)
* **交互**：用户在前端输入目标期刊名称（如 "IEEE Internet of Things Journal" 或 "Information Sciences"）及需要的模板格式（LaTeX 或 Word）。
* **职责**：LangGraph 中的 Search 节点联网搜索官方模板下载链接。
* **动作**：自动下载压缩包，并解压解构到指定的“本地工作路径”。必须保持 LaTeX 目录结构完整（`.cls`, `.sty`, 图片文件夹等）。
* **持久化**：将下载路径、期刊名、模板版本号存入 **PostgreSQL**。

### 3.2 规范知识库提取 (RAG 节点)
* **职责**：处理下载模板中附带的长篇 Author Guidelines PDF。
* **动作**：系统自动解析指南文档，分块 (Chunking) 并向量化，存入 **Milvus**。
* **目的**：为后续的 RAG 提供检索基础，为 Agent 提供格式约束规则（例如“该期刊摘要字数上限是多少”、“参考文献格式要求”等）。

### 3.3 模板分析模块 (Analyst Agent)
* **职责**：读取下载好的 `main.tex` 或 `.docx` 骨架。
* **动作**：不处理正文内容，仅通过分析文件结构，提取出模板中定义的“模块结构树”（如 Title, Abstract, Introduction, Methodology, Conclusion, References）。结合 RAG 检索到的规则，为每个模块附加约束提示。
* **输出**：返回一个 JSON 格式的“占位符映射表 (Mapping JSON)”，明确每个模块在模板中的物理插入点位置（行号或正则锚点/AST叶子节点）。该结构树存入 PostgreSQL，供前端渲染。

### 3.4 模型解耦与多租户配置 (BYOK & Model Agnostic)
* **API 与模型设置**：前端提供独立的设置面板。用户可选择大模型提供商（如下拉菜单提供 OpenAI, Anthropic, Gemini, 以及 Ollama 本地部署）。
* **动态表单**：当用户选择云端模型时，需输入 API Key；当选择 Ollama 等本地服务时，隐藏 API Key 输入框，并可自定义 Base URL。
* **安全与工厂模式**：后端 FastAPI 接收到 API Key 后，禁止明文存库，需使用对称加密（如 `cryptography.fernet`）存入 PostgreSQL。LangChain 根据数据库读取的配置，使用工厂模式动态实例化具体的 `BaseChatModel` 执行当前任务。

### 3.5 用户输入与前端动态 UI
* **动态表单生成**：前端调用 FastAPI 接口，读取映射表 JSON，动态生成对应的论文模块输入框。
* **内容填报**：用户将自己的论文正文分别粘贴进去。支持自定义扩展模块（点击“添加新章节”，系统自动分配层级）。
* **多媒体注入**：提供图表上传与配置组件。用户上传图片文件，输入 Caption（图注）和 Label，并必须提供复选框让用户决定“是否跨栏显示”。对应生成 `\begin{figure}` 或 `\begin{figure*}` 结构。

### 3.6 零 Token 渲染引擎 (Zero-Token Assembler)
* **核心安全约束**：严禁将用户的数万字论文正文发送给 LLM 进行处理，以节省 Token 并防止未发表的敏感科研成果泄露。
* **职责**：系统的数据面。FastAPI 后端读取前端传来的结构化正文内容和图表配置，直接根据 Analyst Agent 提供的“映射表 JSON”，使用纯 Python 代码、正则表达式或 AST（如 `TexSoup` / `pylatexenc` / `python-docx`）将内容精准、安全地注入到本地模板文件中。

## 4. 核心工作流流转 (LangGraph State 建议)
1. `InputState`: 接收期刊名、格式需求及当前用户选择的 LLM 配置。
2. `SearchNode`: 下载并解压模板压缩包。
3. `RAGNode`: 解析指南 PDF 并向量化进入 Milvus。
4. `ParseNode`: 分析模板生成 Mapping JSON 入库 PostgreSQL。
5. *(前端等待：用户在 UI 填写正文内容、上传图表并提交)*
6. `AssembleNode`: 纯 Python 代码将用户内容注入本地模板文件。
7. `OutputState`: 返回编译后的源文件压缩包及最终生成的 PDF 文件路径。

## 5. 开发节奏与问题记录机制 (Development Workflow)
* **渐进式敏捷开发**：请不要一次性生成所有模块的完整代码。我们需要分模块、分步骤进行（例如：第一步先搭建 FastAPI 路由、加密解密工具类和 PostgreSQL 表结构，测试跑通后；第二步再推进 LangGraph 的核心节点）。每次只聚焦一个具体的开发任务。
* **实时问题拦截与方案讨论**：在编写代码或配置环境的过程中，如果你（Agent）预判到或者实际遇到了任何技术难点、API 限制、并发冲突或环境依赖问题：
  1. 请**立即暂停代码生成**。
  2. 向我清晰地解释当前遇到了什么问题，以及导致该问题的底层原因。
  3. 提供你的企业级解决思路或备选方案供我决策。
* **面试复盘导向**：我正在准备 AI Agent 研发工程师的面试。我会将这些真实开发中遇到的卡点、你的 Debug 逻辑和最终的技术权衡过程记录下来作为面试素材。因此，请务必保证代码的工程严谨度（如异常捕获、重试机制、安全限制等）。
## 6. 版本控制与代码提交规范 (Git & GitHub)
* **目标仓库**：`https://github.com/fiofio66/baboonPaperForge`
* **提交流程**：在每一次完成一个核心模块的开发或修复一个重大 Bug 后，你需要主动帮我执行 Git 提交并推送到远程仓库的 `main` 分支。
* **Commit Message 规范**：必须遵循 Conventional Commits 规范。例如：
  * `feat(api): add FastAPI router for model selection`
  * `fix(agent): resolve async deadlock in LangGraph SearchNode`
  * `chore(db): initialize PostgreSQL pgvector schema`
* **前置检查**：在执行 `git commit` 前，请确保代码没有遗留的调试打印（如无意义的 `print()`），并且保证 `.gitignore` 已正确配置（绝对不能把 `.env` 文件、数据库密码或本地的 `venv/` 虚拟环境提交到仓库中）。