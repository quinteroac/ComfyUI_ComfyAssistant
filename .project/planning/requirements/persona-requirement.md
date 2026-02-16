El objetivo es crear una esquema de personas para el agente, de tal forma que el usuario pueda definir distintas personalidades al agente segun su objetivo, el agente podra adoptar personalidades 
más creativas, técnicas, especializadas o divertidas de acuerdo a los objetivos del usuario. Estas personalidades estarn ligadas a un provider y modelo especifico de tal manera que el modelo detrás encaje más con
la personalidad definida, así por ejemplo ciertas personalidades serán más efectivas con modelos de frontera, mientras que otras serán más efectivas con modelos más de entretenimiento.

### Diseño

#### Estructura

Cada persona constara de su propio archivo SOUL.md que vivira dentro de la carpeta user_context/personas/[persona_name]/


El archivo SOUL.md deberá llevar el siguiente formato yaml:

---
Name: Nombre de la persona
Description: Breve descripcion de la persona.
Provider: Proveedor al que corresponde la persona (debe ser un proveedor previamente configurado)
---

Descripcion de la personalidad de la persona.

#### Flujo de creacion

Se deberá crear un skill de sistema para ayudar a crear a las personas, el flujo funcionara como un asistente que ira haciendo preguntas:

Usuario: Quiero crear una persona
Asistente: Excelente! Cual será el nombre de la persona
Usuario: Responde nombre
Asistente: Puedes relatarme la personalidad de tu persona? platicame acerca de ella, como deseas que se comporte, hablame de su pasado, deseas que sea especialista en alguna tarea determinada?  
Usuario: Responde con lo solicitado por el asistente.
Asistente Que proveedor deseas que sea el encargado de representar a tu persona [muestra un listado de proveedores configurados mediante providers list]
Usuario: elige el proveedor 
Asistente: crea la estructura de la persona y le indica al usuario que se realizo correctamente la creacion.

#### Flujo de uso de la persona

El usuario podra cambiar de persona durante una conversacion usando el comando slash /persona [nombre_persona] la persona tendra acceso al historial de la conversacion si es que lo hubiera.

#### Borrado de la persona

El usuario podra borrar a la persona usando el comando /persona del [nombre_persona]

