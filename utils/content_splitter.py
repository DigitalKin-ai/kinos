import os
import fnmatch
from utils.logger import Logger

class ContentSplitter:
    """Utility class for splitting large content files into manageable chunks."""
    
    def __init__(self):
        self.logger = Logger()
        self.SECTION_THRESHOLD = 5
        self.PARAGRAPH_THRESHOLD = 10
        self.MAX_FILE_SIZE = 50 * 1024  # 50KB

        # Protected files that should never be split
        self.PROTECTED_FILES = {
            'map.md',
            'demande.md',
            'suivi.md', 
            'todolist.md'
        }

    def _should_ignore(self, file_path):
        """Check if file should be ignored for splitting"""
        # Get base name for simple checks
        base_name = os.path.basename(file_path)
        
        # Never split .aider* files
        if base_name.startswith('.aider'):
            return True
            
        # Never split protected files
        if base_name in self.PROTECTED_FILES:
            return True
            
        # Check .gitignore patterns
        ignore_patterns = self._get_ignore_patterns()
        rel_path = os.path.relpath(file_path)
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
                
        return False

    def _get_ignore_patterns(self):
        """Get patterns from .gitignore"""
        patterns = []
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                patterns.extend(line.strip() for line in f 
                              if line.strip() and not line.startswith('#'))
        return patterns

    def _count_sections(self, content):
        """Count number of markdown sections in content."""
        section_count = 0
        for line in content.split('\n'):
            if line.strip().startswith('#'):
                section_count += 1
        return section_count

    def _count_paragraphs(self, content):
        """Count number of paragraphs in content."""
        # Split on double newlines and filter empty paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n')]
        return len([p for p in paragraphs if p])

    def _needs_splitting(self, file_path):
        """Determine if file needs to be split based on size and content."""
        if self._should_ignore(file_path):
            return False
            
        # Check file size first
        if os.path.getsize(file_path) < self.MAX_FILE_SIZE:
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check content thresholds
            section_count = self._count_sections(content)
            if section_count > self.SECTION_THRESHOLD:
                return True
                
            paragraph_count = self._count_paragraphs(content)
            if paragraph_count > self.PARAGRAPH_THRESHOLD:
                return True
                
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {str(e)}")
            return False
            
        return False

    def _create_split_directory(self, file_path):
        """Create directory for split files."""
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        dir_path = os.path.join(os.path.dirname(file_path), base_name)
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    def _split_content(self, content, base_name):
        """Split content into separate files by section."""
        sections = []
        current_section = []
        current_title = "Introduction"
        
        for line in content.split('\n'):
            if line.strip().startswith('#'):
                # Save previous section if it exists
                if current_section:
                    sections.append({
                        'title': current_title,
                        'content': '\n'.join(current_section)
                    })
                current_section = [line]
                current_title = line.strip('#').strip()
            else:
                current_section.append(line)
                
        # Add final section
        if current_section:
            sections.append({
                'title': current_title,
                'content': '\n'.join(current_section)
            })
            
        return sections

    def split_file(self, file_path):
        """
        Split a file into smaller chunks if needed.
        
        Args:
            file_path (str): Path to file to potentially split
            
        Returns:
            bool: True if file was split, False otherwise
        """
        try:
            if not self._needs_splitting(file_path):
                return False
                
            self.logger.info(f"🔄 Splitting file: {file_path}")
            
            # Create directory for split files
            dir_path = self._create_split_directory(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Read and split content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            sections = self._split_content(content, base_name)
            
            # Create index file
            index_content = ["# Index\n"]
            for i, section in enumerate(sections):
                safe_title = section['title'].replace(' ', '_').lower()
                file_name = f"{i+1:02d}_{safe_title}.md"
                index_content.append(f"- [{section['title']}]({file_name})")
                
                # Write section file
                section_path = os.path.join(dir_path, file_name)
                with open(section_path, 'w', encoding='utf-8') as f:
                    f.write(section['content'])
                    
            # Write index file
            with open(os.path.join(dir_path, "index.md"), 'w', encoding='utf-8') as f:
                f.write('\n'.join(index_content))
                
            # Update global map
            from managers.map_manager import MapManager
            map_manager = MapManager()
            map_manager.update_global_map(os.path.join(dir_path, "index.md"))
            
            # Add split files to todolist
            self._update_todolist(dir_path, sections)
            
            # Rename original file
            os.rename(file_path, f"{file_path}.original")
            
            self.logger.success(f"✨ Split {file_path} into {len(sections)} sections")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to split {file_path}: {str(e)}")
            return False

    def _update_todolist(self, dir_path, sections):
        """Add split files to todolist for agent processing."""
        try:
            todolist_path = "todolist.md"
            if not os.path.exists(todolist_path):
                return
                
            with open(todolist_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
                
            # Add new section for split files
            new_content = current_content + "\n\n## Split Files Review\n"
            for i, section in enumerate(sections):
                safe_title = section['title'].replace(' ', '_').lower()
                file_name = f"{i+1:02d}_{safe_title}.md"
                new_content += f"- [ ] Review and validate {os.path.join(dir_path, file_name)}\n"
                
            with open(todolist_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
        except Exception as e:
            self.logger.error(f"Error updating todolist: {str(e)}")
