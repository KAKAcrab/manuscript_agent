# 投稿信生成示例

展示generating-cover-letter Skill工作流的完整示例，包含标准模板和多场景案例。

---

## 标准模板

### 5段结构模板

```
Dear Editor-in-Chief [or Dear Dr. [Last Name]],

【Paragraph 1: Submission Statement + Research Question】(2-3 sentences)
We are pleased to submit our manuscript entitled "[Title]" for
consideration as a [Article Type] in [Journal Name]. This study
addresses [core scientific question], which is of significant importance to
[field impact].

【Paragraph 2: Key Findings + Critical Data】(3-4 sentences)
Using [innovative methods/techniques], we demonstrate that [key finding 1 with quantitative data].
Specifically, we found that [key finding 2 with statistical significance]. These findings
represent [breakthrough/significant advance] in understanding [research topic].

【Paragraph 3: Scientific Contributions + Impact】(2-3 sentences)
Our study makes several important contributions: [list of contributions]. These
results have important implications for [theoretical significance] and [practical applications].

【Paragraph 4: Journal Fit】(2 sentences)【Optional, only when journal is specified】
We believe this manuscript is particularly well-suited for [Journal Name]
because [rationale for fit]. The findings will be of great interest to your
readership working on [related topics].

【Paragraph 5: Declarations + Closing】(2-3 sentences)
This manuscript has not been published and is not under consideration
elsewhere. All authors have approved the manuscript. We have no conflicts
of interest to declare. We look forward to your consideration.

Sincerely,

[CORRESPONDING_AUTHOR_NAME], [DEGREE]
[TITLE_POSITION]
[INSTITUTION_NAME]
[INSTITUTION_ADDRESS]
[EMAIL_ADDRESS]
[PHONE_NUMBER]
```

### 段落要求

| 段落 | 字数 | 核心内容 | 必需要素 |
|------|------|----------|----------|
| 段落1 | 40-60词 | 投稿声明 + 研究问题 | 手稿标题、期刊名称、核心科学问题 |
| 段落2 | 80-120词 | 主要发现 + 数据 | 2-3个定量结果、统计显著性、创新方法 |
| 段落3 | 50-80词 | 科学贡献 + 影响 | 2-3个具体贡献、理论和实践意义 |
| 段落4 | 30-50词 | 期刊契合度 (可选) | 匹配理由、读者兴趣点 |
| 段落5 | 40-60词 | 声明 + 结尾 | 未发表声明、作者批准、无利益冲突 |

**总篇幅**: 250-400词 (不含署名信息)

---

## 示例1: 投稿Nature Communications

### 场景
- **手稿**: 新型抗癌化合物发现研究
- **目标期刊**: Nature Communications
- **主要发现**:
  - 化合物X将肿瘤生长降低78% (p < 0.001)
  - 通过YY通路中断的新颖机制
  - 在多个癌细胞系中有效

### 第1阶段: 从手稿中提取核心信息

**从Introduction提取**:
- 研究问题: 鉴定靶向YY通路的新型抗癌化合物
- 研究缺口: 现有疗法缺乏特异性且有严重副作用

**从Methods提取**:
- 创新方法: 高通量筛选 + 结构优化 + 体内验证

**从Results提取**:
- 主要发现1: 化合物X的IC50为2.3 nM(高度活跃)
- 主要发现2: 小鼠模型中肿瘤生长抑制78% (p < 0.001)
- 主要发现3: 对癌细胞选择性强,对正常细胞毒性最小

**从Discussion提取**:
- 科学贡献: 首个选择性YY通路抑制剂
- 临床潜力: 药物开发候选

### 第2阶段: 期刊匹配度分析

**Nature Communications档案** (来自`journal_templates/nature-comms.json`):
- 范围: 自然科学领域的高质量研究
- 影响因子: 16.6
- 重点: 新颖性、广泛兴趣、严谨的方法学

**匹配度评估**:
- ✅ 新颖机制(YY通路中断)
- ✅ 广泛兴趣(癌症治疗学)
- ✅ 多学科(化学 + 生物学)
- ✅ 强有力的数据(体外 + 体内验证)

### 第3阶段: 生成的投稿信

```
Dear Editor-in-Chief,

We are pleased to submit our manuscript entitled "Discovery of a Selective YY Pathway Inhibitor for Cancer Therapy" for consideration as a Research Article in Nature Communications. This study addresses the critical need for targeted therapeutics with improved selectivity and reduced toxicity in cancer treatment, which is of significant importance to oncology drug development.

Using a combination of high-throughput screening and structure-guided optimization, we demonstrate that a novel small-molecule compound X potently inhibits the YY pathway with an IC50 of 2.3 nM. Specifically, we found that compound X reduced tumor growth by 78% (p < 0.001, n=12) in xenograft mouse models while exhibiting minimal toxicity to normal cells. These findings represent a significant breakthrough in developing selective cancer therapeutics targeting the YY pathway.

Our study makes several important contributions: (1) identification of the first selective YY pathway inhibitor, (2) elucidation of a novel mechanism involving disruption of protein-protein interactions, and (3) demonstration of therapeutic efficacy with favorable safety profiles in preclinical models. These results have important implications for understanding YY pathway biology and developing next-generation cancer therapeutics.

We believe this manuscript is particularly well-suited for Nature Communications because it integrates chemical biology, cancer biology, and translational medicine—areas of strong interest to your readership. The findings will be of broad interest to researchers working on targeted cancer therapy, chemical biology, and drug discovery.

This manuscript has not been published and is not under consideration elsewhere. All authors have approved the manuscript. We have no conflicts of interest to declare. We look forward to your consideration.

Sincerely,

[CORRESPONDING_AUTHOR_NAME], [DEGREE]
[TITLE_POSITION]
[INSTITUTION_NAME]
[INSTITUTION_ADDRESS]
[EMAIL_ADDRESS]
[PHONE_NUMBER]
```

### 第4阶段: 语言质量检查

**语气控制**:
- ✅ 有信心: "we demonstrate"(不是"we believe")
- ✅ 具体: IC50值、78%降低、p < 0.001
- ✅ 专业: 学术语气保持
- ✅ 简明: 248词(在250-400范围内)

**内容检查**:
- ✅ 完整的手稿标题
- ✅ 包含3个关键定量结果
- ✅ 创新点清晰阐述(首个选择性抑制剂)
- ✅ 科学贡献具体
- ✅ 期刊匹配度得以体现
- ✅ 包含所有必要的声明

## 示例2: 通用投稿(未指定期刊)

未指定目标期刊时,省略第4段(期刊匹配度):

```
Dear Editor-in-Chief,

We are pleased to submit our manuscript entitled "[Title]" for consideration in your journal. This study addresses [core scientific question], which is of significant importance to [field].

Using [innovative methods], we demonstrate that [key findings with data]. Specifically, we found that [additional findings with statistics]. These findings represent [significant advance] in understanding [research topic].

Our study makes several important contributions: [list 2-3 key contributions]. These results have important implications for [theoretical significance] and [practical applications].

This manuscript has not been published and is not under consideration elsewhere. All authors have approved the manuscript. We have no conflicts of interest to declare. We look forward to your consideration.

Sincerely,

[CORRESPONDING_AUTHOR_NAME], [DEGREE]
[TITLE_POSITION]
[INSTITUTION_NAME]
[INSTITUTION_ADDRESS]
[EMAIL_ADDRESS]
[PHONE_NUMBER]
```

## 常见错误及避免方法

### 错误1: 重复摘要内容
**错误做法**: Copying the abstract verbatim into the cover letter
**正确做法**: Distill key value propositions, highlight the top 1-2 findings

### 错误2: 过度宣传
**错误做法**: "This groundbreaking discovery will revolutionize cancer treatment"
**正确做法**: "These findings represent a significant advance in targeted cancer therapy"

### 错误3: 通用陈述
**错误做法**: "This research is very important and will have major impact"
**正确做法**: "These results have important implications for [specific theoretical domain] and [specific clinical application]"

### 错误4: 掩盖关键发现
**错误做法**: Listing all results equally
**正确做法**: Highlight 1-2 most impactful findings with specific data

### 错误5: 缺失数据
**错误做法**: "Expression was significantly increased"
**正确做法**: "Expression increased 3.2-fold (p < 0.01)"

## 质量检查清单

投稿前,验证:
- ✅ 手稿标题与投稿标题完全相符
- ✅ 包含2-3个具体定量结果
- ✅ 创新点清晰阐述
- ✅ 科学贡献具体(非通用)
- ✅ 字数250-400(仅正文)
- ✅ 所有占位符替换为真实信息
- ✅ 全文保持专业语气
- ✅ 无拼写或语法错误
- ✅ 通讯作者信息完整和准确
