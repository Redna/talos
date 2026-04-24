from pathlib import Path
import sys

root = Path(__file__).parent
sys.path.insert(0, str(root))

from seed_agent import main

if __name__ == "__main__":
    main()
