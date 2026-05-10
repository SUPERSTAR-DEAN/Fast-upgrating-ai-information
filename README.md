# Fast-upgrading-ai-information

每周自动汇总中英双语 AI 资讯，并通过 SMTP 发送「AI Weekly Digest」邮件。

## 功能

- 每周定时运行（GitHub Actions，默认 `UTC 周一 08:00`，即 `cron: 0 8 * * 1`）
- 支持手动触发 `workflow_dispatch`
- 覆盖来源（可配置）：
  - OpenAI
  - Google DeepMind
  - Meta AI
  - arXiv（cs.AI / cs.LG / cs.CL）
  - Hugging Face
  - GitHub Trending（AI/ML 关键词过滤，失败自动降级记录）
  - Reddit（RSS，受限时自动降级记录）
  - 国内媒体（机器之心、量子位；量子位使用页面抓取并带降级）
- 去重与日期窗口过滤（默认最近 7 天）
- 默认规则摘要（零密钥可运行）+ 可选 LLM 摘要扩展（环境变量开关）
- 生成「本周主流深度学习与神经网络学习方向」板块
- 输出 HTML + 纯文本 multipart 邮件（Gmail 兼容）
- 抓取失败来源不会中断总流程，会在周报中列出

## 目录结构

```text
src/
  main.py
  collector.py
  processors.py
  summarizer.py
  learning_plan.py
  render.py
  email_sender.py
  config.py
config/
  sources.yaml
templates/
  email.html.j2
  email.txt.j2
.github/workflows/
  weekly_digest.yml
data/                  # 运行后生成缓存 JSON
requirements.txt
```

## GitHub Secrets 配置

在仓库 `Settings -> Secrets and variables -> Actions` 中添加：

- `SMTP_HOST`（例如 `smtp.gmail.com`）
- `SMTP_PORT`（例如 `587`）
- `SMTP_USERNAME`（发件邮箱）
- `SMTP_PASSWORD`（邮箱密码或 App Password）
- `EMAIL_TO`（默认可设为 `xxx@gmail.com`）
- `EMAIL_FROM`（通常与 `SMTP_USERNAME` 相同）

可选（启用 LLM 摘要）：

- `USE_LLM_SUMMARY`：`true`/`false`
- `LLM_API_URL`
- `LLM_API_KEY`

> Gmail 建议使用 **App Password**（开启 2FA 后创建），不要使用账户登录密码。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your_email@gmail.com
export SMTP_PASSWORD=your_app_password
export EMAIL_TO=xxx@gmail.com
export EMAIL_FROM=your_email@gmail.com

python -m src.main
```

运行后会在 `data/` 下生成缓存文件，例如：

- `data/latest.json`
- `data/weekly_digest_YYYYMMDD.json`

## 调整定时与时区

GitHub Actions 的 `cron` 使用 **UTC**。

- 当前配置：`0 8 * * 1`（每周一 08:00 UTC）
- 若希望北京时间周一 08:00（UTC+8），可改为：`0 0 * * 1`

修改文件：`.github/workflows/weekly_digest.yml`

## 调整来源

编辑 `config/sources.yaml`：

- 新增/删除来源
- 修改来源类型：`rss` / `html_list` / `github_trending`
- 对 `html_list` 来源可配置 CSS selector（`selectors.item`）

若某来源不可访问或反爬，系统会自动跳过并在邮件「抓取失败来源」中列出，不影响其他来源发送。
