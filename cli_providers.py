"""CLI provider detection and utilities."""

from __future__ import annotations

import logging
import os
import shutil

logger = logging.getLogger("ComfyUI_ComfyAssistant.cli_providers")


def _has_cli_provider_command(provider: str, command: str | None = None) -> bool:
    """Return True when provider CLI binary is available in PATH."""
    commands = {
        "claude_code": os.environ.get("CLAUDE_CODE_COMMAND", "claude"),
        "codex": os.environ.get("CODEX_COMMAND", "codex"),
        "gemini_cli": os.environ.get("GEMINI_CLI_COMMAND", "gemini"),
    }
    selected_command = command or commands.get(provider)
    return bool(selected_command) and shutil.which(selected_command) is not None
