"""Tests for persona slash-command listing behavior."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import user_context_store
from slash_commands import handle_persona_command


def _write_persona(root: Path, slug: str, name: str, description: str, provider: str) -> None:
    persona_dir = root / "personas" / slug
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "SOUL.md").write_text(
        "\n".join(
            [
                "---",
                f"Name: {name}",
                f"Description: {description}",
                f"Provider: {provider}",
                "---",
                "",
                description
            ]
        ),
        encoding="utf-8"
    )


class PersonaCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        user_context_store.set_user_context_path(self._tempdir.name)
        user_context_store.ensure_user_context_dirs()

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_persona_list_without_personas_returns_empty_state(self) -> None:
        result = handle_persona_command(command_text="/persona", openai_messages=[])

        self.assertIsNotNone(result)
        self.assertIn("No personas are available yet", str(result.get("text")))

    def test_persona_list_includes_personas_and_active_marker(self) -> None:
        root = Path(user_context_store.ensure_user_context_dirs())
        _write_persona(
            root=root,
            slug="alpha-agent",
            name="Alpha Agent",
            description="Fast analytical helper",
            provider="openai-main"
        )
        _write_persona(
            root=root,
            slug="beta-guide",
            name="Beta Guide",
            description="Explains decisions and tradeoffs clearly",
            provider="anthropic-main"
        )
        user_context_store.add_or_update_preference("active_persona", "beta-guide")

        result = handle_persona_command(command_text="/persona", openai_messages=[])

        self.assertIsNotNone(result)
        text = str(result.get("text"))
        self.assertIn("**Available Personas**", text)
        self.assertIn("**Alpha Agent** (`alpha-agent`)", text)
        self.assertIn("✓ **Beta Guide** (`beta-guide`)", text)

    def test_persona_list_subcommand_is_supported(self) -> None:
        root = Path(user_context_store.ensure_user_context_dirs())
        _write_persona(
            root=root,
            slug="gamma-builder",
            name="Gamma Builder",
            description="Builds practical workflows quickly",
            provider="openai-main"
        )

        result = handle_persona_command(command_text="/persona list", openai_messages=[])

        self.assertIsNotNone(result)
        self.assertIn("**Gamma Builder** (`gamma-builder`)", str(result.get("text")))


if __name__ == "__main__":
    unittest.main()
