"""
Encoding configuration utilities
"""
import sys
import codecs
import locale

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
