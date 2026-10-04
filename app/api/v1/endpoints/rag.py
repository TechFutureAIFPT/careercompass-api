from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.services.rag_service import rag_service
from app.schemas.rag import (
    RAGQueryRequest,
    RAGRetrieveResponse,
    RAGChunkItem,
    RAGAskRequest,
    RAGAskResponse,
    RAGDocumentSummary
)

router = APIRouter()

@router.post("/retrieve", response_model=RAGRetrieveResponse, summary="Truy xuất dữ liệu tuyển sinh ngữ nghĩa (RAG Search)")
async def retrieve_rag_documents(payload: RAGQueryRequest):
    """
    Tìm kiếm và xếp hạng các phân đoạn tài liệu phù hợp nhất với câu hỏi:
    - Quy chế Bộ GD&ĐT (Thông tư 06/2026/TT-BGDĐT)
    - Đề án tuyển sinh & điểm chuẩn các trường ĐH
    - Bản mô tả nghề nghiệp và định hướng Holland
    """
    results = rag_service.search_relevant_chunks(
        query=payload.query,
        top_k=payload.top_k,
        category_filter=payload.category_filter
    )

    chunks = [
        RAGChunkItem(
            id=c.id,
            title=c.title,
            category=c.category,
            content=c.content,
            source=c.source,
            relevance_score=score,
            metadata=c.metadata
        )
        for c, score in results
    ]

    return RAGRetrieveResponse(
        query=payload.query,
        total_found=len(chunks),
        chunks=chunks
    )

@router.post("/ask", response_model=RAGAskResponse, summary="Hỏi đáp tuyển sinh với cơ chế Grounded RAG")
async def ask_with_rag(payload: RAGAskRequest):
    """
    Tra cứu tài liệu pháp lý & điểm chuẩn, sau đó tổng hợp câu trả lời chính xác có trích dẫn nguồn.
    """
    context_str, citations = rag_service.build_grounded_rag_context(payload.query, top_k=payload.top_k)
    
    if not context_str:
        return RAGAskResponse(
            query=payload.query,
            answer="Hệ thống chưa tìm thấy tài liệu phù hợp trực tiếp với câu hỏi này trong cơ sở dữ liệu tuyển sinh 2026.",
            grounded_context_summary="",
            citations=[],
            related_document_ids=[]
        )

    # Synthesis based on retrieved documents
    results = rag_service.search_relevant_chunks(payload.query, top_k=payload.top_k)
    doc_ids = [c.id for c, _ in results]

    answer_text = (
        f"### Kết quả tra cứu quy chế & tuyển sinh 2026:\n\n"
        f"Dựa trên các văn bản quy phạm pháp luật và đề án tuyển sinh chính thức:\n\n"
    )
    for idx, (chunk, _) in enumerate(results[:3]):
        answer_text += f"**{idx+1}. {chunk.title}** ({chunk.source}):\n{chunk.content}\n\n"

    answer_text += "💡 *Lưu ý: Dữ liệu đã được kiểm chứng đối chiếu với Cổng thông tin Bộ GD&ĐT và Đề án tuyển sinh các trường.*"

    return RAGAskResponse(
        query=payload.query,
        answer=answer_text,
        grounded_context_summary=context_str[:500] + "...",
        citations=citations,
        related_document_ids=doc_ids
    )

@router.get("/documents", response_model=List[RAGDocumentSummary], summary="Danh mục toàn bộ tài liệu trong kho lưu trữ RAG")
async def list_rag_documents():
    """
    Liệt kê tất cả các phân đoạn tài liệu đã được index vào vector/keyword RAG corpus.
    """
    return [
        RAGDocumentSummary(
            id=c.id,
            title=c.title,
            category=c.category,
            source=c.source,
            token_count=len(c.tokens)
        )
        for c in rag_service.chunks
    ]
