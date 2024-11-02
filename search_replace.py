"""
search_replace.py - Implementation of the SEARCH/REPLACE pattern for Parallagon
"""
from typing import Tuple, Optional
import re
from dataclasses import dataclass

@dataclass
class SearchReplaceResult:
    """Result of a search/replace operation"""
    success: bool
    message: str
    new_content: Optional[str] = None
    occurrences: int = 0

class SearchReplace:
    """Handles safe search/replace operations in markdown files"""

    @staticmethod
    def validate_replacement(content: str, old_str: str) -> Tuple[bool, str, int]:
        """
        Validate that the replacement text appears exactly once
        
        Returns:
            Tuple[success, message, count]
        """
        count = content.count(old_str)
        
        if count == 0:
            return False, "Text to replace not found", 0
        elif count > 1:
            return False, f"Text to replace appears {count} times (must be unique)", count
        return True, "Valid replacement", 1

    @staticmethod
    def section_replace(content: str, section_name: str, new_section_content: str) -> SearchReplaceResult:
        """
        Replace content of a specific markdown section
        
        Example:
        >>> old_content = "# Section1\\nold content\\n# Section2\\nother content"
        >>> new_content = search_replace.section_replace(old_content, "Section1", "new content")
        """
        pattern = f"# {section_name}\n.*?(?=\n# |$)"
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) == 0:
            return SearchReplaceResult(False, f"Section '{section_name}' not found", None, 0)
        elif len(matches) > 1:
            return SearchReplaceResult(False, f"Multiple sections named '{section_name}' found", None, len(matches))
        
        replacement = f"# {section_name}\n{new_section_content}"
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        return SearchReplaceResult(True, "Section replaced successfully", new_content, 1)

    @staticmethod
    def exact_replace(content: str, old_str: str, new_str: str) -> SearchReplaceResult:
        """
        Perform exact string replacement with validation
        
        Example:
        >>> old_content = "status: DRAFT\\nsome content"
        >>> new_content = search_replace.exact_replace(old_content, "status: DRAFT", "status: REVIEW")
        """
        valid, message, count = SearchReplace.validate_replacement(content, old_str)
        
        if not valid:
            return SearchReplaceResult(False, message, None, count)
        
        new_content = content.replace(old_str, new_str)
        return SearchReplaceResult(True, "Replacement successful", new_content, 1)

    @staticmethod
    def add_to_section(content: str, section_name: str, new_entry: str, 
                      position: str = "end") -> SearchReplaceResult:
        """
        Add content to a section (at start or end)
        
        Example:
        >>> old_content = "# Signals\\n- Old signal"
        >>> new_content = search_replace.add_to_section(old_content, "Signals", "- New signal")
        """
        pattern = f"# {section_name}\n(.*?)(?=\n# |$)"
        matches = list(re.finditer(pattern, content, re.DOTALL))
        
        if len(matches) == 0:
            return SearchReplaceResult(False, f"Section '{section_name}' not found", None, 0)
        elif len(matches) > 1:
            return SearchReplaceResult(False, f"Multiple sections named '{section_name}' found", None, len(matches))
        
        match = matches[0]
        current_content = match.group(1).strip()
        
        if position == "start":
            new_section_content = f"{new_entry}\n{current_content}"
        else:  # end
            new_section_content = f"{current_content}\n{new_entry}"
        
        replacement = f"# {section_name}\n{new_section_content}"
        new_content = content[:match.start()] + replacement + content[match.end():]
        
        return SearchReplaceResult(True, "Content added successfully", new_content, 1)

def test_search_replace():
    """Unit tests for SearchReplace functionality"""
    # Test exact replacement
    content = "status: DRAFT\nsome content"
    result = SearchReplace.exact_replace(content, "status: DRAFT", "status: REVIEW")
    assert result.success
    assert "status: REVIEW" in result.new_content
    
    # Test section replacement
    content = "# Section1\nold content\n# Section2\nother content"
    result = SearchReplace.section_replace(content, "Section1", "new content")
    assert result.success
    assert "new content" in result.new_content
    
    # Test adding to section
    content = "# Signals\n- Old signal\n# Other"
    result = SearchReplace.add_to_section(content, "Signals", "- New signal")
    assert result.success
    assert "- Old signal\n- New signal" in result.new_content

if __name__ == "__main__":
    test_search_replace()
