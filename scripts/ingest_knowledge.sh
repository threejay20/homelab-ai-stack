#!/bin/bash
# Re-ingests all lab docs and study guides into Nezuko's knowledge base
# Run this after a fresh start or when docs are updated

RAG_URL="http://localhost:8000/ingest"
API_KEY="homelab-rag-key-2024"

echo "Ingesting lab documentation..."

for path in \
  /home/jjohnson/homelab/README.md \
  /home/jjohnson/homelab/SECURITY.md \
  /home/jjohnson/homelab/stage1/README.md \
  /home/jjohnson/homelab/stage2/README.md \
  /home/jjohnson/homelab/stage2.5/README.md \
  /home/jjohnson/homelab/stage3/README.md \
  /home/jjohnson/homelab/stage4/README.md \
  /home/jjohnson/homelab/stage5/README.md \
  /home/jjohnson/homelab/stage6/README.md
do
  name=$(basename $(dirname $path))/$(basename $path)
  txt="/tmp/$(echo $path | tr '/' '_').txt"
  cp "$path" "$txt"
  result=$(curl -s -X POST "$RAG_URL" \
    -H "X-API-Key: $API_KEY" \
    -F "file=@$txt;type=text/plain")
  rm "$txt"
  echo "$name: $result"
done

echo "Ingesting AIP-C01 study guide..."
curl -s -X POST "$RAG_URL" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@/home/jjohnson/homelab/scripts/aip_c01_study_guide.txt;type=text/plain"

echo ""
echo "Done."
