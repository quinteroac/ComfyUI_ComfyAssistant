# Refactorización de __init__.py: Separación de Responsabilidades

## Context

El archivo `__init__.py` ha crecido a **2,591 líneas** con **72 funciones** mezclando 9 responsabilidades distintas. El handler principal `chat_api_handler()` solo ocupa 1,032 líneas (40% del archivo). Esta situación crea varios problemas:

1. **Mantenibilidad**: Difícil navegar y entender el código
2. **Testing**: Imposible testear componentes de forma aislada
3. **Conflictos Git**: Alto riesgo cuando múltiples features tocan el mismo archivo
4. **Escalabilidad**: Agregar nuevos providers o features aumenta la complejidad exponencialmente
5. **Onboarding**: Desarrolladores (humanos o AI) tardan mucho en entender el sistema

**Objetivo**: Refactorizar `__init__.py` en módulos especializados siguiendo los patrones existentes del proyecto (`provider_manager.py`, `environment_scanner.py`, `api_handlers.py`), manteniendo 100% de compatibilidad hacia atrás.

---

## Estrategia: 9 Fases Incrementales

La refactorización se realizará en **9 fases incrementales** de menor a mayor riesgo, con **testing y commit después de cada fase**.

### Principios Guía

1. **Compatibilidad total**: Ningún cambio en la API externa
2. **Fases pequeñas**: Cambios incrementales testeables
3. **Test → Commit → Next**: Cada fase se prueba completamente antes de commit
4. **Patrones existentes**: Seguir convenciones de módulos actuales
5. **Rollback fácil**: Git history limpio para revertir si es necesario

---

## Workflow: Test → Commit → Next

**Después de cada fase**:

1. ✅ Implementar fase completa
2. ✅ Reiniciar ComfyUI y verificar sin errores
3. ✅ Ejecutar checklist de testing
4. ✅ **Si pasa TODO → Commit**
5. ✅ **Si falla → Fix y volver a probar (NO commit)**
6. ✅ Continuar con siguiente fase

**1 commit por fase completada** = 9 commits totales

---

## Fase 1: Extraer Transformaciones de Mensajes (2 días)
**Riesgo**: 🟢 BAJO | **Valor**: 🟢 ALTO

**Nuevo módulo**: `message_transforms.py` (~450 líneas)

**14 funciones a extraer** (puras, sin estado):
- `_stringify_message_content()`
- `_openai_messages_to_cli_prompt()`
- `_cli_tool_specs()`
- `_cli_response_schema()`
- `_build_cli_tool_prompt()`
- `_extract_json_from_text()`
- `_parse_cli_tool_calls()`
- `_normalize_cli_structured_response()`
- `_openai_tools_to_anthropic()`
- `_normalize_tool_result_content()`
- `_merge_adjacent_anthropic_messages()`
- `_openai_messages_to_anthropic()`
- `_ui_messages_to_openai()`
- `_extract_content()`

**Patrón**: Ver `provider_manager.py`

**Checklist antes de commit**:
- [ ] ComfyUI inicia sin errores
- [ ] Extension carga correctamente
- [ ] Chat responde "Hello"
- [ ] Tool call: "add a KSampler node"
- [ ] OpenAI provider funciona
- [ ] Anthropic provider funciona (si configurado)

---

## Fase 2: Extraer Gestión de Contexto (2 días)
**Riesgo**: 🟢 BAJO | **Valor**: 🟢 ALTO

**Nuevo módulo**: `context_management.py` (~600 líneas)

**12 funciones + 4 constantes** a extraer

**Checklist antes de commit**:
- [ ] Mensaje largo (>12000 chars) se trunca
- [ ] Conversación >24 mensajes hace trim
- [ ] Sin errores en logs

---

## Fase 3: Extraer Streaming de Providers (3 días)
**Riesgo**: 🟡 MEDIO | **Valor**: 🟢 ALTO

**Nuevo módulo**: `provider_streaming.py` (~900 líneas)

**5 async generators + helpers**

**Checklist antes de commit**:
- [ ] OpenAI streaming funciona
- [ ] Thinking tags se parsean
- [ ] Anthropic streaming funciona
- [ ] CLI providers parsean correctamente

---

## Fases 4-9: Ver plan completo arriba

---

## Commits Esperados

```
feature/refactor-init-py
├── commit 1: "feat(refactor): Phase 1 - message_transforms"
├── commit 2: "feat(refactor): Phase 2 - context_management"
├── commit 3: "feat(refactor): Phase 3 - provider_streaming"
├── commit 4: "feat(refactor): Phase 4 - cli_providers"
├── commit 5: "feat(refactor): Phase 5 - sse_streaming"
├── commit 6: "feat(refactor): Phase 6 - slash_commands"
├── commit 7: "feat(refactor): Phase 7 - chat_utilities"
├── commit 8: "feat(refactor): Phase 8 - chat_handler decomposition"
└── commit 9: "docs(refactor): Phase 9 - update conventions"
```

---

**Ver archivo completo para detalles de todas las fases**
