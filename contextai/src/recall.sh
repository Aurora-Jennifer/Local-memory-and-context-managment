#!/bin/bash

# === 1. Setup base dir consistent with Python modules ===
BASE_DIR="$HOME/.contextai"

# === 2. Usage check ===
if [ $# -lt 2 ]; then
  echo "Usage: recall <project_tag> <keyword>"
  exit 1
fi

PROJECT="$1"
shift
KEYWORD="$*"

# === 3. Construct log path ===
PROJECT_DIR="$BASE_DIR/$PROJECT"
LOGDIR="$PROJECT_DIR/context_logs"

# === 4. Check for matching logs ===
MATCHES=$(grep -l "$KEYWORD" "$LOGDIR"/* 2>/dev/null)

if [[ -z "$MATCHES" ]]; then
  echo "❌ No logs found for '$KEYWORD' in project '$PROJECT'."
  exit 1
fi

echo "📁 Found matches:"
echo "$MATCHES" | nl -w2 -s'. '

# === 5. User selects match(es) ===
echo -en "\n🔍 Enter number to open (or 'all' to summarize): "
read SELECTION

# === 6. Summarize all logs if requested ===
if [[ "$SELECTION" == "all" ]]; then
  cat $MATCHES | @mistral -p "$(printf "Summarize these logs by topic:\n\n")$(cat)"
  exit
fi

# === 7. Show selected log ===
CHOICE=$(echo "$MATCHES" | sed -n "${SELECTION}p")
less "$CHOICE"
