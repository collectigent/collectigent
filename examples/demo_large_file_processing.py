"""大规模文件处理演示 - 完整工作流程"""

import asyncio
import os
from pathlib import Path

# 创建测试数据目录
test_dir = Path("data/test_files")
test_dir.mkdir(parents=True, exist_ok=True)

# 创建测试文件
test_files = {
    "主合同_2024.txt": """
主合同
合同编号：HT-2024-001

甲方：ABC有限公司
乙方：XYZ科技有限公司

一、合同标的
乙方为甲方提供软件开发服务，总金额为人民币壹佰万元整。

二、履行期限
合同生效后12个月内完成全部开发工作。

三、违约责任
任何一方违约，需支付合同金额10%的违约金。

四、争议解决
如发生争议，提交甲方所在地法院解决。

五、合同生效
本合同自双方签字盖章之日起生效。
签署日期：2024年1月15日
""",
    "补充协议_2024.txt": """
补充协议
协议编号：HT-2024-001-补001

甲方：ABC有限公司
乙方：XYZ科技有限公司

鉴于双方于2024年1月15日签署的主合同，现经协商一致，达成如下补充：

一、变更内容
1. 开发期限延长至18个月
2. 合同金额调整为人民币壹佰伍拾万元整

二、违约金调整
任何一方违约，需支付合同金额15%的违约金。

三、生效条件
本协议自双方签字盖章之日起生效，与主合同具有同等法律效力。

签署日期：2024年6月1日
""",
    "财务报表_Q2.txt": """
2024年第二季度财务报表

一、营收情况
本季度营收：500万元
同比增长：15%
环比增长：8%

二、利润分析
净利润：40万元
净利润率：8%

三、现金流
经营活动现金流：120万元

四、应收账款
应收账款余额：80万元
平均回款周期：45天
""",
    "行业报告_2024.txt": """
2024年软件行业发展报告

一、市场规模
中国软件市场规模预计达到8000亿元，同比增长18%。

二、竞争格局
头部企业市场份额进一步集中，CR5达到45%。

三、技术趋势
AI驱动的智能化成为主要发展方向，生成式AI应用加速落地。

四、机会分析
企业服务、工业软件、AI基础设施为三大增长引擎。
""",
    "新闻舆情_202406.txt": """
行业新闻汇总（2024年6月）

【正面】
- XYZ科技获得A轮融资5000万元
- 行业政策利好，软件企业税收优惠延续

【中性】
- 行业人才竞争加剧，薪资水平持续上涨

【负面】
- 部分企业应收账款问题突出
""",
    "历史邮件_沟通记录.txt": """
邮件沟通记录

发件人：张三（ABC公司）
收件人：李四（XYZ科技）
日期：2024年3月10日

主题：关于项目进度的沟通

内容：
李工你好，

关于项目进度，我们希望能够提前2周完成第一阶段交付。
请评估是否可行，并提供新的时间表。

另外，关于付款方式，我们希望能够改为分三期支付。

谢谢！

张三
---

回复：
张经理你好，

收到你的邮件。我们评估后认为提前2周有一定难度，
但可以尽力争取。付款方式改为三期支付没有问题。

具体计划下周一会发给你。

李四
"""
}

# 写入测试文件
for filename, content in test_files.items():
    with open(test_dir / filename, "w", encoding="utf-8") as f:
        f.write(content.strip())


async def main():
    """大规模文件处理完整流程演示"""
    print("=" * 70)
    print("        Collectigent 大规模文件处理演示")
    print("=" * 70)
    
    # 阶段一：文件预处理
    print("\n" + "=" * 50)
    print("阶段一：文件预处理层（Ingestion Pipeline）")
    print("=" * 50)
    
    from collectigent.core.knowledge import FileIngestionPipeline
    
    pipeline = FileIngestionPipeline()
    results = pipeline.batch_process(str(test_dir))
    
    print(f"处理文件数量：{len(results)}")
    for filename, msg, metadata in results:
        status = "✓" if "成功" in msg or "完成" in msg else "✗"
        print(f"  {status} {filename}: {msg}")
    
    stats = pipeline.get_stats()
    print(f"\n预处理统计：{stats}")
    
    # 获取处理后的文件内容
    processed_files = []
    for metadata in pipeline.list_files():
        content = pipeline._parse_by_type(metadata.source_path, metadata.file_type)
        processed_files.append((metadata.file_id, metadata.filename, content))
    
    # 阶段二：智能分块与向量化
    print("\n" + "=" * 50)
    print("阶段二：智能分块与向量化")
    print("=" * 50)
    
    from collectigent.core.knowledge import SemanticChunking, ChunkEmbedding
    
    chunker = SemanticChunking(min_chunk_size=200, max_chunk_size=500, overlap_ratio=0.15)
    all_chunks = []
    
    for file_id, filename, content in processed_files:
        chunks = chunker.multi_granularity_chunking(content, file_id, filename)
        chunks = chunker.add_context_enhancement(chunks, filename)
        all_chunks.extend(chunks)
    
    print(f"生成块数量：{len(all_chunks)}")
    print(f"句子级块：{sum(1 for c in all_chunks if c.granularity.value == 'sentence')}")
    print(f"段落级块：{sum(1 for c in all_chunks if c.granularity.value == 'paragraph')}")
    print(f"章节级块：{sum(1 for c in all_chunks if c.granularity.value == 'section')}")
    
    # 阶段三：文件级并行处理
    print("\n" + "=" * 50)
    print("阶段三：文件级并行处理（File-Level Parallelism）")
    print("=" * 50)
    
    from collectigent.core.knowledge import FileAnalysisManager
    
    manager = FileAnalysisManager()
    analysis_results = await manager.process_files_parallel(processed_files)
    
    print(f"\n分析结果汇总：")
    for result in analysis_results:
        print(f"\n📄 {result.filename}")
        print(f"   分析师：{result.analyst_type}")
        print(f"   模型：{result.model_used}")
        print(f"   摘要：{result.summary}")
        if result.key_points:
            print(f"   关键点：{', '.join(result.key_points)}")
        if result.risks:
            print(f"   风险点：{', '.join(result.risks)}")
        if result.conflicts:
            print(f"   冲突：{', '.join(result.conflicts)}")
    
    blackboard_stats = manager.blackboard.get_stats()
    print(f"\n黑板统计：{blackboard_stats}")
    
    # 阶段四：跨文件综合推理
    print("\n" + "=" * 50)
    print("阶段四：跨文件综合推理（Cross-File Synthesis）")
    print("=" * 50)
    
    from collectigent.core.knowledge import CrossFileSynthesizer
    
    synthesizer = CrossFileSynthesizer()
    synthesis_result = synthesizer.synthesize(processed_files)
    
    print(f"\n知识图谱统计：{synthesis_result['graph_stats']}")
    
    if synthesis_result['conflicts']:
        print("\n🔍 检测到的冲突：")
        for conflict in synthesis_result['conflicts']:
            print(f"   ⚠️ [{conflict.severity.upper()}] {conflict.description}")
            print(f"      {conflict.file1_name}: {conflict.evidence1}")
            print(f"      {conflict.file2_name}: {conflict.evidence2}")
    
    if synthesis_result['timeline']:
        print("\n📅 时间线事件：")
        for event in synthesis_result['timeline']:
            date_str = event.date.strftime("%Y-%m-%d") if event.date else "未知日期"
            print(f"   • {date_str}: {event.description}")
    
    # 阶段五：增量更新演示
    print("\n" + "=" * 50)
    print("阶段五：增量更新与持续优化")
    print("=" * 50)
    
    from collectigent.core.knowledge import IncrementalProcessor, ContinuousOptimizer
    
    processor = IncrementalProcessor()
    optimizer = ContinuousOptimizer()
    
    # 模拟第一次检测（无变更）
    update1 = processor.detect_and_analyze(str(test_dir))
    print(f"第一次检测（无变更）：{update1}")
    
    # 创建一个新文件模拟增量更新
    new_file = test_dir / "新合同_2024.txt"
    with open(new_file, "w", encoding="utf-8") as f:
        f.write("新合同\n合同金额：50万元\n签署日期：2024年7月1日")
    
    # 模拟第二次检测（有新增）
    update2 = processor.detect_and_analyze(str(test_dir))
    if update2:
        print(f"\n检测到变更：")
        for change in update2.changes:
            print(f"   • {change.change_type.value}: {change.filename}")
        
        print(f"\n影响分析：")
        for impact in update2.impact_results:
            print(f"   • {impact.severity.upper()}: {impact.description}")
    
    # 记录性能指标
    optimizer.record_performance({
        "retrieval_precision": 0.85,
        "processing_speed": 12,
        "conflict_detection_rate": 0.92
    })
    
    print(f"\n优化建议：{optimizer.suggest_optimizations()}")
    
    # 清理测试文件
    for file in test_dir.iterdir():
        file.unlink()
    test_dir.rmdir()
    
    print("\n" + "=" * 70)
    print("        大规模文件处理流程演示完成！")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
