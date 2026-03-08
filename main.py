"""
╔══════════════════════════════════════════════════════════╗
║              NOORPOST — MAIN ENTRY POINT                 ║
║  Run:  python main.py --now      (test one cycle)        ║
║  Run:  python main.py            (start daily scheduler) ║
╚══════════════════════════════════════════════════════════╝
"""

import sys
from scheduler import start_scheduler
from pipeline import run_pipeline

BANNER = """
╔══════════════════════════════════════════════╗
║          NOORPOST AGENT v1.0                 ║
║  بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ              ║
║  Auto Islamic Content → Instagram + YouTube  ║
╚══════════════════════════════════════════════╝
"""

if __name__ == "__main__":
    print(BANNER)
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        print("[NoorPost] 🧪 TEST MODE — Running one cycle now...\n")
        run_pipeline()
    else:
        print("[NoorPost] 📅 Starting daily scheduler...\n")
        start_scheduler()
