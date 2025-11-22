---
name: literature-research
description: 在生物医学领域检索、评估、深度阅读学术文献，选择最合适的文献在手稿中精确插入DOI引用。从PubMed/OpenAlex等数据库查找文献，下载全文，评估相关性，提取关键信息生成阅读报告并在手稿对应位置插入DOI引用最合适的文献。当用户需要查找文献、文献综述、检索论文、阅读文献或提到PubMed、DOI时使用。
---

# 文献研究Skill

## 功能概述
文献检索与精准引用，为生物医学论文写作提供高质量文献支持。

## 核心功能
1. **智能检索**: 从PubMed、OpenAlex等数据库检索文献
2. **质量评估**: 基于期刊影响力和相关性筛选
3. **全文处理**: 下载PDF/XML并转换为Markdown
4. **深度阅读**: 语义搜索提取关键信息，生成结构化阅读报告
5. **精准引用**: 在手稿对应位置插入文献DOI

## 输入参数
- `目的`: support(支持性文献) / contrast(对比性文献) / method(方法学文献)
- `查询关键词`: 该论述点的具体关键词
- `论述上下文`: 需要引用的具体论述内容

## 工作流程
**重要！**你有充足的时间和token，优先按照编排的工作流保证文献检索的质量，耐心等待文献检索与评估
### 步骤1: 获取文献

#### 1.1 执行检索
```bash
bash scripts/managing-literature.sh \
    --part Results \
    --query "immunology checkpoint inhibitor" \
    --min-year 2020 \
    --max-year 2025 \
    --article-kind any \
    --max-results 5 \
    --max-oa 2 \
    --root {output_dir}
```

- 参数说明
    --part 撰写部分名（Results|Methods|Discussion|Introduction）
    --query 检索关键词（必填）
    --min-year/--max-year 年限
    --article-kind research|review|any
    --max-results 每源最大条数
    --max-oa OA 补充条数
    --root 根输出目录
    -h | --help 显示帮助

**输出目录结构**
```
 {output_dir}/literature/
 ├── 1.search/              # 原始检索结果
 ├── 2.merge/               # 去重复后的文献元数据
 ├── 3.validate/            # Crossref验证
 ├── 4.quality_score/       # 期刊评分
 ├── 5.texts/               # 全文Markdown
 │   ├── {PART}_{QUERY}-${HHMMSS}.json # 下载文献的元数据
 │   └── {doi_safe}.md      # Markdown格式的原始文献
 └── 6.selected/            # 最终候选文献
    └── selected_{PART}_{QUERY}-${HHMMSS}.json
```

### 1.2: 相关性评估

从`5.texts/{PART}_{QUERY}-${HHMMSS}.json`获取每篇文献的：
- `title`: 标题
- `doi`: 唯一标识符
- `abstract`: 摘要
- `md_file`: 全文路径（如`10_1038_s41573-018-0007-y.md`）
若`abstract`为空，则从全文Markdown获取`abstract`部分

快速浏览标题和摘要了解文献概况，使用`Edit`撰写每篇文献的"relevance_evaluation"四维评分，如:
```json
{
  "relevance_evaluation": {
    "theme_relevance": {
      "score": 0.9,
      "evaluation": "研究主题与当前论述高度匹配"
    },
    "methods_relevance": {
      "score": 0.8,
      "evaluation": "实验方法具有可比性"
    },
    "results_relevance": {
      "score": 0.85,
      "evaluation": "结果数据可直接引用对比"
    },
    "argumentative_value": {
      "score": 0.75,
      "evaluation": "提供关键证据支持论点"
    }
  }
}
```

#### 1.3 筛选文献
筛选进一步深入阅读的文献
```bash
python select_top_papers.py \
  --input {output_dir}/literature/5.texts/{PART}_{QUERY}-${HHMMSS}.json \
  --output-dir {output_dir}/literature/6.selected \
  --part Results
```

- 参数说明
    --input 文献元数据及评估信息`{PART}_{QUERY}-${HHMMSS}.json`
    --output-dir 输出路径
    --part 撰写部分名（Results|Methods|Discussion|Introduction）

### 步骤2：深度阅读与信息提取

#### 2.1 定位全文
从`6.selected/selected_{PART}_{QUERY}-${HHMMSS}.json`获取：
- `doi`: 唯一标识符(如`10.1038/s41573-018-0007-y`)
- `md_file`: 全文路径（如`10_1038_s41573-018-0007-y.md`）

#### 2.2 目标导向阅读
根据搜索目的定位关键章节:
- **背景信息** → Introduction
- **方法细节** → Methods
- **结果对比** → Results + Discussion

随后基于原生语义理解识别所需信息

#### 2.3 提取关键信息
使用`Edit`灵活填写`6.selected/selected_{PART}_{QUERY}-${HHMMSS}.json`中`Reading_Report`的字段，也可根据需要调整`Reading_Report`中的字段名

### 步骤3：精准引用文献

#### 3.1 插入DOI
分析阅读报告后选择最适文献进行引用，在手稿`{output_dir}/draft/{PART}_{DATE}.md`中插入DOI，如:

**原文：**
```markdown
This phenomenon has been widely observed in multiple studies.
```
**插入后：**
```markdown
Komatsu et al. demonstrated that this phenomenon has been widely observed across multiple cohorts (10.1038/s41467-020-15924-x).
```
**或：**
```markdown
This phenomenon has been widely observed in multiple studies (10.1038/s41467-020-15924-x, 10.1038/s41572-020-0158-0).

#### 3.2 引用验证

确保引用的三个维度正确：
1. **准确性**：引用内容与原文一致，数值准确
2. **相关性**：引用确实支持当前论述
3. **规范性**：符合引用格式

## 最佳实践

- ✅ 使用具体的疾病+干预组合关键词
- ✅ 设置合理的时间窗口（近5-7年）
- ❌ 避免过于宽泛的检索词（如单独搜"cancer"）
- 优先引用原始研究而非综述（除非需要概述性观点）
- 注意发表偏倚（negative results往往不发表）
