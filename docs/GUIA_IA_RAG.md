# Guía de IA y RAG

## Qué es un LLM

Un modelo de lenguaje grande predice el siguiente texto a partir de una instrucción. En este proyecto el modelo es Qwen 2.5, de 1.5 mil millones de parámetros, cuantizado en Q4. Sirve para clasificar la pregunta, elegir una herramienta y redactar. No es la fuente de las ventas ni del inventario.

## Qué es Ollama

Ollama ejecuta el modelo en la máquina, en `http://127.0.0.1:11434`. La aplicación usa `POST /api/chat` para conversar y llamar herramientas, y `POST /api/embed` para convertir texto en vectores. No hay clave de OpenAI, Gemini ni Claude.

La versión instalada al construir el proyecto es Ollama 0.40.16. El modelo `qwen2.5:1.5b` anuncia la capacidad `tools`. Se comprobó que, con un esquema corto, devuelve `tool_calls` y no solo prosa.

## Qué es Qwen 2.5

Qwen 2.5 es una familia de modelos de Alibaba. La variante de 7B es más capaz, pero ocupa unos 4,7 GB en disco y alrededor de 6 GB al ejecutarse en CPU. En una PC de 8 GB sin tarjeta gráfica, Windows, PostgreSQL y el navegador no dejan ese margen. Por eso el valor por defecto de `OLLAMA_MODEL` es `qwen2.5:1.5b`. Cambiarlo es editar `.env` y tener el modelo descargado en Ollama.

## Qué son los embeddings

Un embedding es una lista de números que representa el significado de un texto. Dos fragmentos parecidos quedan cerca. Aquí los genera `nomic-embed-text`. Su contexto es de 2048 tokens, así que cada fragmento se corta alrededor de 900 caracteres.

## Qué es ChromaDB

ChromaDB guarda esos vectores en `data/chroma_db`, sin un servidor aparte. La colección se llama `erp_knowledge` y usa distancia coseno. El código envía los vectores que produjo Ollama; Chroma no descarga otro modelo.

## Qué es RAG

RAG significa recuperación aumentada. Antes de explicar un procedimiento, el sistema busca los fragmentos de manual más cercanos a la pregunta y se los entrega a Qwen. La respuesta queda atada a esos textos.

RAG no se usa para ventas, stock ni usuarios. Esos datos cambian y viven en PostgreSQL. Mezclarlos en los manuales haría que el asistente contestara con cifras viejas.

## Cómo se indexan los documentos

1. `scripts/index_knowledge.py` llama a `index_knowledge()` en `rag_service.py`.
2. Se leen los Markdown de `data/knowledge/`.
3. Se parten por títulos y, si un bloque es largo, por párrafos.
4. Ollama genera un embedding por fragmento y luego se descarga de memoria.
5. Chroma reemplaza la colección anterior.

Los doce manuales los escribió el desarrollo del proyecto. Ollama no los redactó. Describen pantallas que existen: por ejemplo, crear un usuario en `/admin/users/new` y registrar una venta en `/sales/new`.

También se puede reindexar con `POST /api/assistant/knowledge/index`, solo si el usuario tiene `knowledge.index`.

## Cómo se recupera el contexto

`retrieve()` embebe la pregunta, pide cuatro vecinos y descarta los que tienen distancia coseno mayor que 0,55. Cada fragmento conservado viaja como fuente: título y extracto.

## Cómo se construye la respuesta

Para un "cómo se hace", el orquestador llama la herramienta `consultar_documentacion` y también `buscar_funcionalidad_erp`. Qwen redacta con los fragmentos. Si no hay fragmentos, dice que el manual no cubre esa pregunta. El enlace, si aparece, sale del catálogo y no del texto del modelo.

## Limitaciones

- El modelo de 1.5B puede clasificar mal una pregunta ambigua. Por eso hay una segunda llamada con una sola herramienta y, si no llama la herramienta, no se inventan cifras.
- Los manuales no se actualizan solos cuando cambia el código. Hay que editar el Markdown y reindexar.
- Una distancia baja no garantiza que el fragmento responda la pregunta. El umbral evita usar textos lejanos, no sustituye la revisión humana.
- RAG no calcula totales ni conoce el stock de hoy.
