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

使用说明：
    1. 将合同文档放入 data/contracts/ 文件夹
    2. 支持格式：.docx, .doc, .pdf, .txt, .md
    3. 运行脚本后选择要审核的文档
"""

import os
import asyncio
from typing import List, Dict, Any, Optional

# 导入框架组件
from collectigent import LLMFactory, Swarm
from collectigent.core.agents import Leader, Researcher, Critic, Innovator, Synthesizer, Executor
from collectigent.core.orchestrator import SwarmConfig
from collectigent.core.debugger import CLIVisualizer
from collectigent.core.knowledge import DocumentLoader


# 合同文档文件夹路径
CONTRACTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "contracts")

# 支持的文件格式
SUPPORTED_FORMATS = (".docx", ".doc", ".pdf", ".txt", ".md", ".json", ".html")


# 示例合同文本（当没有找到文档时使用）
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


def list_contract_files(folder_path: str = CONTRACTS_FOLDER) -> List[str]:
    """列出合同文件夹中的所有文档文件"""
    files = []
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(SUPPORTED_FORMATS):
                files.append(filename)
    return sorted(files)


def select_contract_file(files: List[str]) -> Optional[str]:
    """让用户选择要审核的合同文件"""
    if not files:
        print("📭 合同文件夹中没有找到文档文件")
        print(f"   请将合同文档放入: {CONTRACTS_FOLDER}")
        print(f"   支持格式: {', '.join(SUPPORTED_FORMATS)}")
        return None
    
    print("\n📁 可用的合同文档：")
    for i, filename in enumerate(files, 1):
        print(f"   {i}. {filename}")
    print(f"   0. 使用示例合同")
    
    while True:
        try:
            choice = input("\n请选择要审核的文档 (输入序号): ").strip()
            if choice == "0":
                return None
            index = int(choice) - 1
            if 0 <= index < len(files):
                return files[index]
            print(f"❌ 无效选择，请输入 0-{len(files)}")
        except ValueError:
            print("❌ 请输入有效数字")


async def load_contract(file_path: str = None) -> str:
    """加载合同内容"""
    if file_path:
        full_path = os.path.join(CONTRACTS_FOLDER, file_path)
        if os.path.exists(full_path):
            print(f"📄 正在加载文档: {file_path}")
            try:
                # 使用 DocumentLoader.create() 方法创建具体的加载器
                from collectigent.core.knowledge.loader import DocumentLoader, FileType
                
                # 检测文件类型并创建对应的加载器
                file_type = DocumentLoader.detect_file_type(full_path)
                loader = DocumentLoader.create(file_type)
                doc = loader.load(full_path)
                
                if doc:
                    print(f"   ✓ 文档加载成功 ({len(doc.content)} 字符)")
                    return doc.content
            except ImportError as e:
                print(f"   ⚠ 缺少依赖: {str(e)}")
                print("   将尝试使用文本方式读取...")
            except Exception as e:
                print(f"   ⚠ 文档加载失败: {str(e)}")
                print("   将尝试使用文本方式读取...")
            
            # 回退到文本读取方式
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    print(f"   ✓ 文本方式读取成功 ({len(content)} 字符)")
                    return content
            except Exception as e:
                print(f"   ✗ 无法读取文档内容: {str(e)}")
    
    # 返回示例合同
    print("📄 使用示例合同")
    return SAMPLE_CONTRACT


async def analyze_contract(contract_text: str, contract_name: str = "合同") -> Dict[str, Any]:
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

合同名称：{contract_name}

合同内容：
{contract_text[:3000]}

审核要点：
1. 合同结构完整性（是否包含必备条款）
2. 法律合规性（是否符合《民法典》等相关法律法规）
3. 风险条款识别（模糊表述、漏洞、陷阱条款）
4. 双方权益平衡（权利义务是否对等）
5. 违约责任合理性（违约金比例是否合理）
6. 争议解决条款有效性（管辖法院是否明确）
7. 知识产权归属（技术成果归属是否明确）
8. 保密条款（是否完善）

请给出详细的审核报告，包括：
- 问题清单（按风险等级分类）
- 修改建议
- 风险评估
"""
    
    # 7. 执行审核
    cli.start_session(task)
    result = await swarm.run(task)
    cli.end_session(result.get("result", ""))
    
    return result


def format_review_report(result: Dict[str, Any], contract_name: str = "合同") -> str:
    """格式化审核报告"""
    report = "\n" + "=" * 70 + "\n"
    report += f"                    合同审核报告 - {contract_name}\n"
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
        
        report += f"   群体增益: {metrics.get('group_gain', 0):.2f} {'✓' if metrics.get('group_gain', 0) > 1 else '✗'}\n"
        report += f"   多样性指数: {metrics.get('diversity_index', 0):.2f} {'✓' if metrics.get('diversity_index', 0) > 0.5 else '✗'}\n"
        report += f"   错误修正率: {metrics.get('error_correction_rate', 0):.2%} {'✓' if metrics.get('error_correction_rate', 0) > 0.3 else '✗'}\n\n"
    
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
                        preview = content.get("analysis", "")[:80]
                    elif content_type == "research_findings":
                        findings = content.get("findings", [])
                        preview = str(findings[0].get("content", findings[0]))[:80] if findings else "研究完成"
                    elif content_type == "critique":
                        objections = content.get("objections", [])
                        preview = str(objections[0].get("description", objections[0]))[:80] if objections else content.get("criticism", "")[:80]
                    elif content_type == "innovation_ideas":
                        ideas = content.get("ideas", [])
                        preview = ideas[0].get("description", str(ideas[0]))[:80] if ideas else "创新建议"
                    elif content_type == "synthesis":
                        preview = content.get("final_synthesis", "")[:80]
                    else:
                        preview = str(content)[:60]
                else:
                    preview = str(content)[:60]
                
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
    
    # 1. 列出并选择合同文件
    contract_files = list_contract_files()
    selected_file = select_contract_file(contract_files)
    
    # 2. 加载合同内容
    print("\n📄 加载合同文件...")
    contract_text = await load_contract(selected_file)
    contract_name = selected_file if selected_file else "示例合同"
    
    # 3. 分析合同
    print("\n🔍 开始合同审核...")
    result = await analyze_contract(contract_text, contract_name)
    
    # 4. 输出报告
    if result:
        print("\n" + "=" * 70)
        print(f"                    审核完成！ - {contract_name}")
        print("=" * 70)
        print(format_review_report(result, contract_name))


if __name__ == "__main__":
    asyncio.run(main())