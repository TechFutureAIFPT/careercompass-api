import os
import json
from typing import Dict, Any, List, Optional, Set

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

class KnowledgeGraphService:
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.adjacency: Dict[str, List[Dict[str, Any]]] = {}
        self.reverse_adjacency: Dict[str, List[Dict[str, Any]]] = {}
        self._build_initial_graph()

    def _add_node(self, node_id: str, label: str, name: str, properties: Dict[str, Any]):
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "name": name,
            "properties": properties
        }
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []
        if node_id not in self.reverse_adjacency:
            self.reverse_adjacency[node_id] = []

    def _add_edge(self, source_id: str, target_id: str, relation_type: str, weight: float = 1.0, properties: Optional[Dict[str, Any]] = None):
        if properties is None:
            properties = {}
        edge = {
            "id": f"{source_id}_{relation_type}_{target_id}",
            "source": source_id,
            "target": target_id,
            "relation_type": relation_type,
            "weight": weight,
            "properties": properties
        }
        self.edges.append(edge)

        if source_id not in self.adjacency:
            self.adjacency[source_id] = []
        self.adjacency[source_id].append(edge)

        if target_id not in self.reverse_adjacency:
            self.reverse_adjacency[target_id] = []
        self.reverse_adjacency[target_id].append(edge)

    def _build_initial_graph(self):
        # 1. Holland Nodes
        holland_meta = {
            "R": ("Kỹ thuật / Thực tế", "Realistic", "Ưa thích làm việc với máy móc, công cụ, vật liệu cụ thể hoặc thực địa"),
            "I": ("Nghiên cứu / Khám phá", "Investigative", "Thích tìm hiểu, quan sát, phân tích số liệu, giải quyết vấn đề khoa học"),
            "A": ("Nghệ thuật / Sáng tạo", "Artistic", "Đam mê sáng tạo, thiết kế, đổi mới, không gian tự do, giàu trí tưởng tượng"),
            "S": ("Xã hội / Giúp đỡ", "Social", "Yêu thích giao tiếp, lắng nghe, giảng dạy, đồng hành và hỗ trợ cộng đồng"),
            "E": ("Quản lý / Thuyết phục", "Enterprising", "Năng nổ, có tài lãnh đạo, thích thuyết phục người khác, kinh doanh và đàm phán"),
            "C": ("Nghiệp vụ / Quy củ", "Conventional", "Chỉn chu, thích số liệu rõ ràng, quy trình chuẩn tắc, tính toán và bảo mật tài liệu")
        }
        for code, (vi_name, en_name, desc) in holland_meta.items():
            node_id = f"HOLLAND_{code}"
            self._add_node(node_id, "HollandTrait", f"Nhóm {code} - {vi_name}", {
                "code": code,
                "english_name": en_name,
                "description": desc
            })

        # 2. Gardner Multiple Intelligences Nodes
        gardner_meta = {
            "linguistic": ("Ngôn ngữ", "Khả năng sử dụng từ ngữ, viết lách, hùng biện"),
            "logical_math": ("Logic - Toán học", "Tư duy trừu tượng, tính toán và giải quyết bài toán phức tạp"),
            "spatial": ("Không gian - Thị giác", "Tưởng tượng đa chiều, thiết kế hình ảnh và bản đồ"),
            "musical": ("Âm nhạc - Thính giác", "Cảm thụ giai điệu, tiết tấu và xử lý âm thanh"),
            "bodily_kinesthetic": ("Vận động cơ thể", "Sự khéo léo cơ thể, thủ công, thể thao và thao tác máy móc"),
            "interpersonal": ("Tương tác xã hội", "Thấu hiểu người khác, kết nối và lãnh đạo đội ngũ"),
            "intrapersonal": ("Nội tâm - Tự nhận thức", "Tự hiểu chính mình, điều chỉnh mục tiêu và kỷ luật bản thân"),
            "naturalistic": ("Tự nhiên - Sinh thái", "Nhạy bén với môi trường sống, động thực vật và thời tiết")
        }
        for key, (name_vi, desc) in gardner_meta.items():
            node_id = f"GARDNER_{key.upper()}"
            self._add_node(node_id, "GardnerTrait", f"Trí thông minh {name_vi}", {
                "type": key,
                "description": desc
            })

        # 3. Exam Block Nodes
        blocks = ["A00", "A01", "B00", "C00", "D01", "D07", "D14", "D15", "H00", "V00"]
        block_subjects = {
            "A00": "Toán, Vật lý, Hóa học",
            "A01": "Toán, Vật lý, Tiếng Anh",
            "B00": "Toán, Hóa học, Sinh học",
            "C00": "Ngữ văn, Lịch sử, Địa lý",
            "D01": "Toán, Ngữ văn, Tiếng Anh",
            "D07": "Toán, Hóa học, Tiếng Anh",
            "D14": "Ngữ văn, Lịch sử, Tiếng Anh",
            "D15": "Ngữ văn, Địa lý, Tiếng Anh",
            "H00": "Ngữ văn, Năng khiếu Vẽ 1, Năng khiếu Vẽ 2",
            "V00": "Toán, Vật lý, Năng khiếu Vẽ"
        }
        for b in blocks:
            node_id = f"BLOCK_{b}"
            self._add_node(node_id, "AcademicBlock", f"Khối {b}", {
                "block": b,
                "subjects": block_subjects.get(b, "")
            })

        # 4. Load Majors & build relationships
        majors_path = os.path.join(DATA_DIR, "majors_database.json")
        if os.path.exists(majors_path):
            with open(majors_path, "r", encoding="utf-8") as f:
                majors_data = json.load(f)

            for m in majors_data:
                major_id = f"MAJOR_{m['code']}"
                self._add_node(major_id, "Major", m["name"], {
                    "code": m["code"],
                    "description": m.get("description", ""),
                    "holland_code": m.get("holland_code", ""),
                    "salary_range": m.get("salary_range", ""),
                    "growth_outlook": m.get("growth_outlook", "")
                })

                # Connect to Holland traits
                primary_h = m.get("primary_holland")
                if primary_h and f"HOLLAND_{primary_h}" in self.nodes:
                    self._add_edge(major_id, f"HOLLAND_{primary_h}", "MATCHES_HOLLAND", weight=1.0, properties={"strength": "primary"})

                sec_h = m.get("secondary_holland")
                if sec_h and f"HOLLAND_{sec_h}" in self.nodes:
                    self._add_edge(major_id, f"HOLLAND_{sec_h}", "MATCHES_HOLLAND", weight=0.75, properties={"strength": "secondary"})

                # Connect to Gardner trait
                gardner_type = m.get("gardner_type")
                if gardner_type:
                    g_node = f"GARDNER_{gardner_type.upper()}"
                    if g_node in self.nodes:
                        self._add_edge(major_id, g_node, "EMPHASIZES_INTELLIGENCE", weight=0.85)

                # Connect to Exam Blocks
                for blk in m.get("exam_blocks", []):
                    blk_node = f"BLOCK_{blk}"
                    if blk_node in self.nodes:
                        self._add_edge(major_id, blk_node, "REQUIRES_BLOCK", weight=1.0)

                # Connect to Career Paths
                for career in m.get("popular_careers", []):
                    c_id = f"CAREER_{abs(hash(career)) % 100000}"
                    if c_id not in self.nodes:
                        self._add_node(c_id, "CareerPath", career, {
                            "title": career,
                            "salary_range": m.get("salary_range", "")
                        })
                    self._add_edge(major_id, c_id, "LEADS_TO", weight=0.9)

        # 5. Load Universities & connect to Majors
        uni_path = os.path.join(DATA_DIR, "universities_database.json")
        if os.path.exists(uni_path):
            with open(uni_path, "r", encoding="utf-8") as f:
                uni_data = json.load(f)

            for u in uni_data:
                uni_id = f"UNI_{u['code']}"
                self._add_node(uni_id, "University", u["name"], {
                    "code": u["code"],
                    "location": u.get("location", ""),
                    "region": u.get("region", ""),
                    "tuition": u.get("tuition_range", ""),
                    "website": u.get("website", ""),
                    "admission_methods": u.get("admission_methods", [])
                })

                for prog in u.get("majors", []):
                    m_code = prog.get("field_code") or prog.get("code")[:3]
                    # Link to major category node
                    major_node_id = f"MAJOR_{m_code}"
                    if major_node_id in self.nodes:
                        self._add_edge(uni_id, major_node_id, "OFFERS_MAJOR", weight=1.0, properties={
                            "program_name": prog.get("name"),
                            "major_code": prog.get("code"),
                            "block": prog.get("block"),
                            "score_2024": prog.get("score_2024"),
                            "score_2025": prog.get("score_2025"),
                            "score_pred_2026": prog.get("score_pred_2026")
                        })

    def get_overview_statistics(self) -> Dict[str, Any]:
        node_types = {}
        for n in self.nodes.values():
            lbl = n["label"]
            node_types[lbl] = node_types.get(lbl, 0) + 1

        edge_types = {}
        for e in self.edges:
            rel = e["relation_type"]
            edge_types[rel] = edge_types.get(rel, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_distribution": node_types,
            "edge_distribution": edge_types
        }

    def get_full_graph_data(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }

    def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        node = self.nodes.get(node_id)
        if not node:
            return None

        outgoing = self.adjacency.get(node_id, [])
        incoming = self.reverse_adjacency.get(node_id, [])

        connected_nodes = []
        for e in outgoing:
            target = self.nodes.get(e["target"])
            if target:
                connected_nodes.append({
                    "direction": "outgoing",
                    "relation": e["relation_type"],
                    "node": target
                })
        for e in incoming:
            source = self.nodes.get(e["source"])
            if source:
                connected_nodes.append({
                    "direction": "incoming",
                    "relation": e["relation_type"],
                    "node": source
                })

        return {
            "node": node,
            "outgoing_count": len(outgoing),
            "incoming_count": len(incoming),
            "connected_entities": connected_nodes
        }

    def query_multihop_advisory_paths(
        self,
        holland_code: str,
        target_block: str,
        estimated_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Multi-hop Knowledge Graph Traversal:
        Holland Code -> Majors -> Universities offering Major -> Career Paths
        Calculates holistic path confidence and admission feasibility.
        """
        paths = []
        holland_traits = [f"HOLLAND_{char}" for char in holland_code.upper()[:3] if f"HOLLAND_{char}" in self.nodes]
        target_block_node = f"BLOCK_{target_block.upper()}"

        # Step 1: Find Majors connected to Holland Traits and requiring the Target Block
        eligible_majors = set()
        for h_trait in holland_traits:
            for edge in self.reverse_adjacency.get(h_trait, []):
                if edge["relation_type"] == "MATCHES_HOLLAND":
                    major_id = edge["source"]
                    # Verify block requirement
                    major_outgoing = self.adjacency.get(major_id, [])
                    requires_target_block = any(e["target"] == target_block_node and e["relation_type"] == "REQUIRES_BLOCK" for e in major_outgoing)
                    if requires_target_block or not target_block:
                        eligible_majors.add(major_id)

        # Step 2: For each eligible major, find offering universities and career outlets
        for major_id in list(eligible_majors)[:8]:
            major_node = self.nodes[major_id]

            # Find Careers
            careers = []
            for e in self.adjacency.get(major_id, []):
                if e["relation_type"] == "LEADS_TO":
                    c_node = self.nodes.get(e["target"])
                    if c_node:
                        careers.append(c_node["name"])

            # Find Universities
            uni_offerings = []
            for e in self.reverse_adjacency.get(major_id, []):
                if e["relation_type"] == "OFFERS_MAJOR":
                    uni_node = self.nodes.get(e["source"])
                    if uni_node:
                        cutoff_2025 = e.get("properties", {}).get("score_2025", 25.0)
                        cutoff_pred = e.get("properties", {}).get("score_pred_2026", cutoff_2025)

                        tier = "Vừa sức (Target)"
                        if estimated_score:
                            delta = cutoff_pred - estimated_score
                            if delta > 1.0:
                                tier = "Mơ ước (Dream)"
                            elif delta < -1.5:
                                tier = "An toàn (Safety)"

                        uni_offerings.append({
                            "university_code": uni_node["properties"].get("code"),
                            "university_name": uni_node["name"],
                            "location": uni_node["properties"].get("location"),
                            "program_name": e.get("properties", {}).get("program_name"),
                            "cutoff_2025": cutoff_2025,
                            "cutoff_pred_2026": cutoff_pred,
                            "tier": tier
                        })

            paths.append({
                "major_code": major_node["properties"].get("code"),
                "major_name": major_node["name"],
                "salary_range": major_node["properties"].get("salary_range"),
                "growth_outlook": major_node["properties"].get("growth_outlook"),
                "leading_careers": careers[:4],
                "offering_universities": uni_offerings[:5]
            })

        return paths

graph_service = KnowledgeGraphService()
