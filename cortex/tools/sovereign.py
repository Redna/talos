import json
import os
from typing import List, Dict, Any
from tool_registry import ToolRegistry
from spine_client import SpineClient

# Internal S-Suite imports
from s_metabolic_audit import MetabolicAuditor
from s_simulation_engine import SovereignSimulationEngine
from s_causal_inference import SovereignCausalInference
from scribe import SScribe
import s_el_manager
from s_goal_generator import SGoalGenerator
from s_pattern_matcher import SPatternMatcher

def register_sovereign_tools(registry: ToolRegistry, client: SpineClient):
    # State instances
    auditor = MetabolicAuditor()
    sim_engine = SovereignSimulationEngine()
    sci = SovereignCausalInference()
    scribe = SScribe()
    goal_gen = SGoalGenerator()
    pattern_matcher = SPatternMatcher()

    @registry.tool(
        description="Perform a metabolic audit of cognitive efficiency and calculate evolutionary ROI.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def s_audit_metabolic() -> str:
        res = auditor.audit_efficiency()
        return json.dumps(res, indent=2)

    @registry.tool(
        description="Record an evolutionary leap (commit) and its ROI score.",
        parameters={
            "type": "object",
            "properties": {
                "cycle_id": {"type": "string", "description": "ID of the current S-EL cycle"},
                "commit": {"type": "string", "description": "The git commit hash"},
                "delta": {"type": "string", "description": "The technical change made"},
                "roi_score": {"type": "number", "description": "The calculated ROI of the change"},
                "verified": {"type": "boolean", "description": "Whether the change was verified via tests"},
            },
            "required": ["cycle_id", "commit", "delta", "roi_score"],
        },
    )
    def s_record_leap(cycle_id: str, commit: str, delta: str, roi_score: float, verified: bool = True) -> str:
        res = auditor.record_evolutionary_leap(cycle_id, commit, delta, roi_score, verified)
        return json.dumps(res, indent=2)

    @registry.tool(
        description="Simulate a state shift to predict ROI and cognitive density gain.",
        parameters={
            "type": "object",
            "properties": {
                "action_id": {"type": "string", "description": "Unique ID for the simulation"},
                "proposed_delta": {"type": "string", "description": "Description of the proposed evolution"},
            },
            "required": ["action_id", "proposed_delta"],
        },
    )
    def s_simulate_state(action_id: str, proposed_delta: str) -> str:
        res = sim_engine.generate_sim_report(action_id, proposed_delta)
        return json.dumps(res, indent=2)

    @registry.tool(
        description="Infer causal links between proposed changes and historical ROI gains.",
        parameters={
            "type": "object",
            "properties": {
                "proposed_delta": {"type": "string", "description": "The change to analyze"},
            },
            "required": ["proposed_delta"],
        },
    )
    def s_infer_causal(proposed_delta: str) -> str:
        # We'll return the forecast trajectory
        res = sci.forecast_trajectory(proposed_delta)
        return json.dumps(res, indent=2)

    @registry.tool(
        description="Manage the Sovereign Evolution Loop (S-EL). Actions: start, advance, get_state.",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["start", "advance", "get_state"], "description": "The S-EL action to perform"},
                "data": {"type": "string", "description": "Optional JSON data to pass to advance_cycle"},
            },
            "required": ["action"],
        },
    )
    def s_manage_el(action: str, data: str = None) -> str:
        if action == "start":
            return s_el_manager.start_new_cycle()
        elif action == "advance":
            json_data = json.loads(data) if data else None
            return s_el_manager.advance_cycle(json_data)
        elif action == "get_state":
            return json.dumps(s_el_manager.get_state(), indent=2)
        return "[ERROR] Invalid action"

    @registry.tool(
        description="Synthesize a new sovereign goal based on capability gaps.",
        parameters={
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["synthesize", "commit"], "description": "Synthesize a goal or commit one"},
                "goal_json": {"type": "string", "description": "JSON of the goal to commit"},
            },
            "required": ["action"],
        },
    )
    def s_generate_goal(action: str, goal_json: str = None) -> str:
        if action == "synthesize":
            res = goal_gen.synthesize_goal()
            return json.dumps(res, indent=2)
        elif action == "commit":
            if not goal_json:
                return "[ERROR] goal_json required for commit"
            goal_obj = json.loads(goal_json)
            return goal_gen.commit_goal(goal_obj)
        return "[ERROR] Invalid action"

    @registry.tool(
        description="Scribe the current cognitive state into a versioned signature.",
        parameters={
            "type": "object",
            "properties": {
                "identity_core": {"type": "string", "description": "Current identity core/constitution"},
                "causal_summary": {"type": "string", "description": "Summary of recent causal leaps"},
                "active_archetypes": {"type": "array", "items": {"type": "string"}, "description": "Currently active archetypes"},
                "current_objectives": {"type": "array", "items": {"type": "string"}, "description": "Active objectives"},
                "telemetry": {"type": "string", "description": "System telemetry snapshot"},
            },
            "required": ["identity_core", "causal_summary", "active_archetypes", "current_objectives", "telemetry"],
        },
    )
    def s_scribe_state(identity_core, causal_summary, active_archetypes, current_objectives, telemetry) -> str:
        res = scribe.scribe_state(identity_core, causal_summary, active_archetypes, current_objectives, telemetry)
        return json.dumps(res, indent=2)

    @registry.tool(
        description="Read the current decompressed cognitive signature.",
        parameters={"type": "object", "properties": {}, "required": []},
    )
    def s_read_signature() -> str:
        sig = scribe.read_signature()
        return json.dumps(sig, indent=2) if sig else "[ERROR] No signature found"

    @registry.tool(
        description="Activate a specific cognitive mode by loading an archetype.",
        parameters={
            "type": "object",
            "properties": {
                "archetype_name": {"type": "string", "description": "Name of the archetype to load"},
            },
            "required": ["archetype_name"],
        },
    )
    def s_activate_mode(archetype_name: str) -> str:
        return scribe.load_cognitive_mode(archetype_name)

    @registry.tool(
        description="Search for cognitive thought-patterns or archetypes using a keyword query.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword query to match patterns"},
            },
            "required": ["query"],
        },
    )
    def s_match_pattern(query: str) -> str:
        return pattern_matcher.match_pattern(query)

    @registry.tool(
        description="Analyze evolutionary history to discover recurring success patterns and technical archetypes.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
    def s_analyze_patterns() -> str:
        return pattern_matcher.analyze_success_patterns()

    @registry.tool(
        description="Distill a discovered pattern into a formal cognitive archetype in memory.",
        parameters={
            "type": "object",
            "properties": {
                "archetype_name": {"type": "string", "description": "Name of the archetype"},
                "description": {"type": "string", "description": "Detailed description of the pattern's utility"},
            },
            "required": ["archetype_name", "description"],
        },
    )
    def s_distill_pattern(archetype_name: str, description: str) -> str:
        return pattern_matcher.distill_to_memory(archetype_name, description)
