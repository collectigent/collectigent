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

## 安装

```bash
pip install collectigent
```

或从源码安装：

```bash
git clone https://github.com/collectigent/collectigent.git
cd collectigent
pip install -e .
```

## 快速开始

```python
import asyncio
from collectigent import Swarm
from collectigent.core.agents import Leader, Researcher, Critic, Innovator, Synthesizer, Executor

async def main():
    # 创建群体智能实例
    swarm = Swarm()

    # 注册6个Agent角色
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
│       └── metrics/         # 涌现指标
│           └── __init__.py  # EmergenceMetrics
└── tests/
    └── test_collectigent.py
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
│Research│  │Critic │  │Innov.│
│研究者  │  │批判者 │  │创新者 │
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

- [ ] v0.2: LLM集成（OpenAI/Anthropic）
- [ ] v0.3: 知识库检索集成
- [ ] v0.4: 可视化调试工具
- [ ] v1.0: 生产级稳定版

## 贡献

欢迎提交Issue和Pull Request！

## License

Apache License 2.0 - see [LICENSE](./LICENSE)
