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
    
    # 1. 从配置文件加载模型配置（方式一）
    from collectigent.core.orchestrator import (
        MultiModelConfig,
        create_config_from_file,
        Swarm,
        SwarmConfig,
    )
    
    try:
        model_config = create_config_from_file("config/model_config.yaml")
        print("✅ 已从配置文件加载模型配置")
    except Exception as e:
        print(f"⚠️ 配置文件加载失败: {e}")
        model_config = MultiModelConfig()
        print("⚠️ 使用默认模型配置")
    
    # 显示配置摘要
    print("\n📊 角色模型配置:")
    print(model_config.summary())
    
    # 2. 检查是否有任何配置的API Key
    from collectigent.core.config import get_config_loader
    loader = get_config_loader("config/model_config.yaml")
    api_keys = loader.get_api_keys()
    has_api_key = any(api_keys.get(k) for k in api_keys if api_keys[k])
    
    if not has_api_key:
        print("❌ 配置文件中未设置任何API Key，请在 config/model_config.yaml 中配置")
        return {}
    
    # 3. 创建可视化器
    from collectigent.core.debugger import CLIVisualizer
    cli = CLIVisualizer()
    
    # 4. 创建Swarm配置
    from collectigent.core.orchestrator import SwarmConfig
    config = SwarmConfig(
        max_iterations=3,
        verbose=True,
        progress_callback=cli.handle_event,
    )
    
    # 5. 创建Swarm（传入模型配置）
    swarm = Swarm(config=config, model_config=model_config)
    
    # 6. 注册Agent角色（使用模型配置中的LLM）
    from collectigent.core.llm import LLMFactory, ProviderType
    from collectigent.core.agents.base import Agent
    
    # 创建回退LLM（使用GLM）
    fallback_llm = LLMFactory.create_glm(model="glm-4", api_key=api_keys.get("glm", ""))
    
    for role in model_config.role_configs:
        try:
            llm = model_config.get_provider(role)
            agent_class = {
                "leader": Leader,
                "researcher": Researcher,
                "critic": Critic,
                "innovator": Innovator,
                "synthesizer": Synthesizer,
                "executor": Executor,
            }.get(role.value)
            
            if agent_class:
                # 获取角色中文名称
                role_names = {
                    "leader": "合同审核组长",
                    "researcher": "法律研究员",
                    "critic": "风险评估专家",
                    "innovator": "合同优化顾问",
                    "synthesizer": "报告撰写人",
                    "executor": "合规验证员",
                }
                agent = agent_class(llm=llm, name=role_names.get(role.value, role.value))
                # 设置备用LLM
                agent._fallback_llm = fallback_llm
                swarm.register(agent)
                print(f"   ✅ {role_names.get(role.value)} 已注册 ({model_config.get_config(role).provider.value}/{model_config.get_config(role).model})")
        except Exception as e:
            # 回退到GLM
            agent_class = {
                "leader": Leader,
                "researcher": Researcher,
                "critic": Critic,
                "innovator": Innovator,
                "synthesizer": Synthesizer,
                "executor": Executor,
            }.get(role.value)
            
            if agent_class:
                role_names = {
                    "leader": "合同审核组长",
                    "researcher": "法律研究员",
                    "critic": "风险评估专家",
                    "innovator": "合同优化顾问",
                    "synthesizer": "报告撰写人",
                    "executor": "合规验证员",
                }
                agent = agent_class(llm=fallback_llm, name=role_names.get(role.value, role.value))
                agent._fallback_llm = fallback_llm
                swarm.register(agent)
                print(f"   ⚠️ {role_names.get(role.value)} 初始化失败，已回退到 GLM ({e})")
    
    # 7. 构建审核任务
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
    
    # 8. 执行审核
    cli.start_session(task)
    result = await swarm.run(task)
    cli.end_session(result.get("result", ""))
    
    return result


def format_review_report(result: Dict[str, Any], contract_name: str = "合同") -> str:
    """格式化审核报告 - 清晰、专业的呈现方式"""
    
    # 定义颜色和样式
    COLOR_HEADER = "\033[1;36m"  # 青色加粗
    COLOR_SUCCESS = "\033[1;32m"  # 绿色加粗
    COLOR_WARNING = "\033[1;33m"  # 黄色加粗
    COLOR_DANGER = "\033[1;31m"   # 红色加粗
    COLOR_RESET = "\033[0m"       # 重置颜色
    
    report = "\n" + "=" * 80 + "\n"
    report += f"{COLOR_HEADER}"
    report += f"                    合同审核报告\n"
    report += f"                    {contract_name}\n"
    report += f"{COLOR_RESET}"
    report += "=" * 80 + "\n\n"
    
    # 一、审核结论摘要
    result_text = result.get("result", "")
    if isinstance(result_text, dict):
        if "final_synthesis" in result_text:
            result_text = result_text["final_synthesis"]
        elif "summary" in result_text:
            result_text = result_text["summary"]
        else:
            result_text = str(result_text)
    
    if result_text:
        report += f"{COLOR_HEADER}一、审核结论摘要{COLOR_RESET}\n"
        report += "-" * 60 + "\n"
        report += wrap_text(result_text, width=70, indent="  ") + "\n\n"
    
    # 二、风险等级评估
    report += f"{COLOR_HEADER}二、风险等级评估{COLOR_RESET}\n"
    report += "-" * 60 + "\n"
    
    # 提取风险信息
    risk_level = assess_risk_level(result)
    risk_color = COLOR_DANGER if risk_level == "高" else COLOR_WARNING if risk_level == "中" else COLOR_SUCCESS
    
    report += f"  🔴 综合风险等级: {risk_color}{risk_level}{COLOR_RESET}\n\n"
    
    # 三、问题清单（按风险等级分类）
    issues = extract_issues(result)
    if issues:
        report += f"{COLOR_HEADER}三、问题清单{COLOR_RESET}\n"
        report += "-" * 60 + "\n"
        
        # 按风险等级分组
        high_issues = [i for i in issues if i.get("risk", "中") == "高"]
        medium_issues = [i for i in issues if i.get("risk", "中") == "中"]
        low_issues = [i for i in issues if i.get("risk", "中") == "低"]
        
        if high_issues:
            report += f"\n{COLOR_DANGER}【高风险】{COLOR_RESET}\n"
            for i, issue in enumerate(high_issues, 1):
                report += f"   {i}. {issue.get('title', '未命名问题')}\n"
                report += f"      → {issue.get('description', '')[:60]}...\n"
        
        if medium_issues:
            report += f"\n{COLOR_WARNING}【中风险】{COLOR_RESET}\n"
            for i, issue in enumerate(medium_issues, 1):
                report += f"   {i}. {issue.get('title', '未命名问题')}\n"
                report += f"      → {issue.get('description', '')[:60]}...\n"
        
        if low_issues:
            report += f"\n{COLOR_SUCCESS}【低风险】{COLOR_RESET}\n"
            for i, issue in enumerate(low_issues, 1):
                report += f"   {i}. {issue.get('title', '未命名问题')}\n"
                report += f"      → {issue.get('description', '')[:60]}...\n"
        
        report += "\n"
    
    # 四、修改建议
    suggestions = extract_suggestions(result)
    if suggestions:
        report += f"{COLOR_HEADER}四、修改建议{COLOR_RESET}\n"
        report += "-" * 60 + "\n"
        for i, suggestion in enumerate(suggestions, 1):
            report += f"   {i}. {suggestion}\n"
        report += "\n"
    
    # 五、涌现指标
    metrics = result.get("metrics", {})
    if metrics:
        report += f"{COLOR_HEADER}五、审核指标{COLOR_RESET}\n"
        report += "-" * 60 + "\n"
        
        if "current" in metrics:
            metrics = metrics["current"]
        
        report += "   ┌─────────────────────────────────────────────┐\n"
        report += "   │           群体智能涌现指标                    │\n"
        report += "   ├─────────────────────────────────────────────┤\n"
        
        group_gain = metrics.get("group_gain", 0)
        gain_status = COLOR_SUCCESS if group_gain > 1 else COLOR_WARNING
        report += f"   │  📊 群体增益: {gain_status}{group_gain:.2f}{COLOR_RESET}              │\n"
        
        diversity = metrics.get("diversity_index", 0)
        div_status = COLOR_SUCCESS if diversity > 0.5 else COLOR_WARNING
        report += f"   │  🌈 多样性指数: {div_status}{diversity:.2f}{COLOR_RESET}           │\n"
        
        correction = metrics.get("error_correction_rate", 0)
        corr_status = COLOR_SUCCESS if correction > 0.3 else COLOR_WARNING
        report += f"   │  🔧 错误修正率: {corr_status}{correction:.2%}{COLOR_RESET}          │\n"
        
        report += "   └─────────────────────────────────────────────┘\n"
        report += "\n"
    
    # 六、审核过程概览
    history = result.get("history", [])
    if history:
        report += f"{COLOR_HEADER}六、审核过程概览{COLOR_RESET}\n"
        report += "-" * 60 + "\n"
        
        role_names = {
            "leader": "👑 领导者",
            "researcher": "📚 研究员",
            "critic": "🔍 批判者",
            "innovator": "💡 创新者",
            "synthesizer": "📝 综合者",
            "executor": "⚙️ 执行者",
        }
        
        for i, msg in enumerate(history):
            if msg.get("sender"):
                sender = msg.get("sender")
                if isinstance(sender, dict):
                    role_key = sender.get("value", "unknown")
                else:
                    role_key = str(sender).lower()
                
                role_display = role_names.get(role_key, f"❓ {role_key}")
                
                content = msg.get("content", {})
                if isinstance(content, dict):
                    content_type = content.get("type", "")
                    if content_type == "task_allocation":
                        preview = content.get("analysis", "")[:50]
                    elif content_type == "research_findings":
                        findings = content.get("findings", [])
                        preview = str(findings[0].get("content", findings[0]))[:50] if findings else "研究完成"
                    elif content_type == "critique":
                        objections = content.get("objections", [])
                        preview = str(objections[0].get("description", objections[0]))[:50] if objections else content.get("criticism", "")[:50]
                    elif content_type == "innovation_ideas":
                        ideas = content.get("ideas", [])
                        preview = ideas[0].get("description", str(ideas[0]))[:50] if ideas else "创新建议"
                    elif content_type == "synthesis":
                        preview = content.get("final_synthesis", "")[:50]
                    else:
                        preview = str(content)[:40]
                else:
                    preview = str(content)[:40]
                
                preview = preview.replace("\n", " ").strip()
                report += f"   [{i+1}] {role_display}: {preview}...\n"
        
        report += "\n"
    
    report += "=" * 80 + "\n"
    report += f"{COLOR_HEADER}                    审核报告结束{COLOR_RESET}\n"
    report += "=" * 80 + "\n"
    
    return report


def wrap_text(text: str, width: int = 70, indent: str = "") -> str:
    """文本换行辅助函数"""
    words = text.split()
    lines = []
    current_line = indent
    
    for word in words:
        if len(current_line) + len(word) + 1 <= width:
            current_line += word + " "
        else:
            lines.append(current_line.strip())
            current_line = indent + word + " "
    
    if current_line.strip():
        lines.append(current_line.strip())
    
    return "\n".join(lines)


def assess_risk_level(result: Dict[str, Any]) -> str:
    """评估综合风险等级"""
    metrics = result.get("metrics", {})
    if "current" in metrics:
        metrics = metrics["current"]
    
    # 根据指标评估风险
    error_correction = metrics.get("error_correction_rate", 0)
    diversity = metrics.get("diversity_index", 0)
    
    if error_correction < 0.2 or diversity < 0.3:
        return "高"
    elif error_correction < 0.5 or diversity < 0.6:
        return "中"
    else:
        return "低"


def extract_issues(result: Dict[str, Any]) -> list[dict]:
    """从审核结果中提取问题清单"""
    issues = []
    
    # 从批判者的异议中提取问题
    history = result.get("history", [])
    for msg in history:
        if msg.get("sender"):
            sender = msg.get("sender")
            if isinstance(sender, dict):
                role = sender.get("value", "")
            else:
                role = str(sender).lower()
            
            if role == "critic":
                content = msg.get("content", {})
                if isinstance(content, dict):
                    objections = content.get("objections", [])
                    for obj in objections:
                        issues.append({
                            "title": obj.get("type", "问题"),
                            "description": obj.get("description", str(obj)),
                            "risk": "高" if obj.get("severity") == "high" else "中",
                        })
    
    # 从结果中提取问题
    result_text = result.get("result", "")
    if isinstance(result_text, dict):
        if "issues" in result_text:
            issues.extend(result_text["issues"])
    
    return issues


def extract_suggestions(result: Dict[str, Any]) -> list[str]:
    """从审核结果中提取修改建议"""
    suggestions = []
    
    # 从创新者的建议中提取
    history = result.get("history", [])
    for msg in history:
        if msg.get("sender"):
            sender = msg.get("sender")
            if isinstance(sender, dict):
                role = sender.get("value", "")
            else:
                role = str(sender).lower()
            
            if role == "innovator":
                content = msg.get("content", {})
                if isinstance(content, dict):
                    ideas = content.get("ideas", [])
                    for idea in ideas:
                        suggestions.append(idea.get("description", str(idea)))
    
    # 从结果中提取建议
    result_text = result.get("result", "")
    if isinstance(result_text, str) and ("建议" in result_text or "修改" in result_text):
        # 简单提取包含"建议"或"修改"的句子
        sentences = result_text.split("。")
        for sent in sentences:
            if "建议" in sent or "修改" in sent:
                suggestions.append(sent.strip())
    
    return suggestions[:5]  # 最多返回5条建议


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