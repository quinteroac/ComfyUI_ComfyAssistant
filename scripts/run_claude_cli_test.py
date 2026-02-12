#!/usr/bin/env python3
"""Run the claude_code CLI command by hand to see stdout/stderr/exit code.
Usage: from project root, python scripts/run_claude_cli_test.py
"""
import json
import os
import subprocess
import sys

# Project root = parent of scripts/
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(project_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Load .env manually (avoid dependency on dotenv when run outside ComfyUI)
env_path = os.path.join(project_dir, ".env")
if os.path.isfile(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1].replace('\\"', '"')
                elif v.startswith("'") and v.endswith("'"):
                    v = v[1:-1].replace("\\'", "'")
                if k and k not in os.environ:
                    os.environ[k] = v

from tools_definitions import TOOLS

# Minimal schema we expect from the CLI (same as _cli_response_schema in __init__.py)
def cli_response_schema():
    return {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Assistant user-facing reply."},
            "tool_calls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "input_json": {"type": "string"},
                    },
                    "required": ["name", "input_json"],
                    "additionalProperties": False,
                },
                "default": [],
            },
        },
        "required": ["text", "tool_calls"],
        "additionalProperties": False,
    }


def cli_tool_specs():
    specs = []
    for tool in TOOLS:
        if not isinstance(tool, dict):
            continue
        function = tool.get("function")
        if not isinstance(function, dict):
            continue
        name = function.get("name")
        if not name:
            continue
        specs.append({
            "name": name,
            "description": function.get("description", ""),
            "parameters": function.get("parameters", {"type": "object"}),
        })
    return specs


def build_prompt():
    tools_json = json.dumps(cli_tool_specs(), ensure_ascii=False)
    transcript = "[USER]\nsaludos lovecraftiano"
    return (
        "You are ComfyUI Assistant backend provider adapter.\n"
        "Decide whether to answer normally or call tools.\n"
        "Return JSON only with this exact shape:\n"
        '{ "text": string, "tool_calls": [{"name": string, "input_json": string}] }\n'
        "Rules:\n"
        "- If tools are needed, add one or more tool_calls.\n"
        "- If tool_calls is non-empty, keep text brief or empty.\n"
        "- Use only tool names from the provided tool list.\n\n"
        f"Available tools:\n{tools_json}\n\n"
        f"Conversation transcript:\n{transcript}\n"
    )


def main():
    cmd_name = os.environ.get("CLAUDE_CODE_COMMAND", "claude")
    model = os.environ.get("CLAUDE_CODE_MODEL", "")
    prompt = build_prompt()
    schema_json = json.dumps(cli_response_schema(), ensure_ascii=False)

    cmd = [cmd_name, "-p", prompt, "--output-format", "json", "--json-schema", schema_json]
    if model:
        cmd.extend(["--model", model])

    print("Command (first 4 args):", cmd[:4], "...")
    print("Running (timeout 90s)...")
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90,
            cwd=project_dir,
        )
    except subprocess.TimeoutExpired:
        print("TIMEOUT after 90s")
        return 1
    except FileNotFoundError as e:
        print("ERROR: Command not found:", e)
        return 1
    except Exception as e:
        print("ERROR:", type(e).__name__, e)
        return 1

    print("returncode:", r.returncode)
    print("stdout length:", len(r.stdout or ""))
    print("stderr length:", len(r.stderr or ""))
    if r.stdout:
        print("--- stdout (first 1200 chars) ---")
        print((r.stdout[:1200] + "..." if len(r.stdout) > 1200 else r.stdout))
    if r.stderr:
        print("--- stderr ---")
        print(r.stderr)
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
