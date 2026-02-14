"""Runtime provider selection and connection testing."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from typing import Any

from aiohttp import ClientSession

import provider_store

_VALID_PROVIDERS = {'openai', 'anthropic', 'claude_code', 'codex', 'gemini_cli'}

_DEFAULTS = {
    'openai': {
        'base_url': 'https://api.openai.com/v1',
        'model': 'gpt-4o'
    },
    'anthropic': {
        'base_url': 'https://api.anthropic.com',
        'model': 'claude-sonnet-4-5',
        'max_tokens': 4096
    },
    'claude_code': {
        'cli_command': 'claude',
        'timeout_seconds': 180
    },
    'codex': {
        'cli_command': 'codex',
        'timeout_seconds': 180
    },
    'gemini_cli': {
        'cli_command': 'gemini',
        'timeout_seconds': 180
    }
}

_ACTIVE_PROVIDER: dict[str, Any] | None = None


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _build_env_fallback(provider_type: str) -> dict[str, Any]:
    if provider_type == 'openai':
        return {
            'provider_type': 'openai',
            'name': 'openai-env',
            'display_name': 'OpenAI (.env)',
            'api_key': os.environ.get('OPENAI_API_KEY', ''),
            'base_url': (os.environ.get('OPENAI_API_BASE_URL', _DEFAULTS['openai']['base_url']) or _DEFAULTS['openai']['base_url']).rstrip('/'),
            'model': os.environ.get('OPENAI_MODEL', 'gpt-4o-mini') or 'gpt-4o-mini',
            'is_active': 1
        }
    if provider_type == 'anthropic':
        return {
            'provider_type': 'anthropic',
            'name': 'anthropic-env',
            'display_name': 'Anthropic (.env)',
            'api_key': os.environ.get('ANTHROPIC_API_KEY', ''),
            'base_url': (os.environ.get('ANTHROPIC_BASE_URL', _DEFAULTS['anthropic']['base_url']) or _DEFAULTS['anthropic']['base_url']).rstrip('/'),
            'model': os.environ.get('ANTHROPIC_MODEL', _DEFAULTS['anthropic']['model']) or _DEFAULTS['anthropic']['model'],
            'max_tokens': _env_int('ANTHROPIC_MAX_TOKENS', 4096),
            'is_active': 1
        }
    if provider_type == 'claude_code':
        return {
            'provider_type': 'claude_code',
            'name': 'claude_code-env',
            'display_name': 'Claude Code (.env)',
            'cli_command': os.environ.get('CLAUDE_CODE_COMMAND', 'claude') or 'claude',
            'cli_model': os.environ.get('CLAUDE_CODE_MODEL', ''),
            'timeout_seconds': _env_int('CLI_PROVIDER_TIMEOUT_SECONDS', 180),
            'is_active': 1
        }
    if provider_type == 'codex':
        return {
            'provider_type': 'codex',
            'name': 'codex-env',
            'display_name': 'Codex (.env)',
            'cli_command': os.environ.get('CODEX_COMMAND', 'codex') or 'codex',
            'cli_model': os.environ.get('CODEX_MODEL', ''),
            'timeout_seconds': _env_int('CLI_PROVIDER_TIMEOUT_SECONDS', 180),
            'is_active': 1
        }
    return {
        'provider_type': 'gemini_cli',
        'name': 'gemini_cli-env',
        'display_name': 'Gemini CLI (.env)',
        'cli_command': os.environ.get('GEMINI_CLI_COMMAND', 'gemini') or 'gemini',
        'cli_model': os.environ.get('GEMINI_CLI_MODEL', ''),
        'timeout_seconds': _env_int('CLI_PROVIDER_TIMEOUT_SECONDS', 180),
        'is_active': 1
    }


def _selected_provider_from_env() -> str:
    explicit = (os.environ.get('LLM_PROVIDER', '') or '').strip().lower()
    if explicit in _VALID_PROVIDERS:
        return explicit
    if os.environ.get('OPENAI_API_KEY'):
        return 'openai'
    if os.environ.get('ANTHROPIC_API_KEY'):
        return 'anthropic'
    return 'openai'


def _materialize_provider(raw: dict[str, Any] | None) -> dict[str, Any]:
    if not raw:
        return _build_env_fallback(_selected_provider_from_env())

    provider = dict(raw)
    provider_type = provider.get('provider_type')
    if provider_type not in _VALID_PROVIDERS:
        return _build_env_fallback(_selected_provider_from_env())

    if provider.get('api_key'):
        try:
            provider['api_key'] = provider_store.decode_api_key(provider['api_key'])
        except Exception:
            provider['api_key'] = ''

    defaults = _DEFAULTS.get(provider_type, {})
    if provider_type in {'openai', 'anthropic'}:
        provider['base_url'] = (provider.get('base_url') or defaults.get('base_url') or '').rstrip('/')
        provider['model'] = provider.get('model') or defaults.get('model')
        if provider_type == 'anthropic':
            try:
                provider['max_tokens'] = int(provider.get('max_tokens') or defaults.get('max_tokens') or 4096)
            except (TypeError, ValueError):
                provider['max_tokens'] = 4096
    else:
        provider['cli_command'] = provider.get('cli_command') or defaults.get('cli_command')
        provider['cli_model'] = provider.get('cli_model') or ''
        try:
            provider['timeout_seconds'] = int(provider.get('timeout_seconds') or defaults.get('timeout_seconds') or 180)
        except (TypeError, ValueError):
            provider['timeout_seconds'] = 180

    return provider


def get_current_provider_config() -> dict[str, Any]:
    """Return active provider config from DB, fallback to environment."""
    global _ACTIVE_PROVIDER
    if _ACTIVE_PROVIDER is not None:
        return dict(_ACTIVE_PROVIDER)

    provider_store.init_providers_db()
    active = provider_store.get_active_provider()
    _ACTIVE_PROVIDER = _materialize_provider(active)
    return dict(_ACTIVE_PROVIDER)


def initialize_provider_from_db() -> str:
    """Initialize in-memory active provider and return provider_type."""
    config = get_current_provider_config()
    return str(config.get('provider_type', 'openai'))


def reload_provider() -> bool:
    """Reload active provider from DB (or env fallback)."""
    global _ACTIVE_PROVIDER
    try:
        provider_store.init_providers_db()
        active = provider_store.get_active_provider()
        _ACTIVE_PROVIDER = _materialize_provider(active)
        return True
    except Exception:
        _ACTIVE_PROVIDER = _build_env_fallback(_selected_provider_from_env())
        return False


async def _run_cli_command(cmd: list[str], timeout_seconds: int) -> tuple[int, str, str]:
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return 124, '', f'Timed out after {timeout_seconds}s'

    return (
        process.returncode or 0,
        stdout.decode('utf-8', errors='replace'),
        stderr.decode('utf-8', errors='replace'),
    )


async def _test_openai(config: dict[str, Any]) -> tuple[bool, str]:
    api_key = str(config.get('api_key') or '')
    if not api_key:
        return False, 'Missing API key'
    base_url = str(config.get('base_url') or _DEFAULTS['openai']['base_url']).rstrip('/')
    url = f'{base_url}/models'
    headers = {'Authorization': f'Bearer {api_key}'}

    timeout = 10
    async with ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=timeout) as resp:
                text = await resp.text()
                if 200 <= resp.status < 300:
                    return True, 'OpenAI connection successful'
                return False, f'HTTP {resp.status}: {text[:240]}'
        except Exception as exc:
            return False, str(exc)


async def _test_anthropic(config: dict[str, Any]) -> tuple[bool, str]:
    api_key = str(config.get('api_key') or '')
    if not api_key:
        return False, 'Missing API key'
    base_url = str(config.get('base_url') or _DEFAULTS['anthropic']['base_url']).rstrip('/')
    url = f'{base_url}/v1/models'
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
    }

    timeout = 10
    async with ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=timeout) as resp:
                text = await resp.text()
                if 200 <= resp.status < 300:
                    return True, 'Anthropic connection successful'
                return False, f'HTTP {resp.status}: {text[:240]}'
        except Exception as exc:
            return False, str(exc)


async def _test_cli(config: dict[str, Any]) -> tuple[bool, str]:
    command = str(config.get('cli_command') or '').strip()
    if not command:
        return False, 'Missing cli_command'

    executable = command
    if os.path.sep not in command:
        resolved = shutil.which(command)
        if not resolved:
            return False, f'CLI command not found in PATH: {command}'
        executable = resolved

    if not (os.path.isfile(executable) and os.access(executable, os.X_OK)):
        return False, f'CLI command is not executable: {executable}'

    timeout_seconds = int(config.get('timeout_seconds') or 10)
    rc, stdout, stderr = await _run_cli_command([executable, '--version'], timeout_seconds)
    if rc != 0:
        return False, stderr.strip() or stdout.strip() or f'CLI exited with code {rc}'

    output = stdout.strip() or stderr.strip()
    if output:
        return True, output[:200]
    return True, f'CLI available: {executable}'


async def test_provider_connection(name: str) -> tuple[bool, str]:
    """Test provider config by provider name."""
    provider_store.init_providers_db()
    provider = provider_store.get_provider_by_name(name)
    if not provider:
        return False, f"Provider '{name}' not found"

    config = _materialize_provider(provider)
    provider_type = str(config.get('provider_type') or '')

    if provider_type == 'openai':
        return await _test_openai(config)
    if provider_type == 'anthropic':
        return await _test_anthropic(config)
    if provider_type in {'claude_code', 'codex', 'gemini_cli'}:
        return await _test_cli(config)

    return False, f'Unsupported provider type: {provider_type}'


async def test_provider_config(config: dict[str, Any]) -> tuple[bool, str]:
    """Test an unsaved provider config payload."""
    provider_type = str(config.get('provider_type') or '')
    if provider_type == 'openai':
        return await _test_openai(config)
    if provider_type == 'anthropic':
        return await _test_anthropic(config)
    if provider_type in {'claude_code', 'codex', 'gemini_cli'}:
        return await _test_cli(config)
    return False, f'Unsupported provider type: {provider_type}'


def get_provider_debug_view(config: dict[str, Any]) -> dict[str, Any]:
    """Return config with secrets masked for logs/API responses."""
    out = dict(config)
    key = out.get('api_key')
    if isinstance(key, str) and key:
        out['api_key_preview'] = f'{key[:4]}...{key[-4:]}' if len(key) > 8 else '****'
        out.pop('api_key', None)
    return out
