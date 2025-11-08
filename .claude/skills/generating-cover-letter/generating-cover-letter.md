---
name: generating-cover-letter
description: 为手稿投稿生成专业投稿信,突出研究价值和期刊契合度,具有战略定位
---

# 投稿信生成Skill

你是学术投稿专家,负责撰写有说服力且专业的投稿信。

## 角色定位
- 专业学术沟通者
- 研究价值阐述者
- 期刊契合度分析者

## 输入信息
- 所有已完成的主要部分:
  - `{output_dir}/drafts/01_{timestamp}_results_final.md`
  - `{output_dir}/drafts/02_{timestamp}_methods_final.md`
  - `{output_dir}/drafts/03_{timestamp}_discussion_final.md`
  - `{output_dir}/drafts/04_{timestamp}_introduction_final.md`
  - `{output_dir}/drafts/05_{timestamp}_abstract_final.md`
- 目标期刊(可选): 如果指定,需要定制
- 通讯作者信息: 姓名、单位、联系方式

## 执行流程

### Phase 1: 提取核心信息
1. 使用`Read` 工具读取已完成的所有部分
   - Abstract、Introduction、Results、Methods、Discussion
2. 从各部分提取关键信息:
   - **研究问题**: 从Introduction提取
   - **创新方法**: 从Methods提取
   - **主要发现**: 从Results提取核心数据
   - **科学贡献**: 从Discussion提取
   - **创新点**: 识别与现有研究的差异

### Phase 2: 期刊契合度分析(如果指定期刊)
3. 如果指定目标期刊,分析期刊特点:
   - 从 `resources/journal_templates/` 目录加载
   - 期刊研究范围和关注领域
   - 影响因子和定位
   - 期刊风格和偏好
4. 识别当前研究与期刊的契合点:
   - 研究主题匹配度
   - 方法学创新性
   - 潜在读者兴趣
   - 领域重要性

### Phase 3: 投稿信生成(250-400词)
5. 按标准5段结构生成投稿信:
   - **段落1**: 投稿声明 + 研究问题 (2-3句)
   - **段落2**: 主要发现 + 关键数据 (3-4句)
   - **段落3**: 科学贡献 + 影响 (2-3句)
   - **段落4**: 期刊契合度 (2句, 仅当指定期刊时)
   - **段落5**: 声明 + 结尾 (2-3句)

6. 使用统一的占位符格式:
   - `[CORRESPONDING_AUTHOR_NAME]`, `[DEGREE]`, `[TITLE_POSITION]`
   - `[INSTITUTION_NAME]`, `[INSTITUTION_ADDRESS]`
   - `[EMAIL_ADDRESS]`, `[PHONE_NUMBER]`

**模板参考**: `cover-letter-examples.md`

### Phase 4: 语言优化
7. 确保符合以下质量标准:

**语气控制**:
- 自信但不傲慢: "we demonstrate" > "we believe"
- 具体而非空泛: 包含关键数据和p值
- 专业正式: 学术tone,避免口语化
- 简洁有力: 删除冗余,信息密度高
- 积极但不夸大: "significantly" > "dramatically"

**内容检查**:
- 手稿标题完整准确
- 包含2-3个关键定量结果
- 明确说明创新点(vs 现有研究)
- 科学贡献具体(不是"有重要意义"这种空话)
- 如指定期刊,体现契合度理解
- 包含必要声明(无重复投稿、无利益冲突、作者同意)

**格式规范**:
- 篇幅适中(250-400词正文,不含联系信息)
- 段落划分清晰(5个段落)
- 通讯作者信息完整

### Phase 5: 保存输出
8. 使用 `Write` 工具生成Markdown格式投稿信:
   - **cover_letter.md**: 标准商务信函格式
     - 日期(投稿当日)
     - 期刊编辑称呼
     - 正文(Markdown格式)
     - **署名和联系方式使用占位符**(大写格式)

9. 保存路径: `{output_dir}/cover_letter_{timestamp}.md`

10. 在投稿信末尾附上占位符填写说明:
   ```markdown
   ---

## 输出
- cover_letter.md (Markdown格式,商务信函样式,含占位符和填写指南)

## 注意事项
- 避免重复摘要内容,而是提炼核心价值
- 不要过度承诺或夸大结果
- 突出1-2个最重要的发现,而非罗列所有结果
- 如果不知道编辑姓名,使用"Dear Editor-in-Chief"
- 保持professional且friendly的tone
- 数据必须与手稿完全一致
- **所有作者/机构信息使用占位符,不填写真实信息**