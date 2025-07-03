#!/usr/bin/env python3
"""
Fix Config Key Inconsistencies

This script applies targeted fixes to resolve the config key inconsistencies
identified by the audit script.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple


class ConfigFixer:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        
        # Define the standardization mappings
        self.fixes = {
            # Cleanup prompt standardization
            'custom_instructions': 'custom_cleanup_prompt',
            'custom_prompt': 'custom_cleanup_prompt', 
            'new_custom_prompt': 'custom_cleanup_prompt',
            
            # CLI argument standardization
            '--custom-prompt': '--custom-cleanup-prompt',
            'custom-prompt': 'custom-cleanup-prompt',
            
            # Language field standardization (be more careful here)
            # We'll handle language vs target_language case by case
        }
        
        # Files to modify (excluding test files for now)
        self.target_files = [
            'run_transcription_pipeline_v2.py',
            'scripts/context_correct_transcript.py',
        ]

    def apply_fixes(self):
        """Apply the configuration fixes to target files."""
        print("Applying config key standardization fixes...")
        
        for file_path in self.target_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                self.fix_file(full_path)
            else:
                print(f"Warning: {file_path} not found")
        
        print("Fixes completed!")

    def fix_file(self, file_path: Path):
        """Fix config keys in a specific file."""
        print(f"Processing {file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return
        
        original_content = content
        
        # Apply cleanup prompt fixes
        content = self.fix_cleanup_prompt_keys(content, file_path)
        
        # Apply CLI argument fixes if this is a script file
        if 'scripts/' in str(file_path):
            content = self.fix_cli_arguments(content, file_path)
        
        # Save if changes were made
        if content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✓ Updated {file_path}")
            except Exception as e:
                print(f"  ✗ Error writing {file_path}: {e}")
        else:
            print(f"  - No changes needed for {file_path}")

    def fix_cleanup_prompt_keys(self, content: str, file_path: Path) -> str:
        """Fix cleanup prompt related keys."""
        # Dictionary access patterns
        patterns = [
            (r"config\[[\'\"]custom_instructions[\'\"]\]", "config['custom_cleanup_prompt']"),
            (r"config\[[\'\"]custom_prompt[\'\"]\]", "config['custom_cleanup_prompt']"),
            (r"config\[[\'\"]new_custom_prompt[\'\"]\]", "config['custom_cleanup_prompt']"),
            
            (r"config\.get\([\'\"]custom_instructions[\'\"]", "config.get('custom_cleanup_prompt'"),
            (r"config\.get\([\'\"]custom_prompt[\'\"]", "config.get('custom_cleanup_prompt'"),
            (r"config\.get\([\'\"]new_custom_prompt[\'\"]", "config.get('custom_cleanup_prompt'"),
            
            # Variable assignments
            (r"custom_instructions\s*=", "custom_cleanup_prompt ="),
            (r"new_custom_prompt\s*=", "custom_cleanup_prompt ="),
            
            # Usage in expressions (be careful with this one)
            (r"([^a-zA-Z_])custom_instructions([^a-zA-Z0-9_])", r"\1custom_cleanup_prompt\2"),
            (r"([^a-zA-Z_])new_custom_prompt([^a-zA-Z0-9_])", r"\1custom_cleanup_prompt\2"),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        return content

    def fix_cli_arguments(self, content: str, file_path: Path) -> str:
        """Fix CLI argument definitions."""
        # CLI argument patterns
        patterns = [
            (r"add_argument\(\s*[\'\"]--custom-prompt[\'\"]", "add_argument('--custom-cleanup-prompt'"),
            (r"[\'\"]--custom-prompt[\'\"]", "'--custom-cleanup-prompt'"),
            (r"[\'\"]custom-prompt[\'\"]", "'custom-cleanup-prompt'"),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
            
        return content


def main():
    """Main execution function."""
    fixer = ConfigFixer()
    
    print("Starting config key standardization fixes...")
    print("This will update the following files:")
    for file_path in fixer.target_files:
        print(f"  - {file_path}")
    
    response = input("\nProceed with fixes? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Aborted.")
        return
    
    fixer.apply_fixes()
    
    print("\n" + "="*60)
    print("Config key standardization completed!")
    print("\nRecommended next steps:")
    print("1. Run the audit script again to verify fixes")
    print("2. Test the pipeline to ensure functionality is maintained")
    print("3. Update any documentation that references the old key names")


if __name__ == "__main__":
    main()
