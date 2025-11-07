---
name: parsing-images
description: 从研究报告中提取和分析图片,使用Claude原生多模态能力识别类型、检测子图、提取结构化信息、生成发表级图注
---

# 图片解析和图注生成Skill

## 输出要求(Requirements for Outputs)

### 零上下文丢失
- **每张图片必须关联**到report_content.md中的对应文本
- 提取周围段落的研究目的、方法、结论
- 记录所有段落引用编号

### 零子图遗漏
- **检测所有子图**：多面板图(如Fig1.a/1b/1c)必须全部识别
- 每个子图独立分析类型
- 图注中为每个子图生成独立描述

### 发表级图注
- 遵循`figure-caption-examples.md`标准

### 可追溯提取
- 所有结构化数据必须引用`image-analysis-guidelines.md`的具体章节
- 记录每种图表类型使用的guideline章节
- 精确保留原始统计标注(*, **, ***, p值)

## 快速开始(Quick Start)

```python
# 完整分析一个柱状图的5步流程

# 步骤1: 从DOCX提取图片
# 使用: pandoc或docx skill
extract_images("report.docx", output_dir="{output_dir}/images/")
# → figure_1.png, figure_2.png, ...

# 步骤2: Claude视觉识别类型
fig_type = Read("{output_dir}/images/figure_1.png")
# Claude分析 → "柱状图 (bar_chart)"
# 检查子图 → has_subplots=False

# 步骤3: 关联报告上下文
context = search_references("report_content.md", figure_ref="Figure 1")
# → 研究目的、关键结论、实验方法

# 步骤4: 提取结构化数据(遵循guidelines 1.1节)
data = {
    "axes": {"x": ["对照", "处理A", "处理B"], "y": "表达倍数变化"},
    "data_points": [
        {"value": 1.0, "error": 0.1},
        {"value": 3.2, "error": 0.3, "sig": "**"}
    ],
    "stats": {"n": 3, "method": "One-way ANOVA", "sig_levels": {"**": "p<0.01"}}
}

# 步骤5: 生成图注(遵循examples 2.1节)
caption = """
Figure 1. Treatment A significantly increases target gene expression.
Relative mRNA levels measured by qRT-PCR. Data represent mean ± SEM
(n=3 per group). **p < 0.01 (one-way ANOVA with Tukey's post-hoc test).
"""
# 保存到: {output_dir}/figure_captions.md
```

### 输出文件

| 文件 | 内容 | 用途 |
|-----|------|------|
| `images/*.png` | 提取的图片 | 视觉参考 |
| `figure_captions.md` | 发表级图注 | 直接复制到Results |
| `image_analysis.json` | 结构化数据 | 程序化访问 |
| `image_analysis_report.md` | 摘要报告 | 人类可读概览 |

## 常见任务(Common Tasks)

### 任务1: 分析单面板柱状图

```yaml
# 输入: figure_1.png (柱状图)
# 上下文: "Figure 1展示了处理对基因表达的影响"

步骤1 - 类型识别:
  Read figure_1.png → Claude识别为"柱状图 (bar_chart)"
  子图: 无

步骤2 - 上下文提取:
  搜索"Figure 1"在report_content.md中
  → "24小时处理后qRT-PCR分析基因表达"
  → "处理A: 3.2倍上调(p<0.01)"
  → "n=3生物学重复"

步骤3 - 结构化提取(Guidelines 1.1节):
  axes:
    x: ["对照", "处理A", "处理B"]
    y: "相对表达量(倍数变化)"
  data_points:
    - group: 对照, value: 1.0, error: 0.1 (SEM)
    - group: 处理A, value: 3.2, error: 0.3, sig: **
    - group: 处理B, value: 4.5, error: 0.4, sig: ***
  statistics:
    n: 3
    method: "One-way ANOVA with Tukey's post-hoc test"

步骤4 - 图注生成(Examples 2.1节):
  标题: "Treatment A significantly increases target gene expression"
  完整: "Relative mRNA expression levels measured by qRT-PCR in control
         and treatment groups. Data represent mean ± SEM from three
         independent experiments (n=3 per group). **p < 0.01, ***p < 0.001
         (one-way ANOVA with Tukey's post-hoc test)."
```

### 任务2: 处理多子图组合

```yaml
# 输入: figure_2.png (2×2网格,4个子图)

步骤1 - 子图检测:
  Read figure_2.png → Claude识别4个面板
  左上: 柱状图(2a)
  右上: 热图(2b)
  左下: 显微镜图像(2c)
  右下: 散点图(2d)

步骤2 - 逐个分析:
  2a → Guidelines 1.1节(柱状图提取)
  2b → Guidelines 1.5节(热图提取)
  2c → Guidelines 2.1节(显微镜图像提取)
  2d → Guidelines 1.3节(散点图提取)

步骤3 - 组合图注(Examples 3.1节):
  标题: "Treatment B modulates cellular responses through multiple pathways"
  完整: "(A) Bar chart showing relative mRNA expression of target genes (n=3).
         (B) Heatmap displaying hierarchical clustering of 100 genes across 6 samples.
         (C) Immunofluorescence staining of target protein (green) and DAPI (blue).
         Scale bar = 50 μm.
         (D) Quantification showing positive correlation (R²=0.85, p<0.001).
         Data represent mean ± SEM. ***p < 0.001 (one-way ANOVA)."
```

### 任务3: 通路图图注生成

```yaml
# 输入: figure_5.png (信号通路示意图)

步骤1 - 类型识别:
  Read figure_5.png → "通路图 (pathway_diagram)"

步骤2 - 组件提取(Guidelines 3.2节):
  components:
    - 受体X(膜)
    - 激酶Y(细胞质)
    - 转录因子Z(核)
  interactions:
    - 受体X → 激酶Y(磷酸化)
    - 激酶Y → 转录因子Z(激活)

步骤3 - 图注生成(Examples 4.1节):
  标题: "Proposed signaling cascade for target gene regulation"
  完整: "Schematic diagram showing downstream signaling pathway of receptor X.
         Ligand binding activates receptor X, leading to phosphorylation of
         kinase Y, which activates transcription factor Z, resulting in target
         gene expression. Arrows indicate activation; blunt ends indicate
         inhibition. Components validated in this study are highlighted in bold."
```

## 详细工作流(Detailed Workflow)

### Phase 1: 图片提取
**目的**: 从DOCX提取所有图片为PNG文件

**关键操作**:
- 使用`pandoc --extract-media`或`docx` skill从word/media/提取
- 重命名为`figure_1.png`, `figure_2.png`, ...(顺序编号)
- 从DOCX相邻段落提取原始图注文本
- 记录位置元数据(页码、段落索引)

**输出**: `{output_dir}/images/*.png` + 元数据

### Phase 2: 类型分类和子图检测
**目的**: 识别每张图片的类型并检测多面板图

**关键操作**:
- 对每张图片: `Read(图片路径)` → Claude视觉分析
- 分类为: 数据图表(5种)、生物图像(4种)、示意图(3种)
- 检测子图: 查找面板标签(A/B/C或a/b/c)、网格布局、多标题
- 若检测到子图: 为每个子图独立识别类型

**输出**: JSON含`figure_id`, `type`, `has_subplots`, `subplots[]`(若多面板)

### Phase 3: 上下文关联
**目的**: 将每张图片关联到报告文本内容

**关键操作**:
- 读取`{output_dir}/report_content.md`(Phase 0.5已提取)
- 搜索图片引用: "Figure 1", "Fig. 1", "图1", "图 1", "图一"
- 提取前后2-3段
- 解析出: 研究目的、实验方法、关键结论

**输出**: 每张图片的`context_from_report`(目的、结论、方法)

### Phase 4: 分类型信息提取
**目的**: 按guidelines为每种图表类型提取结构化数据

**关键操作**:
- 查阅`image-analysis-guidelines.md`对应章节
- 柱状图(1.1): 提取轴、数据点、误差线、统计标注
- 热图(1.5): 提取行列标签、颜色映射、聚类信息
- 显微镜(2.1): 提取染色类型、标尺、面板条件
- 通路图(3.2): 提取组件、相互作用、定位信息

**输出**: `structured_data`(字段依类型而定) + 统计信息

### Phase 5: 发表级图注生成
**目的**: 撰写符合Nature/Cell/Science标准的英文图注

**关键操作**:
- 从`figure-caption-examples.md`选择模板
- 单面板: 使用examples 2.1-2.4结构
- 多面板: 使用examples 3.1-3.4结构
- 应用写作原则(第5章): 一句话标题、被动语态、无形容词
- 质量检查(第6章): 所有子图已描述、n已说明、统计完整

**输出**: `{output_dir}/figure_captions.md`

### Phase 6: 数据整合和报告
**目的**: 将所有分析结果整合为JSON和摘要报告

**关键操作**:
- 按`image-analysis-json-structure.md`模板构建JSON
- 包含: 元数据、所有figures[]、subplots[]、contexts[]、structured_data[]、captions[]
- 生成摘要报告: 图片总数、类型分布、每张图片的关键发现
- 添加可追溯性: 链接每个提取到具体guidelines/examples章节

**输出**: `image_analysis.json` + `image_analysis_report.md`

## 质量检查清单(Quality Checklist)

### 分析前验证
- [ ] `report_content.md`存在(Phase 0.5已创建)
- [ ] 图片提取成功(检查{output_dir}/images/)
- [ ] 所有图片可读(有效的PNG/JPG格式)

### 分析过程中
- [ ] **子图检测**: 已验证所有图片(不只是明显的多面板)
- [ ] **上下文关联**: 每张图片都已关联报告文本(100%成功率)
- [ ] **Guidelines引用**: 每种图表类型使用了正确章节

### 图注质量检查(Examples第6章)
- [ ] 所有子图已描述(若多面板)
- [ ] 样本量已说明(n=X)
- [ ] 误差类型已明确(SEM或SD)
- [ ] 统计方法已列出(检验名称)
- [ ] 技术细节完整(标尺、染色、放大倍数)
- [ ] 标题简洁(一句话,无形容词)
- [ ] 方法使用被动语态
- [ ] 无主观语言("惊人"、"优秀"、"显著提升")

### 生成后验证
- [ ] **零上下文丢失**: 所有图片上下文已提取
- [ ] **零子图遗漏**: 子图数量与视觉检查一致
- [ ] **统计准确性**: 原始p值和符号精确保留
- [ ] **文件完整性**: 4个输出文件全部生成
- [ ] **图注可读性**: 图注符合期刊风格指南

### 常见错误预防
- [ ] **子图遗漏**: 总是检查面板,即使看起来像单图
- [ ] **Guidelines误用**: 柱状图不能用热图guidelines
- [ ] **图注不完整**: 缺少n、误差类型或统计方法
- [ ] **上下文错配**: Figure 2图注使用了Figure 1的上下文
- [ ] **数值硬编码**: 使用报告原始数字,不用计算近似值

