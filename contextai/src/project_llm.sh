#!/bin/bash

# === 1. Prompt user for project directory ===
read -e -p "📁 Enter project directory: " CTX_DIR
CTX_DIR="${CTX_DIR/#\~/$HOME}"  # expand ~ to full path

# === 2. Check if project directory exists ===
if [[ ! -d "$CTX_DIR" ]]; then
  echo "❌ Project directory does not exist: $CTX_DIR"
  exit 1
fi

# === 3. Prompt user for file name or keyword ===
read -e -p "🔎 File name or keyword to focus on: " FILE_TARGET

# === 4. Prompt for model alias (default to @ds) ===
read -e -p "🤖 Which model to use? (default: @ds): " MODEL
MODEL=${MODEL:-@ds}

# === 5. Optional cached history ===
CACHE="$CTX_DIR/.context_history.log"

# === 6. Build context from file or keyword ===
if [[ -f "$CTX_DIR/$FILE_TARGET" ]]; then
  CONTEXT=$(sed -n '/^class /,/^$/p;/^def /,/^$/p' "$CTX_DIR/$FILE_TARGET")
else
  CONTEXT=$(grep -ir "$FILE_TARGET" "$CTX_DIR" | head -n 40)
fi

# === 7. Get user prompt ===
echo "📝 Enter your prompt (end with Ctrl+D):"
PROMPT=$(</dev/stdin)

# === 8. Assemble full input ===
INPUT="Project path: $CTX_DIR\n\nContext from '$FILE_TARGET':\n$CONTEXT\n\nRecent cache:\n$(tail -n 20 "$CACHE" 2>/dev/null)\n\nUser prompt:\n$PROMPT"

# === 9. Run model ===
eval $MODEL -p "\"$INPUT\""

# === 10. Save interaction to cache ===
echo -e "[Q] $PROMPT\n[A] <<< response omitted >>>\n" >> "$CACHE"

# === 11. Save full context to log file ===
# === 12.  Ask for optional project tag ===
read -e -p "🏷️ Project tag (e.g. blacknode, calc): " TAG
TAG=${TAG:-general}

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
DATESTAMP=$(date +"%Y-%m-%d")
LOGDIR="$CTX_DIR/context_logs"
INDEX="$CTX_DIR/prompt_index_$DATESTAMP.log"
mkdir -p "$LOGDIR"

FILENAME="$LOGDIR/${TIMESTAMP}_${TAG}@${MODEL#@}.txt"

echo -e "🕒 $TIMESTAMP\n📁 $CTX_DIR\n🏷️ Project: $TAG\n🔎 File/Keyword: $FILE_TARGET\n🤖 Model: $MODEL\n\n===== PROMPT =====\n$PROMPT\n\n===== CONTEXT =====\n$CONTEXT" > "$FILENAME"
echo -e "\n===== RESPONSE =====\n(response omitted)" >> "$FILENAME"

echo -e "[$(date +"%H:%M")] $TAG: $FILE_TARGET → $(basename "$FILENAME")" >> "$INDEX"

