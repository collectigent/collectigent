"""快速验证脚本 - 使用GLM模型验证群体智能框架"""

import asyncio
import os

# 设置GLM API Key
if not os.environ.get("ZHIPU_API_KEY"):
    os.environ["ZHIPU_API_KEY"] = input("请输入智谱AI (GLM) API Key: ").strip()

from collectigent import Swarm, LLMFactory
from collectigent.core.agents import Leader, Researcher, Critic


async def quick_test():
    """快速测试群体智能框架"""
    
    print("\n" + "=" * 60)
    print("群体智能框架快速验证")
    print("=" * 60)
    
    # 1. 创建LLM (使用GLM)
    print("\n[1] 初始化LLM (GLM-4)...")
    llm = LLMFactory.create_glm(model="glm-4")
    print("    ✓ 完成")
    
    # 2. 创建Swarm
    print("\n[2] 创建Swarm...")
    swarm = Swarm()
    print("    ✓ 完成")
    
    # 3. 注册Agent（每个Agent传入LLM）
    print("\n[3] 注册Agent (Leader, Researcher, Critic)...")
    swarm.register(Leader(llm=llm, name="领导"))
    swarm.register(Researcher(llm=llm, name="研究者"))
    swarm.register(Critic(llm=llm, name="批判者"))
    print("    ✓ 完成")
    
    # 4. 执行任务
    question = "人工智能将如何改变教育行业？"
    print(f"\n[4] 执行任务...")
    print(f"    问题: {question}")
    
    result = await swarm.run(question)
    
    # 5. 显示结果
    print("\n" + "=" * 60)
    print("结果")
    print("=" * 60)
    
    result_data = result.get("result", {})
    
    if isinstance(result_data, dict):
        print(f"\n回答:\n{result_data}")
    else:
        print(f"\n回答:\n{result_data}")
    
    # 也显示原始历史记录
    history = result.get("history", [])
    if history:
        print(f"\n📋 Agent协作过程 (共 {len(history)} 条消息):")
        print("-" * 60)
        for i, msg in enumerate(history[:5]):
            sender = msg.get("sender", "unknown")
            content = msg.get("content", {})
            if isinstance(content, dict):
                content_str = str(content)[:100]
            else:
                content_str = str(content)[:100]
            print(f"  {i+1}. [{sender}]: {content_str}...")
    
    metrics = result.get("metrics", {})
    print(f"\n群体增益: {metrics.get('group_gain', 0):.2f}")
    print(f"多样性指数: {metrics.get('diversity_index', 0):.2f}")
    print(f"错误修正率: {metrics.get('error_correction_rate', 0):.2%}")
    print(f"迭代次数: {result.get('iterations', 1)}")
    
    print("\n✅ 验证完成!")


async def test_llm_direct():
    """直接测试LLM调用"""
    print("\n" + "=" * 60)
    print("GLM模型调用测试")
    print("=" * 60)
    
    llm = LLMFactory.create_glm(model="glm-4")
    
    print("\n发送测试请求...")
    response = await llm.generate("用一句话解释什么是群体智能")
    
    print(f"\n回答: {response.content}")
    print(f"Token使用: {response.token_count if hasattr(response, 'token_count') else 'N/A'}")
    print("\n✅ GLM测试完成!")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        群体智能框架 - GLM模型验证                           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 测试LLM
    asyncio.run(test_llm_direct())
    
    # 询问是否继续完整测试
    print("\n是否运行完整群体智能测试? (y/n): ", end="")
    if input().strip().lower() == 'y':
        asyncio.run(quick_test())
