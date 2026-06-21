"""
合同审核示例 - 使用群体智能架构审核合同文档

演示如何使用6角色架构进行合同审核：
1. Leader - 任务分解和协调
2. Researcher - 研究相关法律法规和先例
3. Critic - 识别风险点和漏洞
4. Innovator - 提出优化建议
5. Synthesizer - 综合生成审核报告
6. Executor - 验证条款合规性

运行方式：
    ZHIPU_API_KEY="your-key" python examples/demo_contract_review.py
"""

import os
import asyncio
from typing import List, Dict, Any

# 导入框架组件
from collectigent import LLMFactory, Swarm
from collectigent.core.agents import Leader, Researcher, Critic, Innovator, Synthesizer, Executor
from collectigent.core.orchestrator import SwarmConfig
from collectigent.core.debugger import CLIVisualizer


# 示例合同文本
SAMPLE_CONTRACT = """
技术服务合同

甲方（委托方）：北京科技创新有限公司
乙方（服务方）：上海智能科技有限公司

一、服务内容
乙方为甲方提供人工智能模型开发服务，包括但不限于：
1. 模型设计与开发
2. 模型训练与优化
3. 技术支持与维护

二、服务期限
本合同有效期自2024年1月1日至2024年12月31日。

三、费用与支付
1. 服务费用总计：人民币壹佰万元整（¥1,000,000）
2. 支付方式：合同签订后30日内支付50%，项目完成后支付剩余50%

四、双方权利与义务
甲方权利：
1. 要求乙方按时交付服务成果
2. 对服务质量提出异议

乙方权利：
1. 要求甲方按时支付费用
2. 获得必要的工作条件

五、违约责任
任何一方违约，需支付合同金额10%的违约金。

六、争议解决
因本合同引起的争议，双方应协商解决；协商不成的，提交甲方所在地法院诉讼解决。

七、其他
本合同一式两份，甲乙双方各执一份，具有同等法律效力。

甲方（盖章）：__________    乙方（盖章）：__________
法定代表人：__________      法定代表人：__________
签订日期：2024年1月1日
"""


async def load_contract(file_path: str = None) -> str:
    """加载合同内容"""
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return SAMPLE_CONTRACT


async def analyze_contract(contract_text: str) -> Dict[str, Any]:
    """使用群体智能分析合同"""
    
    # 1. 初始化LLM
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("❌ 请设置 ZHIPU_API_KEY 环境变量")
        return {}
    
    llm = LLMFactory.create_glm(api_key=api_key, model="glm-4")
    
    # 2. 创建可视化器
    cli = CLIVisualizer()
    
    # 3. 创建Swarm配置
    config = SwarmConfig(
        max_iterations=3,
        verbose=True,
        progress_callback=cli.handle_event,
    )
    
    # 4. 创建Swarm
    swarm = Swarm(config=config)
    
    # 5. 注册Agent角色
    swarm.register(Leader(llm=llm, name="合同审核组长"))
    swarm.register(Researcher(llm=llm, name="法律研究员"))
    swarm.register(Critic(llm=llm, name="风险评估专家"))
    swarm.register(Innovator(llm=llm, name="合同优化顾问"))
    swarm.register(Synthesizer(llm=llm, name="报告撰写人"))
    swarm.register(Executor(llm=llm, name="合规验证员"))
    
    # 6. 构建审核任务
    task = f"""请对以下合同进行全面审核：

合同内容：
{contract_text}

审核要点：
1. 合同结构完整性
2. 法律合规性（是否符合相关法律法规）
3. 风险条款识别（模糊表述、漏洞、陷阱）
4. 双方权益平衡
5. 违约责任合理性
6. 争议解决条款有效性

请给出详细的审核报告和修改建议。
"""
    
    # 7. 执行审核
    cli.start_session(task)
    result = await swarm.run(task)
    cli.end_session(result.get("result", ""))
    
    return result


def format_review_report(result: Dict[str, Any]) -> str:
    """格式化审核报告"""
    report = "\n" + "=" * 70 + "\n"
    report += "                    合同审核报告\n"
    report += "=" * 70 + "\n\n"
    
    # 结果摘要
    result_text = result.get("result", "")
    
    # 处理result可能是字典的情况
    if isinstance(result_text, dict):
        if "final_synthesis" in result_text:
            result_text = result_text["final_synthesis"]
        elif "summary" in result_text:
            result_text = result_text["summary"]
        else:
            result_text = str(result_text)
    
    if result_text:
        report += "📋 审核结论：\n"
        report += "-" * 40 + "\n"
        report += result_text + "\n\n"
    
    # 涌现指标
    metrics = result.get("metrics", {})
    if metrics:
        report += "📊 审核指标：\n"
        report += "-" * 40 + "\n"
        
        # 处理metrics格式
        if "current" in metrics:
            metrics = metrics["current"]
        
        report += f"   群体增益: {metrics.get('group_gain', 0):.2f}\n"
        report += f"   多样性指数: {metrics.get('diversity_index', 0):.2f}\n"
        report += f"   错误修正率: {metrics.get('error_correction_rate', 0):.2%}\n\n"
    
    # 审核历史
    history = result.get("history", [])
    if history:
        report += "🔍 审核过程：\n"
        report += "-" * 40 + "\n"
        
        for i, msg in enumerate(history):
            if msg.get("sender"):
                sender = msg.get("sender")
                if isinstance(sender, dict):
                    role = sender.get("value", "unknown")
                else:
                    role = str(sender)
                
                content = msg.get("content", {})
                if isinstance(content, dict):
                    # 根据内容类型提取关键信息
                    content_type = content.get("type", "")
                    if content_type == "task_allocation":
                        preview = content.get("analysis", "")[:100]
                    elif content_type == "research_findings":
                        findings = content.get("findings", [])
                        preview = str(findings[0].get("content", findings[0]))[:100] if findings else "研究完成"
                    elif content_type == "critique":
                        objections = content.get("objections", [])
                        preview = str(objections[0].get("description", objections[0]))[:100] if objections else content.get("criticism", "")[:100]
                    elif content_type == "innovation_ideas":
                        ideas = content.get("ideas", [])
                        preview = ideas[0].get("description", str(ideas[0]))[:100] if ideas else "创新建议"
                    elif content_type == "synthesis":
                        preview = content.get("final_synthesis", "")[:100]
                    else:
                        preview = str(content)[:80]
                else:
                    preview = str(content)[:80]
                
                preview = preview.replace("\n", " ").strip()
                report += f"   [{i+1}] {role}: {preview}...\n"
    
    report += "\n" + "=" * 70 + "\n"
    return report


async def main():
    """主函数"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        Collectigent 合同审核演示                          ║
    ║                                                           ║
    ║        使用群体智能架构审核合同文档                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 加载合同
    print("📄 加载合同文件...")
    contract_text = await load_contract()
    print(f"   ✓ 合同内容已加载 ({len(contract_text)} 字符)")
    
    # 分析合同
    print("\n🔍 开始合同审核...")
    result = await analyze_contract(contract_text)
    
    # 输出报告
    if result:
        print("\n" + "=" * 70)
        print("                    审核完成！")
        print("=" * 70)
        print(format_review_report(result))


if __name__ == "__main__":
    asyncio.run(main())