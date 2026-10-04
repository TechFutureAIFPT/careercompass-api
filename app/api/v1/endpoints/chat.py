from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.deepseek_service import deepseek_service
from app.services.supabase_service import supabase_service

router = APIRouter()

@router.post("/message", response_model=Dict[str, Any], summary="Trợ lý Hướng nghiệp AI (DeepSeek CoT + RAG + Knowledge Graph)")
async def chat_with_advisor(request: ChatRequest):
    """
    Điểm chạm tư vấn trực tiếp kết hợp 3 lớp tri thức:
    1. Đồ thị tri thức (Knowledge Graph multi-hop)
    2. Kho văn bản quy chế tuyển sinh RAG (Thông tư 06/2026/TT-BGDĐT)
    3. Tra cứu trực tiếp đề án tuyển sinh thời gian thực
    Tự động lưu lịch sử hội thoại nếu có user_id.
    """
    try:
        conv_id = request.conversation_id
        if request.user_id and not conv_id:
            conv_id = await supabase_service.create_chat_conversation(
                user_id=request.user_id,
                title=f"Hỏi đáp: {request.message[:40]}..."
            )

        if conv_id and request.user_id:
            await supabase_service.save_chat_message(
                conversation_id=conv_id,
                sender="user",
                content=request.message
            )

        response: ChatResponse = await deepseek_service.get_advisory_response(
            user_message=request.message,
            history=request.conversation_history,
            student_profile=request.student_profile_context,
            use_deep_research=request.use_deep_research
        )

        if conv_id and request.user_id:
            response.conversation_id = conv_id
            await supabase_service.save_chat_message(
                conversation_id=conv_id,
                sender="assistant",
                content=response.reply,
                citations=[c.model_dump() for c in response.citations]
            )

        return {
            "success": True,
            "data": response.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phản hồi cố vấn AI: {str(e)}")

@router.get("/conversations/{user_id}", summary="Lấy danh sách các cuộc trò chuyện của học sinh")
async def list_user_conversations(user_id: str):
    # Returns conversation list from local cache or supabase
    convs = [
        conv for conv in supabase_service._local_conversations.values()
        if conv.get("user_id") == user_id
    ]
    return {
        "success": True,
        "conversations": convs
    }

@router.get("/history/{conversation_id}", summary="Lấy lịch sử tin nhắn của một cuộc trò chuyện")
async def get_conversation_history(conversation_id: str):
    messages = await supabase_service.get_conversation_messages(conversation_id)
    return {
        "success": True,
        "conversation_id": conversation_id,
        "messages": messages
    }
