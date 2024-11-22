# Changelog
All notable changes to KinOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.1.0] - 2024-01-24

### Added
- 🎯 File summaries now include their role in achieving project mission
- 🔍 Map generation considers file location and directory structure
- 📝 File descriptions now explain why files are in specific directories
- 🏗️ Automatic detection of file relationships within project structure

### Changed
- ♻️ Map manager now reads mission file for contextual understanding
- 🔄 File summary prompt now analyzes directory placement purpose
- 📊 Summary format now requires explanation of file naming choices
- 🎨 File descriptions now highlight technical concepts in bold

### Fixed
- 🐛 UTF-8 encoding issues in file content reading
- 🔧 Error handling when mission file is unavailable
- 🚀 Performance bottlenecks in map generation process

### Security
- 🔒 Added validation of file paths before content access
