#!/bin/bash

BASE_DIR="$HOME/.contextai"
MODEL="@ds"
PREVIEW=false

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --model)
      MODEL="$2"
      shift 2
      ;;
    --preview)
      PREVIEW=true
      shift
      ;;
    -*)
      echo "Unknown flag: $1"
      exit 1
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done
set -- "${POSITIONAL[@]}"

PROJECT=$1
KEYWORD="${@:2}"

if [[ -z "$PROJECT" || -z "$KEYWORD" ]]; then
  echo "Usage: @recall <project_tag> <keyword> [--model @ds|@wiz] [--preview]"
  exit 1
fi

# === 1. Setup directories ===
PROJECT_DIR="$BASE_DIR/$PROJECT"
LOGDIR="$PROJECT_DIR/context_logs"
SUMMARY_SESSION="$(date +"%Y-%m-%d_%H-%M")"
SUMMARY_DIR="$PROJECT_DIR/$SUMMARY_SESSION"
mkdir -p "$SUMMARY_DIR"

# === 2. Find logs ===
MATCHES=$(grep -il "$KEYWORD" "$LOGDIR"/*_"$PROJECT"*.txt 2>/dev/null)

if [[ -z "$MATCHES" ]]; then
  echo "❌ No logs found for '$KEYWORD' in project '$PROJECT'."
  exit 1
fi

echo "📁 Matching logs:"
echo "$MATCHES" | nl -w2 -s'. '

echo -en "\n🔍 Use 'all', or pick file(s) by number (e.g. 1 or 1 2 3): "
read -a SELECTION

# === 3. Combine content ===
if [[ "${SELECTION[0]}" == "all" ]]; then
  FILES=($MATCHES)
else
  FILES=()
  for i in "${SELECTION[@]}"; do
    FILE=$(echo "$MATCHES" | sed -n "${i}p")
    FILES+=("$FILE")
  done
fi

if $PREVIEW; then
  echo -e "\n🧾 Previewing selected log(s)..."
  less "${FILES[@]}"
  exit 0
fi

CONTEXT=$(cat "${FILES[@]}")

# === 4. Capture source logs used ===
LOG_REFERENCES=$(for f in "${FILES[@]}"; do echo "- $(basename "$f")"; done)

# === 5. Get follow-up prompt ===
echo -e "\n📝 Enter your follow-up prompt (Ctrl+D to end):"
NEW_PROMPT=$(</dev/stdin)

# === 6. Build input ===
FINAL_PROMPT="Here is relevant project context from prior logs:\n\n$CONTEXT\n\nNow, respond to this new prompt:\n$NEW_PROMPT"

# === 7. Run model + capture output ===
echo -e "\n🤖 Using model: $MODEL"
echo -e "\033[1;34m[Prompt]\033[0m $NEW_PROMPT\n"
RESPONSE=$(eval $MODEL -p "\"$FINAL_PROMPT\"")

# === Print response with color ===
echo -e "\n\033[1;32m[Response]\033[0m\n$RESPONSE"

# === Save to Markdown ===
SUMMARY_FILE="$SUMMARY_DIR/summary.md"
LOG_LIST_FILE="$SUMMARY_DIR/logs_used.txt"

{
  echo "## 🕒 $SUMMARY_SESSION"
  echo "**Project**: $PROJECT"
  echo "**Model**: \`$MODEL\`"
  echo "**Prompt**:"
  echo '```'
  echo "$NEW_PROMPT"
  echo '```'
  echo "**Response**:"
  echo '```'
  echo "$RESPONSE"
  echo '```'
  echo "**Logs Used**:"
  echo '```' 
  echo "$LOG_REFERENCES"
  echo '```'
  echo ""
} > "$SUMMARY_FILE"

# === 8. Optional: Raw list of logs for programmatic use ===
printf "%s\n" "${FILES[@]}" > "$LOG_LIST_FILE"

echo -e "\n📄 Appended to: \033[1;33m$SUMMARY_FILE\033[0m"
