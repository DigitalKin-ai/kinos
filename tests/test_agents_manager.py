import unittest
import os
import tempfile
from managers.agents_manager import AgentsManager

class TestAgentsManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.manager = AgentsManager()
        
        # Create a temporary mission file
        self.temp_dir = tempfile.mkdtemp()
        self.mission_file = os.path.join(self.temp_dir, "test_mission.md")
        with open(self.mission_file, 'w') as f:
            f.write("""# Test Mission
            
## Objectives
- Build a test system
- Implement core features
- Validate functionality""")

    def tearDown(self):
        """Clean up after each test method."""
        # Remove temporary files
        if os.path.exists(self.mission_file):
            os.remove(self.mission_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
            
        # Clean up any generated agent files
        for i in range(8):
            agent_file = f".aider.agent.agent_{i+1}.md"
            if os.path.exists(agent_file):
                os.remove(agent_file)

    def test_generate_agents_valid_mission(self):
        """Test agent generation with valid mission file."""
        self.manager.generate_agents(self.mission_file)
        
        # Verify that 8 agent files were created
        for i in range(8):
            agent_file = f".aider.agent.agent_{i+1}.md"
            self.assertTrue(os.path.exists(agent_file))
            
    def test_generate_agents_invalid_mission(self):
        """Test agent generation with invalid mission file."""
        invalid_path = "nonexistent_mission.md"
        with self.assertRaises(ValueError):
            self.manager.generate_agents(invalid_path)
            
    def test_agent_file_content(self):
        """Test that generated agent files have valid content."""
        self.manager.generate_agents(self.mission_file)
        
        # Check content of first agent file
        with open(".aider.agent.agent_1.md", 'r') as f:
            content = f.read()
            self.assertIn("# Agent Configuration", content)
            self.assertIn("## Role", content)
            self.assertIn("## Capabilities", content)
            self.assertIn("## Success Metrics", content)
            
    def test_generate_agents_default_mission(self):
        """Test agent generation with default mission file path."""
        # Create default mission file
        with open(".aider.mission.md", 'w') as f:
            f.write("# Default Test Mission\n\n## Objectives\n- Test default behavior")
            
        try:
            self.manager.generate_agents()  # Using default path
            
            # Verify agent files were created
            self.assertTrue(os.path.exists(".aider.agent.agent_1.md"))
            
        finally:
            # Cleanup default mission file
            if os.path.exists(".aider.mission.md"):
                os.remove(".aider.mission.md")

if __name__ == '__main__':
    unittest.main()
