# Contributing to Collectigent

感谢你对 Collectigent 的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告问题

如果你发现了 bug 或有功能建议，请：

1. 在 [GitHub Issues](https://github.com/collectigent/collectigent/issues) 搜索是否已有类似问题
2. 如果没有，创建新的 Issue，详细描述：
   - 问题描述
   - 复现步骤（如果是 bug）
   - 期望行为
   - 实际行为

### 提交代码

1. Fork 仓库
2. 创建分支：`git checkout -b feature/your-feature`
3. 编写代码并添加测试
4. 运行测试：`pytest tests/ -v`
5. 提交：`git commit -m "描述你的修改"`
6. 推送：`git push origin feature/your-feature`
7. 创建 Pull Request

### 代码规范

- 使用 Python 3.9+ 特性
- 遵循 PEP 8 风格
- 添加类型注解
- 为新功能编写测试

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/collectigent/collectigent.git
cd collectigent

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/
```

## 许可证

贡献的代码将采用 Apache 2.0 许可证。