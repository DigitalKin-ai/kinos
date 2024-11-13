"""
Script to compress large Aider discussion files using GPT-4 in a map-reduce pattern
"""
import os
import glob
import time
from typing import List, Optional
import anthropic
from pathlib import Path
from utils.logger import Logger
from utils.path_manager import PathManager

def split_content(content: str, chunk_size: int = 50000) -> List[str]:
    """Split content into chunks of approximately equal size"""
    # Split on newlines to preserve message boundaries
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_size = len(line) + 1  # +1 for newline
        if current_size + line_size > chunk_size and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size
            
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
        
    return chunks

def summarize_chunk(chunk: str, client: anthropic.Anthropic) -> Optional[str]:
    """Summarize a chunk of conversation using Claude"""
    try:
        prompt = f"""Summarize this Aider conversation chunk while preserving the most important technical details and decisions. Focus on:
- Key technical decisions and their rationale
- Important changes and improvements
- Critical insights and learnings
- Major refactoring decisions

Conversation chunk:
{chunk}

Provide a concise but technically detailed summary."""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
        
    except Exception as e:
        print(f"Error summarizing chunk: {str(e)}")
        return None

def merge_summaries(summaries: List[str], client: anthropic.Anthropic) -> Optional[str]:
    """Merge multiple summaries into a cohesive final summary"""
    try:
        combined = "\n\n".join(summaries)
        
        prompt = f"""Combine these conversation summaries into a single cohesive summary that preserves the key technical details and progression of the discussion. Focus on:
- Maintaining chronological flow
- Preserving critical technical decisions
- Highlighting major code changes
- Keeping important context and rationale

Summaries to combine:
{combined}

Create a unified technical summary."""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
        
    except Exception as e:
        print(f"Error merging summaries: {str(e)}")
        return None

def compress_aider_files():
    """Compress large Aider discussion files using map-reduce summarization"""
    try:
        # Initialize logger
        logger = Logger()
        logger.log("Starting Aider history compression", 'info')
        
        # Initialize Anthropic client
        client = anthropic.Anthropic()
        
        # Find all Aider history files
        aider_files = glob.glob(".aider.*.history.md")
        
        for file_path in aider_files:
            try:
                # Check file size
                size = Path(file_path).stat().st_size
                if size < 100000:  # Skip if under 100K chars
                    continue
                    
                logger.log(f"Processing {file_path} ({size/1000:.1f}K chars)", 'info')
                
                # Read content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Split into chunks
                chunks = split_content(content)
                logger.log(f"Split into {len(chunks)} chunks", 'info')
                
                # Map: Summarize each chunk
                summaries = []
                for i, chunk in enumerate(chunks, 1):
                    logger.log(f"Summarizing chunk {i}/{len(chunks)}", 'info')
                    summary = summarize_chunk(chunk, client)
                    if summary:
                        summaries.append(summary)
                    else:
                        logger.log(f"Failed to summarize chunk {i}", 'error')
                        
                if not summaries:
                    logger.log(f"No successful summaries for {file_path}", 'error')
                    continue
                    
                # Reduce: Merge summaries
                logger.log("Merging summaries...", 'info')
                final_summary = merge_summaries(summaries, client)
                
                if not final_summary:
                    logger.log(f"Failed to merge summaries for {file_path}", 'error')
                    continue
                    
                # Create backup in proper backup directory
                backup_dir = os.path.join(PathManager.get_project_root(), "backups")
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, f"{os.path.basename(file_path)}.{int(time.time())}.backup")
                os.rename(file_path, backup_path)
                
                # Write compressed version
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(final_summary)
                    
                logger.log(f"Successfully compressed {file_path}", 'success')
                
            except Exception as e:
                logger.log(f"Error processing {file_path}: {str(e)}", 'error')
                continue
                
    except Exception as e:
        logger.log(f"Error in compression script: {str(e)}", 'error')

if __name__ == "__main__":
    compress_aider_files()
