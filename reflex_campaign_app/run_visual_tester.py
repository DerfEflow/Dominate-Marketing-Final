#!/usr/bin/env python3
"""
Launch script for the visual content tester
Run this to see detailed output from each module
"""

import subprocess
import sys
import os

def main():
    print("🎨 LAUNCHING VISUAL CONTENT TESTER")
    print("=" * 50)
    print("This will start a Reflex app to visually test each module")
    print("You can see detailed output for:")
    print("  • Web Scraper - Business data extraction")  
    print("  • Competitor Analyzer - Competitor discovery")
    print("  • AI Strategy Generator - Marketing strategies")
    print("  • Content Generator - Images, videos, and text")
    print()
    print("The app will run on: http://localhost:3000")
    print("=" * 50)
    
    try:
        # Change to the app directory
        app_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(app_dir)
        
        # Run the visual tester
        cmd = [sys.executable, "-m", "reflex", "run", "--app", "visual_tester:visual_app"]
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n\nVisual tester stopped by user")
    except Exception as e:
        print(f"\nError launching visual tester: {e}")
        print("\nTry running manually:")
        print(f"  cd {app_dir}")
        print("  python -m reflex run --app visual_tester:visual_app")

if __name__ == "__main__":
    main()