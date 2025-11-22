---
name: manuscript
description: 完整的生命医学论文生成工作流,通过manuscript-orchestrator代理编排专业写作技能
category: workflow
complexity: advanced
personas: [manuscript-orchestrator]
---

# /manuscript - 生物医学论文生成工作流

## 概述

将研究报告自动转化为符合期刊规范的可发表论文,包含100%真实文献引用和完整投稿准备。

**适用场景**:
- 生物医学领域研究论文撰写

## 快速开始

### 标准完整论文生成
```bash
/manuscript @your_research_report.docx --output_dir output_dir
```
- **输出**: 完整论文(MD+DOCX)

## 参数配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `@report` | 路径 | **必需** | 研究报告文件路径 (**.docx格式**) |
| `--parse-images` | 标志 | `true` | 提取和分析图片 (默认开启) |
| `--output_dir` | 路径 | `.manuscript` | 工作目录位置 |

## 错误处理

**文件格式错误**
```
错误: 研究报告必须是.docx格式,当前文件: report.pdf
解决: 请重新上传.docx格式的研究报告
验证: file --mime-type report.docx  # 应显示 application/vnd.openxmlformats-officedocument.wordprocessingml.document
```