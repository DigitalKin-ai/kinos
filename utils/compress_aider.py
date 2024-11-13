"""
Script to compress large Aider discussion files using GPT-4 in a map-reduce pattern
"""
import os
import glob
from typing import List, Optional
import anthropic
from pathlib import Path

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
                    
                print(f"Processing {file_path} ({size/1000:.1f}K chars)")
                
                # Read content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Split into chunks
                chunks = split_content(content)
                print(f"Split into {len(chunks)} chunks")
                
                # Map: Summarize each chunk
                summaries = []
                for i, chunk in enumerate(chunks, 1):
                    print(f"Summarizing chunk {i}/{len(chunks)}")
                    summary = summarize_chunk(chunk, client)
                    if summary:
                        summaries.append(summary)
                    else:
                        print(f"Failed to summarize chunk {i}")
                        
                if not summaries:
                    print(f"No successful summaries for {file_path}")
                    continue
                    
                # Reduce: Merge summaries
                print("Merging summaries...")
                final_summary = merge_summaries(summaries, client)
                
                if not final_summary:
                    print(f"Failed to merge summaries for {file_path}")
                    continue
                    
                # Create backup
                backup_path = f"{file_path}.backup"
                os.rename(file_path, backup_path)
                
                # Write compressed version
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(final_summary)
                    
                print(f"Successfully compressed {file_path}")
                
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error in compression script: {str(e)}")

if __name__ == "__main__":
    compress_aider_files()
