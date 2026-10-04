from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from app.services.graph_service import graph_service
from app.schemas.graph import (
    GraphOverviewResponse,
    GraphNode,
    GraphEdge,
    NodeDetailResponse,
    GraphTraversalRequest,
    GraphTraversalResponse,
    GraphPathItem,
    OfferingUniversityItem
)

router = APIRouter()

@router.get("/overview", response_model=GraphOverviewResponse, summary="Tổng quan đồ thị tri thức hướng nghiệp (Knowledge Graph)")
async def get_graph_overview():
    """
    Trả về cấu trúc tổng thể của đồ thị tri thức:
    - 6 đỉnh Holland Traits (R, I, A, S, E, C)
    - 8 đỉnh Trí thông minh Gardner
    - 10 đỉnh Khối thi tốt nghiệp THPT
    - Đỉnh các nhóm ngành chuẩn GD&ĐT
    - Đỉnh các trường Đại học & Điểm chuẩn
    - Đỉnh các nghề nghiệp đầu ra
    """
    nodes_list = list(graph_service.nodes.values())
    edges_list = graph_service.edges

    node_labels: Dict[str, int] = {}
    for n in nodes_list:
        lbl = n.get("label", "Unknown")
        node_labels[lbl] = node_labels.get(lbl, 0) + 1

    relation_types: Dict[str, int] = {}
    for e in edges_list:
        rt = e.get("relation_type", "Unknown")
        relation_types[rt] = relation_types.get(rt, 0) + 1

    sample_nodes = [
        GraphNode(
            id=n["id"],
            label=n["label"],
            name=n["name"],
            properties=n.get("properties", {})
        )
        for n in nodes_list[:15]
    ]

    sample_edges = [
        GraphEdge(
            id=e["id"],
            source=e["source"],
            target=e["target"],
            relation_type=e["relation_type"],
            weight=e.get("weight", 1.0),
            properties=e.get("properties", {})
        )
        for e in edges_list[:25]
    ]

    return GraphOverviewResponse(
        total_nodes=len(nodes_list),
        total_edges=len(edges_list),
        node_labels_summary=node_labels,
        relation_types_summary=relation_types,
        sample_nodes=sample_nodes,
        sample_edges=sample_edges
    )

@router.get("/node/{node_id}", response_model=NodeDetailResponse, summary="Chi tiết đỉnh và các liên kết 2 chiều trong đồ thị")
async def get_node_details(node_id: str):
    """
    Truy vấn thông tin chi tiết một đỉnh (ví dụ: HOLLAND_I, BLOCK_A00, UNI_BKA, MAJOR_7480201)
    kèm toàn bộ các đỉnh liên quan liền kề (incoming và outgoing).
    """
    details = graph_service.get_node_details(node_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đỉnh đồ thị với ID '{node_id}'.")
    return details

@router.post("/traverse", response_model=GraphTraversalResponse, summary="Duyệt đồ thị đa chặng (Multi-hop Graph Traversal)")
async def traverse_advisory_paths(payload: GraphTraversalRequest):
    """
    Duyệt đồ thị đa chặng:
    Holland Code -> Nhóm ngành liên quan -> Tổ hợp môn -> Trường ĐH đào tạo -> Đầu ra nghề nghiệp.
    Phân loại tự động 3 tầng: Mơ ước (Dream), Vừa sức (Target), An toàn (Safety) dựa theo điểm thi.
    """
    raw_paths = graph_service.query_multihop_advisory_paths(
        holland_code=payload.holland_code,
        target_block=payload.target_block,
        estimated_score=payload.estimated_score
    )

    formatted_paths: List[GraphPathItem] = []
    for p in raw_paths:
        unis = [
            OfferingUniversityItem(
                university_code=u.get("university_code", ""),
                university_name=u.get("university_name", ""),
                location=u.get("location"),
                program_name=u.get("program_name"),
                cutoff_2025=float(u.get("cutoff_2025", 25.0)),
                cutoff_pred_2026=float(u.get("cutoff_pred_2026", 25.0)),
                tier=u.get("tier", "Vừa sức (Target)")
            )
            for u in p.get("offering_universities", [])
        ]
        formatted_paths.append(
            GraphPathItem(
                major_code=p.get("major_code", ""),
                major_name=p.get("major_name", ""),
                salary_range=p.get("salary_range"),
                growth_outlook=p.get("growth_outlook"),
                leading_careers=p.get("leading_careers", []),
                offering_universities=unis
            )
        )

    return GraphTraversalResponse(
        holland_code=payload.holland_code,
        target_block=payload.target_block,
        estimated_score=payload.estimated_score,
        paths_count=len(formatted_paths),
        paths=formatted_paths
    )

@router.get("/search", summary="Tìm kiếm đỉnh trong Knowledge Graph theo từ khóa")
async def search_graph_nodes(q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm (tên trường, tên ngành, mã khối)")):
    q_lower = q.lower()
    matches = []
    for node in graph_service.nodes.values():
        if q_lower in node["name"].lower() or q_lower in node["id"].lower():
            matches.append(node)
    return {
        "query": q,
        "total_matches": len(matches),
        "results": matches[:20]
    }
