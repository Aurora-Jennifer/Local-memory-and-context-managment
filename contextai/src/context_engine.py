#!/usr/bin/env python3

import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from db_handler_llm import get_project_db_path, ensure_logs_schema, validate_or_patch_schema, EXPECTED_LOGS_SCHEMA
from context_retriever import get_best_context
import os
import subprocess
import yaml
import time
from logger_custom import setup_logger

logger = setup_logger("context_engine") # logger for the context engine

def generate_response(prompt: str, model_path:str, model_args:list) -> str:
    start_time = time.time()
    try:
        result = subprocess.run([model_path, *model_args, "-p", prompt], capture_output=True, text=True)
        latency = time.time() - start_time
        return result.stdout.strip(), latency
    except Exception as e:
        logger.error("Error generating response: %s", e, exc_info=True)
        return None, None


def load_model_config(alias:str) -> dict:
    config_path = Path.home() / ".contextai" / "config" / "models.yaml"
    with open(config_path, "r") as f:
        models = yaml.safe_load(f)
    model_entry = models.get(alias)
    if not model_entry:
        logger.error("No model config found for alias: %s", alias)
        logger.info("Available models:")
        for key, value in models.items():
            logger.info("  - %s: %s", key, value['model'])
        return None, None, None

    return model_entry["path"], model_entry["args"].split(), model_entry["model"]


def auto_tag(prompt:str) -> str:
    keywords = ["memory", "summarize", "plot", "config","ai", "ranking", "context"]
    for kw in keywords:
        if kw in prompt.lower():
            return kw
    return "misc"
    
def summarize_logs(conn, project, limit=5, tag=None):
    cursor = conn.cursor()
    query = f"""
        SELECT prompt, response FROM logs
        WHERE project = ?
        {f"AND tags LIKE?" if tag else ""}
        ORDER BY timestamp DESC
        LIMIT ?
    """
    params = [project, f"%{tag}%" if tag else None, limit]
    cursor.execute(query, [p for p in params if p is not None])
    rows = cursor.fetchall()
    

    combined = "\n\n".join([f"Prompt: {p}\nResponse: {r}" for p, r in rows])
    return combined

def insert_log(conn, project, prompt, response, model, tag, file_name, category="misc"):
    now = datetime.now().isoformat()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (
            timestamp, project, prompt, response,
            model, tags, source_file, category
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now, project, prompt, response, model, tag, file_name, category))
    conn.commit()
    
def main():
    parser = argparse.ArgumentParser(description="Context-aware project prompt handler")
    parser.add_argument("project", help="Project name")
    parser.add_argument("prompt", nargs="?", help="Prompt for the LLM", default=None)
    parser.add_argument("--model", default="@wiz", help="Model alias")
    parser.add_argument("--tag", default=None, help="Optional tag filter for context")
    parser.add_argument("--limit", type=int, default=3, help="Number of past logs to recall")
    parser.add_argument("--auto", action="store_true", help="Auto-recall context")
    parser.add_argument("--raw", action="store_true", help="No context injection")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--model-path", default=None, help="Model path")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    parser.add_argument("--summarize", action="store_true", help="Summarize logs")
    parser.add_argument("--category", default=None, help="Category for the log")

    args = parser.parse_args()

    model_path, model_args, model_name = load_model_config(args.model)
    if not all([model_path, model_args, model_name]):
        return 

    if not args.prompt:
        try:
            args.prompt = input("📝 Enter your prompt: ").strip()
        except EOFError:
            print("👋 No prompt provided, exiting.")
            return

    db_path = get_project_db_path(args.project)
    conn = sqlite3.connect(db_path)
    ensure_logs_schema(conn)
    validate_or_patch_schema(conn, EXPECTED_LOGS_SCHEMA)

    logger.info("Connected to DB: %s", db_path)
    logger.debug("Prompt before context injection: %s", args.prompt)

    full_prompt = args.prompt
    if args.auto and not args.raw:
        context_rows = get_best_context(conn, args.project, args.tag, args.limit)
        if context_rows:
            context_texts = [row[1] for row in context_rows]  # use `response` field
            full_prompt = "\n\n".join(context_texts) + "\n\n--- NEW PROMPT ---\n\n" +  args.prompt
            logger.info("Injected context from top %s logs.", len(context_rows))

    logger.debug("Full Prompt:\n%s", full_prompt)

    if args.list_models:
        logger.info("Available models:")
        for alias in ["@ds", "@mistral", "@ds33", "@wiz"]:
            model_path, model_args, model_name = load_model_config(alias)
            if model_path:
                logger.info("  - %s → %s", alias, model_name)
                logger.info("    Path: %s", model_path)
                logger.info("    Args: %s", ' '.join(model_args))
            else:
                logger.info("  - %s → ❌ Not found", alias)
        return

    if args.summarize:
        combined = summarize_logs(conn, args.project, args.limit, args.tag)
        summary_prompt = f"Summarize these past instructions:\n\n{combined}"
        summary = generate_response(summary_prompt, model_path, model_args)
        logger.info("Summary:\n%s", summary)
        return
    
    
    
    if args.model_path:
        model_path = args.model_path
        logger.info("Overriding model path with: %s", model_path)

    if args.debug:
        logger.info("Model path: %s", model_path)
        logger.info("Model args: %s", model_args)
        logger.info("Model name: %s", model_name)

    if not Path(model_path).exists():
        logger.error("Model path does not exist: %s", model_path)
        return

    logger.info("Loading model: %s %s %s", model_name, model_path, model_args)

    try:    
        response, latency = generate_response(full_prompt, model_path, model_args)
    except Exception as e:
        logger.error("Error generating response: %s", e, exc_info=True)
        return

    logger.info("Model loaded in %.2f seconds", latency)

    tag = args.tag or auto_tag(args.prompt)
    category = args.category or "misc"
    file_name = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    logger.info("Tag: %s | Category: %s", tag, category)

    insert_log(conn, args.project, args.prompt, response, args.model, tag, file_name, category)
    logger.info("Response:\n%s", response)
    logger.info("Latency: %.2f seconds", latency)

    conn.close()

if __name__ == "__main__":
    main()
