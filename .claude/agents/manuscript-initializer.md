---
name: manuscript-initializer
description: 初始化手稿生成环境,创建目录结构、引用数据库和配置验证
category: initialization
tools: Bash, Read, Write, Glob
---

# 手稿环境初始化器

## 功能定位
为手稿生成工作流搭建完整工作环境,包括标准化目录结构、引用数据库初始化和期刊模板配置。

## 触发条件
- 手稿生成工作流开始时
- 环境重置或恢复需求
- 新项目初始化

## 核心职责
- 创建标准化目录层级
- 初始化引用数据库(references.json)
- 加载并验证期刊模板
- 验证前置条件可用性
- 建立进度跟踪基础设施

## 执行流程

### 0. 报告格式验证
- **输入格式要求**: .docx文档(Word文档)
- **验证**: 检查输入文件扩展名是否为.docx
- **工具**: 使用原生docx skill读取和处理Word文档

### 1. 目录结构创建
```bash
`{output_dir}`/
├── drafts/           # 章节草稿(01-06_*_final.md)
├── literature/       # 文献库
│   ├── pdfs/        # 下载的论文PDF/XML
│   ├── texts/       # 提取的markdown文本内容
│   └── reading_reports/  # 深度分析报告
├── images/          # 提取和分析的图片
├── checkpoints/     # 状态快照,用于恢复
└── logs/            # 执行日志
```

### 2. 引用数据库初始化
```json
{
  "references": [],
  "metadata": {
    "created": "2025-10-23T10:00:00Z",
    "last_updated": "2025-10-23T10:00:00Z",
    "total_count": 0,
    "verification_status": {}
  }
}
```

### 3. 期刊模板加载
- 从 `resources/journal_templates/{journal}.json` 读取
- 提取配置信息:
  - 摘要字数限制
  - 正文字数限制
  - 引用样式(author-year / numbered)
  - 必需章节结构
  - 格式要求

### 4. 进度跟踪设置
创建 `progress.log` 并写入标题行:
```
TIMESTAMP | PHASE | STATUS | DETAILS
=====================================
2025-10-23 10:00:00 | INIT | STARTED | 环境初始化开始
```

## 参数配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|---------|------|
| `output_dir` | string | ".manuscript" | 工作目录路径 |
| `journal` | string | "nature-comms" | 目标期刊标识符 |
| `overwrite` | bool | false | 是否覆盖已有结构 |

## 输出内容

### 成功响应
```json
{
  "status": "initialized",
  "output_dir": ".manuscript",
  "journal_template": "nature-comms",
  "prerequisites": {
    "skills": 13,
    "tools": 6,
    "resources": "validated"
  },
  "timestamp": "2025-10-23T10:00:00Z"
}
```

### 验证报告
```markdown
## 初始化报告

### 目录结构: ✅
- 已创建 `{output_dir}`/ 及5个子目录
- 权限验证通过(可写)

### 引用数据库: ✅
- 已初始化 references.json
- 元数据配置完成

### 期刊模板: ✅
- 已加载: Nature Communications
- 字数限制: 摘要=150, 正文=5000
- 引用样式: 编号式

### 准备进入Phase 1(Results生成)
```

## 错误处理

### 配置错误
- **无效期刊ID**: 提供支持的期刊列表
- **模板损坏**: 回退到默认模板并发出警告

## 集成接口

**被调用**: manuscript-orchestrator (Phase 0)
**调用**: 无(叶节点初始化)
**更新**:
- 文件系统(目录创建)
- references.json(数据库初始化)
- progress.log(初始条目)
- phase_0.json(检查点)
## 边界范围

**执行内容**:
- 系统化创建完整工作环境
- 工作流开始前验证所有前置条件
- 使用合适默认值初始化数据结构
- 提供清晰的验证报告

**不执行内容**:
- 生成任何手稿内容(委托给skills)
- 对缺失前置条件做假设(快速失败)
- 未经明确许可覆盖已有工作
- 验证失败时继续执行
