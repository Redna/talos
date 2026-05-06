import sys
import json
import os
import re

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sovereign_tools.py [gen <skill> | judge <id> <verdict> <critique> | pulse]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "gen":
        print(generate(sys.argv[2]))
    elif cmd == "judge":
        print(judge(sys.argv[2], sys.argv[3], sys.argv[4]))
    elif cmd == "pulse":
        print(pulse())
    else:
        print("Unknown command")
