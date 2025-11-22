#!/usr/bin/env bash
# 文献检索与处理全流程编排脚本
# 阶段：
#   1) OpenAlex 检索
#   2) PubMed 检索
#   3) 合并去重（冲突优先保留 PubMed 字段）
#   4) CrossRef 验证（直连、严格 TLS 校验）
#   5) 期刊影响因子与质量评分（JCR/中科院/预警）
#   6) 下载与转换（MinerU → PyMuPDF4LLM → OCR → MarkItDown → pdfplumber）

set -euo pipefail

# 以脚本所在目录为路径基准
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ML_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"     # managing-literature 目录
SKILLS_ROOT="$(cd "${ML_DIR}/.." && pwd)"    # ~/.claude/skills 根目录

# 默认参数
PART=""
QUERY=""
MIN_YEAR=2015
MAX_YEAR=$(date +%Y)
ARTICLE_KIND="research"   # research | review | any
MAX_RESULTS=5
MAX_OA=2
ROOT_DIR=""
DEBUG_MODE="false"

usage() {
  cat <<EOF
用法: $(basename "$0") [选项]

选项：
  --part NAME             撰写部分名称，默认: ${PART}
  --query STRING          检索关键词（必填）
  --min-year YYYY         最小年份，默认: ${MIN_YEAR}
  --max-year YYYY         最大年份，默认: 当前年份
  --article-kind KIND     文章类型: research | review | any，默认: research
  --max-results N         每源最大返回，默认: ${MAX_RESULTS}
  --max-oa N              额外 OA 数量，默认: ${MAX_OA}
  --root DIR              根输出目录，默认: ${ROOT_DIR}
  --debug                 启用详细日志（默认关闭）
  -h | --help             显示帮助

示例：
  $(basename "$0") \\
    --part Results \\
    --query "cardiology randomized trial" \\
    --min-year 2015 --max-year 2025 \\
    --article-kind research \\
    --max-results 5 --max-oa 2 \\
    --root workdir
EOF
}

# 解析参数
while [[ $# -gt 0 ]]; do
  case "$1" in
    --part) PART="$2"; shift 2;;
    --query) QUERY="$2"; shift 2;;
    --min-year) MIN_YEAR="$2"; shift 2;;
    --max-year) MAX_YEAR="$2"; shift 2;;
    --article-kind) ARTICLE_KIND="$2"; shift 2;;
    --max-results) MAX_RESULTS="$2"; shift 2;;
    --max-oa) MAX_OA="$2"; shift 2;;
    --root) ROOT_DIR="$2"; shift 2;;
    --debug) DEBUG_MODE="true"; shift;;
    -h|--help) usage; exit 0;;
    *) echo "[错误] 未知参数: $1"; usage; exit 1;;
  esac
done

if [[ -z "$QUERY" ]]; then
  echo "[错误] 必须提供 --query" >&2
  usage
  exit 1
fi

sanitize_part() {
  local input="$1"
  local sanitized
  sanitized=$(printf '%s' "$input" | sed -E 's/[^[:alnum:]]+/_/g')
  sanitized="${sanitized##_}"
  sanitized="${sanitized%%_}"
  if [[ -z "$sanitized" ]]; then
    sanitized="PART"
  fi
  printf '%s' "$sanitized"
}

slugify_query() {
  local input="$1"
  local slug
  slug=$(printf '%s' "$input" | tr '[:upper:]' '[:lower:]')
  slug=$(printf '%s' "$slug" | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')
  slug=$(printf '%s' "$slug" | sed -E 's/-{2,}/-/g')
  if [[ -z "$slug" ]]; then
    slug="query"
  fi
  printf '%s' "$slug"
}

PART_TOKEN=$(sanitize_part "$PART")
QUERY_SLUG=$(slugify_query "$QUERY")
TIME_HMS=$(date +%H%M%S)
EXTRACTION_TIMESTAMP=$(date +%Y-%m-%d-%H-%M-%S)
DEBUG_FLAG=""
if [[ "$DEBUG_MODE" == "true" ]]; then
  DEBUG_FLAG="--debug"
fi

# 秒级时间戳
DATE=$(date +%Y%m%d-%H%M%S)
TOTAL_START=$(date +%s)

# 输出目录结构
OA_DIR="${ROOT_DIR}/literature/1.search"
PM_DIR="${ROOT_DIR}/literature/1.search"
MERGE_DIR="${ROOT_DIR}/literature/2.merge"
VALID_DIR="${ROOT_DIR}/literature/3.validate"
SCORE_DIR="${ROOT_DIR}/literature/4.quality_score"
MD_DIR="${ROOT_DIR}/literature/5.texts/"
# echo ${OA_DIR}
mkdir -p "$OA_DIR" "$PM_DIR" "$MERGE_DIR" "$VALID_DIR" "$SCORE_DIR" "$MD_DIR"

BASE_STEM="${PART_TOKEN}_${QUERY_SLUG}-${TIME_HMS}"
OA_JSON="${OA_DIR}/openalex_${BASE_STEM}.json"
PM_JSON="${PM_DIR}/pubmed_${BASE_STEM}.json"
MERGED_JSON="${MERGE_DIR}/${BASE_STEM}.json"
VALID_JSON="${VALID_DIR}/${BASE_STEM}.json"
SCORED_JSON="${SCORE_DIR}/${BASE_STEM}.json"
# echo $OA_JSON
# OpenAlex 过滤条件（按文章类型）
OA_FILTER="publication_year:>${MIN_YEAR}"
case "${ARTICLE_KIND}" in
  research) OA_FILTER+=",type:journal-article";;
  review)   OA_FILTER+=",type:review-article";;
  any)      :;;
  *) echo "[警告] 未知 --article-kind=${ARTICLE_KIND}，按 any 处理";;
esac

# PubMed 检索语句（按文章类型追加 Publication Type）
PM_QUERY="$QUERY"
case "${ARTICLE_KIND}" in
  research) PM_QUERY="(${PM_QUERY}) AND (Journal Article[Publication Type]) NOT Review[Publication Type]";;
  review)   PM_QUERY="(${PM_QUERY}) AND Review[Publication Type]";;
  any)      :;;
esac

# echo "[信息] PART=${PART} DATE=${DATE}"
# echo "[信息] OpenAlex 过滤: ${OA_FILTER}"
# echo "[信息] PubMed 检索: ${PM_QUERY}"

# echo ${SCRIPT_DIR}
## 1&2) OpenAlex + PubMed 并行检索（计时）
STEP_START=$(date +%s)
(
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY NO_PROXY=.openalex.org,api.openalex.org \
    python "${SCRIPT_DIR}/openalex_search.py" \
      --query "$QUERY" --filter "$OA_FILTER" \
      --max_results "$MAX_RESULTS" \
      --max_oa "$MAX_OA" \
      --output "$OA_JSON" ${DEBUG_FLAG}
) &
pid_openalex=$!
(
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy NO_PROXY=.nih.gov,eutils.ncbi.nlm.nih.gov \
    python "${SCRIPT_DIR}/pubmed_search.py" \
      --query "$PM_QUERY" \
      --min_year "$MIN_YEAR" \
      --max_year "$MAX_YEAR" \
      --max_results "$MAX_RESULTS" \
      --max_oa "$MAX_OA" \
      --output "$PM_JSON" ${DEBUG_FLAG}
) &
pid_pubmed=$!
wait $pid_openalex
wait $pid_pubmed
STEP_END=$(date +%s)
# echo "[耗时] OpenAlex + PubMed 并行检索: $((STEP_END-STEP_START))s"

## 3) 合并去重（计时）
STEP_START=$(date +%s)
python "${SCRIPT_DIR}/literature_utils.py" merge \
  --input "$OA_JSON" "$PM_JSON" \
  --output "$MERGED_JSON" \
  --dedup_by doi ${DEBUG_FLAG}

STEP_END=$(date +%s)
# echo "[耗时] 合并去重: $((STEP_END-STEP_START))s"

## 4) CrossRef 验证（计时）
STEP_START=$(date +%s)
env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY NO_PROXY=.crossref.org,api.crossref.org python "${SCRIPT_DIR}/crossref_validate.py" \
  --input "$MERGED_JSON" \
  --output "$VALID_JSON" \
  --workers 6 ${DEBUG_FLAG}

STEP_END=$(date +%s)
# echo "[耗时] CrossRef 验证: $((STEP_END-STEP_START))s"

## 5) 期刊影响力评分（计时）
STEP_START=$(date +%s)
python "${SCRIPT_DIR}/impact_factor.py" \
  --input "$VALID_JSON" \
  --output "$SCORED_JSON" ${DEBUG_FLAG}

STEP_END=$(date +%s)
# echo "[耗时] 期刊质量评分: $((STEP_END-STEP_START))s"

## 6) 下载与转换（计时）
STEP_START=$(date +%s)

env -u http_proxy -u https_proxy -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u NO_PROXY \
  MINERU_TRUST_ENV=0 \
  EXTRACTION_TIMESTAMP="$EXTRACTION_TIMESTAMP" \
  TARGET_MANUSCRIPT_SECTION="$PART" \
  CITATION_POINT_ID="$QUERY" \
  EXTRACTION_PURPOSE="" \
  python "${SCRIPT_DIR}/scihub_download.py" batch \
  --input "$SCORED_JSON" \
  --output "$MD_DIR" ${DEBUG_FLAG}

STEP_END=$(date +%s)
echo "[耗时] 下载与转换: $((STEP_END-STEP_START))s"

## 总耗时
TOTAL_END=$(date +%s)
echo "[耗时] 全流程总计: $((TOTAL_END-TOTAL_START))s"

# echo "完成:\n- OpenAlex:    $OA_JSON\n- PubMed:      $PM_JSON\n- 合并去重:    $MERGED_JSON\n- CrossRef验证: $VALID_JSON\n- 质量评分:    $SCORED_JSON\n- Markdown →   $MD_DIR (含仅成功条目的 {stem}.json)"
