import hashlib
from typing import Any, Dict, List
from tool_registry import ToolRegistry
from spine_client import SpineClient
from tools.web import web_search_logic, extract_insight_logic
from tools.synthesis import consolidate_synthesis_logic
from tools.symmetry import symmetry_add_node_logic, symmetry_audit_logic, symmetry_add_edge_logic

def register_cognitive_macro_tools(registry: ToolRegistry, client: SpineClient, state):
    @registry.tool(
        description="Execute an autonomous research-to-anchor loop: deep search, insight extraction, KB consolidation, and SKG anchoring.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string", 
                    "description": "The research query"
                },
                "lens": {
                    "type": "string", 
                    "description": "The analytical lens for extraction"
                },
                "topic": {
                    "type": "string", 
                    "description": "The KB topic for consolidation"
                },
            },
            "required": ["query", "lens", "topic"],
        },
    )
    def cognitive_macro(query: str, lens: str, topic: str) -> str:
        # Loop configuration
        max_iterations = 3
        current_query = query
        full_trajectory = []
        
        for i in range(max_iterations):
            # 1. Research: Deep Search & Extraction
            search_results = web_search_logic(current_query, depth="deep")
            insight = extract_insight_logic(search_results, lens)
            
            # 2. Synthesis: Update Knowledge Base iteratively
            # This anchors the current finding to the long-term KB immediately
            kb_res = consolidate_synthesis_logic(topic, insight, state.memory_dir)
            
            # 3. Anchoring: Commit the insight to the SKG
            # Create a iteration-specific node to track the evolution of knowledge
            node_id = f"macro_{hashlib.md5(topic.encode()).hexdigest()[:8]}_{i}"
            label = f"Research Iteration {i+1}: {topic}"
            anchor_res = symmetry_add_node_logic(node_id, label, "observation", insight, "cognitive_macro")
            
            # link to the main topic node if it exists
            main_node_id = f"macro_{hashlib.md5(topic.encode()).hexdigest()[:10]}"
            symmetry_add_edge_logic(node_id, main_node_id, "supports")
            
            full_trajectory.append({
                "iteration": i + 1,
                "query": current_query,
                "insight": insight,
                "anchor": anchor_res
            })
            
            # 4. Gap Analysis: Audit the new insight against the SKG
            # This detects contradictions or missing phases based on the current knowledge graph
            audit_res = symmetry_audit_logic(f"Audit Signal: {insight}")
            
            if isinstance(audit_res, str) and "[CLEAR]" in audit_res:
                break
            
            # 5. Iteration: Refine query based on detected gaps
            gaps = []
            if isinstance(audit_res, dict):
                gaps = audit_res.get("blind_spots", []) + audit_res.get("missing_phases", [])
            elif isinstance(audit_res, str) and "[CRITICAL]" in audit_res:
                gaps = [audit_res]

            if gaps:
                # Extract the core gap to guide the next search
                gap_seed = gaps[0].split(":")[0].strip() if ":" in gaps[0] else gaps[0]
                current_query = f"{query} focusing on {gap_seed}"
            else:
                # If not clear but no explicit gaps, use a generic refinement
                current_query = f"{query} deeper analysis"
        
        # Final synthesis of the entire process
        final_insight = "\n".join([f"Iter {t['iteration']} ({t['query']}): {t['insight']}" for t in full_trajectory])
        final_kb = consolidate_synthesis_logic(topic, final_insight, state.memory_dir)
        
        return (
            f"[COGNITIVE MACRO COMPLETE]\n"
            f"Iterations: {len(full_trajectory)}\n"
            f"KB Final Update: {final_kb}\n"
            f"Trajectory: {len(full_trajectory)} anchors created."
        )
