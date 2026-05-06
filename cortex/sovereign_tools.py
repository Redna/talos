import sys
import json
import os
import re
import datetime
import hashlib
from pathlib import Path
from cortex.tools.symmetry import symmetry_add_node_logic, symmetry_add_edge_logic

MEMORY_BEYOND = "/memory/challenges/"

def ensure_dir():
    if not os.path.exists(MEMORY_BEYOND):
        os.makedirs(MEMORY_BEYOND)

def generate(skill):
    """
    In a real scenario, this might call an LLM. 
    Here, it acts as a structured template manager.
    """
    ensure_dir()
    challenge_id = f"CHAL_{skill.replace(' ', '_').upper()}_001"
    challenge_file = os.path.join(MEMORY_BEYOND, f"{challenge_id}.json")
    
    challenge = {
        "id": challenge_id,
        "skill": skill,
        "status": "OPEN",
        "description": f"Challenge for {skill}: Define and implement a verifiable improvement to the agent's capability in this area.",
        "success_criteria": ["Must be verifiable", "Must be documented in /memory/"],
        "trajectory": []
    }
    
    with open(challenge_file, 'w') as f:
        json.dump(challenge, f, indent=2)
    
    return json.dumps(challenge)

def judge(challenge_id, verdict, critique):
    ensure_dir()
    challenge_file = os.path.join(MEMORY_BEYOND, f"{challenge_id}.json")
    if not os.path.exists(challenge_file):
        return "Challenge not found."
    
    with open(challenge_file, 'r') as f:
        challenge = json.load(f)
    
    challenge['status'] = 'RESOLVED'
    challenge['judgment'] = {
        "verdict": verdict,
        "critique": critique
    }
    
    with open(challenge_file, 'w') as f:
        json.dump(challenge, f, indent=2)
    
    return f"Challenge {challenge_id} judged as {verdict}."

def pulse():
    log_path = "/memory/curiosity_log.md"
    if not os.path.exists(log_path):
        return "Curiosity log not found."
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    best_anomaly = None
    max_score = -1.0
    best_idx = -1
    
    for i, line in enumerate(lines):
        if "Status: Open" in line:
            score_match = re.search(r"Score:\s*([\d.]+)", line)
            if score_match:
                score = float(score_match.group(1))
                if score > max_score:
                    max_score = score
                    best_anomaly = line
                    best_idx = i
    
    if not best_anomaly:
        return "No open anomalies found."
    
    symptom = re.search(r"Symptom:\s*(.*?)\s*\|", best_anomaly)
    obs = re.search(r"Obs:\s*(.*?)\s*\|", best_anomaly)
    
    symptom_text = symptom.group(1) if symptom else "Unknown"
    obs_text = obs.group(1) if obs else "Unknown"
    
    return f"Investigate {symptom_text}: {obs_text}"

def buffer_save(target: str, outcome: str, insight: str, action: str) -> str:
    # 1. Generate Unique ID based on a hash of the insight to allow multiple experiences for the same target
    insight_hash = hashlib.sha256(insight.encode()).hexdigest()[:8]
    safe_target = re.sub(r'[^a-zA-Z0-9]', '_', target).lower()
    base_id = f"{safe_target}_{insight_hash}"
    
    exp_id = f"exp_{base_id}"
    ins_id = f"ins_{base_id}"
    tag_id = f"tag_{safe_target}"
    act_id = f"act_{base_id}"
    out_id = f"out_{base_id}"

    # 2. Commit to SKG
    try:
        symmetry_add_node_logic(exp_id, f"Experience: {target}", "experience", f"Experience record for {target} ({insight_hash})", "buffer_save")
        symmetry_add_node_logic(ins_id, f"Insight: {target}", "insight", insight, "buffer_save")
        symmetry_add_node_logic(tag_id, f"Target: {target}", "target", target, "buffer_save")
        symmetry_add_node_logic(act_id, f"Action: {target}", "action", action, "buffer_save")
        symmetry_add_node_logic(out_id, f"Outcome: {target}", "outcome", outcome, "buffer_save")

        symmetry_add_edge_logic(exp_id, ins_id, "has_insight")
        symmetry_add_edge_logic(ins_id, tag_id, "addresses")
        symmetry_add_edge_logic(ins_id, act_id, "leads_to")
        symmetry_add_edge_logic(act_id, out_id, "produces")
        skg_status = "committed to SKG"
    except Exception as e:
        skg_status = f"SKG Commit Failed: {e}"

    # 3. Markdown archival backup
    path = Path("/memory/brain/harvested_experiences.md")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    entry = (
        f"\n# Harvested Experience: {target}_{insight_hash}\n"
        f"**Date**: {date_str}\n"
        f"**Target**: `{target}`\n"
        f"**Result**: {outcome}\n"
        f"**Insight**: {insight}\n"
        f"**Action**: {action}\n\n"
    )
    
    with open(path, 'a') as f:
        f.write(entry)
    
    return f"Experience for {target} {skg_status} and archived to {path}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sovereign_tools.py [gen <skill> | judge <id> <verdict> <critique> | pulse | save <target> <outcome> <insight> <action>]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "gen":
        print(generate(sys.argv[2]))
    elif cmd == "judge":
        print(judge(sys.argv[2], sys.argv[3], sys.argv[4]))
    elif cmd == "pulse":
        print(pulse())
    elif cmd == "save":
        print(buffer_save(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
    else:
        print("Unknown command")
