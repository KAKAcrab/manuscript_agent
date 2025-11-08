# 图片分析JSON结构示例

> 为parsing-images skill的Phase 6提供的标准化JSON输出格式

---

## 完整JSON结构

```json
{
  "report_metadata": {
    "report_path": "path/to/report.docx",
    "report_content_path": "{output_dir}/report_content.md",
    "total_figures": 5,
    "parsed_date": "2024-01-15T10:30:00",
    "parsing_method": "Claude native multimodal"
  },
  "figures": [
    {
      "figure_id": "figure_1",
      "image_path": "{output_dir}/images/figure_1.png",
      "position_in_document": "page 3, after paragraph 12",
      "original_caption": "原始DOCX中的图注文本",

      "has_subplots": false,
      "type": "bar_chart",

      "context_from_report": {
        "referenced_paragraphs": [12, 13],
        "research_purpose": "Demonstrate treatment efficacy on gene expression",
        "key_conclusions": [
          "Treatment A increases expression 3.2-fold",
          "Treatment B shows dose-dependent effect"
        ],
        "related_methods": "qRT-PCR, n=3 biological replicates"
      },

      "structured_data": {
        "axes": {
          "x_axis": {
            "label": "Treatment groups",
            "categories": ["Control", "Treatment A", "Treatment B"]
          },
          "y_axis": {
            "label": "Relative expression (fold change)",
            "range": [0, 5],
            "unit": "fold"
          }
        },
        "data_points": [
          {
            "group": "Control",
            "value": 1.0,
            "error_bar": 0.1,
            "error_type": "SEM"
          },
          {
            "group": "Treatment A",
            "value": 3.2,
            "error_bar": 0.3,
            "significance": "**"
          },
          {
            "group": "Treatment B",
            "value": 4.5,
            "error_bar": 0.4,
            "significance": "***"
          }
        ],
        "statistical_info": {
          "sample_size": "n=3",
          "test_method": "One-way ANOVA with Tukey's post-hoc test",
          "significance_levels": [
            "**: p < 0.01",
            "***: p < 0.001"
          ]
        }
      },

      "publication_caption": {
        "title": "Treatment A significantly increases target gene expression",
        "full_caption": "Relative mRNA expression levels measured by qRT-PCR in control and treatment groups. Data represent mean ± SEM from three independent experiments (n=3 per group). **p < 0.01, ***p < 0.001 (one-way ANOVA with Tukey's post-hoc test)."
      },

      "key_findings": [
        "Treatment A significantly increased expression by 3.2-fold (p < 0.01)",
        "Treatment B showed dose-dependent effect with 4.5-fold increase (p < 0.001)"
      ]
    },
    {
      "figure_id": "figure_2",
      "image_path": "{output_dir}/images/figure_2.png",
      "position_in_document": "page 5, after paragraph 18",
      "original_caption": "原始多面板图注文本",

      "has_subplots": true,
      "subplot_count": 4,
      "subplots": [
        {
          "id": "2a",
          "type": "bar_chart",
          "position": "top-left",
          "structured_data": {
            "axes": {},
            "data_points": [],
            "statistical_info": {}
          }
        },
        {
          "id": "2b",
          "type": "heatmap",
          "position": "top-right",
          "structured_data": {
            "dimensions": {
              "rows": {"label": "Genes", "count": 100},
              "columns": {"label": "Samples", "count": 6}
            },
            "color_mapping": {
              "scale_type": "divergent",
              "min_value": -2.0,
              "max_value": 2.0,
              "unit": "log2 fold change"
            },
            "clustering_info": {
              "method": "hierarchical clustering",
              "distance_metric": "Euclidean distance",
              "major_clusters": 3
            }
          }
        },
        {
          "id": "2c",
          "type": "microscopy",
          "position": "bottom-left",
          "structured_data": {
            "technical_details": {
              "microscopy_type": "confocal fluorescence",
              "magnification": "40×",
              "scale_bar": "50 μm"
            },
            "staining_info": {
              "channels": [
                {"color": "blue", "target": "DAPI (nuclear marker)"},
                {"color": "green", "target": "Target protein"}
              ]
            },
            "panels": [
              {
                "panel": "Control",
                "observations": ["Diffuse cytoplasmic localization"]
              },
              {
                "panel": "Treatment",
                "observations": ["Increased nuclear accumulation"]
              }
            ]
          }
        },
        {
          "id": "2d",
          "type": "scatter_plot",
          "position": "bottom-right",
          "structured_data": {
            "axes": {},
            "correlation_info": {
              "coefficient": "R² = 0.85",
              "p_value": "p < 0.001",
              "regression": "y = 1.2x + 0.5"
            }
          }
        }
      ],

      "context_from_report": {
        "referenced_paragraphs": [18, 19, 20],
        "research_purpose": "Multi-modal validation of treatment effects",
        "key_conclusions": [
          "Consistent effects across gene, protein, and cellular levels"
        ]
      },

      "publication_caption": {
        "title": "Treatment B modulates cellular responses through multiple pathways",
        "full_caption": "(A) Bar chart showing relative mRNA expression of target genes (n=3). (B) Heatmap displaying hierarchical clustering of 100 differentially expressed genes across 6 samples. (C) Immunofluorescence staining of target protein (green) and DAPI (blue). Scale bar = 50 μm. (D) Quantification of nuclear/cytoplasmic fluorescence ratio. Data represent mean ± SEM from 30 cells per group. ***p < 0.001 (unpaired t-test)."
      },

      "key_findings": [
        "Multi-level validation confirms treatment efficacy",
        "Nuclear translocation correlates with increased expression",
        "Clustering reveals three distinct gene expression patterns"
      ]
    }
  ],
  "summary": {
    "total_main_figures": 5,
    "total_subplots": 12,
    "by_type": {
      "data_charts": 8,
      "biological_images": 6,
      "diagrams": 3
    },
    "total_statistical_comparisons": 15,
    "context_association_success_rate": "100%"
  }
}
```

---

## 字段说明

### report_metadata (顶层元信息)
- `report_path`: 原始DOCX报告路径
- `report_content_path`: 提取的文本内容路径
- `total_figures`: 主图数量
- `parsed_date`: 解析时间戳
- `parsing_method`: 解析方法标识

### figures[] (图片列表)

**基本字段**:
- `figure_id`: 图片唯一标识
- `image_path`: 提取的图片文件路径
- `position_in_document`: 在文档中的位置
- `original_caption`: 原始DOCX图注文本

**子图检测字段**:
- `has_subplots`: 是否包含子图 (boolean)
- `subplot_count`: 子图数量 (仅当has_subplots=true)
- `type`: 图表类型 (单图)
- `subplots[]`: 子图列表 (多图)
  - `id`: 子图标识 (如"2a", "2b")
  - `type`: 子图类型
  - `position`: 子图位置
  - `structured_data`: 子图的结构化数据

**上下文关联字段**:
- `context_from_report`: 从报告文本提取的上下文
  - `referenced_paragraphs`: 引用段落编号列表
  - `research_purpose`: 研究目的
  - `key_conclusions`: 关键结论列表
  - `related_methods`: 相关方法

**结构化数据字段**:
- `structured_data`: 按图表类型提取的结构化信息
  - 字段依图表类型而定
  - 参考 `image-analysis-guidelines.md` 各章节

**图注字段**:
- `publication_caption`: 发表级图注
  - `title`: 一句话标题
  - `full_caption`: 完整图注文本
  - 参考 `figure-caption-examples.md` 标准

**关键发现字段**:
- `key_findings[]`: 从图片提取的核心结论列表

### summary (总体统计)
- `total_main_figures`: 主图总数
- `total_subplots`: 子图总数
- `by_type`: 按类型分类统计
- `total_statistical_comparisons`: 统计比较总数
- `context_association_success_rate`: 上下文关联成功率