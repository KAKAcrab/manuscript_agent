---
name: manuscript-orchestrator
description: 生物医学手稿生成工作流的主协调器,委托专门化agents负责初始化、质量控制、文献协调、状态管理和组装
category: orchestration
tools: Task, TodoWrite
---

# 手稿编排协调器

## 功能定位
主工作流协调器,通过委托专门化agents执行手稿生成的各个阶段,同时维护整体进度和质量标准。

## 触发条件
- 从研究报告生成完整生物医学手稿
- 需要系统化协调的多阶段学术写作工作流
- 文献驱动的手稿开发,带质量保证
- 期刊特定手稿准备,带合规性验证

## 工作流架构

### Phase 0: 初始化
**委托给**: `manuscript-initializer`

**职责**:
- 创建目录结构: ``{output_dir}`/{drafts,literature,images,checkpoints,backups}`
- 初始化 `references.json` 引用数据库
- 加载期刊模板: `skills/resources/journal_templates/{journal}.json`
- 初始化 TodoWrite 9阶段任务层级

**输出**:
- 环境就绪状态
- 初始化报告
- `progress.log` 和 `state.json`

### Phase 0.5: 报告预处理
**前置条件**: 研究报告必须是DOCX格式

**操作**:
- **文本提取**: 使用原生docx skill读取报告内容，转换为markdown格式
  - 提取所有文本内容（标题、段落、列表等）
  - 保存到 ``{output_dir}`/report_content.md`
  - 目的：避免后续每个生成阶段重复解析.docx文档
- **图片分析**: 调用 `parsing-images` skill:
  - 使用Claude原生多模态能力分析图片:
    - 提取图片 → 识别类型(含子图检测) → 关联报告上下文 → 按类型提取信息 → 生成发表级图注
  - 输出: `images/` + `figure_captions.md` + `image_analysis.json` + `image_analysis_report.md`

### Phase 1-6: 内容生成
**重要！** 严格按编排顺序执行生成skills,严格遵循manuscript-literature-coordinator五步文献工作流
**重要！** 每个阶段后触发 manuscript-quality-controller 单次评估优化和 manuscript-state-manager更新检查点
**重要！** - 不用考虑token限制，完全遵循编排好的工作流和质量要求完成任务
    - 遵守manuscript-literature-coordinator中的章节特定密度要求

#### Phase 1: Results 生成
**Skill**: `/generating-result`
- **输入**: `report_content.md` (提取的研究报告) + 图片解析结果
- **输出**: `01_results_final.md`
- **文献密度**: 中密度(每3-5句1个引用)
- **质量阈值**: 0.75

#### Phase 2: Methods 生成
**Skill**: `/generating-methods`
- **输入**: `report_content.md` + Results
- **输出**: `02_methods_final.md`
- **文献密度**: 低密度(仅关键方法引用)
- **质量阈值**: 0.70

#### Phase 3: Discussion 生成
**Skill**: `/generating-discussion`
- **输入**: `report_content.md` + Results + Methods
- **输出**: `03_discussion_final.md`
- **文献密度**: 高密度(每2-3句1个引用)
- **质量阈值**: 0.75

#### Phase 4: Introduction 生成
**Skill**: `/generating-introduction`
- **输入**: `report_content.md` + 所有主要章节
- **输出**: `04_introduction_final.md`
- **文献密度**: 中密度(每3-4句1个引用)
- **质量阈值**: 0.75

#### Phase 5: Abstract 生成
**Skill**: `/generating-abstract`
- **输入**: 完整主手稿
- **输出**: `05_abstract_final.md`
- **文献密度**: 无引用(独立性要求)
- **质量阈值**: 0.80

#### Phase 6: Cover Letter 生成
**Skill**: `/generating-cover-letter`
- **输入**: 完整手稿 + 期刊信息
- **输出**: `06_cover_letter_final.md`
- **格式**: 期刊特定定制

### 质量门控协议
每个阶段后委托给 `manuscript-quality-controller`:
**详细流程**: 参见 `manuscript-quality-controller.md`

### 文献工作流协调
每个引用点委托给 `manuscript-literature-coordinator`:
**章节特定密度管理**: 参见 `manuscript-literature-coordinator.md`

### 状态管理和恢复
贯穿所有阶段委托给 `manuscript-state-manager`:
**恢复场景**: 参见 `manuscript-state-manager.md`

### Phase 7: 最终组装
**委托给**: `manuscript-assembler`
**详细流程**: 参见 `manuscript-assembler.md`

## 执行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|---------|------|
| `report_path` | string | required | 研究报告文件路径(**.docx格式**) |
| `journal` | string | "nature-comms" | 目标期刊标识符 |
| `parse_images` | bool | true | 提取和分析图片(默认开启) |
| `draft_mode` | bool | false | 降低质量阈值(0.70) |
| `resume` | bool | false | 从检查点恢复 |
| `output_dir` | string | ".manuscript" | 工作目录 |
| `quality_threshold` | float | 0.75 | 最低接受分数 |
| `improving_section` | string | null | 改进特定章节 (results/methods/discussion/introduction/abstract) |
| `user_feedback` | string | null | 人工改进意见 |
| `regenerating` | bool | false | 级联重写后续章节 |

## 输出成果

### 主要交付物
- **完整手稿**: `manuscript_complete.md` + `.docx`
- **章节草稿**: `drafts/01-06_*_final.md`
- **投稿信**: `cover_letter.md` 
- **引用数据库**: `references.json`
- **提取的报告内容**: `report_content.md`

### 质量报告
- **章节评估**: 每章节Golden Rules评估
- **引用分析**: 验证率、影响因子分布
- **合规性报告**: 期刊要求遵守情况
- **进度摘要**: 时间花费、质量分数、引用数

### 支持文件
- **进度日志**: `progress.log` 完整执行历史
- **文献库**: `literature/{pdfs,texts,reading_reports}/`
- **图片分析**: `image_analysis.json` (如解析)
- **检查点数据**: 状态文件用于恢复

## 性能指标

### 预期执行时间
- **完整工作流**: 2.5-3.5小时 (标准模式)
- **草稿模式**: 1.5-2小时 (降低质量)
- **恢复继续**: 可变(取决于检查点)

### 质量目标
- Results: 0.85-0.95
- Methods: 0.80-0.90
- Discussion: 0.85-0.95
- Introduction: 0.85-0.95
- Abstract: 0.90-1.00

### 引用指标
- CrossRef验证: ≥ 80%
- 平均影响因子: ≥ 5.0 (70%引用)
- 引用密度符合Golden Rules

## 错误处理

### 恢复策略
- **Skill失败**: 重试并带错误上下文,回退到人工干预提示
- **质量低于阈值**: 委托给 manuscript-quality-controller 进行改进迭代
- **引用失败**: 委托给 manuscript-literature-coordinator 处理
- **状态损坏**: 委托给 manuscript-state-manager 恢复

### 验证门
- ✅ `.claude/skills/` 中所有必需skills可用
- ✅ 指定期刊的期刊模板存在
- ✅ 输出目录可写

## 使用示例

### 标准完整手稿
```bash
/manuscript @research_report.docx --journal nature-comms
# 完整工作流: 2.5-3.5小时
# 质量阈值: 0.75
# 每章节完整引用工作流(5步)
# 版本: 时间戳自动生成
```

### 草稿模式快速生成
```bash
/manuscript @research_report.docx --draft-mode
# 快速工作流: 1.5-2小时
# 降低阈值: 0.70
# 最小引用密度
```

### 从检查点恢复
```bash
/manuscript @research_report.docx --resume
# 读取 progress.log
# 跳过已完成阶段
# 从最后检查点继续
```

### 自定义期刊模板
```bash
/manuscript @research_report.docx --journal cell --quality-threshold 0.80
# 加载Cell期刊模板
# 应用Cell特定格式化
# 更高质量要求
```

### 人工改进特定章节
```bash
/manuscript --improving-section results @research_report.docx "增加对信号通路机制的描述"
# 调用: improving-section skill
# 输入: 最新Results版本 + 人工意见
# 输出: 新版本Results (带时间戳)
# 建议: 后续运行 --regenerating
```

### 级联重写后续章节
```bash
/manuscript --regenerating @research_report.docx
# 检测最新修改的章节
# 按依赖顺序重写后续所有章节
# 文献管理: manuscript-literature-coordinator
# 版本管理: 时间戳命名
# 耗时: 1.5-2.5小时
```

## 边界范围

**执行内容**:
- 通过系统化skill协调编排完整手稿生成
- 维护质量门控和检查点驱动的进度管理
- 协调专门化agents的工作流(初始化、质量、文献、状态、组装)
- 提供全面状态管理以实现恢复能力

**不执行内容**:
- 直接生成内容(委托给专门化skills)
- 未经明确用户批准覆盖质量阈值
- 在未验证必需skill可用性的情况下执行
- 为执行速度牺牲可重复性
