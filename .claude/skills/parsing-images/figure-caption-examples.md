# 发表级图注示例

> 为parsing-images skill生成英文图注提供的参考模板和写作规范

---

## 一、基本结构模板

###标准格式
```
Figure X. [一句话标题].
(A-C) [各子图描述]. [技术细节]. [统计说明].
```

### 核心组成
1. **图编号**: Figure 1, Figure 2, etc.
2. **主标题**: 简洁概括图片核心信息(一句话)
3. **子图描述**: (A), (B), (C) 分别说明
4. **技术细节**: 样本量、方法、条件
5. **统计说明**: 误差类型、统计方法、显著性

---

## 二、单面板图注示例

### 2.1 单纯柱状图

**Figure 1. Treatment A significantly increases gene expression.**
Expression levels of target gene in control and treatment groups measured by qRT-PCR. Data represent mean ± SEM from three independent experiments (n=3 per group). **p < 0.01, ***p < 0.001 (one-way ANOVA with Tukey's post-hoc test).

**要点**:
- 标题说明核心发现
- 说明检测方法(qRT-PCR)
- 明确误差表示(mean ± SEM)
- 明确重复次数(n=3)
- 列出统计方法和显著性标准

---

### 2.2 单纯折线图

**Figure 2. Time-course analysis of cell proliferation.**
Cell viability was measured at indicated time points (0, 24, 48, 72 h) using MTT assay. Control (black) and treatment (red) groups are shown. Data represent mean ± SEM (n=4 per time point). **p < 0.01 compared to control at 72 h (two-way repeated measures ANOVA).

**要点**:
- 说明时间点
- 标注曲线含义(颜色对应)
- 每个时间点的样本量
- 比较时间点的统计方法

---

### 2.3 单纯散点图

**Figure 3. Positive correlation between protein X and protein Y expression.**
Scatter plot showing correlation between protein X and Y levels measured by ELISA in patient samples (n=50). Linear regression analysis: R² = 0.72, p < 0.0001. Gray shading indicates 95% confidence interval.

**要点**:
- 说明检测方法(ELISA)
- 样本类型和数量(patient samples, n=50)
- 相关系数和p值
- 置信区间说明

---

### 2.4 单纯热图

**Figure 4. Hierarchical clustering of differentially expressed genes.**
Heatmap showing expression profiles of 100 genes across 6 samples (3 control, 3 treatment). Color scale represents log2 fold change relative to control group mean. Dendrogram indicates hierarchical clustering by Euclidean distance.

**要点**:
- 基因数量和样本数量
- 颜色映射含义(log2 fold change)
- 聚类方法(Euclidean distance)
- 参照标准(control group mean)

---

## 三、多面板组合图注示例

### 3.1 混合数据图表

**Figure 5. Treatment B modulates multiple cellular responses.**
(A) Bar chart showing relative mRNA expression of target genes (n=3).
(B) Western blot analysis of protein levels. β-actin serves as loading control. Representative image from three independent experiments.
(C) Flow cytometry analysis of cell cycle distribution. Numbers indicate percentage of cells in each phase (n=3).
Data in (A) and (C) represent mean ± SEM. *p < 0.05, **p < 0.01, ***p < 0.001 (one-way ANOVA).

**要点**:
- 每个子图单独说明
- Western blot注明loading control和重复次数
- Flow cytometry说明数值含义(percentage)
- 统一的统计说明(适用于A和C)

---

### 3.2 显微镜图像组

**Figure 6. Treatment enhances protein localization to nucleus.**
(A-C) Immunofluorescence staining of target protein (green) and DAPI (blue) in control (A), treatment 1 (B), and treatment 2 (C) groups. Scale bar = 50 μm.
(D) Quantification of nuclear fluorescence intensity. Data represent mean ± SEM from 30 cells per group across three independent experiments. ***p < 0.001 compared to control (one-way ANOVA with Dunnett's test).

**要点**:
- 染色类型和颜色标注
- 各面板对应条件
- 标尺信息
- 定量分析的样本量(30 cells per group)
- 统计比较方法

---

### 3.3 时间序列组合

**Figure 7. Temporal dynamics of signal activation.**
(A) Representative Western blots showing phosphorylation of target protein at indicated time points (0, 5, 15, 30, 60 min). Total protein serves as loading control.
(B) Quantification of phosph protein / total protein ratio by densitometry. Data represent mean ± SEM from four independent experiments. *p < 0.05, **p < 0.01 compared to t=0 (one-way ANOVA with Dunnett's test).

**要点**:
- 时间点明确列出
- Western blot注明loading control
- 定量方法(densitometry)
- 计算方式(ratio)
- 统计比较的参照点(t=0)

---

### 3.4 完整故事型(多种类型组合)

**Figure 8. Mechanism of compound X-induced apoptosis.**
(A) Chemical structure of compound X.
(B) Dose-response curve of cell viability. IC50 = 5.2 μM. Data represent mean ± SEM (n=4).
(C) Flow cytometry analysis of apoptotic cells (Annexin V+/PI+) after 24 h treatment. Representative dot plots are shown.
(D) Quantification of apoptotic cell percentage. Data represent mean ± SEM from three independent experiments. ***p < 0.001 (unpaired t-test).
(E) Proposed signaling pathway leading to apoptosis. Arrows indicate activation, blunt ends indicate inhibition.

**要点**:
- 化学结构图简单说明
- 剂量反应包含IC50值
- Flow cytometry说明门设置标准
- 定量数据分开说明
- 示意图说明符号含义

---

## 四、特殊类型图注

### 4.1 通路示意图

**Figure 9. Proposed signaling cascade for gene regulation.**
Schematic diagram showing the downstream signaling pathway of receptor X. Ligand binding activates receptor X, leading to phosphorylation of kinase Y, which in turn activates transcription factor Z, resulting in target gene expression. Arrows indicate activation; blunt ends indicate inhibition. Components validated in this study are highlighted in bold.

**要点**:
- 用文字描述信号流程
- 说明符号含义(arrows, blunt ends)
- 标注哪些是本研究验证的

---

### 4.2 实验流程图

**Figure 10. Experimental design and workflow.**
Schematic illustration of the study design. Mice were treated with compound X or vehicle for 4 weeks, followed by behavioral testing and tissue collection. Tissues were processed for histological analysis, qRT-PCR, and Western blotting. n=8 per group.

**要点**:
- 实验设计概述
- 时间线说明
- 实验动物/样本数量
- 后续分析方法列举

---

## 五、写作要点

### 5.1 标题写作原则

**✅ 正确示例**:
- Figure 1. Treatment increases protein expression.
- Figure 2. Correlation between A and B.
- Figure 3. Loss of protein X impairs cell migration.

**❌ 错误示例**:
- Figure 1. Protein expression. (过于简略)
- Figure 2. Amazing results showing strong effects. (主观评价)
- Figure 3. As shown in the figure, protein X is important. (口语化)

**原则**:
- 简洁准确,一句话概括核心发现
- 避免主观形容词
- 使用主动语态
- 不使用"as shown", "figure shows"等冗余表述

---

### 5.2 技术细节必需项

**数据图表必需**:
- ✅ 样本量 (n=X)
- ✅ 重复次数 (three independent experiments)
- ✅ 误差类型 (mean ± SEM or SD)
- ✅ 统计方法 (one-way ANOVA, t-test, etc.)
- ✅ 显著性标准 (*p < 0.05, etc.)

**生物图像必需**:
- ✅ 染色类型和颜色
- ✅ 标尺(scale bar)和单位
- ✅ 放大倍数(如需要)
- ✅ 重复次数/图片数量
- ✅ 定量分析的样本量

**示意图必需**:
- ✅ 符号说明(arrows, colors)
- ✅ 验证状态说明(if applicable)

---

### 5.3 统计信息标准格式

**显著性标注**:
```
*p < 0.05, **p < 0.01, ***p < 0.001 (statistical test name)
```

**比较说明**:
```
- compared to control
- versus vehicle group
- relative to baseline
```

**统计方法完整形式**:
```
- one-way ANOVA followed by Tukey's multiple comparison test
- two-way ANOVA with Bonferroni post-hoc test
- unpaired two-tailed Student's t-test
- Mann-Whitney U test (non-parametric)
```

---

### 5.4 缩写和符号规范

**常用缩写**(首次使用需全称):
- qRT-PCR: quantitative real-time PCR
- ELISA: enzyme-linked immunosorbent assay
- IHC: immunohistochemistry
- IF: immunofluorescence
- WB: Western blot

**样本量表示**:
- n=3 (小写n,生物学重复)
- per group, per condition
- from X independent experiments

**误差表示**:
- mean ± SEM (标准误,优先)
- mean ± SD (标准差)
- 95% CI (置信区间)

---

### 5.5 语言和语法

**动词时态**:
- 描述图片内容: 现在时
  - "Figure 1 shows..." ❌
  - "Bar chart showing..." ✅
- 描述实验操作: 过去时
  - "Cells were treated..."
  - "Expression was measured..."

**语态选择**:
- 优先被动语态: "Cells were treated with..."
- 数据描述可用主动: "Data represent..."

**句式结构**:
- 简洁为主: 避免从句套从句
- 并列信息用分号: "...n=3; p < 0.01."
- 括号补充: "(A-C)"、"(n=3)"、"(one-way ANOVA)"

---

## 六、质量检查清单

### 内容完整性
- [ ] 所有子图都有描述
- [ ] 样本量已说明
- [ ] 误差类型已标注
- [ ] 统计方法已列出
- [ ] 技术细节齐全(标尺、染色等)

### 准确性
- [ ] 数值与图片一致
- [ ] 单位正确
- [ ] 显著性标注准确
- [ ] 专业术语规范

### 可读性
- [ ] 标题简洁明确
- [ ] 句子通顺流畅
- [ ] 逻辑清晰
- [ ] 无语法错误

---

## 七、顶级期刊风格参考

### Nature/Cell风格
- 简洁精练
- 技术细节完整
- 统计信息详尽
- 示例:
  > Figure 1. Loss of protein X impairs cell migration. (A) Western blot analysis. (B) Quantification. Data are mean ± s.e.m. n=3 biologically independent experiments. **P < 0.01 (two-tailed Student's t-test).

### Science风格
- 更加简练
- 统计信息可放在Methods
- 示例:
  > Fig. 1. Protein X expression. (A) mRNA levels. (B) Protein levels. Error bars, SEM; n=3. **P < 0.01.

### 通用原则
- 准确 > 优美
- 完整 > 简短
- 专业 > 口语

---

**使用说明**: parsing-images skill在Phase 5生成图注阶段，参考本文档的对应类型示例和写作要点,为每张主图生成符合发表标准的英文图注。
