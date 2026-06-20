# Collectigent - 群体智能涌现引擎

[English](./README.md) | 中文

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/)

**Collectigent** 是全球首个可量化、可复现的群体智能开源框架。通过6个专业化AI Agent的结构化协作，实现超越单体Agent的涌现智能。

## 核心特性

| 模块 | 开源内容 | 目的 |
|------|---------|------|
| **6角色架构** | 研究者、批判者、创新者、综合者、执行者、领导者的角色定义与接口 | 建立行业标准，让开发者快速上手 |
| **迭代辩论引擎** | 多轮对话循环、观点收敛机制的基础实现 | 展示核心协作逻辑，吸引社区贡献 |
| **共享记忆系统** | 短期记忆（对话上下文）+ 长期记忆（知识库检索）的接口与基础实现 | 降低使用门槛 |
| **任务编排器** | Agent 调度、消息路由、状态管理 | 框架基础设施 |
| **基础涌现指标** | 群体增益、多样性指数、错误修正率的计算接口 | 建立"可验证"的品牌认知 |
| **LLM多提供商集成** | 支持OpenAI、Anthropic、GLM、DeepSeek、Doubao、Qwen | 灵活适配多种大模型 |
| **知识库检索集成** | RAG检索增强生成、多向量存储支持(FAISS/Pinecone/Weaviate) | 智能问答、知识增强 |

## 安装

```bash
pip install collectigent
```

或安装完整依赖（包含所有LLM提供商）：

```bash
pip install collectigent[llm]
```

或从源码安装：

```bash
git clone https://github.com/collectigent/collectigent.git
cd collectigent
pip install -e ".[dev,llm]"
```

## 快速开始

```python
import asyncio
from collectigent import Swarm, LLMFactory
from collectigent.core.agents import Leader, Researcher, Critic, Innovator, Synthesizer, Executor

async def main():
    # 创建LLM提供商（支持OpenAI/Anthropic/GLM/DeepSeek/Doubao/Qwen）
    llm = LLMFactory.create_openai(model="gpt-4o")
    
    # 创建群体智能实例
    swarm = Swarm(llm=llm)

    # 注册6个Agent角色（自动配置LLM）
    swarm.register(Leader())
    swarm.register(Researcher())
    swarm.register(Critic())
    swarm.register(Innovator())
    swarm.register(Synthesizer())
    swarm.register(Executor())

    # 执行任务
    result = await swarm.run("分析量子计算对加密货币的影响")

    # 打印结果
    print(f"群体增益: {result['metrics']['group_gain']}")
    print(f"多样性指数: {result['metrics']['diversity_index']}")

asyncio.run(main())
```

## 项目结构

```
collectigent/
├── src/collectigent/
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── agents/          # 6角色定义
│       │   ├── __init__.py
│       │   ├── base.py      # Agent基类、Role枚举、Message类
│       │   ├── leader.py
│       │   ├── researcher.py
│       │   ├── critic.py
│       │   ├── innovator.py
│       │   ├── synthesizer.py
│       │   └── executor.py
│       ├── engine/          # 迭代辩论引擎
│       │   └── __init__.py  # DebateEngine、三种共识协议
│       ├── memory/          # 共享记忆系统
│       │   └── __init__.py  # ShortTermMemory、LongTermMemory、MemorySystem
│       ├── orchestrator/   # 任务编排器
│       │   └── __init__.py  # Swarm编排器
│       ├── metrics/         # 涌现指标
│       │   └── __init__.py  # EmergenceMetrics
│       └── llm/             # LLM多提供商集成
│           ├── __init__.py
│           ├── base.py      # LLMProvider基类、LLMConfig、LLMResponse
│           ├── factory.py   # LLMFactory工厂类
│           ├── openai.py    # OpenAI提供商
│           ├── anthropic.py # Anthropic提供商
│           ├── glm.py       # 智谱AI提供商
│           ├── deepseek.py  # DeepSeek提供商
│           ├── doubao.py    # 字节跳动提供商
│           └── qwen.py      # 阿里云通义千问提供商
│       ├── knowledge/       # 知识库检索模块
│       │   ├── __init__.py
│       │   ├── loader.py    # 文档加载器(txt/md/pdf/docx)
│       │   ├── splitter.py  # 文本分块器
│       │   ├── embedding.py # Embedding向量化器
│       │   ├── vector_store.py # 向量存储(FAISS/Pinecone/Weaviate)
│       │   ├── retriever.py # 检索器
│       │   └── rag.py       # RAG系统
│       └── debugger/       # 可视化调试工具
│           ├── __init__.py  # Debugger主类
│           ├── cli.py       # CLI可视化组件
│           ├── flow.py      # 消息流程可视化
│           └── dashboard.py # 涌现指标仪表盘
└── tests/
    ├── test_collectigent.py
    ├── test_llm.py
    └── test_knowledge.py
```

## 核心概念

### 6角色架构

```
         ┌─────────────┐
         │   Leader    │  领导者
         │  (策略/协调) │
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Research│ │Critic │  │ Innov.│
│研究者  │  │ 批判者 │  │ 创新者 │
└───┬───┘  └───┬───┘  └───┬───┘
    │          │          │
    └──────────┼──────────┘
               │
         ┌─────▼─────┐
         │Synthesizer│  综合者
         │  (整合)   │
         └─────┬─────┘
               │
         ┌─────▼─────┐
         │ Executor  │  执行者
         │  (评估)   │
         └───────────┘
```

### 三种共识协议

```python
from collectigent.core.engine import DebateEngine, ConsensusProtocol, DebateConfig

# 优先级裁决：按角色优先级选择
engine = DebateEngine(DebateConfig(protocol=ConsensusProtocol.PRIORITY_RULING))

# 置信度加权：按置信度平方加权汇总
engine = DebateEngine(DebateConfig(protocol=ConsensusProtocol.CONFIDENCE_WEIGHTED))

# 迭代辩论：多轮辩论逐步收敛
engine = DebateEngine(DebateConfig(protocol=ConsensusProtocol.ITERATIVE_DEBATE))
```

### 涌现指标

```python
from collectigent.core.metrics import EmergenceMetrics

metrics = EmergenceMetrics()

# 计算当前对话的指标
result = metrics.calculate(conversation_messages)

# 指标包括：
# - group_gain: 群体增益（>1表示群体优于最优个体）
# - diversity_index: 多样性指数（0-1）
# - error_correction_rate: 错误修正率（0-1）
```

### LLM多提供商集成

支持6大LLM提供商，通过统一接口调用：

```python
from collectigent import LLMFactory

# OpenAI
llm = LLMFactory.create_openai(model="gpt-4o")

# Anthropic Claude
llm = LLMFactory.create_anthropic(model="claude-3-5-sonnet-20241022")

# 智谱AI GLM
llm = LLMFactory.create_glm(model="glm-4")

# DeepSeek
llm = LLMFactory.create_deepseek(model="deepseek-chat")

# 字节跳动 Doubao
llm = LLMFactory.create_doubao(model="doubao-pro-32k")

# 阿里云通义千问
llm = LLMFactory.create_qwen(model="qwen-turbo")
```

**环境变量配置：**

| 提供商 | API Key环境变量 | 默认模型 |
|--------|----------------|----------|
| OpenAI | OPENAI_API_KEY | gpt-4o |
| Anthropic | ANTHROPIC_API_KEY | claude-3-5-sonnet |
| 智谱AI | ZHIPU_API_KEY | glm-4 |
| DeepSeek | DEEPSEEK_API_KEY | deepseek-chat |
| 字节Doubao | DOUBAO_API_KEY | doubao-pro-32k |
| 阿里云Qwen | DASHSCOPE_API_KEY | qwen-turbo |

**Agent调用LLM：**

```python
from collectigent.core.agents import Leader

leader = Leader(llm=llm)
response = await leader.call_llm("分析这个问题")
```

### 知识库检索集成 (RAG)

支持多种向量存储和Embedding提供商，实现检索增强生成：

```python
from collectigent import RAGFactory

# 创建RAG系统（使用本地FAISS和MiniLM）
rag = RAGFactory.create_basic(
    embedding_provider="local",
    vector_store="faiss",
    llm_provider="openai",
)

# 添加文档到知识库
await rag.add_document("群体智能是指多个智能体通过协作产生的涌现智能。")

# 执行检索增强问答
result = await rag.query("什么是群体智能？")
print(result.answer)
```

**支持的向量存储：**

| 存储类型 | 描述 |
|---------|------|
| FAISS | 本地向量数据库（Meta） |
| Pinecone | 云向量数据库 |
| Weaviate | 开源向量数据库 |
| Chroma | 轻量级向量数据库 |
| Milvus | 企业级向量数据库 |

**支持的Embedding提供商：**

| 提供商 | 环境变量 |
|--------|----------|
| OpenAI | OPENAI_API_KEY |
| 智谱AI | ZHIPU_API_KEY |
| 百川智能 | BAICHUAN_API_KEY |
| Minimax | MINIMAX_API_KEY |
| Local (MiniLM) | 无需API Key |

**高级RAG系统（支持多轮对话）：**

```python
from collectigent import RAGFactory

# 创建高级RAG系统
rag = RAGFactory.create_advanced(
    embedding_provider="openai",
    vector_store="pinecone",
    llm_provider="anthropic",
)

# 从目录构建知识库
await rag.build_knowledge_base("./docs/")

# 多轮对话
result1 = await rag.query("什么是群体智能？")
result2 = await rag.query("它和传统AI有什么区别？")  # 支持上下文理解
```

### 可视化调试工具 (v0.4)

提供实时可视化调试功能，支持CLI界面、流程图和指标仪表盘：

```python
from collectigent import Swarm, create_debugger

# 创建调试器
debugger = create_debugger(
    enable_cli=True,      # 启用CLI可视化
    enable_flow=True,     # 启用流程可视化
    enable_dashboard=True, # 启用指标仪表盘
)

# 集成到Swarm
config = SwarmConfig(
    max_iterations=3,
    verbose=True,
    progress_callback=debugger.on_event,
)

swarm = Swarm(config=config)

# 开始调试会话
debugger.start("人工智能将如何改变工作方式？")

# 执行任务...
result = await swarm.run("人工智能将如何改变工作方式？")

# 结束会话并打印摘要
debugger.end(result.get("result", ""), result.get("metrics", {}))
debugger.print_summary()
```

**CLI可视化输出示例：**

```
═══════════════════════════════════════════════════════════════
                    群体智能调试会话
═══════════════════════════════════════════════════════════════
📌 任务: 人工智能将如何改变工作方式？

⏳ 等待Agent响应...

──────────────────────────────────────────────────────────────
│ [步骤 1] 👑 领导者 - 张三
──────────────────────────────────────────────────────────────
  💭 思考中... ✓

  📝 响应内容:
  ───────────────────────────────────────────────────────────
  │ main_task: 分析人工智能对未来工作方式的影响及应对策略...
  ───────────────────────────────────────────────────────────
```

**涌现指标仪表盘：**

```
═══════════════════════════════════════════════════════════════
                    涌现指标仪表盘
═══════════════════════════════════════════════════════════════

  📊 群体增益 (Group Gain)
     [████████████░░░░] 1.25 ✓
     → 群体表现优于个体

  🌈 多样性指数 (Diversity)
     [████████████████░░] 0.85 ✓
     → 高多样性带来更多创意

  🔧 错误修正率 (Error Correction)
     [█████████░░░░░░░░░] 0.45 ✓
     → 有效识别和修正错误
```

## 开发

```bash
# 克隆仓库
git clone https://github.com/collectigent/collectigent.git

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v
```

## Roadmap

- [x] v0.2: LLM集成（OpenAI/Anthropic/GLM/DeepSeek/Doubao/Qwen）
- [x] v0.3: 知识库检索集成（RAG/FAISS/Pinecone）
- [x] v0.4: 可视化调试工具（CLI/流程图/指标仪表盘）
- [ ] v1.0: 生产级稳定版

## 贡献

欢迎提交Issue和Pull Request！

## License

Apache License 2.0 - see [LICENSE](./LICENSE)
