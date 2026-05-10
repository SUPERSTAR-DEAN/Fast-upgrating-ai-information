from __future__ import annotations

from src.models import LearningDirection, NewsItem


def _pick_recommended_reads(items: list[NewsItem], limit: int = 8) -> list[str]:
    picks: list[str] = []
    keywords = ["paper", "arxiv", "llm", "transformer", "diffusion", "agent", "rag", "benchmark", "pytorch"]
    for item in items:
        text = f"{item.title} {item.summary}".lower()
        if any(k in text for k in keywords):
            picks.append(f"{item.title} ({item.source_name}) - {item.url}")
        if len(picks) >= limit:
            break

    if len(picks) < limit:
        for item in items:
            candidate = f"{item.title} ({item.source_name}) - {item.url}"
            if candidate not in picks:
                picks.append(candidate)
            if len(picks) >= limit:
                break
    return picks


def build_learning_directions(items: list[NewsItem]) -> list[LearningDirection]:
    recommended_reads = _pick_recommended_reads(items)

    return [
        LearningDirection(
            title="基础巩固",
            bullets=[
                "复习反向传播、常见损失函数（CE/MSE）、优化器（SGD/AdamW）和学习率调度。",
                "系统梳理正则化、归一化与过拟合诊断方法，形成最小实验模板。",
                "结合本周新闻中的模型案例，做一次从数据清洗到验证集分析的端到端复盘。",
            ],
        ),
        LearningDirection(
            title="进阶主题（Transformer/LLM、Diffusion、多模态、RAG/Agent、对齐与评测）",
            bullets=[
                "Transformer/LLM：关注长上下文、推理能力（reasoning）与工具调用趋势。",
                "Diffusion & 多模态：跟踪文生图/视频模型的效率优化与评测基准。",
                "RAG/Agent：实践检索质量评估、工具路由和函数调用可靠性测试。",
                "对齐与评测：建立任务级指标（准确率、幻觉率、延迟、成本）并每周复盘。",
            ],
        ),
        LearningDirection(
            title="工程实践（PyTorch、训练/推理加速、部署、MLOps）",
            bullets=[
                "PyTorch：熟悉 AMP、梯度累积、检查点保存/恢复与 reproducibility 设置。",
                "训练/推理加速：尝试 Flash Attention、量化（INT8/4bit）、KV Cache 优化。",
                "部署与 MLOps：将模型服务化（API + 监控 + 回滚），记录 Prometheus 指标。",
                "把本周最有价值的 1 个项目做最小复现并输出实验日志。",
            ],
        ),
        LearningDirection(
            title="本周推荐论文/项目阅读清单",
            bullets=recommended_reads[:8] if recommended_reads else ["本周未抓取到足够条目，建议补充 arXiv 和 GitHub Trending 来源。"],
        ),
    ]
