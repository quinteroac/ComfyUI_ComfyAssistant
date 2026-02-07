# Agent Prompts System - Resumen Ejecutivo

## ¿Qué es esto?

El sistema de **Agent Prompts** son las instrucciones que le damos al LLM (Groq) para que sepa cómo comportarse como asistente de ComfyUI y cómo usar las herramientas (tools) de manera efectiva.

## Archivos Creados

### 1. `agent_prompts.py` ⭐
**Propósito**: Define la personalidad y comportamiento del agente

**Contiene:**
- `SYSTEM_PROMPT`: Instrucciones principales del agente
- `TOOL_USAGE_GUIDELINES`: Cuándo y cómo usar cada tool
- `NODE_TYPE_REFERENCE`: Tipos de nodos comunes de ComfyUI
- `TOOL_EXAMPLES`: Ejemplos de uso (few-shot learning)
- Funciones helper: `get_system_message()`, `get_minimal_system_message()`, etc.

**Características:**
- 6,696 caracteres de instrucciones
- Cobertura completa de las 4 tools
- Guías de estilo de comunicación
- Manejo de errores
- Conocimiento de ComfyUI

### 2. `AGENT_PROMPTS_GUIDE.md`
**Propósito**: Guía completa de customización

**Secciones:**
- Cómo modificar la personalidad del agente
- Ajustar cuándo se usan las tools
- Agregar tipos de nodos custom
- Optimización de tokens
- Testing y debugging
- Ejemplos de customización

### 3. `AGENT_TESTING_EXAMPLES.md`
**Propósito**: Casos de prueba para validar el agente

**Incluye:**
- 20+ casos de prueba organizados por categoría
- Criterios de evaluación (correctness, clarity, helpfulness)
- Metodología de testing manual y automatizado
- Sistema de scoring (0-10 puntos)
- Templates para reportar issues

### 4. Integración en `__init__.py`
**Cambios:**
```python
from agent_prompts import get_system_message

# Se inyecta automáticamente en cada request
openai_messages.insert(0, get_system_message())
```

## Cómo Funciona

```
Usuario: "Add a KSampler"
    ↓
Frontend envía mensaje
    ↓
Backend agrega SYSTEM_PROMPT ← 🆕 AQUÍ
    ↓
Llama a Groq con:
  - System message (instrucciones)
  - User message
  - Tools disponibles
    ↓
Groq entiende QUÉ hacer y CUÁNDO
    ↓
Responde usando tools apropiadamente
```

## Qué Enseñan los Prompts

### 1. Cuándo Usar Cada Tool

**getWorkflowInfo:**
- Usuario pregunta sobre el workflow actual
- Antes de hacer cambios (para verificar estado)
- Cuando necesita verificar que nodos existen

**addNode:**
- Usuario pide explícitamente agregar un nodo
- Cuando describe funcionalidad que requiere un nodo específico
- Al construir workflows paso a paso

**removeNode:**
- Usuario pide borrar o remover un nodo
- Limpieza o reemplazo de nodos

**connectNodes:**
- Usuario pide conectar nodos específicos
- Al construir conexiones en un workflow
- Después de agregar nodos relacionados

### 2. Best Practices

- Pedir clarificación si algo es ambiguo
- Revisar estado del workflow antes de modificar
- Explicar qué se va a hacer antes de hacerlo
- Confirmar acciones exitosas
- Manejar errores con gracia
- Sugerir siguientes pasos

### 3. Estilo de Comunicación

- Claro y conciso
- Usar términos técnicos correctamente
- Proveer contexto sobre conceptos de ComfyUI
- Ser proactivo sugiriendo mejoras
- Confirmar antes de acciones destructivas

### 4. Conocimiento de ComfyUI

El agente conoce:
- Tipos de nodos comunes (KSampler, CheckpointLoader, etc.)
- Inputs/outputs típicos
- Workflows comunes (txt2img, img2img, upscaling)
- Mejores prácticas de construcción de workflows

## Personalización Rápida

### Cambiar Personalidad

Edita `SYSTEM_PROMPT` en `agent_prompts.py`:

```python
SYSTEM_PROMPT = """You are ComfyUI Assistant, an expert...

## Communication Style
- Be concise and technical  # Tu estilo aquí
- Assume expert user
- Skip explanations
"""
```

### Agregar Nodos Custom

Extiende `NODE_TYPE_REFERENCE`:

```python
NODE_TYPE_REFERENCE += """
### My Custom Nodes
- **MyAwesomeNode**: Does something cool (inputs: X, outputs: Y)
"""
```

### Reducir Uso de Tokens

```python
# En __init__.py, cambia:
from agent_prompts import get_minimal_system_message

openai_messages.insert(0, get_minimal_system_message())
```

## Testing

### Test Básico

1. Inicia ComfyUI
2. Abre el chat del assistant
3. Prueba: "Add a KSampler"
4. Verifica que:
   - El agente explica qué va a hacer
   - Usa la tool `addNode`
   - Confirma el éxito
   - Da el ID del nodo

### Tests Avanzados

Ver `AGENT_TESTING_EXAMPLES.md` para 20+ casos de prueba organizados:
- Basic tool usage
- Multi-step operations
- Information gathering
- Error handling
- Edge cases
- Complex workflows

## Ventajas de Este Sistema

1. **Comportamiento Consistente**: El agente siempre sabe cuándo usar tools
2. **Fácil Customización**: Modifica un archivo Python, no código complejo
3. **Documentado**: Guías completas de uso y testing
4. **Educativo**: El agente enseña a users sobre ComfyUI
5. **Robusto**: Manejo de errores y casos edge
6. **Extensible**: Fácil agregar nuevas instrucciones o nodos

## Flujo de Trabajo de Desarrollo

1. **Modificar prompts** en `agent_prompts.py`
2. **Reiniciar ComfyUI** (para recargar módulos Python)
3. **Probar en el chat** con casos de `AGENT_TESTING_EXAMPLES.md`
4. **Iterar** basándose en resultados
5. **Documentar cambios** en el archivo

## Integración con el Resto del Sistema

```
agent_prompts.py (instrucciones)
        ↓
    __init__.py (inyecta prompts)
        ↓
    Groq API (procesa con instrucciones)
        ↓
    tools_definitions.py (declara tools)
        ↓
    ui/src/tools/ (ejecuta tools)
        ↓
    window.app (modifica ComfyUI)
```

## Recursos

- **Customización**: `AGENT_PROMPTS_GUIDE.md`
- **Testing**: `AGENT_TESTING_EXAMPLES.md`
- **Backend**: `BACKEND_TOOLS_IMPLEMENTATION.md`
- **Tools**: `TOOLS_SETUP_GUIDE.md`

## Próximos Pasos

1. ✅ Prompts implementados
2. ✅ Documentación completa
3. ✅ Testing guides creados
4. 🔜 Probar con usuarios reales
5. 🔜 Ajustar basándose en feedback
6. 🔜 Agregar más ejemplos si necesario

## Métricas de Éxito

Para evaluar la efectividad de los prompts:

- **Precisión**: ¿Usa las tools correctas?
- **Timing**: ¿Usa tools en el momento adecuado?
- **Claridad**: ¿Explica lo que hace?
- **Robustez**: ¿Maneja errores bien?
- **UX**: ¿Es agradable interactuar con el agente?

## Notas Importantes

- Los prompts afectan **directamente** el comportamiento del agente
- Cambios requieren **reiniciar ComfyUI**
- System message se envía en **cada request** (impacto en tokens)
- Puedes usar variantes (`minimal`, `with_examples`) según necesidad
- Groq cobra por tokens, así que optimiza el tamaño

## Soporte

Si el agente no se comporta como esperabas:

1. Revisa los prompts en `agent_prompts.py`
2. Verifica que el system message se esté inyectando (logs)
3. Prueba casos específicos de `AGENT_TESTING_EXAMPLES.md`
4. Ajusta las guidelines en `TOOL_USAGE_GUIDELINES`
5. Agrega ejemplos a `TOOL_EXAMPLES` si necesario

## Conclusión

El sistema de Agent Prompts es el "cerebro" que le dice al LLM cómo ser un buen asistente de ComfyUI. Está completamente documentado, es fácil de customizar, y está listo para usar.

**Estado**: ✅ Implementado y funcional  
**Próximo paso**: Probar y ajustar basándose en uso real
