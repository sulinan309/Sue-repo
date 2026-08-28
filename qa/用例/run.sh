#!/usr/bin/env bash
# 一条命令跑完整套回归。
#
#   ./qa/用例/run.sh              跑全部
#   ./qa/用例/run.sh t02 t05      只跑名字里含 t02 / t05 的
#   ./qa/用例/run.sh --bless      重建 qa/回归基线/ 下的快照
#
# 退出码：0 全部通过；1 有失败。
# 已知缺陷（XFAIL）不算失败——它们记在 qa/缺陷清单.md 里等工程师修；
# 但如果某条已知缺陷的行为变了（XPASS），会**故意**判为失败，
# 逼着有人回来更新清单。
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

BLESS=""
PICK=()
for a in "$@"; do
  case "$a" in
    --bless) BLESS="--bless" ;;
    *) PICK+=("$a") ;;
  esac
done

mapfile -t ALL < <(ls "$HERE"/t*.py | sort)
FILES=()
if [ ${#PICK[@]} -eq 0 ]; then
  FILES=("${ALL[@]}")
else
  for f in "${ALL[@]}"; do
    for p in "${PICK[@]}"; do
      [[ "$(basename "$f")" == *"$p"* ]] && FILES+=("$f") && break
    done
  done
fi

if [ ${#FILES[@]} -eq 0 ]; then
  echo "没有匹配到用例：${PICK[*]:-}" >&2
  exit 1
fi

echo "攀岩标注管线 · 回归测试"
echo "工作目录 $(cd "$HERE/../.." && pwd)"
echo "python   $($PY -V 2>&1)"
echo "用例     ${#FILES[@]} 个"

FAILED=()
for f in "${FILES[@]}"; do
  if ! $PY "$f" $BLESS; then
    FAILED+=("$(basename "$f")")
  fi
done

echo
echo "======================================================================"
if [ ${#FAILED[@]} -eq 0 ]; then
  echo "全部通过：${#FILES[@]} 个用例文件"
  echo "======================================================================"
  exit 0
fi
echo "失败 ${#FAILED[@]} / ${#FILES[@]} 个用例文件："
for f in "${FAILED[@]}"; do echo "  - $f"; done
echo "======================================================================"
exit 1
