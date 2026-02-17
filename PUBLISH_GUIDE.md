# 🚀 GitHub 发布快速指南

## 发布前最后检查

运行以下命令确保安全：

```bash
# 1. 运行安全检查脚本
./scripts/check-secrets.sh

# 2. 确认 .env 未被追踪
git status .env

# 3. 查看即将提交的更改
git diff
```

## 推荐的提交流程

```bash
# 1. 添加所有更改（.env 会被自动忽略）
git add .

# 2. 提交更改
git commit -m "chore: remove sensitive information and prepare for public release

- Add .env.example with placeholder values
- Remove hardcoded API keys from config.py
- Update Docker configs to use environment variables
- Add security check script
- Update .gitignore to exclude .env files"

# 3. 推送到 GitHub
git push origin main
```

## 新用户设置指南

其他用户克隆项目后需要：

```bash
# 1. 克隆项目
git clone https://github.com/llmsresearch/paperbanana.git
cd paperbanana

# 2. 复制环境变量模板
cp .env.example .env

# 3. 编辑 .env 文件，添加 API key
# 获取免费的 Google Gemini API key: https://makersuite.google.com/app/apikey
nano .env

# 4. 安装依赖
pip install -e ".[dev,google]"

# 5. 运行测试
paperbanana setup  # 交互式配置向导
```

## 环境变量说明

最小配置（使用免费的 Google Gemini）：

```bash
GOOGLE_API_KEY=your_google_api_key_here
```

完整配置示例见 `.env.example` 文件。

## 注意事项

- ✅ `.env` 文件已在 `.gitignore` 中，不会被提交
- ✅ 所有 API keys 必须通过环境变量配置
- ✅ Docker 部署时通过 `docker-compose.yml` 的 `env_file` 读取 `.env`
- ⚠️ 永远不要在代码中硬编码 API keys
- ⚠️ 不要将 `.env` 文件提交到版本控制

## 持续集成 (CI/CD)

如果使用 GitHub Actions，在仓库设置中添加 Secrets：

1. 进入 Settings → Secrets and variables → Actions
2. 添加以下 secrets:
   - `GOOGLE_API_KEY`
   - `APICORE_API_KEY` (可选)
   - `KIE_API_KEY` (可选)

在 workflow 中使用：

```yaml
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

---

**准备就绪！** 🎉 项目现在可以安全地发布到 GitHub 了。
