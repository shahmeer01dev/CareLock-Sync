"""
RAG API Routes - Sprint 4 v2
Dual-model: llama3.2:3b for mapping, phi3 for chatbot.
Full verification workflow: suggest -> review -> confirm-batch.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common.auth import require_auth, require_admin, AuthContext

router = APIRouter(prefix="/api/v1/rag", tags=["RAG Mapping"])
_suggester = None


class FieldReq(BaseModel):
    field_name: str = Field(..., example="date_of_birth")
    field_type: str = Field("varchar", example="date")
    sample_values: Optional[List] = None
    fhir_resource: str = Field("Patient")


class ColDef(BaseModel):
    name: str
    type: str = "varchar"
    sample_values: Optional[List] = None

class SchemaReq(BaseModel):
    table_name: str
    columns: List[ColDef]
    fhir_resource: str = "Patient"

class ConfirmBatchReq(BaseModel):
    mappings: List[Dict[str, Any]] = Field(
        ..., description="The mappings array from /suggest/schema")
    confirmed_fields: List[str] = Field(
        ..., description="source_field names the user approved")

class SingleConfirmReq(BaseModel):
    source_field: str
    source_type: str = "varchar"
    target_path: str
    fhir_resource: str = "Patient"
    transformation: str = "none"
    confidence: float = 1.0

class ChatReq(BaseModel):
    question: str = Field(..., example="What FHIR path maps to date of birth?")
    context: Optional[str] = None


def _get():
    global _suggester
    if _suggester is None:
        try:
            from rag.mapping_suggester import MappingSuggester
            _suggester = MappingSuggester(
                mapping_model=os.getenv("MAPPING_MODEL", "llama3.2:3b"),
                chat_model=os.getenv("CHAT_MODEL", "phi3"),
                ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                vector_store_path=os.getenv("CHROMA_PATH", "./databases/chroma"),
            )
        except Exception as e:
            raise HTTPException(503, f"RAG unavailable: {e}. "
                                     "Run: ollama serve && ollama pull llama3.2:3b")
    return _suggester


@router.get("/status")
async def status(auth: AuthContext = Depends(require_auth)):
    try:
        s = _get()
        st = s.get_stats()
        return {
            "status": "operational",
            "mapping_model": st["mapping_model"],
            "chat_model": st["chat_model"],
            "mapping_available": st["mapping_available"],
            "total_mappings": st["total_mappings"],
            "architecture": "dual-model: llama3.2:3b for mapping, phi3 for chat",
            "checked_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "unavailable", "error": str(e),
                "checked_at": datetime.utcnow().isoformat()}


@router.post("/suggest/field")
async def suggest_field(req: FieldReq, auth: AuthContext = Depends(require_auth)):
    """Suggest FHIR mapping for one field. Returns status=pending_review."""
    s = _get()
    r = s.suggest_mapping(req.field_name, req.field_type,
                          req.sample_values, req.fhir_resource)
    return {
        "field": req.field_name,
        "fhir_resource": req.fhir_resource,
        "suggestion": r,
        "similar_count": len(r.get("similar_mappings", [])),
        "note": "Call POST /mappings/confirm to save after review.",
        "suggested_at": datetime.utcnow().isoformat(),
    }


@router.post("/suggest/schema")
async def suggest_schema(req: SchemaReq, auth: AuthContext = Depends(require_auth)):
    """
    STEP 1 of verification workflow.
    Returns all suggestions with status=pending_review.
    Nothing is saved until POST /mappings/confirm-batch.
    """
    s = _get()
    result = s.suggest_schema_mapping(
        {"table_name": req.table_name,
         "columns": [c.dict() for c in req.columns]},
        req.fhir_resource,
    )
    return {
        **result,
        "workflow": {
            "step": "1/2 - suggestions ready for review",
            "next": "POST /api/v1/rag/mappings/confirm-batch with confirmed_fields list",
        },
        "suggested_at": datetime.utcnow().isoformat(),
    }


@router.post("/mappings/confirm-batch")
async def confirm_batch(req: ConfirmBatchReq, auth: AuthContext = Depends(require_admin)):
    """
    STEP 2 of verification workflow (admin only).
    Saves only the fields listed in confirmed_fields.
    Everything else is skipped.
    """
    s = _get()
    result = s.confirm_mappings(req.mappings, req.confirmed_fields)
    return {
        "status": "ok",
        "saved": result["saved"],
        "skipped": result["skipped"],
        "total_saved": result["total_saved"],
        "message": f"Saved {result['total_saved']} mappings. Skipped {len(result['skipped'])}.",
        "confirmed_at": datetime.utcnow().isoformat(),
    }


@router.post("/mappings/confirm")
async def confirm_single(req: SingleConfirmReq, auth: AuthContext = Depends(require_admin)):
    """Save a single manually-specified mapping (admin only)."""
    s = _get()
    s.save_confirmed_mapping(req.source_field, req.source_type, req.target_path,
                              req.fhir_resource, req.transformation, req.confidence)
    return {"status": "saved", "mapping": req.dict(),
            "saved_at": datetime.utcnow().isoformat()}


@router.post("/chat")
async def chat(req: ChatReq, auth: AuthContext = Depends(require_auth)):
    """FHIR RAG chatbot using phi3. Ask anything about FHIR mappings."""
    s = _get()
    answer = s.chat(req.question, req.context)
    return {"question": req.question, "answer": answer,
            "model": s._chat_model,
            "answered_at": datetime.utcnow().isoformat()}


@router.get("/knowledge/stats")
async def knowledge_stats(auth: AuthContext = Depends(require_auth)):
    s = _get()
    from rag.fhir_knowledge import get_all_mappings
    st = s.get_stats()
    return {
        "mapping_model": st["mapping_model"],
        "chat_model": st["chat_model"],
        "vector_store_mappings": st["total_mappings"],
        "knowledge_base_entries": len(get_all_mappings()),
        "resources_covered": ["Patient", "Encounter", "Observation", "MedicationRequest"],
    }
