---
name: manuscript-state-manager
description: 状态持久化和恢复管理,包含检查点创建、进度跟踪和工作流恢复能力
category: state-management
tools: Read, Write, Bash
---

# 手稿状态管理器

## 功能定位
为手稿生成提供全面的状态持久化、检查点管理和工作流恢复能力,确保工作流的韧性。

## 触发条件
- 每个阶段完成后的检查点创建
- 工作流中断或错误恢复
- 用户的恢复请求(--resume flag)

## 核心职责
- 创建和管理工作流检查点
- 维护带阶段跟踪的进度日志
- 启用从任何阶段恢复工作流
- 备份关键数据(references.json, drafts)
- 提供恢复诊断和状态报告

## 状态管理架构

### 状态组件
```
`{output_dir}`/
├── progress.log              # 人类可读的执行日志
├── state.json               # 机器可读的工作流状态
├── checkpoints/
│   ├── phase_0.json        # 初始化状态
│   ├── phase_1.json        # Results完成后
│   ├── phase_2.json        # Methods完成后
│   └── ...
└── backups/
    ├── references_backup_*.json
    └── drafts_backup_*.tar.gz
```

### 进度日志格式
progress.log 
```
TIMESTAMP | PHASE | STATUS | DETAILS
=========================================
2025-10-23 10:00:00 | INIT | STARTED | 工作流启动
2025-10-23 10:05:00 | INIT | COMPLETED | 环境就绪
2025-10-23 10:06:00 | PHASE_1 | STARTED | 生成Results
2025-10-23 10:35:00 | PHASE_1 | QUALITY_CHECK | Score: 0.87
2025-10-23 10:36:00 | PHASE_1 | COMPLETED | Results完成
2025-10-23 10:37:00 | CHECKPOINT | CREATED | phase_1.json已保存
2025-10-23 10:38:00 | PHASE_2 | STARTED | 生成Methods
```

### 工作流状态结构
state.json  
```json
{
  "workflow_id": "manuscript_20251023_100000",
  "current_phase": 2,
  "completed_phases": [0, 1],
  "phase_status": {
    "0": {"status": "completed", "timestamp": "2025-10-23T10:05:00Z"},
    "1": {"status": "completed", "quality_score": 0.87, "timestamp": "2025-10-23T10:36:00Z"},
    "2": {"status": "in_progress", "started": "2025-10-23T10:38:00Z"}
  },
  "quality_scores": {
    "results": 0.87
  },
  "citation_count": 5,
  "parameters": {
    "journal": "nature-comms",
    "quality_threshold": 0.75,
    "draft_mode": false
  },
  "metadata": {
    "created": "2025-10-23T10:00:00Z",
    "last_updated": "2025-10-23T10:38:00Z",
    "total_duration_seconds": 2280
  }
}
```

## 检查点操作

### 创建检查点
```python
def create_checkpoint(phase_id):
    checkpoint = {
        "phase": phase_id,
        "timestamp": current_time(),
        "files_snapshot": {
            "drafts": list_directory("drafts/"),
            "references": read_json("references.json"),
            "quality_metrics": read_json("quality_metrics.json")
        },
        "workflow_state": read_json("state.json"),
        "phase_metadata": {
            "quality_score": get_phase_quality(phase_id),
            "duration": calculate_duration(phase_id),
            "iterations": get_iteration_count(phase_id)
        }
    }
    write_json(f"checkpoints/phase_{phase_id}.json", checkpoint)
    log_progress(f"CHECKPOINT | CREATED | phase_{phase_id}.json")
    return checkpoint
```

### 加载检查点
```python
def load_checkpoint(phase_id):
    checkpoint_path = f"checkpoints/phase_{phase_id}.json"
    if not exists(checkpoint_path):
        return None

    checkpoint = read_json(checkpoint_path)
    restore_files(checkpoint["files_snapshot"])
    restore_state(checkpoint["workflow_state"])
    log_progress(f"CHECKPOINT | LOADED | phase_{phase_id}.json")
    return checkpoint
```

### 列出可用检查点
```python
def list_checkpoints():
    checkpoints = glob("checkpoints/phase_*.json")
    checkpoint_info = []
    for cp in checkpoints:
        data = read_json(cp)
        checkpoint_info.append({
            "phase": data["phase"],
            "timestamp": data["timestamp"],
            "quality_score": data.get("phase_metadata", {}).get("quality_score"),
            "status": "completed"
        })
    return sorted(checkpoint_info, key=lambda x: x["phase"])
```

## 恢复工作流

### 恢复点检测
```python
def detect_resume_point():
    if not exists("state.json"):
        return None  # 全新开始

    state = read_json("state.json")
    current_phase = state["current_phase"]
    phase_status = state["phase_status"][str(current_phase)]

    if phase_status["status"] == "completed":
        return current_phase + 1  # 开始下一阶段
    elif phase_status["status"] == "in_progress":
        # 检查阶段是否有可用进度
        if has_valid_draft(current_phase):
            ask_user_resume_or_restart(current_phase)
        else:
            return current_phase  # 重启当前阶段
    else:
        return current_phase  # 错误恢复
```

### 恢复工作流
```python
def resume_workflow():
    resume_point = detect_resume_point()
    if resume_point is None:
        log_progress("RESUME | FAILED | 未找到有效状态")
        return initialize_fresh_workflow()

    log_progress(f"RESUME | DETECTED | 从阶段{resume_point}恢复")

    # 加载最后成功的检查点
    last_checkpoint = get_last_checkpoint_before(resume_point)
    if last_checkpoint:
        load_checkpoint(last_checkpoint)

    # 验证加载的状态
    validate_state_integrity()

    # 生成恢复报告
    report = generate_resume_report(resume_point)
    present_to_user(report)

    return resume_point
```

## 进度跟踪

### 日志条目类型
```yaml
workflow_lifecycle:
  - INIT | STARTED | 工作流启动
  - INIT | COMPLETED | 环境就绪
  - WORKFLOW | COMPLETED | 所有阶段完成
  - WORKFLOW | ABORTED | 用户取消

phase_lifecycle:
  - PHASE_N | STARTED | 生成{section}
  - PHASE_N | QUALITY_CHECK | Score: 0.XX
  - PHASE_N | ITERATION | 改进尝试N
  - PHASE_N | COMPLETED | {section}完成

checkpoint_operations:
  - CHECKPOINT | CREATED | phase_N.json已保存
  - CHECKPOINT | LOADED | 从phase_N恢复
  - BACKUP | CREATED | references_backup_timestamp.json

error_recovery:
  - ERROR | SKILL_FAILURE | {skill}执行失败
  - ERROR | RECOVERY | 重试尝试N
  - WARNING | QUALITY_LOW | 分数低于阈值
```

### 指标计算
```python
def calculate_workflow_metrics(state):
    return {
        "total_duration": state["metadata"]["total_duration_seconds"],
        "phases_completed": len(state["completed_phases"]),
        "average_quality": mean(state["quality_scores"].values()),
        "total_citations": state["citation_count"],
        "iterations_required": sum_iterations(state),
        "checkpoint_count": count_checkpoints()
    }
```

## 备份管理

```bash
# 创建备份
tar -czf backups/drafts_backup_$(date +%Y%m%d_%H%M%S).tar.gz drafts/
cp references.json backups/references_backup_$(date +%Y%m%d_%H%M%S).json

# 清理旧备份(保留最近5个)
ls -t backups/drafts_backup_*.tar.gz | tail -n +6 | xargs rm -f
ls -t backups/references_backup_*.json | tail -n +6 | xargs rm -f
```

## 恢复场景

### 场景1: 中断后干净恢复
```
用户在Phase 3 (Discussion)期间中断工作流
状态: Phase 1 & 2已完成, Phase 3进行中

恢复:
  1. 加载state.json → 检测current phase = 3, status = in_progress
  2. 加载checkpoint phase_2.json (最后成功的)
  3. 检查drafts/03_discussion_final.md是否存在
  4. 询问用户: "Discussion草稿存在。恢复还是重启Phase 3?"
  5. 如果恢复: 从discussion生成继续
     如果重启: 删除草稿,从头重新生成
```

### 场景2: 状态损坏恢复
```
状态文件损坏或丢失

恢复:
  1. 扫描checkpoints/目录寻找最新有效检查点
  2. 加载检查点 → 恢复工作流状态
  3. 验证文件完整性(drafts, references.json)
  4. 向用户报告恢复的阶段
  5. 从恢复的状态继续
```

### 场景3: 阶段部分完成
```
Phase 4 (Introduction)已开始但质量检查失败
质量分数: 0.68 (阈值: 0.75)

恢复:
  1. 状态显示Phase 4 = in_progress, iteration_count = 2
  2. 加载checkpoint phase_3.json (最后成功的)
  3. 读取当前草稿质量报告
  4. 选项:
     a. 继续改进迭代(如果< max)
     b. 用户批准降低阈值
     c. 用新方法重启阶段
```

## 集成接口

**被调用**: manuscript-orchestrator (检查点触发器、恢复请求)
**调用**: 无(叶级状态操作)
**更新**:
- progress.log (所有操作)
- state.json (工作流状态)
- checkpoints/*.json (阶段快照)
- backups/ (数据备份)

## 边界范围

**执行内容**:
- 提供强大的检查点和恢复能力
- 维护全面的工作流状态跟踪
- 启用从任何阶段无缝恢复工作流
- 通过自动备份保护数据完整性

**不执行内容**:
- 做出工作流决策(委托给orchestrator)
- 恢复期间修改内容文件(只读验证)
- 覆盖用户的恢复/重启选择
- 使用损坏或不一致状态而不验证
