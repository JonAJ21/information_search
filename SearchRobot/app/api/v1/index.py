from fastapi import APIRouter, Depends
from pydantic import BaseModel
from logic.boolean_index import get_boolean_index

router = APIRouter(
    tags=["index"],
)    

@router.get("/search")
async def search(query: str, offset: int = 0, limit: int = 100, index = Depends(get_boolean_index)):
    search_result = index.search(query, offset, limit)
    return {"index": search_result}

@router.get("/documents/count")
async def get_documents_count(index = Depends(get_boolean_index)):
    return {"count": index.get_document_count()}

@router.get("/terms/count")
async def get_terms_count(index = Depends(get_boolean_index)):
    return {"count": index.get_term_count()}

@router.get("/document/{doc_id}/terms/")
async def get_document_terms(doc_id: int, index = Depends(get_boolean_index)):
    return {"terms": index.get_document_terms(doc_id)}

@router.post("/document/{doc_id}")
async def add(doc_id: int, terms: list[str], index = Depends(get_boolean_index)):
    index.add_document(doc_id, terms)
    return {"index": "ok"}

@router.delete("/document/{doc_id}")
async def remove(doc_id: int, terms: list[str], index = Depends(get_boolean_index)):
    index.remove_document(doc_id, terms)
    return {"index": "ok"}

@router.delete("/documents")
async def clear(index = Depends(get_boolean_index)):
    index.clear()
    return {"index": "ok"}

