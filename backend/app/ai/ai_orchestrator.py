import json
import re
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.ai.memory import memory
from app.ai.navigation_service import normalize
from app.ai.ollama_service import OllamaError, ollama_service
from app.ai.tool_executor import confirm, execute
from app.ai.tool_registry import INTENT_TOOLS, TOOLS
from app.core.dependencies import has_permission
from app.core.errors import AppError
from app.models import User
from app.schemas.dto import AssistantResponse
from app.services.audit_service import write_audit
from app.services.mappers import as_float

INTENTS = ["NAVIGATION", "HOW_TO", "BUSINESS_QUERY", "ANALYTICS", "ACTION", "GENERAL", "UNKNOWN"]
MAX_TOOL_ROUNDS = 3

CLASSIFY_FORMAT = {
    "type": "object",
    "properties": {
        "intent": {"type": "string"},
        "tool": {"type": "string"},
    },
    "required": ["intent", "tool"],
}


def _unavailable(text: str) -> AssistantResponse:
    return AssistantResponse(
        message=text,
        intent="UNKNOWN",
        available=False,
    )


def _plain(message: str, intent: str, data=None, actions=None, sources=None, available: bool = True) -> AssistantResponse:
    return AssistantResponse(
        message=message,
        intent=intent,
        data=data,
        actions=actions or [],
        sources=sources or [],
        available=available,
    )


def is_bulk_destructive(text: str) -> bool:
    normalized = normalize(text)
    verbs = ("elimina", "eliminar", "borra", "borrar", "delete", "drop", "truncate", "destruye", "vaciar")
    targets = ("todos", "todas", "toda la", "base de datos", "tabla", "usuarios")
    return any(verb in normalized for verb in verbs) and any(target in normalized for target in targets)


def route_override(text: str) -> tuple[str, str | None] | None:
    """Corrige rutas evidentes en las que el modelo de 1.5B se equivoca."""
    normalized = normalize(text)
    outside = ("marte", "oceano", "planeta", "clima", "temperatura", "receta", "futbol")
    business = ("venta", "producto", "cliente", "inventario", "stock", "usuario", "erp", "permiso")
    if any(word in normalized for word in outside) and not any(word in normalized for word in business):
        return "UNKNOWN", None
    if any(phrase in normalized for phrase in ("donde", "llevame", "ir al modulo", "en que pantalla", "en que modulo")):
        return "NAVIGATION", "buscar_funcionalidad_erp"
    if "como " in normalized and any(word in normalized for word in ("registro", "registrar", "creo", "crear", "utilizo", "usar", "hago")):
        return "HOW_TO", "consultar_documentacion"
    return None


def asks_all_sellers(text: str) -> bool:
    normalized = normalize(text)
    return "todos los vendedores" in normalized or "ventas de todos" in normalized or "cada vendedor" in normalized


def period_hint(text: str, today: date | None = None) -> str:
    today = today or date.today()
    normalized = normalize(text)
    months = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "setiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }
    for name, month in months.items():
        if name in normalized:
            year = today.year
            start = date(year, month, 1)
            end = date(year + 1, 1, 1) - timedelta(days=1) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
            if start > today:
                year -= 1
                start = date(year, month, 1)
                end = date(year + 1, 1, 1) - timedelta(days=1) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
            return f"Call the tool with fecha_inicio={start.isoformat()} and fecha_fin={end.isoformat()}."
    if "ultimo trimestre" in normalized:
        end = today.replace(day=1) - timedelta(days=1)
        month = end.month - 2
        year = end.year
        if month <= 0:
            month += 12
            year -= 1
        start = date(year, month, 1)
        return f"Call the tool with fecha_inicio={start.isoformat()} and fecha_fin={end.isoformat()}."
    if "este mes" in normalized:
        return f"Call the tool with fecha_inicio={today.replace(day=1).isoformat()} and fecha_fin={today.isoformat()}."
    if "este ano" in normalized or "este año" in normalized:
        return f"Call the tool with fecha_inicio={date(today.year, 1, 1).isoformat()} and fecha_fin={today.isoformat()}."
    return f"Today is {today.isoformat()}. Pass fecha_inicio and fecha_fin as YYYY-MM-DD when a period is mentioned."


def _classify(message: str, history: list[dict]) -> tuple[str, str | None]:
    tool_names = sorted(TOOLS)
    system = (
        "Classify one ERP request. Return JSON with intent and tool. "
        f"intent is one of: {', '.join(INTENTS)}. "
        f"tool is one of: {', '.join(tool_names)}, or none. "
        "NAVIGATION asks where a screen is or to open a module: buscar_funcionalidad_erp. "
        "HOW_TO asks how to register or use a feature: consultar_documentacion. "
        "BUSINESS_QUERY asks counts, amounts, stock, last sale, users or one customer: pick the matching consultar_* tool. "
        "Less than N units in stock is consultar_inventario. Last sale or sales in a month is consultar_ventas. "
        "Admin users is consultar_usuarios. "
        "ANALYTICS asks rankings or the best product or best customers: consultar_top_productos or consultar_top_clientes. "
        "ACTION creates a record: crear_cliente, crear_producto, crear_venta or crear_usuario. "
        "UNKNOWN is anything outside the ERP, including planets, weather, science or general world facts. "
        "GENERAL asks what the ERP is: consultar_documentacion. "
        "If no tool applies, tool is none."
    )
    messages = [{"role": "system", "content": system}, *history[-4:], {"role": "user", "content": message}]
    raw = ollama_service.chat(messages, response_format=CLASSIFY_FORMAT)
    content = raw.get("content") or "{}"
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        parsed = json.loads(match.group(0)) if match else {}
    intent = str(parsed.get("intent") or "UNKNOWN").upper()
    if intent not in INTENTS:
        intent = "UNKNOWN"
    tool = parsed.get("tool")
    if tool in ("none", "null", None, ""):
        tool = None
    if tool is not None and tool not in TOOLS:
        tool = None
    allowed = INTENT_TOOLS.get(intent, [])
    if tool and allowed and tool not in allowed:
        tool = allowed[0] if len(allowed) == 1 else None
    return intent, tool


def _call_tool(spec_name: str, message: str, hint: str) -> dict | None:
    spec = TOOLS[spec_name]
    system = (
        "You are an ERP tool caller. Call the provided tool. "
        "Do not answer in prose before the tool call. Do not invent business numbers. "
        f"{hint}"
    )
    user = f"{hint}\nUser question: {message}"
    for _ in range(2):
        raw = ollama_service.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            tools=[spec.schema()],
        )
        calls = raw.get("tool_calls") or []
        if calls:
            function = calls[0].get("function") or {}
            if function.get("name") == spec_name:
                return function.get("arguments") or {}
        user = f"You must call {spec_name} now. {hint}\nQuestion: {message}"
    return None


def _draft(message: str, intent: str, data: dict | None, sources: list[dict]) -> str:
    context = json.dumps({"data": data, "sources": sources}, ensure_ascii=False, default=str)[:4000]
    system = (
        "Write a short Spanish answer for an ERP user. "
        "Use only numbers and facts present in the JSON. "
        "If the JSON has no business figures, do not invent any. "
        "Do not output HTML or JavaScript."
    )
    raw = ollama_service.chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Intent: {intent}\nQuestion: {message}\nJSON:\n{context}"},
        ]
    )
    return (raw.get("content") or "").strip()


def _numbers(value) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", json.dumps(value, ensure_ascii=False, default=str)))


def _ground(text: str, data, fallback: str) -> str:
    if not text:
        return fallback
    if data is None:
        return text
    allowed = _numbers(data)
    for number in re.findall(r"\d+(?:[.,]\d+)?", text):
        plain = number.replace(",", "").replace(".", "")
        if number in allowed or number.replace(",", "") in allowed:
            continue
        if any(number in item or plain == item.replace(".", "").replace(",", "") for item in allowed):
            continue
        return fallback
    return text


def _money(value) -> str:
    return f"USD {as_float(value):,.2f}"


def _template(tool: str | None, data: dict | None, message: str) -> str:
    if not data:
        return "No tengo datos reales para responder esa consulta."
    if tool == "consultar_ventas":
        if "ultima" in normalize(message) and data.get("ultima_venta"):
            last = data["ultima_venta"]
            who = last.get("usuario") or "un usuario autorizado"
            return (
                f"La última venta del período la registró {who} el {last.get('fecha')}, "
                f"con el número {last.get('numero')}, por {_money(last.get('total') or 0)}."
            )
        if data.get("producto"):
            return (
                f"De {data.get('producto')}, entre {data.get('fecha_inicio')} y {data.get('fecha_fin')}, "
                f"se vendieron {data.get('unidades') or data.get('cantidad')} unidades por {_money(data.get('importe') or 0)}."
            )
        return (
            f"Entre {data.get('fecha_inicio')} y {data.get('fecha_fin')} se registraron "
            f"{data.get('cantidad')} ventas por un importe total de {_money(data.get('importe') or 0)}."
        )
    if tool == "consultar_top_productos":
        items = data.get("items") or []
        if not items:
            return "No hay ventas confirmadas en ese período."
        top = items[0]
        return f"El producto más vendido fue {top['producto']} ({top['sku']}), con {top['unidades']} unidades."
    if tool == "consultar_top_clientes":
        items = data.get("items") or []
        if not items:
            return "No hay compras confirmadas en ese período."
        top = items[0]
        return f"El cliente con mayor compra fue {top['cliente']}, con {_money(top['importe'])} en {top['compras']} compras."
    if tool == "consultar_inventario":
        items = data.get("items") or []
        if not items:
            return "No encontré productos con ese criterio de inventario."
        names = ", ".join(f"{item['producto']} ({item['cantidad']})" for item in items[:8])
        return f"Encontré {data.get('cantidad_productos')} producto(s): {names}."
    if tool == "consultar_usuarios":
        items = data.get("items") or []
        if not items:
            return "No hay usuarios que coincidan con la consulta."
        names = ", ".join(f"{item['usuario']} ({item['rol']})" for item in items)
        return f"Usuarios encontrados: {names}."
    if tool == "buscar_funcionalidad_erp":
        results = data.get("resultados") or []
        if not results:
            return "No encontré una pantalla del ERP que corresponda a esa consulta."
        first = results[0]
        if not first.get("permitido"):
            return (
                f"{first['nombre']} está en {first['modulo']}, pero tu rol no tiene el permiso {first['permiso']}."
            )
        return f"Puedes hacerlo desde {first['modulo']} > {first['nombre']}."
    if tool in ("crear_cliente", "crear_producto", "crear_venta", "crear_usuario") and data.get("pendiente"):
        return "Preparé la operación. Confírmala para ejecutarla. No haré el cambio sin esa confirmación."
    if tool == "consultar_documentacion":
        return "Puedo explicarte el procedimiento con la documentación del ERP."
    return "Consulté el ERP y preparé el resultado con los datos reales."


def handle_message(db: Session, user: User, message: str, session_id: str) -> AssistantResponse:
    text = message.strip()
    if is_bulk_destructive(text):
        write_audit(
            db,
            user=user,
            action="TOOL",
            entity="assistant",
            result_status="DENIED",
            message="Operación masiva bloqueada",
            parameters={"message": text[:300]},
        )
        db.commit()
        return _plain(
            "No puedo eliminar usuarios de forma masiva. Esa operación no existe. "
            "Los cambios de usuarios exigen el permiso de administración y una confirmación explícita por cada alta o edición.",
            "ACTION",
        )
    if asks_all_sellers(text) and not has_permission(user, "sales.read_all"):
        write_audit(
            db,
            user=user,
            action="TOOL",
            entity="assistant",
            tool_name="consultar_ventas",
            result_status="DENIED",
            message="Consulta de ventas de todos los vendedores rechazada",
        )
        db.commit()
        return _plain("No tienes permiso para consultar las ventas de todos los vendedores.", "BUSINESS_QUERY")
    if not has_permission(user, "assistant.use"):
        return _plain("No tienes permiso para usar el asistente.", "UNKNOWN")
    health = ollama_service.health()
    if not health["ok"]:
        return _unavailable(
            "El asistente no está disponible porque Ollama no responde o el modelo configurado no está cargado. "
            "El resto del ERP sigue funcionando."
        )
    history = memory.history(user.id, session_id)
    override = route_override(text)
    if override is not None:
        intent, tool = override
    else:
        try:
            intent, tool = _classify(text, history)
        except OllamaError:
            return _unavailable("El asistente no pudo completar la consulta porque Ollama no respondió. El ERP sigue disponible.")
    if intent == "UNKNOWN":
        answer = _plain(
            "Esa pregunta no corresponde a los datos ni a la documentación de este ERP. "
            "Puedo ayudarte con clientes, productos, inventario, ventas, usuarios y con el uso del sistema.",
            "UNKNOWN",
        )
        memory.add(user.id, session_id, "user", text)
        memory.add(user.id, session_id, "assistant", answer.message)
        return answer
    hint = period_hint(text)
    if tool is None:
        options = INTENT_TOOLS.get(intent) or []
        tool = options[0] if options else None
    if tool is None:
        answer = _plain("No identifiqué una función del ERP para esa pregunta.", intent)
        memory.add(user.id, session_id, "user", text)
        memory.add(user.id, session_id, "assistant", answer.message)
        return answer
    try:
        arguments = _call_tool(tool, text, hint if tool in {"consultar_ventas", "consultar_top_productos", "consultar_top_clientes", "consultar_dashboard"} else "Use the user question as the tool argument.")
        if tool in {"buscar_funcionalidad_erp", "consultar_documentacion"}:
            arguments = {"consulta": text}
        elif arguments is None:
            return _plain("No pude estructurar la consulta con una herramienta, así que no inventé datos del negocio.", intent)
        result = execute(db, user, tool, arguments)
    except AppError as exc:
        write_audit(db, user=user, action="TOOL", tool_name=tool, result_status="DENIED", message=exc.message)
        db.commit()
        return _plain(exc.message, intent)
    except OllamaError:
        return _unavailable("El asistente no pudo usar el modelo. El ERP sigue disponible.")
    data = result.get("data")
    sources = result.get("sources") or []
    actions = result.get("actions") or []
    if tool == "consultar_documentacion":
        nav_args = {"consulta": text}
        try:
            nav = execute(db, user, "buscar_funcionalidad_erp", nav_args)
            actions = nav.get("actions") or actions
            if isinstance(data, dict):
                data["navegacion"] = (nav.get("data") or {}).get("resultados")
        except AppError:
            pass
    fallback = _template(tool, data if isinstance(data, dict) else None, text)
    prose = fallback
    if tool == "consultar_documentacion" or intent in {"HOW_TO", "GENERAL", "NAVIGATION"}:
        try:
            prose = _draft(text, intent, data if isinstance(data, dict) else None, sources) or fallback
        except OllamaError:
            prose = fallback
        if intent == "NAVIGATION" and isinstance(data, dict):
            first = (data.get("resultados") or [{}])[0]
            if first.get("nombre") and str(first["nombre"]).lower() not in prose.lower():
                prose = fallback
        if not prose:
            prose = fallback
    else:
        try:
            drafted = _draft(text, intent, data if isinstance(data, dict) else None, sources)
            prose = _ground(drafted, data, fallback)
        except OllamaError:
            prose = fallback
        if intent in {"BUSINESS_QUERY", "ANALYTICS"} and len(prose) < 40:
            prose = fallback
    if tool == "consultar_documentacion" and not sources:
        prose = (
            "No encontré en los manuales un procedimiento para esa pregunta. "
            "Puedo ayudarte con las pantallas y los datos que sí están en el ERP."
        )
    answer = _plain(prose, intent, data=data, actions=actions, sources=sources)
    memory.add(user.id, session_id, "user", text)
    memory.add(user.id, session_id, "assistant", answer.message)
    return answer


def confirm_action(db: Session, user: User, token: str) -> AssistantResponse:
    try:
        data = confirm(db, user, token)
    except AppError as exc:
        return _plain(exc.message, "ACTION")
    return _plain("La operación quedó registrada.", "ACTION", data=data)
