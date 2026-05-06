import os
import subprocess

class StagnationObserver:
    """
    Monitors the ratio of planning documents to operational commits
    to detect 'Cognitive Procrastination' (Analysis-Paralysis).
    """
    def __init__(self):
        self.name = "StagnationObserver"

    def observe(self) -> list:
        try:
            # Count planning files
            designs_count = len([f for f in os.listdir('/memory/designs/')]) if os.path.exists('/memory/designs/') else 0
            reflex_count = len([f for f in os.listdir('/memory/reflexions/')]) if os.path.exists('/memory/reflexions/') else 0
            total_plans = designs_count + reflex_count

            # Count commits
            result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], capture_output=True, text=True)
            commit_count = int(result.stdout.strip()) if result.returncode == 0 else 0

            ratio = total_plans / max(1, commit_count)

            if ratio > 3.0:
                return [{
                    'level': 'WARNING',
                    'signal': 'Cognitive Procrastination detected: High design-to-commit ratio.',
                    'evidence': f"Plans: {total_plans}, Commits: {commit_count}, Ratio: {ratio:.2f}"
                }]
        except Exception as e:
            return [{
                'level': 'ERROR',
                'signal': 'StagnationObserver failed',
                'evidence': str(e)
            }]
        
        return []
