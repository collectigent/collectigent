"""
可视化调试工具使用示例

展示如何使用v0.4的可视化调试功能：
- CLI可视化：实时显示Agent沟通过程
- 流程可视化：显示消息流转图
- 指标仪表盘：显示涌现指标变化
"""

import asyncio
import os
from collectigent import (
    Swarm,
    LLMFactory,
    create_debugger,
    CLIVisualizer,
    FlowVisualizer,
    MetricsDashboard,
)
from collectigent.core.orchestrator import SwarmConfig
from collectigent.core.agents import (
    Leader, Researcher, Critic, Innovator, Synthesizer, Executor,
)


async def demo_cli_visualizer():
    """
    示例1: CLI可视化器
    
    最简单的可视化方式，实时显示Agent沟通过程
    """
    print("\n" + "=" * 60)
    print("示例1: CLI可视化器")
    print("=" * 60)
    
    # 1. 初始化LLM
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 请设置 ZHIPU_API_KEY 环境变量")
        return
    
    llm = LLMFactory.create_glm(api_key=api_key, model="glm-4")
    
    # 2. 创建CLI可视化器
    cli = CLIVisualizer()
    
    # 3. 创建Swarm（使用可视化器的回调）
    config = SwarmConfig(
        max_iterations=2,
        verbose=True,
        progress_callback=cli.handle_event,  # 集成可视化
    )
    swarm = Swarm(config=config)
    
    # 4. 注册Agent
    swarm.register(Leader(llm=llm, name="张三"))
    swarm.register(Researcher(llm=llm, name="李四"))
    swarm.register(Critic(llm=llm, name="王五"))
    swarm.register(Synthesizer(llm=llm, name="钱七"))
    
    # 5. 执行任务
    task = "人工智能在教育领域的应用前景如何？"
    
    # 开始调试会话
    cli.start_session(task)
    
    # 运行任务
    result = await swarm.run(task)
    
    # 结束会话
    cli.end_session(result.get("result", ""))
    
    # 打印摘要
    cli.print_summary()


async def demo_full_debugger():
    """
    示例2: 完整调试器
    
    启用所有可视化功能：CLI + 流程图 + 指标仪表盘
    """
    print("\n" + "=" * 60)
    print("示例2: 完整调试器")
    print("=" * 60)
    
    # 1. 初始化LLM
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 请设置 ZHIPU_API_KEY 环境变量")
        return
    
    llm = LLMFactory.create_glm(api_key=api_key, model="glm-4")
    
    # 2. 创建完整调试器
    debugger = create_debugger(
        enable_cli=True,       # CLI可视化
        enable_flow=True,      # 流程可视化
        enable_dashboard=True, # 指标仪表盘
    )
    
    # 3. 创建Swarm
    config = SwarmConfig(
        max_iterations=3,
        verbose=True,
        progress_callback=debugger.on_event,
    )
    swarm = Swarm(config=config)
    
    # 4. 注册Agent
    swarm.register(Leader(llm=llm, name="张三"))
    swarm.register(Researcher(llm=llm, name="李四"))
    swarm.register(Critic(llm=llm, name="王五"))
    swarm.register(Innovator(llm=llm, name="赵六"))
    swarm.register(Synthesizer(llm=llm, name="钱七"))
    
    # 5. 执行任务
    task = "如何提高团队协作效率？"
    
    # 开始调试会话
    debugger.start(task)
    
    # 运行任务
    result = await swarm.run(task)
    
    # 结束会话
    debugger.end(
        result.get("result", ""),
        result.get("metrics", {})
    )
    
    # 打印所有可视化摘要
    debugger.print_summary()


async def demo_flow_visualizer():
    """
    示例3: 流程可视化器
    
    专门展示消息流转图
    """
    print("\n" + "=" * 60)
    print("示例3: 流程可视化器")
    print("=" * 60)
    
    # 1. 初始化LLM
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 请设置 ZHIPU_API_KEY 环境变量")
        return
    
    llm = LLMFactory.create_glm(api_key=api_key, model="glm-4")
    
    # 2. 创建流程可视化器
    flow = FlowVisualizer()
    
    # 3. 创建Swarm
    config = SwarmConfig(
        max_iterations=2,
        verbose=False,  # 不显示详细日志
    )
    swarm = Swarm(config=config)
    
    # 4. 注册Agent
    swarm.register(Leader(llm=llm, name="张三"))
    swarm.register(Researcher(llm=llm, name="李四"))
    swarm.register(Critic(llm=llm, name="王五"))
    swarm.register(Synthesizer(llm=llm, name="钱七"))
    
    # 5. 执行任务
    task = "区块链技术的未来发展趋势"
    
    # 开始流程记录
    flow.start_session(task)
    
    # 运行任务（手动添加消息到流程）
    result = await swarm.run(task)
    
    # 从结果中提取历史并添加到流程
    history = result.get("history", [])
    for msg in history:
        if msg.get("sender"):
            flow.add_message({
                "role": msg.get("sender", {}).get("value", "unknown"),
                "step": len(flow._nodes) + 1,
                "content": msg.get("content", {}),
                "content_type": msg.get("content", {}).get("type", ""),
            })
    
    # 结束流程记录
    flow.end_session(result.get("result", ""))
    
    # 打印流程图（三种样式）
    print("\n样式1: 简单流程图")
    flow.print_flow_diagram("simple")
    
    print("\n样式2: 水平流程图")
    flow.print_flow_diagram("horizontal")
    
    print("\n样式3: 垂直流程图")
    flow.print_flow_diagram("vertical")


async def demo_metrics_dashboard():
    """
    示例4: 指标仪表盘
    
    专门展示涌现指标变化
    """
    print("\n" + "=" * 60)
    print("示例4: 指标仪表盘")
    print("=" * 60)
    
    # 1. 初始化LLM
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 请设置 ZHIPU_API_KEY 环境变量")
        return
    
    llm = LLMFactory.create_glm(api_key=api_key, model="glm-4")
    
    # 2. 创建指标仪表盘
    dashboard = MetricsDashboard()
    
    # 3. 创建Swarm
    config = SwarmConfig(
        max_iterations=3,
        verbose=False,
    )
    swarm = Swarm(config=config)
    
    # 4. 注册Agent
    swarm.register(Leader(llm=llm, name="张三"))
    swarm.register(Researcher(llm=llm, name="李四"))
    swarm.register(Critic(llm=llm, name="王五"))
    swarm.register(Innovator(llm=llm, name="赵六"))
    swarm.register(Synthesizer(llm=llm, name="钱七"))
    
    # 5. 执行任务
    task = "如何平衡工作与生活？"
    
    # 开始仪表盘
    dashboard.start_session()
    
    # 运行任务
    result = await swarm.run(task)
    
    # 更新指标
    metrics = result.get("metrics", {})
    dashboard.update_metrics(metrics)
    
    # 结束仪表盘
    dashboard.end_session(metrics)
    
    # 打印指标
    dashboard.print_metrics()
    
    # 打印演化图
    dashboard.print_evolution_chart()


async def demo_minimal_visualization():
    """
    示例5: 最小化可视化
    
    只显示关键信息，适合生产环境
    """
    print("\n" + "=" * 60)
    print("示例5: 最小化可视化（生产环境推荐）")
    print("=" * 60)
    
    # 1. 初始化LLM
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 请设置 ZHIPU_API_KEY 环境变量")
        return
    
    llm = LLMFactory.create_glm(api_key=api_key, model="glm-4")
    
    # 2. 创建最小化CLI（无动画，简短内容）
    from collectigent.core.debugger.cli import CLIConfig
    config = CLIConfig(
        show_messages=True,
        max_content_length=80,  # 更短的内容
        animate=False,          # 无动画
        show_timestamp=False,   # 无时间戳
    )
    cli = CLIVisualizer(config)
    
    # 3. 创建Swarm
    swarm_config = SwarmConfig(
        max_iterations=2,
        verbose=False,  # 不显示verbose日志
        progress_callback=cli.handle_event,
    )
    swarm = Swarm(config=swarm_config)
    
    # 4. 注册Agent
    swarm.register(Leader(llm=llm, name="张三"))
    swarm.register(Researcher(llm=llm, name="李四"))
    swarm.register(Synthesizer(llm=llm, name="钱七"))
    
    # 5. 执行任务
    task = "如何提高代码质量？"
    
    cli.start_session(task)
    result = await swarm.run(task)
    cli.end_session(result.get("result", ""))
    
    # 只显示结果，不显示详细摘要
    print(f"\n✅ 任务完成")
    print(f"结果: {result.get('result', '')[:100]}...")
    print(f"群体增益: {result.get('metrics', {}).get('group_gain', 0):.2f}")


async def main():
    """运行所有示例"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        Collectigent 可视化调试工具 - 使用示例              ║
    ║                                                           ║
    ║        v0.4: CLI / 流程图 / 指标仪表盘                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 检查API Key
    if not os.getenv("ZHIPU_API_KEY"):
        print("\n❌ 请设置 ZHIPU_API_KEY 环境变量")
        print("\n示例命令:")
        print("  export ZHIPU_API_KEY='your-api-key'")
        print("  python examples/demo_debugger.py")
        return
    
    # 选择示例
    print("\n请选择要运行的示例:")
    print("  1. CLI可视化器（推荐入门）")
    print("  2. 完整调试器（所有功能）")
    print("  3. 流程可视化器（消息流转）")
    print("  4. 指标仪表盘（涌现指标）")
    print("  5. 最小化可视化（生产环境）")
    print("  0. 运行所有示例")
    
    choice = input("\n请输入选择 (0-5): ").strip()
    
    if choice == "1":
        await demo_cli_visualizer()
    elif choice == "2":
        await demo_full_debugger()
    elif choice == "3":
        await demo_flow_visualizer()
    elif choice == "4":
        await demo_metrics_dashboard()
    elif choice == "5":
        await demo_minimal_visualization()
    elif choice == "0":
        # 运行所有示例
        await demo_cli_visualizer()
        await demo_full_debugger()
        await demo_flow_visualizer()
        await demo_metrics_dashboard()
        await demo_minimal_visualization()
    else:
        print("无效选择，运行示例1...")
        await demo_cli_visualizer()
    
    print("\n✅ 演示完成！")


if __name__ == "__main__":
    asyncio.run(main())