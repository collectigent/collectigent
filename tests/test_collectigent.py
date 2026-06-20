"""Collectigent 测试套件"""

import pytest
import asyncio

from collectigent import Swarm
from collectigent.core.agents.base import Role, Message
from collectigent.core.agents import Leader, Researcher, Critic, Innovator, Synthesizer, Executor
from collectigent.core.memory import MemorySystem, ShortTermMemory, LongTermMemory
from collectigent.core.engine import DebateEngine, ConsensusProtocol, DebateConfig
from collectigent.core.metrics import EmergenceMetrics


class TestAgents:
    """Agent角色测试"""
    
    def test_leader_creation(self):
        leader = Leader()
        assert leader.role == Role.LEADER
        assert leader.temperature == 0.6
    
    def test_researcher_creation(self):
        researcher = Researcher()
        assert researcher.role == Role.RESEARCHER
        assert researcher.temperature == 0.8
    
    def test_critic_creation(self):
        critic = Critic()
        assert critic.role == Role.CRITIC
        assert critic.temperature == 0.5
    
    def test_innovator_creation(self):
        innovator = Innovator()
        assert innovator.role == Role.INNOVATOR
        assert innovator.temperature == 1.0
    
    def test_synthesizer_creation(self):
        synthesizer = Synthesizer()
        assert synthesizer.role == Role.SYNTHESIZER
    
    def test_executor_creation(self):
        executor = Executor()
        assert executor.role == Role.EXECUTOR


class TestMemory:
    """记忆系统测试"""
    
    def test_short_term_memory(self):
        memory = ShortTermMemory(max_items=2)
        
        # 存储
        memory.set("key1", "value1")
        memory.set("key2", "value2")
        
        # 读取
        assert memory.get("key1") == "value1"
        
        # LRU淘汰
        memory.set("key3", "value3")
        assert memory.get("key1") is None  # 被淘汰
    
    def test_long_term_memory(self):
        memory = LongTermMemory()
        
        # 存储知识
        memory.store_knowledge("k1", {"fact": "test"}, tags=["test"])
        
        # 按标签检索
        results = memory.retrieve_by_tags(["test"])
        assert len(results) == 1
    
    def test_memory_system(self):
        mem = MemorySystem()
        
        # 短期记忆
        mem.remember("short", "data")
        assert mem.recall("short") == "data"
        
        # 长期记忆
        mem.memorize("long", {"info": "persistent"}, tags=["tag1"])
        assert mem.recall("long") == {"info": "persistent"}


class TestDebateEngine:
    """辩论引擎测试"""
    
    @pytest.mark.asyncio
    async def test_iterative_debate(self):
        config = DebateConfig(max_rounds=3, protocol=ConsensusProtocol.ITERATIVE_DEBATE)
        engine = DebateEngine(config)
        
        # 创建简单上下文
        context = [
            Message(sender=None, content={"task": "测试任务"})
        ]
        
        agents = {
            Role.LEADER: Leader(),
            Role.RESEARCHER: Researcher(),
            Role.CRITIC: Critic(),
        }
        
        result = await engine.run_debate(context, agents)
        
        assert result["rounds"] >= 1
        assert "verdict" in result


class TestEmergenceMetrics:
    """涌现指标测试"""
    
    def test_group_gain(self):
        metrics = EmergenceMetrics()
        
        # 模拟对话
        messages = [
            Message(sender=Role.RESEARCHER, content={"type": "research"}, metadata={"confidence": 0.7}),
            Message(sender=Role.CRITIC, content={"type": "critique", "has_objection": False}, metadata={"confidence": 0.8}),
            Message(sender=Role.SYNTHESIZER, content={"type": "synthesis"}, metadata={"confidence": 0.85}),
        ]
        
        gain = metrics.group_gain(messages)
        assert gain >= 1.0
    
    def test_diversity_index(self):
        metrics = EmergenceMetrics()
        
        messages = [
            Message(sender=Role.RESEARCHER),
            Message(sender=Role.CRITIC),
            Message(sender=Role.INNOVATOR),
        ]
        
        diversity = metrics.diversity_index(messages)
        assert 0 <= diversity <= 1.0
    
    def test_error_correction_rate(self):
        metrics = EmergenceMetrics()
        
        messages = [
            Message(sender=Role.CRITIC, content={"has_objection": True, "objections": [{"type": "error"}]}),
            Message(sender=Role.SYNTHESIZER, content={"resolved_conflicts": [{"issue": "error"}]}),
        ]
        
        rate = metrics.error_correction_rate(messages)
        assert 0 <= rate <= 1.0


class TestSwarm:
    """Swarm编排器测试"""
    
    @pytest.mark.asyncio
    async def test_swarm_creation(self):
        swarm = Swarm()
        assert len(swarm.agents) == 0
        
        # 注册Agent
        swarm.register(Leader())
        swarm.register(Researcher())
        
        assert len(swarm.agents) == 2
    
    @pytest.mark.asyncio
    async def test_swarm_run(self):
        swarm = Swarm()
        swarm.register(Leader())
        swarm.register(Researcher())
        swarm.register(Critic())
        swarm.register(Innovator())
        swarm.register(Synthesizer())
        swarm.register(Executor())
        
        result = await swarm.run("分析量子计算对金融行业的影响")
        
        assert "result" in result
        assert "metrics" in result
        assert len(result["history"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
