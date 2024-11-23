# Changelog
All notable changes to KinOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.1.0] - 2024-01-24

### Added
- ✨ Added interactive mode with `kin interactive` command
- 🎯 Two-phase planning and action workflow
- 📝 Enhanced objective processing with GPT
- 🔍 Smart file context analysis

### Removed
- 🗑️ Removed dependency on .aider.map.{name}.md files
- 🔄 Switched to aider's automatic file handling

### Added
- ✨ Added --model parameter (currently supports gpt-4o-mini)
- 🎯 Enhanced map generation with mission context
- 🔍 Improved file role detection in project structure
- 📝 Better directory context in file descriptions

### Changed
- ♻️ Refactored map manager for better mission integration
- 🔄 Improved file context analysis
- 📊 Enhanced file relationship mapping
- 🎨 Clearer file role documentation
- 🌐 Translated remaining French phrases to English for consistency

### Fixed
- 🐛 UTF-8 encoding issues
- 🔧 Mission file validation
- 🚀 Map generation performance

### Security
- 🔒 Added path validation checks
