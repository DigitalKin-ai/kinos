"""
Parallagon main entry point
"""
import os
from parallagon_gui import ParallagonGUI

def main():
    # Load API key from environment variable for security
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if not anthropic_key or not openai_key:
        raise ValueError("Please set both ANTHROPIC_API_KEY and OPENAI_API_KEY environment variables")
        
    config = {
        "anthropic_api_key": anthropic_key,
        "openai_api_key": openai_key
    }
    
    # Initialize and run GUI
    gui = ParallagonGUI(config)
    gui.run()

if __name__ == "__main__":
    main()
