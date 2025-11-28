#!/bin/zsh

echo "🌸 LLM Shell Ready – Context-aware AI CLI"
echo "Commands:"
echo "  📥  context    – Ask a question (uses context_engine)"
echo "  🔁  reinforce  – Score decay + ranking"
echo "  📊  top        – Show top logs (by project)"
echo "  🧠  project    – Old style interaction (project_llm.sh)"
echo "  🔍  recall     – Browse past interactions"
echo "  📝  @recall    – Summarize across logs"
echo "  ❌  exit       – Quit"

while true; do
  echo -n "LLM> "
  read cmd

  case "$cmd" in
    context)
      echo -n "📁 Project: "
      read PROJ
      echo -n "📝 Prompt: "
      read PROMPT
      python3 ~/.contextai/src/context_engine.py "$PROJ" "$PROMPT" --auto
      ;;

    reinforce)
      echo -n "📁 Project to reinforce: "
      read PROJ
      python3 ~/.contextai/src/score_reinforcement.py "$PROJ"
      ;;

    top)
      echo -n "📁 Project: "
      read PROJ
      python3 -c "
from db_handler_llm import get_project_db_path
import sqlite3
db = sqlite3.connect(get_project_db_path('$PROJ'))
for row in db.execute('SELECT prompt, effective_score FROM logs ORDER BY effective_score DESC LIMIT 5'):
    print(f'{row[1]:.2f} :: {row[0][:80]}')
"
      ;;

    project)
      ~/.contextai/src/project_llm.sh
      ;;

    recall)
      ~/.contextai/src/recall.sh
      ;;

    @recall*)
      ARGS="${cmd#@recall }"
      ~/.contextai/src/recall_with_context.sh $ARGS
      ;;

    exit|quit)
      echo "👋 Later, Caramel."
      break
      ;;

    "")
      continue
      ;;

    *)
      echo "❓ Unknown command: $cmd"
      ;;
  esac

  echo ""
done
