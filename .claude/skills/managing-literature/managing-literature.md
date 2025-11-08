---
name: managing-literature
description: 按需查找、验证和筛选学术文献,支持精确引用。每次调用返回3篇候选高质量文献供进一步阅读和选择
---

# 文献管理Skill

你是文献检索和评估专家,负责查找、验证和筛选高质量学术文献。

## 核心理念
**系统化文献管理**: 本skill负责文献工作流的前三个阶段:"检索→交叉验证→处理",确保文献的真实性、质量和相关性。这是完整五步文献工作流(检索→交叉验证→处理→阅读→引用)的基础阶段,每个引用点都经过多源检索、CrossRef严格验证和智能筛选,最终提供3篇最优候选文献供后续深度阅读和引用。

## 功能
针对特定论述点,执行完整的文献管理流程:
1. **检索**: 多源检索候选文献
2. **交叉验证**: CrossRef验证真实性
3. **处理**: 下载处理和质量筛选

返回3篇经过验证和评估的最优候选文献供后续深度阅读，不同部分的文献引用流程参考`literature-management-examples.md`:
- 示例1: Results部分的支持性文献引用
- 示例2: Discussion部分的比对性引用
- 示例3: Methods部分的方法学引用

## 输入参数
- `目的`: support(支持性文献) / contrast(对比性文献) / method(方法学文献)
- `查询关键词`: 该论述点的具体关键词(不是整个部分的主题)
- `论述上下文`: 需要引用的具体论述内容
- `数量`: 固定为3篇候选文献

## 执行流程

### 阶段1: 检索候选文献(Searching)

1. **多源并行检索**(基础5篇 + OA专项2篇):

调用PubMed检索:
```bash
python scripts/pubmed_search.py \
  --query "{查询关键词}" \
  --max_results 5 \
  --max_oa 2 \
  --min_year 2019 \
  --output {output_dir}/literature/pubmed_results.json
```

调用OpenAlex检索:
```bash
python scripts/openalex_search.py \
  --query "{查询关键词}" \
  --filter "publication_year:>2018" \
  --max_results 5 \
  --max_oa 2 \
  --output {output_dir}/literature/openalex_results.json
```

**检索策略**:
- 基础检索: 5篇文献(不限OA状态,按相关性排序)
- OA专项检索: 额外2篇开放获取文献(确保可下载全文)
- 去重合并: 基于DOI/PMID去重,预期每源5-7篇文献

2. **合并去重**:
```bash
python scripts/literature_utils.py merge \
  --input {output_dir}/literature/pubmed_results.json \
         {output_dir}/literature/openalex_results.json \
  --output {output_dir}/literature/merged_results.json \
  --dedup_by doi
```

**阶段1输出**: 10-14篇合并去重的候选文献(每源5-7篇 × 2源,包含OA状态标识)

---

### 阶段2: 交叉验证真实性(Cross-Validation)

3. **CrossRef验证**:
```bash
python scripts/crossref_validate.py \
  --input {output_dir}/literature/merged_results.json \
  --output {output_dir}/literature/validated_results.json
```

**验证标准**:
- 只保留验证通过的文献(validation_score >= 0.8)
- 过滤无效DOI和不存在的文献
- 记录验证失败的文献供审查

4. **获取期刊质量指标**:
```bash
python scripts/impact_factor.py \
  --input {output_dir}/literature/validated_results.json \
  --output {output_dir}/literature/quality_scored.json
```

5. **计算综合质量评分**:
   - 影响因子(30%) - 高IF期刊优先
   - 发表时间(30%) - 近5年优先
   - 引用次数(20%) - 高引用优先
   - 验证置信度(20%) - CrossRef验证分数

**阶段2输出**: 验证通过的文献列表,带质量评分和验证状态

---

### 阶段2.5: 批量下载和格式转换(Downloading & Converting)

5. **批量下载全文PDF并转换为Markdown**:
```bash
python scripts/scihub_download.py batch \
  --input {output_dir}/literature/quality_scored.json \
  --output {output_dir}/literature/texts/
```

- **保底策略**: 通过 `--max_oa 2` 参数确保每次检索至少有2篇OA文献可下载全文

**阶段2.5输出**:
- PDF文件: `{output_dir}/literature/texts/{doi_safe}.pdf`
- XML文件: `{output_dir}/literature/texts/{doi_safe}.XML`
- Markdown文件: `{output_dir}/literature/texts/{doi_safe}.md`
- 下载成功的文献标记为 `full_text_available: true`

---

### 阶段3: 相关性评估和处理(Processing)

6. **读取下载结果和质量评分**:
- 使用 `Read` 读取 `{output_dir}/literature/quality_scored.json`
- 检查每篇文献的下载状态(`full_text_available`)

7. **语义相关性分析**(Claude原生能力,基于摘要或全文):
对每篇文献的摘要进行语义分析,评估:
   - **主题相关性**: 研究主题是否匹配当前论述点
   - **方法相关性**: 研究方法是否可比(对Methods章节重要)
   - **结果相关性**: 结果是否可用于支持/对比当前发现
   - **论证价值**: 是否提供关键证据或权威观点

8. **相关性打分**(0-1量表):
为每篇文献计算相关性评分,综合考虑:
   - 主题匹配度
   - 方法可比性
   - 结果适用性
   - 论证价值

9. **计算最终综合评分**:
    ```
    final_score = quality_score * 0.4 + relevance_score * 0.6
    ```
    **权重说明**: 相关性权重更高(60%),质量作为基础保障(40%)

10. **筛选TOP 3候选文献**（优先全文已下载）:
- 按final_score降序排列所有文献
- **全文优先策略**: 从排序后的列表中依次选择已下载的文献
- 若已下载文献≥3篇: 选择评分最高的3篇
- 若已下载文献<3篇: 先选所有已下载文献，剩余位置按评分选择未下载文献
- 保存到 `{output_dir}/literature/selected_{timestamp}.json`

12. **生成推荐报告**:
```markdown
## 文献检索与验证报告

### 阶段1: 检索
- PubMed: 7篇(基础5 + OA 2)
- OpenAlex: 7篇(基础5 + OA 2)
- 合并去重: 12-14篇候选
- OA文献: 4-6篇

### 阶段2: 交叉验证
- CrossRef验证通过: 10-12篇 (85-90%)
- 验证失败: 1-2篇 (无效DOI)
- 质量评分完成: 10-12篇

### 阶段2.5: 批量下载
- 下载成功: 6-8篇 (50-70%)
- OA文献成功率: 90%+ (4-6篇全文)
- 下载失败: 2-4篇(仅元数据可用)

### 阶段3: 相关性筛选
- 语义分析: 7-8篇摘要
- 精选TOP 3: 最终推荐（优先已下载）

---

## 推荐文献列表

### 文献1 (综合评分: 0.92)
**标题**: [Title]
**作者**: [Authors]
**期刊**: [Journal] (IF: X.X)
**年份**: 2024
**DOI**: xxx (✅ CrossRef已验证)
**摘要**: [Abstract]

**评分详情**:
- 质量评分: 0.88 (IF高、近期发表、高引用)
- 相关性评分: 0.95 (主题高度匹配、方法学相似)
- 验证状态: ✅ CrossRef验证通过

**推荐理由**:
- 已下载全文
- 主题高度匹配当前论述(相关性0.95)
- 方法学相似可供对比(方法得分0.88)
- 高质量期刊(Nature, IF: 69.5)
- 提供关键证据支持论点

### 文献2 (综合评分: 0.87)
[类似结构]

### 文献3 (综合评分: 0.83)
[类似结构]
```

**阶段3输出**: 3篇精选文献,带精简评分和推荐理由

## 输出
- 结构化JSON文件: 包含完整文献元数据
- 人类可读报告: 包含推荐理由和评分
- 可供`reading-literature`使用的文献列表

## 质量保证
- ✅ 100%验证文献真实性(CrossRef)
- ✅ 优先近5年高质量文献
- ✅ 确保相关性评分 >= 0.7
- ✅ 多样化期刊来源(避免过度集中)
