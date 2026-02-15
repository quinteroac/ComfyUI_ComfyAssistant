# Temp Files for Workflows — Implementation Summary

## Overview

Archivos temporales en `user_context/temp/` para workflows JSON y prompts CLI, evitando límites ARG_MAX en CLIs y optimizando payloads a APIs.

## Implemented

### 1. `temp_file_store.py`
- `write_temp_file(content, prefix, suffix)` — escribe a user_context/temp/{prefix}_{uuid}{suffix}
- `read_temp_file(path_or_id)` — lee contenido; dict para .json, str para .txt
- `delete_temp_file(path_or_id)` — borra archivo
- `get_temp_file_path(path_or_id)` — path absoluto
- `cleanup_old_temp_files(max_age_hours)` — borra archivos antiguos
- `is_safe_file_id(id)` — valida nombres de archivo (sin path traversal)

### 2. API Endpoints
- `POST /api/temp/file` — body JSON con `content` (opcional `prefix`); devuelve `{id, path}`
- `GET /api/temp/file?id=xxx` — devuelve contenido del archivo
- `DELETE /api/temp/file?id=xxx` — borra archivo

### 3. Post-proceso de tool results (`message_transforms.py`)
- `substitute_workflow_tool_results_with_temp_refs(messages)` — detecta `fullWorkflow`, `apiWorkflow`, `workflow` en tool results
- Siempre (sin umbral): escribe workflow en temp, sustituye por `{_tempFile, summary, fullWorkflowRef}`

### 4. `applyWorkflowJson` con `workflowPath`
- Backend: `workflowPath` opcional en tools_definitions.py
- Frontend: schema Zod con `workflowPath?: string`; si se proporciona, fetch `/api/temp/file?id=...` y aplica JSON

### 5. CLI prompt vía stdin
- **claude_code**: `-p -` con stdin (prompt_bytes); escribe también a user_context/temp
- **gemini_cli**: `-p -` con stdin; escribe a temp
- **codex**: mantiene prompt como arg (no soporta stdin para prompt); escribe a temp para persistencia

### 6. Cleanup
- En arranque (`_auto_scan_environment`): `cleanup_old_temp_files(max_age_hours=24)`

### 7. Documentación
- `.agents/project-context.md` — user_context/temp/
- `.agents/skills/system-and-user-context/SKILL.md` — temp/ en layout
- `system_context/skills/02_tool_guidelines/SKILL.md` — workflowPath para applyWorkflowJson
- `system_context/skills/05_workflow_execution/SKILL.md` — workflowPath cuando viene de getWorkflowInfo

## Branch

`feature/temp-files-workflow`
