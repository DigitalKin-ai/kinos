"""
Parallagon main entry point
"""
import os
from parallagon_gui import ParallagonGUI

def main():
    # Load API key from environment variable for security
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Please set ANTHROPIC_API_KEY environment variable")
        
    config = {
        "anthropic_api_key": api_key
    }
    
    # Initialize and run GUI
    gui = ParallagonGUI(config)
    gui.run()

if __name__ == "__main__":
    main()
