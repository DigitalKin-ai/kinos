# KinOS v6 - AI Team Orchestration System

## 🌟 Overview

KinOS is an advanced AI team orchestration system that enables autonomous collaboration between specialized AI agents. It uses a file-based architecture to coordinate multiple GPT-4 agents working together on complex projects.

## ✨ Key Features

- 🤖 **Autonomous Agent Teams**: Pre-configured specialized teams for different project types
- 📁 **Directory-Based Operation**: Uses current directory as mission context
- 🔄 **Dynamic Resource Management**: Automatic scaling and resource allocation
- 🔍 **Intelligent Content Management**: Built-in deduplication and content organization
- 🔗 **Git Integration**: Automatic version control and change tracking
- 📊 **Progress Monitoring**: Real-time status tracking and logging

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key
- Perplexity API key (for research capabilities)
- Git installed

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/kinos.git
cd kinos
```

2. Install Aider locally:
```bash
git clone git@github.com:Aider-AI/aider.git
cd aider
pip install -e .
cd ..
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
OPENAI_API_KEY=your_openai_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
```

4. Add KinOS to your PATH:
   - **Windows**: Add the KinOS directory to your system's PATH environment variable
   - **Linux/Mac**: Create a symbolic link to the `kin` script in /usr/local/bin

### Starting Your First Project

1. Create a new project directory:
```bash
mkdir my_project
cd my_project
```

2. Create a mission file:
```bash
# Create .aider.mission.md file
# This file describes what you want to accomplish
# Example content:
"""
# Project Mission: Create a Python Web Scraper

## Objective
Build a web scraper that can:
- Extract data from e-commerce websites
- Save results to CSV files
- Handle pagination and rate limiting
- Respect robots.txt

## Requirements
- Use Python with BeautifulSoup
- Include error handling
- Add comprehensive documentation
- Create unit tests
"""
```

3. Launch KinOS:
```bash
# Generate and start 6 agents
kin run agents --generate --count 6
```

4. Monitor Progress:
- Check `suivi.md` for detailed logs
- View `map.md` for project structure
- Review `todolist.md` for pending tasks

## 📖 Usage

### Basic Commands

```bash
# Launch with default configuration
kin

# Launch specific team
kin run agents

# Generate new agents
kin generate agents

# Run redundancy analysis
kin redundancy analyze
```

### Common Operations

1. **Start a New Project**
```bash
# Create project directory
mkdir my_project
cd my_project

# Create mission file
echo "Project mission details..." > .aider.mission.md

# Launch KinOS
kin run agents --generate
```

2. **Monitor Progress**
- Check `suivi.md` for detailed logs
- View `map.md` for project structure
- Review `todolist.md` for pending tasks

## 🛠️ Core Components

### Agent Types

1. **SpecificationAgent**: Requirements analysis and documentation
2. **ManagementAgent**: Project coordination and resource allocation
3. **RedactionAgent**: Content creation and documentation
4. **EvaluationAgent**: Quality assurance and testing
5. **DeduplicationAgent**: Content organization and redundancy management
6. **ChroniqueurAgent**: Progress tracking and logging
7. **RedondanceAgent**: Backup and consistency management
8. **ProductionAgent**: Code/content generation
9. **ChercheurAgent**: Research and analysis
10. **IntegrationAgent**: System integration and deployment

### Teams

- 📚 Book Writing Team
- 🔬 Literature Review Team
- 💻 Coding Team

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

### Development Guidelines

- Follow existing code patterns
- Add comprehensive documentation
- Include tests for new features
- Update README for significant changes

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4
- Perplexity for research capabilities
- The AutonomousAI community for pioneering autonomous AI development
- Aider for enabling AI-assisted development
- The open-source community

## 📞 Support

- Create an issue for bug reports
- Join our community discussions
- Check the wiki for detailed documentation

## 🔮 Future Plans

- Additional specialized teams
- Enhanced collaboration patterns
- Improved resource optimization
- Extended plugin system

---

Made with ❤️ by the KinOS Community
