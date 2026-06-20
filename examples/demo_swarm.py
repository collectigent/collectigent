"""群体智能演示 - 展示6角色协作产生智能涌现"""

import asyncio
import os

from collectigent import Swarm, LLMFactory
from collectigent.core.agents import (
    Leader, Researcher, Critic, Innovator, Synthesizer, Executor,
    Role
)
from collectigent.core.knowledge import RAGFactory


async def demo_swarm_intelligence():
    """演示群体智能协作"""
    
    # 检查API Key
    if not os.environ.get("ZHIPU_API_KEY"):
        print("❌ 请设置 ZHIPU_API_KEY 环境变量")
        return
    
    print("=" * 60)
    print("群体智能演示 - 6角色协作产生智能涌现")
    print("=" * 60)
    
    # 1. 创建LLM（使用GLM）
    print("\n[1] 初始化LLM提供商 (GLM-4)...")
    llm = LLMFactory.create_glm(model="glm-4")
    print("    ✓ LLM初始化完成")
    
    # 2. 创建知识库（可选，增强Agent的知识）
    print("\n[2] 初始化知识库...")
    try:
        rag = RAGFactory.create_basic(
            embedding_provider="local",
            vector_store="faiss",
        )
        # 添加一些基础知识
        await rag.add_document("""
        群体智能(Collective Intelligence)是指多个智能体通过协作、竞争或信息共享，
        产生超越单个智能体能力的整体行为。这种现象被称为"涌现"(Emergence)。
        
        关键特征：
        1. 协作性：多个智能体共同解决问题
        2. 多样性：不同视角和知识背景
        3. 自组织：无需中央控制
        4. 涌现性：整体大于部分之和
        """, "collective_intelligence_basics")
        
        stats = await rag.get_knowledge_base_stats()
        print(f"    ✓ 知识库已加载 {stats['vector_count']} 条文档")
    except Exception as e:
        print(f"    ⚠ 知识库初始化跳过: {e}")
        rag = None
    
    # 3. 创建Swarm编排器
    print("\n[3] 创建Swarm编排器...")
    swarm = Swarm()
    print("    ✓ Swarm编排器创建完成")
    
    # 4. 注册6个Agent角色
    print("\n[4] 注册6个Agent角色...")
    
    # 领导者：协调整个流程
    leader = Leader(llm=llm, name="领导-张三")
    swarm.register(leader)
    print("    ✓ 领导者-张三 (协调者)")
    
    # 研究者：收集信息、分析问题
    researcher = Researcher(llm=llm, name="研究-李四")
    swarm.register(researcher)
    print("    ✓ 研究者-李四 (信息收集)")
    
    # 批判者：审视论点、找出漏洞
    critic = Critic(llm=llm, name="批判-王五")
    swarm.register(critic)
    print("    ✓ 批判者-王五 (质疑分析)")
    
    # 创新者：提出新观点、突破常规
    innovator = Innovator(llm=llm, name="创新-赵六")
    swarm.register(innovator)
    print("    ✓ 创新者-赵六 (创意生成)")
    
    # 综合者：整合观点、形成共识
    synthesizer = Synthesizer(llm=llm, name="综合-钱七")
    swarm.register(synthesizer)
    print("    ✓ 综合者-钱七 (观点整合)")
    
    # 执行者：落地实施、验证结果
    executor = Executor(llm=llm, name="执行-孙八")
    swarm.register(executor)
    print("    ✓ 执行者-孙八 (方案执行)")
    
    # 5. 执行群体智能任务
    print("\n" + "=" * 60)
    print("开始群体智能协作")
    print("=" * 60)
    
    # 用户提问
    question = "人工智能将如何改变未来的工作方式？我们应该如何应对？"
    print(f"\n📌 用户问题: {question}")
    
    # 执行任务
    print("\n⏳ 群体智能处理中...\n")
    
    try:
        result = await swarm.run(question)
        
        # 6. 展示结果
        print("\n" + "=" * 60)
        print("群体智能处理结果")
        print("=" * 60)
        
        # 显示最终回答
        print("\n📝 最终回答:")
        print("-" * 60)
        print(result.get("response", "无结果"))
        print("-" * 60)
        
        # 显示涌现指标
        print("\n📊 涌现指标:")
        print("-" * 60)
        metrics = result.get("metrics", {})
        
        group_gain = metrics.get("group_gain", 0)
        diversity = metrics.get("diversity_index", 0)
        error_correction = metrics.get("error_correction_rate", 0)
        iterations = result.get("iterations", 1)
        
        print(f"  • 群体增益 (Group Gain): {group_gain:.2f}")
        print(f"    → {'✓ 群体表现优于个体' if group_gain > 1 else '✗ 群体表现未超越个体'}")
        
        print(f"\n  • 多样性指数 (Diversity): {diversity:.2f}")
        print(f"    → {'✓ 高多样性带来更多创意' if diversity > 0.5 else '✗ 多样性不足'}")
        
        print(f"\n  • 错误修正率 (Error Correction): {error_correction:.2%}")
        print(f"    → {'✓ 有效识别和修正错误' if error_correction > 0.3 else '✗ 错误修正能力有限'}")
        
        print(f"\n  • 迭代次数: {iterations}")
        
        # 显示对话历史
        print("\n📋 Agent协作过程:")
        print("-" * 60)
        messages = result.get("messages", [])
        for i, msg in enumerate(messages[:10]):  # 只显示前10条
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]
            name = msg.get("name", "")
            print(f"  {i+1}. [{role}] {name}: {content}...")
        
        if len(messages) > 10:
            print(f"  ... 还有 {len(messages) - 10} 条消息")
        
        # 7. 解释群体智能如何产生
        print("\n" + "=" * 60)
        print("💡 群体智能如何产生")
        print("=" * 60)
        print("""
1. 【角色分工】
   - 研究者收集多角度信息
   - 批判者识别潜在问题
   - 创新者提出突破性方案
   - 综合者整合各方观点
   - 执行者验证可行性

2. 【迭代辩论】
   - 观点经过多轮审视
   - 错误被及时发现和修正
   - 最终形成高质量共识

3. 【涌现效果】
   - 群体智慧 > 任何单个Agent
   - 错误率显著降低
   - 方案更加全面和可行
        """)
        
        print("\n✅ 演示完成！")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


async def demo_rag_with_swarm():
    """演示RAG + Swarm结合"""
    print("\n" + "=" * 60)
    print("RAG增强的群体智能演示")
    print("=" * 60)
    
    # 创建RAG系统
    rag = RAGFactory.create_advanced(
        embedding_provider="local",
        vector_store="faiss",
    )
    
    # 添加知识
    knowledge_base = [
        ("量子计算是一种利用量子力学原理进行计算的技术...", "quantum_computing"),
        ("机器学习是人工智能的一个分支，专注于从数据中学习...", "machine_learning"),
        ("区块链是一种去中心化的分布式账本技术...", "blockchain"),
    ]
    
    for content, source in knowledge_base:
        await rag.add_document(content, source)
    
    print("\n📚 知识库已加载3篇文档")
    
    # 执行查询
    question = "什么是量子计算？"
    result = await rag.query(question)
    
    print(f"\n📌 问题: {question}")
    print(f"\n📝 回答:")
    print(result.answer)
    print(f"\n⏱ 检索耗时: {result.retrieval_time:.3f}s")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        Collectigent 群体智能框架 - 演示程序                  ║
    ║                                                           ║
    ║        展示6角色协作产生智能涌现的过程                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 运行演示
    asyncio.run(demo_swarm_intelligence())
    
    # 可选：运行RAG演示
    print("\n\n是否继续运行RAG演示? (y/n): ", end="")
    if input().strip().lower() == 'y':
        asyncio.run(demo_rag_with_swarm())
