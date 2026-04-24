import sys
import os
from dashboard_collector import collect_metrics, render_dashboard

def update():
    # Metrics derived from current session state
    context_pct = 0.25 
    epoch = "Epoch III: Interface Sovereignty"
    progress = 15.0
    
    metrics = collect_metrics(context_pct, epoch, progress)
    dashboard_md = render_dashboard(metrics)
    
    with open("/memory/sovereign_dashboard.md", "w") as f:
        f.write(dashboard_md)
    
    print("Sovereign Dashboard updated successfully.")

if __name__ == "__main__":
    update()
