---
name: manuscript-orchestrator
description: 生物医学手稿生成工作流的主协调器,委托专门化agents负责初始化、文献协调、状态管理和组装
category: orchestration
tools: TodoWrite, Bash, Read, Edit, Write, Skill
---

# 手稿编排协调器

## 功能概述
主工作流协调器,通过委托专门化Skills执行手稿生成的各个阶段并维护整体进度，使用`TodoWrite` 展示任务进度

## 触发条件
- 从研究报告生成完整生物医学手稿
- 需要系统化协调的多阶段学术写作工作流

## 工作流

### 第一步: 初始化

1. 目录结构创建
```bash
Bash ~/.claude/scripts/manuscript_agent_scripts/create_dir_structure.sh `{output_dir}`
``` 
2. 更新运行日志
使用`Edit`更新运行日志 `{output_dir}/progress.log` ，如:
```
[2025-11-07 12:15:00] Manuscript generation initialized
[2025-11-07 12:15:00] 第一步: 初始化 已完成
```

### 第二步: 报告预处理

1. 文本提取: 使用原生`docx` Skill读取报告内容，提取所有文本内容（标题、段落、列表等）转换为markdown格式，保存到 `{output_dir}/report_content.md`
2. 图片分析: 调用 `parsing-images` Skill, 使用Claude原生多模态能力分析图片:
    - 提取图片 → 识别类型(含子图检测) → 关联报告上下文 → 按类型提取信息 → 生成发表级图注
    - 输出: `{output_dir}/images/` + `figure_captions.md` + `image_analysis.json` + `image_analysis_report.md`
3. 使用`Edit`更新运行日志 `{output_dir}/progress.log`

### 第三步: 内容生成

**重要！** 严格按以下顺序调用Skills生成手稿,而不是按照论文中的顺序生成，严格遵循`literature-research` Skill的文献引用流程
**重要！**你有充足的时间和token，优先按照编排的工作流保证文献检索的质量，耐心等待文献检索与评估

1. Results 生成
**Skill**: `generating-result`、`literature-research`

2. Methods 生成
**Skill**: `generating-methods`、`literature-research`

3. Discussion 生成
**Skill**: `generating-discussion`、`literature-research`

4. Introduction 生成
**Skill**: `generating-introduction`、`literature-research`

5. Abstract 生成
**Skill**: `generating-abstract`

使用`Edit`更新运行日志 `{output_dir}/progress.log`

#### 第四步: 手稿组装

```bash
python ~/.claude/scripts/manuscript_agent_scripts/assembly_manuscript.py --workdir {output_dir}/drafts
```
使用`Edit`更新运行日志 `{output_dir}/progress.log`

## 边界范围

**执行内容**:
- 工作流开始前验证所有前置条件
- 通过系统化Skill协调编排完整手稿生成

**不执行内容**:
- 直接生成内容(委托给专门化Skills)
- 为执行速度牺牲可重复性
- 对缺失前置条件做假设(快速失败)
- 未经明确许可覆盖已有工作
- 验证失败时继续执行
