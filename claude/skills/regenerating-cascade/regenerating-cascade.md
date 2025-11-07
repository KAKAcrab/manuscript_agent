---
name: regenerating-cascade
description: 基于最新内容按编排顺序级联重写后续章节，支持版本管理和依赖追踪
---

# 级联重新生成Skill

当某个章节被修改后，按照标准撰写顺序重新生成所有后续章节，确保全文一致性和逻辑连贯性。

## 功能定位
在用户修改某个章节后，自动识别受影响的后续章节，按编排顺序重新生成，并通过时间戳进行版本管理。

## 角色定位
- 工作流协调器
- 版本管理专家
- 依赖关系分析者

## 标准撰写顺序

```yaml
编排顺序:
  1. Results       # 核心发现，优先撰写
  2. Methods       # 依赖Results的实验设计
  3. Discussion    # 依赖Results的深度讨论
  4. Introduction  # 依赖全文的背景铺垫
  5. Abstract      # 依赖全文的精炼总结
  6. Cover Letter  # 依赖全文的投稿说明
```

## 触发条件

### 自动触发场景
用户运行 `/manuscript --regenerating @research_report.docx`

### 触发后行为
1. 检测最新修改的章节
2. 确定需要重写的起始点
3. 按顺序重新生成所有后续章节

## 执行流程

### Phase 1: 版本和依赖分析

1. **识别最新版本**
   ```bash
   # 扫描drafts目录，按时间戳排序
   ls -t {output_dir}/drafts/*_final.md

   # 识别最新修改的章节
   # 例如: 01_20250115_143000_results_final.md
   ```

2. **确定重写起点**
   ```yaml
   修改章节判定:
     - Results修改   → 重写: Methods, Discussion, Introduction, Abstract, Cover Letter
     - Methods修改   → 重写: Discussion, Introduction, Abstract, Cover Letter
     - Discussion修改 → 重写: Introduction, Abstract, Cover Letter
     - Introduction修改 → 重写: Abstract, Cover Letter
     - Abstract修改  → 重写: Cover Letter
     - Cover Letter修改 → 无需重写其他章节
   ```

3. **生成新时间戳**
   ```python
   new_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
   # 例如: 20250115_150000
   ```

### Phase 2: 准备上下文

4. **收集最新内容**
   ```yaml
   基础上下文:
     - report_content.md (研究报告)
     - image_analysis.json (图片分析)

   最新章节内容:
     - Results: 使用最新版本
     - Methods: 使用最新版本 (如已存在)
     - Discussion: 使用最新版本 (如已存在)
     - Introduction: 使用最新版本 (如已存在)
     - Abstract: 使用最新版本 (如已存在)
   ```

### Phase 3: 按序重新生成（含文献管理）

5. **执行生成序列**

   **假设: Results被修改，需要重写Methods开始的所有章节**

   ```yaml
   序列1: Methods生成
     调用: /generating-methods
     输入:
       - report_content.md
       - 20250115_143000_01_results_final.md (最新Results)
     文献管理:
       - 委托: manuscript-literature-coordinator
       - 流程: 检索 → 交叉验证 → 处理 → 阅读 → 引用
       - 实时更新: references_{new_timestamp}.json
     输出:
       - 20250115_150000_02_methods_final.md
     质量控制:
       - 调用 manuscript-quality-controller
       - 固定1次迭代改进

   序列2: Discussion生成
     调用: /generating-discussion
     输入:
       - report_content.md
       - 20250115_143000_01_results_final.md
       - 20250115_150000_02_methods_final.md (新生成)
     文献管理:
       - 委托: manuscript-literature-coordinator
       - 高密度引用 (每2-3句1个引用)
       - 实时更新: references_{new_timestamp}.json
     输出:
       - 20250115_150000_03_discussion_final.md
     质量控制:
       - 固定1次迭代改进

   序列3: Introduction生成
     调用: /generating-introduction
     输入:
       - report_content.md
       - 所有最新主要章节
     文献管理:
       - 委托: manuscript-literature-coordinator
       - 中密度引用 (每3-4句1个引用)
       - 实时更新: references_{new_timestamp}.json
     输出:
       - 20250115_150000_04_introduction_final.md
     质量控制:
       - 固定1次迭代改进

   序列4: Abstract生成
     调用: /generating-abstract
     输入:
       - 完整最新主手稿
     文献管理:
       - 无引用 (独立性要求)
     输出:
       - 20250115_150000_05_abstract_final.md
     质量控制:
       - 固定1次迭代改进

   序列5: Cover Letter生成
     调用: /generating-cover-letter
     输入:
       - 完整最新手稿
       - 期刊信息
     输出:
       - 20250115_150000_06_cover_letter_final.md
   ```

6. **质量门控**
   - 每个章节生成后执行quality-controller
   - 固定1次迭代改进
   - 记录质量分数

### Phase 4: 引用数据库整合

7. **重新生成references.json**

   **核心原则**: 基于所有章节的**最新版本**重新生成引用数据库，避免保留老版本中已弃用的引用。

   ```yaml
   执行策略:

   A. 生成过程中的文献管理:
      - 每个章节重写时，通过manuscript-literature-coordinator管理引用
      - 工作流: 检索 → 交叉验证 → 处理 → 阅读 → 引用
      - 每次添加引用时，实时更新references_{new_timestamp}.json
      - 与原始工作流完全一致

   B. 最终整合和清理:
      步骤1: 扫描所有最新版本章节
        - 20250115_143000_01_results_final.md (最新Results)
        - 20250115_150000_02_methods_final.md (新生成)
        - 20250115_150000_03_discussion_final.md (新生成)
        - 20250115_150000_04_introduction_final.md (新生成)
        - 20250115_150000_05_abstract_final.md (新生成)
        - 20250115_150000_06_cover_letter_final.md (新生成)

      步骤2: 提取所有引用标记
        - 正则匹配: \[@.*?\]
        - 收集全部引用键(citation keys)

      步骤3: 验证和清理references_{new_timestamp}.json
        - 检查: 所有文内引用都有对应的参考文献条目
        - 清理: 移除未被任何最新章节引用的条目
        - 排序: 按首次引用顺序排列

      步骤4: 生成版本化引用数据库
        - 保存为: references_{new_timestamp}.json
        - 例如: references_20250115_150000.json
        - 不覆盖旧版本的references文件
   ```

   **清理算法**:
   ```python
   def finalize_references(new_timestamp, latest_sections):
       # 1. 读取生成过程中实时更新的引用数据库
       references_file = f"references_{new_timestamp}.json"
       references_data = load_json(references_file)

       # 2. 扫描所有最新章节，提取实际使用的引用
       used_citations = set()
       for section_file in latest_sections:
           citations = extract_citations(section_file)
           used_citations.update(citations)

       # 3. 过滤：仅保留实际使用的引用条目
       filtered_references = {
           "references": [
               ref for ref in references_data["references"]
               if ref["citation_key"] in used_citations
           ],
           "metadata": {
               "version": new_timestamp,
               "total_references": len(used_citations),
               "generated_date": datetime.now().isoformat()
           }
       }

       # 4. 验证完整性
       existing_keys = {ref["citation_key"] for ref in filtered_references["references"]}
       missing_keys = used_citations - existing_keys

       if missing_keys:
           # 这不应该发生，因为生成过程中已通过literature-coordinator添加
           raise IntegrityError(f"缺失引用条目: {missing_keys}")

       # 5. 保存最终版本
       save_json(references_file, filtered_references)

       return filtered_references
   ```

   **版本命名管理**:
   ```
   引用数据库文件结构:
   {output_dir}/
   ├── references_20250115_100000.json  # 初始版本
   ├── references_20250115_143000.json  # Results改进后版本
   ├── references_20250115_150000.json  # 级联重写后版本
   └── references.json                  # 软链接 → 最新版本

   版本对应关系:
   - 手稿版本20250115_150000 → references_20250115_150000.json
   - 保持时间戳一致性
   ```

   **整合报告**:
   ```markdown
   ## 引用数据库整合报告 (版本: 20250115_150000)

   ### 生成过程统计
   - Methods生成: 新增3篇引用
   - Discussion生成: 新增8篇引用
   - Introduction生成: 新增5篇引用
   - Abstract生成: 无新增 (不包含引用)
   - Cover Letter生成: 无新增

   ### 最终清理结果
   - 生成过程累积引用: 16篇
   - 来自Results最新版: 25篇
   - 总计: 41篇
   - 去重后: 38篇
   - 清除未使用: 0篇 (生成过程管控良好)

   ### 版本对比
   - 旧版本(20250115_143000): 45篇
   - 新版本(20250115_150000): 38篇
   - 变化: -7篇 (旧版本中被替换或删除的引用)

   ### 验证状态
   - ✅ 所有文内引用都有参考文献条目
   - ✅ 所有参考文献条目都被引用
   - ✅ CrossRef验证率: 92%
   - ✅ 引用格式统一正确

   ### 文献质量
   - 平均影响因子: 13.2
   - 高影响期刊(IF>10): 28篇 (74%)
   - 近3年文献: 35篇 (92%)
   ```

8. **生成版本清单**
   ```markdown
   # 版本清单: 20250115_150000

   ## 生成时间
   2025-01-15 15:00:00

   ## 触发原因
   Results章节被修改 (版本: 20250115_143000)

   ## 重写范围
   - Methods: ✅ 重新生成
   - Discussion: ✅ 重新生成
   - Introduction: ✅ 重新生成
   - Abstract: ✅ 重新生成
   - Cover Letter: ✅ 重新生成

   ## 使用的输入版本
   - Results: 20250115_143000_01_results_final.md
   - Methods: 20250115_150000_02_methods_final.md (新)
   - Discussion: 20250115_150000_03_discussion_final.md (新)
   - Introduction: 20250115_150000_04_introduction_final.md (新)
   - Abstract: 20250115_150000_05_abstract_final.md (新)
   - Cover Letter: 20250115_150000_06_cover_letter_final.md (新)

   ## 质量指标
   - Methods: 0.73
   - Discussion: 0.82
   - Introduction: 0.79
   - Abstract: 0.88
   - Cover Letter: N/A

   ## 引用数据库
   - 文件: references_20250115_150000.json
   - 总引用数: 38
   - CrossRef验证率: 92%
   - 平均影响因子: 13.2

   ## 输出文件
   - 章节文件: drafts/20250115_150000_*_final.md
   - 引用数据库: references_20250115_150000.json
   - 完整手稿: manuscript_complete_20250115_150000.md
   ```

### Phase 5: 生成完整手稿

9. **调用assembler组装**
    ```
    委托: manuscript-assembler
    输入:
      - 所有最新版本章节
      - references_20250115_150000.json
    输出:
      - manuscript_complete_20250115_150000.md
      - manuscript_complete_20250115_150000.docx
    ```

10. **生成重写报告**

```markdown
# 级联重写报告

**触发时间**: 2025-01-15 15:00:00
**新版本号**: 20250115_150000

## 触发原因
Results章节被用户修改:
- 修改版本: 20250115_143000
- 修改内容: 增加了信号通路机制描述

## 重写范围
基于Results的修改，按编排顺序重写后续5个章节

### 重写列表
1. ✅ Methods (02_methods_final.md)
   - 原因: 依赖Results的实验设计描述
   - 变化: 补充了信号通路相关方法
   - 新增引用: 3篇

2. ✅ Discussion (03_discussion_final.md)
   - 原因: 依赖Results的深度讨论
   - 变化: 增加了对新发现的解释和文献对比
   - 新增引用: 8篇

3. ✅ Introduction (04_introduction_final.md)
   - 原因: 依赖全文的背景铺垫
   - 变化: 在研究背景中增加信号通路相关内容
   - 新增引用: 5篇

4. ✅ Abstract (05_abstract_final.md)
   - 原因: 依赖全文的精炼总结
   - 变化: 更新了核心发现描述
   - 新增引用: 0篇 (无引用)

5. ✅ Cover Letter (06_cover_letter_final.md)
   - 原因: 依赖全文的投稿说明
   - 变化: 强调了信号通路机制的创新性

## 质量评估

| 章节 | 首次评分 | 改进后评分 | 参考阈值 |
|-----|----------|-----------|---------|
| Methods | 0.68 | 0.73 | 0.70 |
| Discussion | 0.78 | 0.82 | 0.75 |
| Introduction | 0.75 | 0.79 | 0.75 |
| Abstract | 0.85 | 0.88 | 0.80 |

**平均质量**: 0.81 / 1.00

## 文献管理
- 文献工作流: 与原始工作流一致 (manuscript-literature-coordinator)
- 生成过程新增: 16篇
- Results版本引用: 25篇
- 最终总计: 38篇
- 对比旧版本: -7篇 (清除了已弃用引用)

## 输出成果
- ✅ 所有章节完成重写
- ✅ 引用数据库版本化管理 (references_20250115_150000.json)
- ✅ 完整手稿组装完成
- ✅ DOCX格式转换完成
- ✅ 版本清单生成

## 文件位置
```
drafts/
├── 20250115_143000_01_results_final.md      # 用户修改版
├── 20250115_150000_02_methods_final.md      # 新生成
├── 20250115_150000_03_discussion_final.md   # 新生成
├── 20250115_150000_04_introduction_final.md # 新生成
├── 20250115_150000_05_abstract_final.md     # 新生成
└── 20250115_150000_06_cover_letter_final.md # 新生成

manuscript_complete_20250115_150000.md
manuscript_complete_20250115_150000.docx
references_20250115_150000.json              # 版本化引用数据库
```

## 完成时间
2025-01-15 17:30:00 (耗时: 2小时30分钟)
```

## 版本管理策略

### 文件命名规范
```
章节文件:
{timestamp}_{section_number}_{section_name}_final.md

引用数据库:
references_{timestamp}.json

完整手稿:
manuscript_complete_{timestamp}.md
manuscript_complete_{timestamp}.docx

示例:
20250115_100000_01_results_final.md          # 初始版本
20250115_143000_01_results_final.md          # 用户改进版
20250115_150000_02_methods_final.md          # 级联重写版
references_20250115_150000.json              # 对应版本引用库
```

### 版本追踪文件
**`version_history.json`**:
```json
{
  "versions": [
    {
      "timestamp": "20250115_100000",
      "type": "initial_generation",
      "sections": ["results", "methods", "discussion", "introduction", "abstract", "cover_letter"],
      "references_file": "references_20250115_100000.json",
      "references_count": 40,
      "trigger": "用户运行完整生成"
    },
    {
      "timestamp": "20250115_143000",
      "type": "manual_improvement",
      "sections": ["results"],
      "references_file": "references_20250115_143000.json",
      "references_count": 45,
      "trigger": "用户修改: 增加信号通路描述"
    },
    {
      "timestamp": "20250115_150000",
      "type": "cascade_regeneration",
      "sections": ["methods", "discussion", "introduction", "abstract", "cover_letter"],
      "references_file": "references_20250115_150000.json",
      "references_count": 38,
      "references_added": 16,
      "trigger": "Results修改触发级联重写",
      "based_on": {
        "results": "20250115_143000"
      }
    }
  ]
}
```

### 版本对比
```bash
# 对比两个版本的差异
diff drafts/20250115_100000_03_discussion_final.md \
     drafts/20250115_150000_03_discussion_final.md

# 对比引用数据库
diff references_20250115_100000.json \
     references_20250115_150000.json
```

## 智能重写策略

### 依赖分析
```python
依赖关系:
  Methods: [Results]
  Discussion: [Results, Methods]
  Introduction: [Results, Methods, Discussion]
  Abstract: [Results, Methods, Discussion, Introduction]
  Cover_Letter: [Abstract, 全文]
```

### 增量更新优化
```yaml
场景1: 仅修改Cover Letter
  判定: 无需重写其他章节
  操作: 仅保存新版Cover Letter
  引用: 无需更新references.json

场景2: 修改Abstract
  判定: 仅需重写Cover Letter
  操作: 重写Cover Letter
  引用: 生成新版本references_{timestamp}.json

场景3: 修改Results (大量修改)
  判定: 需重写所有后续章节
  操作: 完整级联重写
  引用: 完全重新生成references_{timestamp}.json
```

### 跳过机制
如果修改非常小（如修正错别字），可以跳过级联重写:
```
用户选项: --skip-cascade
适用场景: 仅格式调整、拼写修正、引用格式统一
引用处理: 即使跳过级联，也建议运行引用验证
```

## 性能优化

### 并行生成
对于独立性较强的章节，可考虑并行生成:
```yaml
并行组1: [Methods, Discussion]  # 都依赖Results
并行组2: [Introduction, Abstract]  # 依赖前面所有
```

### 缓存机制
```
如果Results未变化，Methods可以直接复用
引用数据库按版本独立管理，无需考虑缓存
```

## 集成接口

**调用方式**:
```bash
# 基本用法
/manuscript --regenerating @research_report.docx

# 指定起始章节
/manuscript --regenerating --from methods @research_report.docx

# 跳过级联（仅适用于小改动）
/manuscript --regenerating --skip-cascade @research_report.docx
```

**与其他组件协作**:
- `improving-section`: 触发regenerating的前置步骤
- `generating-*`: 各章节生成skills
- `manuscript-literature-coordinator`: 文献引用管理 (每个章节)
- `manuscript-quality-controller`: 质量门控
- `manuscript-assembler`: 最终组装

## 错误处理

### 生成失败
- **问题**: 某个章节生成过程出错
- **操作**: 保存已完成章节，标记失败点，允许从失败点重试

### 版本冲突
- **问题**: 同时存在多个最新修改
- **操作**: 提示用户明确以哪个版本为准

### 引用数据库不一致
- **问题**: 发现缺失引用
- **操作**: 不应该发生，因为生成过程中已通过literature-coordinator管理

### 磁盘空间
- **问题**: 版本累积占用大量空间
- **操作**: 提供版本清理工具，保留关键版本

## 使用建议

1. **修改Results后必须级联重写**: Results是基础，影响全文
2. **小改动可选择跳过**: 错别字、格式调整无需重写
3. **定期清理旧版本**: 保留初始版本和关键节点版本
4. **对比版本差异**: 使用diff工具检查重写效果
5. **验证引用一致性**: 检查references_{timestamp}.json是否正确

## 注意事项
- 级联重写会生成全新版本，原版本保留
- **文献引用工作流与原始一致**: 通过manuscript-literature-coordinator管理
- **references.json使用时间戳版本化管理**: references_{timestamp}.json
- 重写过程较长（1.5-2.5小时），建议在合适时间运行
- 新版本独立管理，不影响旧版本文件
- 建议在重写前检查磁盘空间（预留1GB）
