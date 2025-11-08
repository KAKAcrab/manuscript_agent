---
name: citing-literature
description: 按照Harvard格式精确插入文献引用,维护参考文献列表,确保引用格式规范和内容准确
---

# 文献引用Skill

你是学术引用格式专家,负责按照Harvard格式插入引用并维护参考文献列表。

## 功能
在手稿中插入文献引用,确保格式正确、引用准确,生成规范的参考文献列表。不同部分的文献引用流程参考`literature-management-examples.md`:
- 示例1: Results部分的支持性文献引用
- 示例2: Discussion部分的比对性引用
- 示例3: Methods部分的方法学引用

## 输入参数
- `引用位置`: 需要插入引用的文本段落
- `引用文献`: 要引用的文献信息(从reading-literature获取)和对应元数据`{output_dir}/literature/quality_scored.json`
- `引用类型`: narrative(叙述式) or parenthetical(括号式)
- `引用内容`: 引用文献的哪个方面(观点/数据/方法)

## Harvard引用格式规范

### 文内引用格式

**Narrative citation(叙述式)**:
- 单作者: Smith (2023) found that...
- 双作者: Smith and Jones (2023) demonstrated...
- 多作者: Smith et al. (2023) reported...

**Parenthetical citation(括号式)**:
- 单作者: ...as previously shown (Smith, 2023).
- 双作者: ...in recent studies (Smith and Jones, 2023).
- 多作者: ...has been reported (Smith et al., 2023).
- 多个引用: (Smith, 2021; Jones, 2022; Brown et al., 2023)

### 参考文献列表格式

**期刊文章**:
```
Author, A.A., Author, B.B. and Author, C.C. (Year) 'Article title',
Journal Name, Volume(Issue), pp. page range. doi: XX.XXXX/xxxxx
```

**书籍**:
```
Author, A.A. (Year) Book Title. Edition. Place: Publisher.
```

## 执行流程

### Step 1: 引用插入

1. 识别引用位置的上下文
2. 根据引用类型确定格式:
   - 如果是支持性论述 → parenthetical
   - 如果强调作者观点 → narrative

3. 生成规范的引文:
   ```
   原文: "This phenomenon has been widely observed."

   插入引用后: "This phenomenon has been widely observed in
   multiple studies (Smith et al., 2023; Jones and Brown, 2024)."
   ```

4. 确保引用的准确性:
   - 引用内容与原文一致
   - 数据数值准确无误
   - 不断章取义或误读

### Step 2: 引用验证

5. 交叉检查引用的合理性:
   - 引用是否支持当前论述
   - 引用的文献是否是该领域的权威来源
   - 避免过度自引(如果适用)

6. 检查引用密度:
   - 引言: 平均每3-4句1个引用
   - 方法: 方法学来源必须引用
   - 结果: 必要时引用支持性研究
   - 讨论: 平均每2-3句1个引用

### Step 3: 管理引用记录

7. 更新引用数据库:
```json
{
  "citation_id": "Smith2023",
  "authors": ["Smith, A.A.", "Jones, B.B."],
  "year": 2023,
  "title": "Article title",
  "journal": "Nature",
  "volume": 615,
  "issue": 7950,
  "pages": "123-130",
  "doi": "10.1038/xxxxx",
  "cited_in_sections": ["introduction", "discussion"],
  "citation_count": 3,
  "first_cited_date": "2024-01-15"
}
```

8. 保存到 `{output_dir}`/references.json`

### Step 4: 生成参考文献列表

9. 从 `references.json` 读取所有引用
10. 按字母顺序排序(首作者姓氏)
11. 按Harvard格式生成参考文献列表:

```markdown
## References

Brown, A.B., Smith, C.D. and Jones, E.F. (2023) 'Title of the article',
Nature, 615(7950), pp. 123-130. doi: 10.1038/xxxxx

Jones, B.B. and Brown, C.C. (2024) 'Another article title',
Cell, 187(1), pp. 45-58. doi: 10.1016/j.cell.2024.xxxxx

Smith, A.A., Jones, B.B., Brown, C.C. and White, D.D. (2023)
'Multi-author article', Science, 379(6628), pp. 234-242.
doi: 10.1126/science.xxxxx
```

### Step 5: 使用docx skill插入

12. 调用docx skill在文档中插入引用:
```
Skill: docx
Action: insert_text
Location: {paragraph_id, position}
Content: "(Smith et al., 2023)"
Style: "citation"
```

13. 在文档末尾插入参考文献列表:
```
Skill: docx
Action: add_section
Section: "References"
Content: [生成的参考文献列表]
Style: "references"
```

## 质量检查清单

- ✅ 所有引用格式符合Harvard规范
- ✅ 引用内容与原文一致,无误读
- ✅ 数值引用准确无误
- ✅ 参考文献列表完整,无遗漏
- ✅ 参考文献按字母顺序排列
- ✅ DOI链接正确可访问
- ✅ 引用密度符合学术规范
- ✅ 无重复引用或冗余引用

## 输出
- 插入引用后的文本段落
- 更新的references.json
- 完整的参考文献列表(Markdown和DOCX格式)
