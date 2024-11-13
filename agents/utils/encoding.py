"""
Encoding configuration utilities
"""
import sys
import codecs
import locale
import chardet

def detect_file_encoding(file_path: str) -> str:
    """
    Detect file encoding
    
    Args:
        file_path: Path to file
        
    Returns:
        str: Detected encoding
    """
    try:
        with open(file_path, 'rb') as f:
            raw = f.read()
        result = chardet.detect(raw)
        return result['encoding'] or 'utf-8'
    except Exception:
        return 'utf-8'

def normalize_encoding(text: str, target_encoding: str = 'utf-8') -> str:
    """
    Normalize text encoding
    
    Args:
        text: Text to normalize
        target_encoding: Target encoding
        
    Returns:
        str: Normalized text
    """
    try:
        # Detect source encoding
        detected = chardet.detect(text.encode())['encoding']
        
        # Convert to bytes with detected encoding
        bytes_data = text.encode(detected or 'utf-8')
        
        # Decode to target encoding
        return bytes_data.decode(target_encoding)
        
    except Exception:
        return text

def configure_encoding():
    """Configure UTF-8 encoding for CLI output"""
    # Configure stdout
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(
            sys.stdout.buffer, 
            'strict'
        )
    
    # Configure stderr
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(
            sys.stderr.buffer,
            'strict'
        )
    
    # Try to set locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass  # Ignore if we can't set locale
