from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.ai_orchestrator import confirm_action, handle_message
from app.ai.ollama_service import ollama_service
from app.ai.rag_service import index_knowledge, stats
from app.core.dependencies import require_permissions
from app.database.session import get_db
from app.models import User
from app.schemas.dto import AssistantRequest, AssistantResponse, ConfirmRequest

router = APIRouter(prefix="/assistant", tags=["Asistente"])


@router.post("/chat", response_model=AssistantResponse)
def chat(
    data: AssistantRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("assistant.use")),
):
    return handle_message(db, actor, data.message, data.session_id)


@router.post("/confirm", response_model=AssistantResponse)
def confirm(
    data: ConfirmRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("assistant.use")),
):
    return confirm_action(db, actor, data.token)


@router.get("/health")
def health(_: User = Depends(require_permissions("assistant.use"))):
    status = ollama_service.health()
    return {
        "status": "ok" if status["ok"] else "unavailable",
        "model": status["model"],
        "embedding_model": ollama_service.settings.ollama_embedding_model,
        "model_ready": status["ok"],
    }


@router.post("/knowledge/index")
def index(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permissions("knowledge.index")),
):
    from app.services.audit_service import write_audit

    result = index_knowledge()
    write_audit(db, user=actor, action="INDEX", entity="knowledge", parameters=result, message="Reindexación de manuales")
    db.commit()
    return result


@router.get("/knowledge/stats")
def knowledge_stats(_: User = Depends(require_permissions("knowledge.index"))):
    return stats()
