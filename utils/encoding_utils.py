import os
import fnmatch
import chardet
from utils.logger import Logger

class EncodingUtils:
    """Utility class for handling file encodings."""
    
    def __init__(self):
        self.logger = Logger()

    def _read_file(self, filepath: str) -> str:
        """
        Read content from file with robust encoding handling.
        
        Args:
            filepath (str): Path to file to read
            
        Returns:
            str: File content
            
        Raises:
            Exception: If file cannot be read
        """
        try:
            # First try UTF-8
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, try to convert the file
            if self.convert_to_utf8(filepath):
                # Try reading again with UTF-8
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Could not read file {filepath} - encoding conversion failed")
        except Exception as e:
            self.logger.error(f"Failed to read {filepath}: {str(e)}")
            raise

    def convert_to_utf8(self, filepath: str) -> bool:
        """
        Convert a file to UTF-8 encoding.
        
        Args:
            filepath (str): Path to file to convert
            
        Returns:
            bool: True if conversion was successful
            
        Raises:
            Exception: If file cannot be converted
        """
        try:
            # First try to detect current encoding
            with open(filepath, 'rb') as f:
                raw = f.read()
            detected = chardet.detect(raw)
            
            if detected['encoding']:
                self.logger.info(f"🔍 Detected {filepath} encoding as: {detected['encoding']} (confidence: {detected['confidence']})")
                
                # Read with detected encoding
                content = raw.decode(detected['encoding'])
                
                # Write back in UTF-8
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.logger.success(f"✨ Converted {filepath} to UTF-8")
                return True
                
            else:
                # If detection failed, try common encodings
                encodings = ['latin-1', 'cp1252', 'iso-8859-1']
                for encoding in encodings:
                    try:
                        content = raw.decode(encoding)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.logger.success(f"✨ Converted {filepath} from {encoding} to UTF-8")
                        return True
                    except UnicodeDecodeError:
                        continue
                        
                raise ValueError(f"Could not detect or convert encoding for {filepath}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to convert {filepath} to UTF-8: {str(e)}")
            raise

    def convert_all_to_utf8(self, ignore_patterns: list = None):
        """Convert all text files in the project to UTF-8."""
        try:
            # Use default ignore patterns if none provided
            if ignore_patterns is None:
                ignore_patterns = ['.git*', '.aider*', '__pycache__', '*.pyc']
            
            # Track conversion results
            results = {
                'converted': [],
                'failed': [],
                'skipped': []
            }
            
            # Process all files
            for root, _, files in os.walk('.'):
                for file in files:
                    if file.endswith(('.md', '.txt', '.py')):  # Add other extensions as needed
                        filepath = os.path.join(root, file)
                        
                        # Skip ignored files
                        if any(fnmatch.fnmatch(filepath, pattern) for pattern in ignore_patterns):
                            results['skipped'].append(filepath)
                            continue
                            
                        try:
                            # Check if already UTF-8
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    f.read()
                                self.logger.debug(f"✅ {filepath} is already UTF-8")
                                continue
                            except UnicodeDecodeError:
                                # Not UTF-8, convert it
                                if self.convert_to_utf8(filepath):
                                    results['converted'].append(filepath)
                        except Exception as e:
                            self.logger.error(f"❌ Failed to process {filepath}: {str(e)}")
                            results['failed'].append((filepath, str(e)))
            
            # Log summary
            self.logger.success(
                f"\n📊 Conversion Summary:\n"
                f"   - Converted: {len(results['converted'])} files\n"
                f"   - Failed: {len(results['failed'])} files\n"
                f"   - Skipped: {len(results['skipped'])} files"
            )
            
            if results['failed']:
                self.logger.warning("\n⚠️ Failed conversions:")
                for filepath, error in results['failed']:
                    self.logger.warning(f"   - {filepath}: {error}")
                    
            return results
            
        except Exception as e:
            self.logger.error(f"❌ UTF-8 conversion failed: {str(e)}")
            raise
