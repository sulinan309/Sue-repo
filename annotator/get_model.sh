#!/bin/sh
# 下载 MediaPipe 姿态模型（约 9.4MB）。模型不入库。
set -e
M=pose_landmarker_full.task
[ -f "$M" ] && { echo "$M 已存在"; exit 0; }
curl -sSL -o "$M" \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/$M"
echo "已下载 $M ($(du -h "$M" | cut -f1))"
