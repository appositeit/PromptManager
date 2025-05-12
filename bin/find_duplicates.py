#!/usr/bin/env python3
"""
A script to identify duplicated code blocks across the codebase.
This is a simplified version that searches for repeated blocks of code
with configurable minimum size and reports them.
"""

import os
import re
import hashlib
from collections import defaultdict
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple


class CodeDuplicationFinder:
    def __init__(
        self,
        min_lines: int = 6,
        min_tokens: int = 50,
        ignore_patterns: List[str] = None,
        include_extensions: List[str] = None,
    ):
        """
        Initialize the duplicate code finder.
        
        Args:
            min_lines: Minimum number of lines to consider a duplication
            min_tokens: Minimum number of tokens to consider a duplication
            ignore_patterns: List of patterns to ignore in file paths
            include_extensions: List of file extensions to include
        """
        self.min_lines = min_lines
        self.min_tokens = min_tokens
        self.ignore_patterns = ignore_patterns or [
            r"__pycache__",
            r"\.git",
            r"\.venv",
            r"venv",
            r"node_modules",
        ]
        self.include_extensions = include_extensions or [
            ".py", ".js", ".html", ".css", ".md"
        ]
        
        self.block_hashes = defaultdict(list)
        self.total_loc = 0
        self.total_files = 0
        self.duplication_count = 0
        self.duplicate_lines = 0

    def should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed based on patterns and extensions."""
        # Check if file should be ignored based on patterns
        for pattern in self.ignore_patterns:
            if re.search(pattern, file_path):
                return False
                
        # Check if file extension should be included
        _, ext = os.path.splitext(file_path)
        return ext in self.include_extensions

    def normalize_code(self, code: str, file_ext: str) -> str:
        """
        Normalize code to make comparison more meaningful.
        Remove comments, whitespace, etc.
        """
        # Simple normalization for now
        if file_ext == '.py':
            # Remove Python comments and normalize whitespace
            code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        elif file_ext in ['.js', '.html', '.css']:
            # Remove JS/HTML/CSS comments
            code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            
        # Remove blank lines and normalize whitespace for all files
        lines = [line.strip() for line in code.split('\n')]
        lines = [line for line in lines if line]
        return '\n'.join(lines)

    def tokenize(self, code: str) -> List[str]:
        """Simple tokenization by splitting on whitespace and punctuation."""
        return re.findall(r'[a-zA-Z0-9_]+', code)

    def process_file(self, file_path: str) -> None:
        """Process a single file to find code blocks."""
        _, ext = os.path.splitext(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.total_loc += len(content.split('\n'))
                self.total_files += 1
        except UnicodeDecodeError:
            print(f"Warning: Could not decode {file_path}, skipping")
            return
        
        # Normalize the code
        normalized = self.normalize_code(content, ext)
        lines = normalized.split('\n')
        
        # Sliding window to find blocks
        for start_idx in range(len(lines) - self.min_lines + 1):
            for size in range(self.min_lines, min(31, len(lines) - start_idx + 1)):
                block = '\n'.join(lines[start_idx:start_idx + size])
                tokens = self.tokenize(block)
                
                # Only process blocks with sufficient tokens
                if len(tokens) < self.min_tokens:
                    continue
                
                # Hash the block
                block_hash = hashlib.md5(block.encode()).hexdigest()
                self.block_hashes[block_hash].append({
                    'file': file_path,
                    'start_line': start_idx + 1,  # 1-indexed for human readability
                    'end_line': start_idx + size,
                    'code': block,
                    'tokens': len(tokens)
                })

    def find_duplicates(self, directory: str) -> Dict[str, List[dict]]:
        """Find duplicated code blocks in the directory."""
        print(f"Scanning for duplicated code in {directory}...")
        print(f"Minimum lines: {self.min_lines}, Minimum tokens: {self.min_tokens}")
        
        # Walk through the directory
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if self.should_process_file(file_path):
                    self.process_file(file_path)
        
        # Filter out unique blocks
        duplicates = {h: blocks for h, blocks in self.block_hashes.items() if len(blocks) > 1}
        
        # Count duplications
        self.duplication_count = len(duplicates)
        for _, blocks in duplicates.items():
            # Count each duplicated instance after the first one
            duplicate_blocks = len(blocks) - 1
            block_size = blocks[0]['end_line'] - blocks[0]['start_line'] + 1
            self.duplicate_lines += duplicate_blocks * block_size
        
        return duplicates

    def print_report(self, duplicates: Dict[str, List[dict]], detailed: bool = False) -> None:
        """Print a report of the duplicated code."""
        total_duplications = len(duplicates)
        
        print("\n===== Duplication Report =====")
        print(f"Total files scanned: {self.total_files}")
        print(f"Total lines of code: {self.total_loc}")
        print(f"Duplicate code blocks found: {total_duplications}")
        
        # Calculate duplication percentage
        duplication_percentage = (self.duplicate_lines / self.total_loc * 100) if self.total_loc > 0 else 0
        print(f"Duplicated lines: {self.duplicate_lines} ({duplication_percentage:.2f}%)")
        
        if not duplicates:
            print("No code duplications found!")
            return
            
        # Sort duplications by size (number of instances * lines)
        sorted_duplicates = sorted(
            duplicates.items(), 
            key=lambda x: (len(x[1]) * (x[1][0]['end_line'] - x[1][0]['start_line'] + 1)), 
            reverse=True
        )
        
        # Print top duplications
        print("\nTop 10 duplications by impact:")
        for i, (_, blocks) in enumerate(sorted_duplicates[:10], 1):
            instances = len(blocks)
            lines = blocks[0]['end_line'] - blocks[0]['start_line'] + 1
            tokens = blocks[0]['tokens']
            print(f"{i}. {instances} occurrences of a {lines}-line block ({tokens} tokens)")
            
            # List all instances
            for j, block in enumerate(blocks[:5], 1):  # Show first 5 instances
                print(f"   {j}. {block['file']}:{block['start_line']}-{block['end_line']}")
            
            if len(blocks) > 5:
                print(f"   ... and {len(blocks) - 5} more instances")
                
            # Show the code if detailed report is requested
            if detailed and i <= 3:  # Only show first 3 duplications in detail
                print("\n   Code:")
                code_lines = blocks[0]['code'].split('\n')
                for k, line in enumerate(code_lines[:10]):  # Show first 10 lines
                    print(f"      {k+1}: {line[:100]}")
                if len(code_lines) > 10:
                    print(f"      ... {len(code_lines) - 10} more lines")
                print()
        
        # Recommendations
        print("\nRecommendations:")
        
        if duplication_percentage < 5:
            print("- Duplication level is low (< 5%). This is generally acceptable.")
        elif duplication_percentage < 15:
            print("- Moderate duplication detected (5-15%). Consider refactoring the larger duplicated blocks.")
        else:
            print("- High duplication detected (>15%). Consider a focused refactoring effort.")
            
        # Specific recommendations based on top duplications
        if total_duplications > 0:
            top_dup = sorted_duplicates[0]
            blocks = top_dup[1]
            lines = blocks[0]['end_line'] - blocks[0]['start_line'] + 1
            instances = len(blocks)
            
            if instances > 3 and lines > 10:
                print(f"- Consider extracting the most duplicated block ({instances} occurrences, {lines} lines) into a reusable component/function")
            
            # Check if there are duplications across specific types of files
            file_types = defaultdict(int)
            for _, blocks in sorted_duplicates[:5]:
                for block in blocks:
                    _, ext = os.path.splitext(block['file'])
                    file_types[ext] += 1
            
            for ext, count in file_types.items():
                if count > 5:
                    if ext == '.py':
                        print(f"- Consider creating utility functions for duplicated Python code")
                    elif ext == '.js':
                        print(f"- Consider creating shared JavaScript modules for duplicated code")
                    elif ext == '.html':
                        print(f"- Consider using template inheritance or components for duplicated HTML")
                        
        print("\n==============================")


def main():
    parser = argparse.ArgumentParser(description='Find duplicated code in a project')
    parser.add_argument('directory', type=str, help='Directory to scan')
    parser.add_argument('--min-lines', type=int, default=6, help='Minimum lines to consider a duplication')
    parser.add_argument('--min-tokens', type=int, default=50, help='Minimum tokens to consider a duplication')
    parser.add_argument('--detailed', action='store_true', help='Show detailed code snippets')
    parser.add_argument('--extensions', type=str, default='.py,.js,.html,.css,.md', 
                        help='Comma-separated list of file extensions to include')
    
    args = parser.parse_args()
    
    extensions = args.extensions.split(',')
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    
    finder = CodeDuplicationFinder(
        min_lines=args.min_lines,
        min_tokens=args.min_tokens,
        include_extensions=extensions
    )
    
    duplicates = finder.find_duplicates(args.directory)
    finder.print_report(duplicates, detailed=args.detailed)


if __name__ == '__main__':
    main()
