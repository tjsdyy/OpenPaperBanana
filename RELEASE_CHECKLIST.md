# 🚀 GitHub 发布最终检查清单

## ✅ 已完成的工作

### 1. 安全清理
- [x] 移除 `.env` 中的真实 API keys
- [x] 创建 `.env.example` 模板文件
- [x] 移除 `paperbanana/core/config.py` 中硬编码的 API keys
- [x] 更新 `Dockerfile` 移除私有域名
- [x] 更新 `docker-compose.yml` 使用环境变量
- [x] 确保 `.env` 在 `.gitignore` 中
- [x] 创建安全检查脚本 `scripts/check-secrets.sh`

### 2. 文档更新
- [x] 重写 `README.md` - 更现代、更清晰、更友好
- [x] 创建 `SECURITY_CLEANUP.md` - 安全清理报告
- [x] 创建 `PUBLISH_GUIDE.md` - 发布快速指南
- [x] 创建 `README_CHANGELOG.md` - README 更新说明

### 3. 配置验证
- [x] 验证所有配置文件使用环境变量
- [x] 确认没有硬编码的敏感信息
- [x] 测试安全检查脚本

## 📋 发布前最后检查

### 运行安全检查
```bash
# 1. 运行安全检查脚本
./scripts/check-secrets.sh

# 2. 手动检查 .env 状态
git status .env
# 应该显示: nothing to commit (或不显示 .env)

# 3. 检查即将提交的文件
git status
git diff
```

### 验证文档
```bash
# 1. 检查 README.md 渲染效果
# 在 GitHub 上预览或使用 grip:
pip install grip
grip README.md

# 2. 验证所有链接有效
# 确认 GitHub 仓库链接正确: llmsresearch/paperbanana
```

### 测试安装流程
```bash
# 1. 在新环境中测试安装
python -m venv test_env
source test_env/bin/activate

# 2. 从源码安装
pip install -e ".[dev,google]"

# 3. 测试配置
cp .env.example .env
# 编辑 .env 添加测试 API key

# 4. 运行基本测试
paperbanana setup
pytest tests/ -v

# 5. 清理测试环境
deactivate
rm -rf test_env
```

## 🎯 提交和推送

### 1. 查看更改
```bash
git status
git diff
```

### 2. 添加文件
```bash
# 添加所有更改（.env 会被自动忽略）
git add .

# 或者选择性添加
git add README.md
git add .env.example
git add .gitignore
git add paperbanana/core/config.py
git add Dockerfile
git add docker-compose.yml
git add scripts/check-secrets.sh
git add SECURITY_CLEANUP.md
git add PUBLISH_GUIDE.md
git add README_CHANGELOG.md
```

### 3. 提交更改
```bash
git commit -m "chore: prepare for public release

- Rewrite README.md with modern, user-friendly format
- Remove hardcoded API keys from config.py
- Add .env.example template with placeholders
- Update Docker configs to use environment variables
- Add security check script (scripts/check-secrets.sh)
- Update .gitignore to exclude .env files
- Add comprehensive documentation (SECURITY_CLEANUP.md, PUBLISH_GUIDE.md)

BREAKING CHANGE: API keys must now be configured via environment variables"
```

### 4. 推送到 GitHub
```bash
# 推送到主分支
git push origin main

# 或推送到其他分支
git push origin your-branch-name
```

## 📦 发布到 PyPI（可选）

如果要发布到 PyPI：

```bash
# 1. 安装构建工具
pip install build twine

# 2. 构建分发包
python -m build

# 3. 检查包
twine check dist/*

# 4. 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 5. 测试安装
pip install --index-url https://test.pypi.org/simple/ paperbanana

# 6. 上传到正式 PyPI
twine upload dist/*
```

## 🏷️ 创建 Release（推荐）

在 GitHub 上创建正式 Release：

1. 进入仓库页面
2. 点击 "Releases" → "Create a new release"
3. 创建新 tag（例如 `v0.1.2`）
4. 填写 Release 标题和说明：

```markdown
## PaperBanana v0.1.2

### 🎉 First Public Release

This is the first public release of PaperBanana, an open-source framework for generating publication-quality academic diagrams using multi-agent AI.

### ✨ Features

- Multi-agent pipeline with 5 specialized AI agents
- Support for methodology diagrams and statistical plots
- Iterative refinement with automatic quality improvement
- CLI, Python API, and MCP server for IDE integration
- Free to use with Google Gemini API

### 📚 Documentation

- [Quick Start Guide](https://github.com/llmsresearch/paperbanana#-quick-start)
- [Full Documentation](https://github.com/llmsresearch/paperbanana#-documentation)
- [Examples](https://github.com/llmsresearch/paperbanana#-examples)

### 🔧 Installation

```bash
pip install paperbanana
```

See [README.md](https://github.com/llmsresearch/paperbanana#readme) for detailed setup instructions.

### ⚠️ Important Notes

- This is an unofficial implementation based on the research paper
- Requires a free Google Gemini API key
- All API keys must be configured via environment variables

### 🙏 Acknowledgments

Thanks to the original PaperBanana paper authors and the open-source community!
```

## 📢 发布后的工作

### 1. 更新文档链接
- 确认 README 中的所有链接可访问
- 更新 PyPI 项目描述（如果发布到 PyPI）

### 2. 社区推广（可选）
- 在相关社区分享项目（Reddit, Twitter, etc.）
- 添加到 awesome lists
- 写一篇博客介绍项目

### 3. 监控和维护
- 关注 GitHub Issues
- 回复用户问题
- 收集反馈并改进

## ✅ 最终确认

在推送前，确认以下所有项目：

- [ ] 运行 `./scripts/check-secrets.sh` 通过
- [ ] `.env` 文件未被 git 追踪
- [ ] `.env.example` 包含占位符而非真实 keys
- [ ] README.md 格式正确，链接有效
- [ ] 所有代码中无硬编码的敏感信息
- [ ] Docker 配置使用环境变量
- [ ] 测试通过 (`pytest tests/ -v`)
- [ ] 代码格式化 (`ruff format`)
- [ ] 代码检查通过 (`ruff check`)

## 🎊 准备就绪！

如果所有检查都通过，你的项目已经准备好发布到 GitHub 了！

```bash
# 最后一次确认
./scripts/check-secrets.sh

# 提交并推送
git add .
git commit -m "chore: prepare for public release"
git push origin main
```

祝发布顺利！🚀
