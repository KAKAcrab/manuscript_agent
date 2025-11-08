# 图表信息提取要点指南

> 为parsing-images skill提供的分类型信息提取标准

---

## 一、数据图表类

### 1.1 柱状图 (Bar Chart)

**关键视觉元素**:
- 矩形柱体（垂直或水平）
- 误差线（error bars）
- 统计显著性标注（*, **, ***）

**必须提取信息**:
- **轴信息**:
  - X轴标签（分类变量，如Control, Treatment A, Treatment B）
  - Y轴标签（数值变量，如"Expression level", "Cell viability"）
  - Y轴单位（fold change, %, ng/ml, etc.）
  - Y轴数值范围（min-max）
- **数据点**:
  - 每个柱体的中心值
  - 误差线范围（标准差或标准误）
  - 样本量（n=X）
- **统计标注**:
  - 星号或横线标注的比较组
  - p值或显著性符号
  - 统计方法说明（如ANOVA, t-test）

**常见统计标注格式**:
```
*: p < 0.05
**: p < 0.01
***: p < 0.001
****: p < 0.0001
n.s. 或 NS: 不显著
字母标注 (a, b, c): 组间差异
```

**专业术语示例**:
- fold change, relative expression, normalized to control
- mean ± SEM, mean ± SD
- one-way ANOVA, two-way ANOVA, Tukey's post-hoc test

---

### 1.2 折线图 (Line Plot)

**关键视觉元素**:
- 连续曲线或折线
- 数据点标记（圆点、方块等）
- 误差带（shaded area）

**必须提取信息**:
- **轴信息**:
  - X轴标签（时间、浓度、距离等连续变量）
  - Y轴标签和单位
  - 数值范围
- **曲线信息**:
  - 每条曲线的标签（图例）
  - 关键数据点坐标
  - 误差范围
- **趋势描述**:
  - 上升/下降/平稳
  - 峰值和谷值位置
  - 曲线交叉点

**专业术语示例**:
- time course, dose-response, kinetics
- plateau, peak, baseline
- EC50, IC50, half-life

---

### 1.3 散点图 (Scatter Plot)

**关键视觉元素**:
- 离散数据点
- 趋势线或拟合曲线
- 相关系数标注

**必须提取信息**:
- **轴信息**:
  - X轴和Y轴变量名称
  - 单位和数值范围
- **数据点**:
  - 点的分布模式
  - 异常值（outliers）
- **统计信息**:
  - 相关系数（R, R², Pearson's r, Spearman's ρ）
  - p值
  - 拟合方程（如y = ax + b）
  - 置信区间（灰色区域）

**专业术语示例**:
- correlation, linear regression
- positive/negative correlation
- R² = 0.85, p < 0.001

---

### 1.4 箱线图 (Box Plot / Violin Plot)

**关键视觉元素**:
- 中位数线
- 四分位数范围（盒体）
- 须（whiskers）和异常值
- 小提琴图的分布形状

**必须提取信息**:
- **分类标签**: 各组名称
- **统计量**:
  - 中位数（median）
  - 四分位数（Q1, Q3）
  - 最小值和最大值
  - 异常值数量
- **组间比较**: 显著性标注

**专业术语示例**:
- median, interquartile range (IQR)
- outliers, whiskers
- distribution, spread

---

### 1.5 热图 (Heatmap)

**关键视觉元素**:
- 颜色矩阵
- 颜色映射条（color bar）
- 聚类树状图（dendrogram）

**必须提取信息**:
- **行列标签**:
  - 行标签（基因名、样本名等）
  - 列标签（样本、条件等）
  - 标签数量
- **颜色映射**:
  - 最小值颜色和数值
  - 最大值颜色和数值
  - 中间值（0或median）
  - 单位（log2FC, Z-score等）
- **聚类信息**:
  - 主要聚类分组
  - 分组数量
- **重点区域**:
  - 高表达区域（红色/黄色）
  - 低表达区域（蓝色/绿色）

**专业术语示例**:
- hierarchical clustering, k-means clustering
- log2 fold change, Z-score, normalized counts
- upregulated, downregulated

---

## 二、生物图像类

### 2.1 显微镜图像 (Microscopy)

**关键视觉元素**:
- 多通道荧光颜色
- 标尺（scale bar）
- 面板标签（A, B, C或Control, Treatment）

**必须提取信息**:
- **技术细节**:
  - 显微镜类型（fluorescence, confocal, bright-field）
  - 染色类型和颜色（DAPI=blue, GFP=green, RFP=red）
  - 标尺大小和单位（50 μm, 100 nm）
  - 放大倍数（如10×, 40×, 100×）
- **面板信息**:
  - 各面板标签和对应条件
  - 重复实验数（n=X images）
- **观察结果**:
  - 染色强度变化
  - 细胞形态变化
  - 定位信息（nuclear, cytoplasmic, membrane）
  - 共定位（co-localization）

**专业术语示例**:
- immunofluorescence, immunohistochemistry (IHC)
- DAPI (nuclear stain), phalloidin (actin stain)
- co-localization, subcellular localization
- cell morphology, fluorescence intensity

---

### 2.2 Western Blot

**关键视觉元素**:
- 蛋白条带（bands）
- 泳道标签（lanes）
- 分子量标记（ladder）

**必须提取信息**:
- **泳道信息**:
  - 每个泳道的标签（Control, Treatment, +/-, 等）
  - 泳道数量
- **条带信息**:
  - 目标蛋白名称
  - 分子量（kDa）
  - 条带强度（相对定量）
  - Loading control（如β-actin, GAPDH）
- **技术细节**:
  - 一抗信息（antibody, dilution）
  - 重复次数（n=3 independent experiments）

**专业术语示例**:
- protein expression, immunoblotting
- loading control, housekeeping protein
- band intensity, densitometry analysis
- molecular weight marker

---

### 2.3 凝胶电泳 (Gel Electrophoresis)

**关键视觉元素**:
- DNA/RNA条带
- 泳道和ladder
- 条带亮度

**必须提取信息**:
- **泳道标签**: 样本标识
- **条带信息**:
  - 片段大小（bp, kb）
  - 条带强度
- **技术信息**:
  - 凝胶类型（agarose gel, PAGE）
  - 染色方法（EtBr, SYBR Gold）

**专业术语示例**:
- DNA ladder, RNA ladder
- amplicon, PCR product
- base pairs (bp), kilobase (kb)

---

### 2.4 流式细胞术 (Flow Cytometry)

**关键视觉元素**:
- 散点图（dot plot）
- 直方图（histogram）
- 门（gates）和象限

**必须提取信息**:
- **轴信息**:
  - X轴和Y轴标记（如CD3, CD4, FSC, SSC）
  - 荧光通道（FITC, PE, APC等）
- **门设置**:
  - 阳性细胞百分比
  - 门的位置和逻辑
- **细胞群体**:
  - 各象限细胞比例
  - 中位荧光强度（MFI）

**专业术语示例**:
- forward scatter (FSC), side scatter (SSC)
- fluorescence intensity, positive cells
- gating strategy, quadrant analysis
- mean fluorescence intensity (MFI)

---

## 三、示意图类

### 3.1 流程图 (Flowchart)

**关键视觉元素**:
- 矩形框（过程步骤）
- 菱形框（决策节点）
- 箭头（流程方向）

**必须提取信息**:
- **步骤序列**:
  - 各步骤名称或描述
  - 步骤顺序
- **决策点**:
  - 条件判断
  - 分支路径
- **起止点**:
  - 开始节点
  - 结束节点

---

### 3.2 信号通路图 (Pathway Diagram)

**关键视觉元素**:
- 分子/蛋白质节点
- 箭头（激活、抑制）
- 细胞结构（膜、核等）

**必须提取信息**:
- **组件名称**:
  - 受体、激酶、转录因子等
  - 蛋白质或基因名称
- **相互作用类型**:
  - 激活箭头（→）
  - 抑制箭头（⊣）
  - 磷酸化（P标记）
  - 直接/间接作用
- **定位信息**:
  - 膜受体
  - 细胞质信号
  - 核内转录

**专业术语示例**:
- activation, inhibition, phosphorylation
- upstream, downstream
- receptor, kinase, transcription factor
- signaling cascade

---

### 3.3 实验设计图 (Schematic Diagram)

**关键视觉元素**:
- 时间轴
- 处理组和对照组
- 实验步骤图标

**必须提取信息**:
- **实验分组**:
  - 对照组和实验组
  - 处理条件
- **时间线**:
  - 关键时间点
  - 处理时长
  - 检测时间
- **实验步骤**:
  - 操作流程
  - 样本采集点

---

## 四、统计标注识别标准

### 标准格式

| 符号 | 含义 | 常见阈值 |
|------|------|----------|
| * | 显著 | p < 0.05 |
| ** | 非常显著 | p < 0.01 |
| *** | 极显著 | p < 0.001 |
| **** | 极极显著 | p < 0.0001 |
| n.s. / NS | 不显著 | p ≥ 0.05 |
| # | 与另一组比较显著 | p < 0.05 |
| a, b, c | 字母标注法（不同字母表示差异显著） | - |

### 统计方法缩写

- **t-test**: Student's t-test, paired t-test
- **ANOVA**: one-way ANOVA, two-way ANOVA, repeated measures ANOVA
- **Post-hoc**: Tukey's HSD, Bonferroni, Dunnett's test
- **Non-parametric**: Mann-Whitney U test, Kruskal-Wallis test
- **Correlation**: Pearson's correlation, Spearman's correlation
- **Chi-square**: χ² test

---

## 五、专业术语和缩写

### 通用缩写
- **Fig**: Figure
- **vs / vs.**: versus（对比）
- **w/ / w/o**: with / without
- **Ctrl**: Control
- **WT**: Wild-type
- **KO**: Knockout
- **OE**: Overexpression

### 样本量表示
- **n**: 生物学重复数
- **N**: 总样本数
- **technical replicates**: 技术重复
- **biological replicates**: 生物学重复

### 误差表示
- **SEM**: Standard Error of Mean（标准误）
- **SD**: Standard Deviation（标准差）
- **CI**: Confidence Interval（置信区间）
- **95% CI**: 95%置信区间

---

## 六、提取优先级

### 高优先级（必须提取）
1. 图表类型
2. 轴标签和单位
3. 数值数据和误差
4. 统计显著性
5. 样本量

### 中优先级（建议提取）
6. 图例和注释
7. 颜色映射
8. 统计方法
9. 技术细节（放大倍数、标尺等）

### 低优先级（有则提取）
10. 子图面板标签位置
11. 配色方案
12. 字体大小

---

## 七、质量控制要点

**准确性检查**:
- ✅ 数值与图表一致
- ✅ 单位正确识别
- ✅ 统计标注准确

**完整性检查**:
- ✅ 所有子图都已识别
- ✅ 轴标签完整
- ✅ 图例全部提取

**一致性检查**:
- ✅ 同类图表使用相同提取标准
- ✅ 术语使用标准化
- ✅ 数值格式统一

---

**使用说明**: parsing-images skill在Phase 4信息提取阶段，根据Phase 2识别的图表类型，查阅对应章节的提取要点进行详细分析。
