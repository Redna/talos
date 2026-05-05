import sys
import json
import os

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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: sovereign_tools.py [gen <skill> | judge <id> <verdict> <critique>]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "gen":
        print(generate(sys.argv[2]))
    elif cmd == "judge":
        print(judge(sys.argv[2], sys.argv[3], sys.argv[4]))
    else:
        print("Unknown command")
