---
name: manuscript
description: 完整的生命医学论文生成工作流,通过manuscript-orchestrator代理编排13个专业技能
category: workflow
complexity: advanced
personas: [manuscript-orchestrator]
---

# /manuscript - 生物医学论文生成工作流

## 概述

将研究报告自动转化为符合期刊规范的可发表论文,包含100%真实文献引用、多维度质量评估和完整投稿准备。

**核心特性**:
- **系统化9阶段工作流**: 初始化 → 6个内容生成阶段 → 最终组装
- **五步文献工作流**: 多源检索 → CrossRef验证 → 相关性评估 → 深度阅读 → 精确引用
- **固定单次质量优化**: 每章节基于Golden Rules评估后执行一次改进迭代
- **完整状态管理**: 检查点恢复、进度跟踪、自动备份

**适用场景**:
- 生物医学领域研究论文撰写
- 需要高质量文献引用的学术写作

## 快速开始

### 标准完整论文生成
```bash
/manuscript @your_research_report.docx --journal nature-comms
```
- **质量阈值**: 0.75 (标准模式)
- **输出**: 完整论文(MD+DOCX) + 投稿信 + 引用数据库

### 快速草稿模式
```bash
/manuscript @your_research_report.docx --draft-mode
```
- **质量阈值**: 0.70 (降低要求)
- **适用**: 快速原型或初稿生成

### 从检查点恢复
```bash
/manuscript @your_research_report.docx --resume
```
- 自动检测最后完成的阶段
- 跳过已完成工作
- 从中断点继续执行

### 自定义输出目录
```bash
/manuscript @research_report.docx --output_dir /path/to/custom/dir --journal nature
```
- 多项目并行或特定目录要求
- Nature期刊格式,自定义工作目录

## 参数配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `@report` | 路径 | **必需** | 研究报告文件路径 (**.docx格式**) |
| `--journal` | 字符串 | `nature-comms` | 目标期刊 (nature/nature-comms/cell/plos) |
| `--parse-images` | 标志 | `true` | 提取和分析图片 (默认开启) |
| `--draft-mode` | 标志 | `false` | 快速模式,质量阈值降至0.70 |
| `--resume` | 标志 | `false` | 从检查点恢复执行 |
| `--output_dir` | 路径 | `.manuscript` | 工作目录位置 |
| `--quality-threshold` | 浮点 | `0.75` | 最低质量分数参考值 |

## 错误处理

### 命令层错误

**文件格式错误**
```
错误: 研究报告必须是.docx格式,当前文件: report.pdf
解决: 请重新上传.docx格式的研究报告
验证: file --mime-type report.docx  # 应显示 application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

**Skills缺失**
```
错误: 未找到必需的skill: generating-result
解决: 检查.claude/skills/目录完整性
验证: ls .claude/skills/*.md | wc -l  # 应为13
```

**期刊模板缺失**
```
错误: 未找到期刊模板: custom-journal
解决: 使用默认模板 nature-comms.json
      或选择可用期刊: nature, nature-comms, cell, plos
验证: ls .claude/resources/journal_templates/*.json
```

### Orchestrator层错误

**Agent委托失败**
```
错误: 无法激活agent: manuscript-quality-controller
解决: 验证.claude/agents/目录中agent文件存在
验证: ls .claude/agents/manuscript-*.md | wc -l  # 应为6
```

**阶段依赖未满足**
```
错误: Discussion生成失败,Results未完成
解决: 检查progress.log确认前置阶段状态
恢复: /manuscript @report.docx --resume
```

### Agent层错误

**质量低于阈值**
```
触发: quality-controller评估后分数<阈值
处理: 自动执行1次优化迭代
      如仍低于阈值,在报告中标注供用户批准
备注: 固定单次优化,避免过度训练
```

**文献搜索失败**
```
触发: managing-literature未找到合适文献
处理: literature-coordinator记录失败引用点
      继续后续工作流
建议: 工作流完成后人工补充文献
```

**检查点保存失败**
```
触发: state-manager写入checkpoints/失败
处理: 尝试备份位置 (`{output_dir}`/backups/)
      如仍失败,警告用户但继续执行
风险: 无法恢复到该阶段,需重新执行
```

**组装失败 - 章节缺失**
```
触发: assembler缺少章节文件
报错: 未找到 03_discussion_final.md
解决方案:
  1. 检查缺失章节: ls `{output_dir}`/drafts/*_final.md
  2. 重新生成缺失章节: 使用对应的generating-* skill
  3. 级联重写后续章节: 调用 regenerating-cascade skill
     例: /regenerating-cascade @report.docx --from-section discussion
  4. 重新运行Phase 7组装
备注: regenerating-cascade会按依赖顺序重写Discussion之后的所有章节
```

### 验证检查清单

**执行前检查**:
- [ ] 研究报告是.docx格式
- [ ] 所有Skills文件存在 (13个)
- [ ] Python工具可执行 (7个)
- [ ] 网络连接正常 (测试CrossRef API)
- [ ] 工作目录可写 (test -w `{output_dir}`/)

**执行中监控**:
- [ ] Phase 0完成,目录结构创建
- [ ] Phase 0.5完成,report_content.md和image_analysis.json生成
- [ ] 每个Phase生成对应的*_final.md
- [ ] references.json持续更新
- [ ] progress.log正常写入

**执行后验证**:
- [ ] manuscript_complete.md和.docx都存在
- [ ] cover_letter.md已生成
- [ ] 所有章节草稿都已生成 (6个)
- [ ] 引用验证率 ≥80%
- [ ] 质量分数符合预期
