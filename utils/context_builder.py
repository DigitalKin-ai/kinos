import os
import fnmatch
from pathlib import Path
import mimetypes
from typing import List, Set

class ContextBuilder:
    """Utility class for building a complete project context file."""
    
    def __init__(self):
        # Initialize mimetypes
        mimetypes.init()
        
        # Text file extensions to always include
        self.text_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.json', 
            '.yaml', '.yml', '.ini', '.cfg', '.conf', '.sh', '.bat',
            '.ps1', '.env', '.rst', '.xml', '.csv', '.sql', '.htaccess',
            '.gitignore', '.dockerignore', '.editorconfig', '.toml',
            '.properties', '.gradle', '.jsx', '.tsx', '.vue', '.php',
            '.rb', '.pl', '.java', '.kt', '.go', '.rs', '.c', '.cpp',
            '.h', '.hpp', '.cs', '.vb', '.swift', '.r', '.scala',
            '.clj', '.ex', '.exs', '.erl', '.fs', '.fsx', '.dart'
        }

    def _get_ignore_patterns(self) -> List[str]:
        """Get patterns from .gitignore and .aiderignore."""
        patterns = []
        
        # Always exclude these patterns
        patterns.extend([
            '.git*',
            '.aider*',
            'node_modules',
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.DS_Store',
            'Thumbs.db'
        ])
        
        # Read .gitignore
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r', encoding='utf-8') as f:
                patterns.extend(line.strip() for line in f 
                              if line.strip() and not line.startswith('#'))
                
        # Read .aiderignore
        if os.path.exists('.aiderignore'):
            with open('.aiderignore', 'r', encoding='utf-8') as f:
                patterns.extend(line.strip() for line in f 
                              if line.strip() and not line.startswith('#'))
                
        return patterns

    def _should_ignore(self, file_path: str, ignore_patterns: List[str]) -> bool:
        """Check if file should be ignored based on patterns."""
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def _is_text_file(self, file_path: str) -> bool:
        """
        Determine if a file is a text file based on extension and content analysis.
        """
        # Check extension first
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.text_extensions:
            return True

        # Try to detect mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('text/'):
            return True

        # Try to read file as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Read first 1024 bytes
            return True
        except UnicodeDecodeError:
            return False

    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        return os.path.getsize(file_path)

    def build_context(self, root_dir: str = ".", output_file: str = "context.md", 
                     max_file_size: int = 1024 * 1024) -> None:
        """
        Build context file from all text files in directory.
        
        Args:
            root_dir: Root directory to start from
            output_file: Output context file name
            max_file_size: Maximum file size to include (default 1MB)
        """
        ignore_patterns = self._get_ignore_patterns()
        processed_files: Set[str] = set()
        
        with open(output_file, 'w', encoding='utf-8') as out:
            out.write("# Project Context\n\n")
            out.write("This file contains all text files from the project for context.\n\n")
            
            for root, dirs, files in os.walk(root_dir):
                # Remove ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore(
                    os.path.join(root, d), ignore_patterns
                )]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)
                    
                    # Skip if file should be ignored
                    if self._should_ignore(rel_path, ignore_patterns):
                        continue
                        
                    # Skip if already processed
                    if file_path in processed_files:
                        continue
                        
                    # Skip if file is too large
                    if self._get_file_size(file_path) > max_file_size:
                        print(f"Skipping large file: {rel_path}")
                        continue
                    
                    # Process only text files
                    if self._is_text_file(file_path):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            out.write(f"\n## File: {rel_path}\n")
                            out.write("```\n")
                            out.write(content)
                            out.write("\n```\n")
                            
                            processed_files.add(file_path)
                            print(f"Added: {rel_path}")
                            
                        except Exception as e:
                            print(f"Error processing {rel_path}: {str(e)}")

def main():
    """Main function to run the context builder."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build project context file.')
    parser.add_argument('--dir', default='.', help='Root directory to process')
    parser.add_argument('--output', default='context.md', help='Output file name')
    parser.add_argument('--max-size', type=int, default=1024*1024, 
                       help='Maximum file size in bytes (default 1MB)')
    
    args = parser.parse_args()
    
    builder = ContextBuilder()
    builder.build_context(args.dir, args.output, args.max_size)
    print(f"\nContext file created: {args.output}")

if __name__ == "__main__":
    main()
