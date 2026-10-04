#!/usr/bin/env bash
# Rakit & push backend ke Hugging Face Space. Jalankan dari ROOT repo:
#   HF_USER=username HF_SPACE=lnt-camp-2026-api HF_TOKEN=hf_xxx bash hf_space/deploy.sh
# (HF_TOKEN = Access Token dengan izin *write*: huggingface.co/settings/tokens)
set -euo pipefail
: "${HF_USER:?isi HF_USER}" "${HF_SPACE:?isi HF_SPACE}" "${HF_TOKEN:?isi HF_TOKEN}"

WORK="$(mktemp -d)"
git clone "https://${HF_USER}:${HF_TOKEN}@huggingface.co/spaces/${HF_USER}/${HF_SPACE}" "$WORK/space"
cd "$WORK/space"
git lfs install
git lfs track "*.pkl"          # file model > 10 MB wajib lewat LFS di HF

ROOT="$OLDPWD"
rm -rf backend model
cp "$ROOT/Dockerfile" .
cp "$ROOT/hf_space/README.md" README.md
cp -r "$ROOT/backend" backend
cp -r "$ROOT/model" model
find . -name "__pycache__" -type d -prune -exec rm -rf {} +

git add -A
git commit -m "Deploy backend" || echo "Tidak ada perubahan"
git push
echo "Selesai. Cek: https://${HF_USER}-${HF_SPACE}.hf.space/health"
