from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class GraphNode(BaseModel):
    id: str
    label: str
    name: str
    properties: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation_type: str
    weight: float
    properties: Dict[str, Any]

class GraphOverviewResponse(BaseModel):
    total_nodes: int
    total_edges: int
    node_labels_summary: Dict[str, int]
    relation_types_summary: Dict[str, int]
    sample_nodes: List[GraphNode]
    sample_edges: List[GraphEdge]

class ConnectedEntity(BaseModel):
    direction: str = Field(..., description="'incoming' hoặc 'outgoing'")
    relation: str = Field(..., description="Loại quan hệ kiến thức")
    node: GraphNode

class NodeDetailResponse(BaseModel):
    node: GraphNode
    outgoing_count: int
    incoming_count: int
    connected_entities: List[ConnectedEntity]

class GraphTraversalRequest(BaseModel):
    holland_code: str = Field(..., min_length=1, max_length=6, description="Mã Holland RIASEC, ví dụ: IRE, SEC, R")
    target_block: str = Field("A00", description="Khối xét tuyển đại học mục tiêu (A00, A01, D01, B00, C00...)")
    estimated_score: Optional[float] = Field(None, description="Điểm thi dự kiến của học sinh")

class OfferingUniversityItem(BaseModel):
    university_code: str
    university_name: str
    location: Optional[str] = None
    program_name: Optional[str] = None
    cutoff_2025: float
    cutoff_pred_2026: float
    tier: str = Field(..., description="Mơ ước (Dream), Vừa sức (Target), An toàn (Safety)")

class GraphPathItem(BaseModel):
    major_code: str
    major_name: str
    salary_range: Optional[str] = None
    growth_outlook: Optional[str] = None
    leading_careers: List[str]
    offering_universities: List[OfferingUniversityItem]

class GraphTraversalResponse(BaseModel):
    holland_code: str
    target_block: str
    estimated_score: Optional[float]
    paths_count: int
    paths: List[GraphPathItem]
