#!/usr/bin/env python3
"""
Config Key Audit Script for Transcriber Pipeline

This script scans all Python files in the project to identify config keys and CLI arguments
to ensure consistency in naming conventions across the codebase.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple


class ConfigAuditor:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.findings = defaultdict(lambda: defaultdict(set))
        
        # Known config key patterns to look for
        self.config_patterns = [
            # Dictionary-style config access
            r"config\[[\'\"]([^\'\"]+)[\'\"]\]",
            r"args\[[\'\"]([^\'\"]+)[\'\"]\]",
            r"config\.get\([\'\"]([^\'\"]+)[\'\"]",
            r"args\.get\([\'\"]([^\'\"]+)[\'\"]",
            
            # Direct attribute access
            r"config\.([a-zA-Z_][a-zA-Z0-9_]*)",
            r"args\.([a-zA-Z_][a-zA-Z0-9_]*)",
            
            # CLI argument definitions
            r"add_argument\(\s*[\'\"]--([^\'\"]+)[\'\"]",
            r"add_argument\(\s*[\'\"]([^\'\"]+)[\'\"]",
            
            # Variable assignments with common config names
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=.*config",
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=.*args",
        ]
        
        # Common config key categories to focus on
        self.key_categories = {
            'cleanup': ['cleanup', 'custom_cleanup', 'custom_prompt', 'custom_instructions'],
            'language': ['language', 'target_language', 'src_language', 'source_language'],
            'level': ['level', 'cleanup_level', 'processing_level'],
            'model': ['model', 'model_name', 'ai_model'],
            'output': ['output', 'output_dir', 'output_path', 'out_dir'],
            'input': ['input', 'input_dir', 'input_path', 'in_dir'],
            'format': ['format', 'output_format', 'file_format'],
            'diarization': ['diarization', 'diarize', 'speaker_diarization'],
            'translation': ['translation', 'translate', 'translate_transcript'],
        }

    def scan_python_files(self) -> List[Path]:
        """Find all Python files in the project (excluding venv)."""
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Skip virtual environment and other common excluded directories
            dirs[:] = [d for d in dirs if d not in ['venv', '.git', '__pycache__', '.pytest_cache', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files

    def extract_config_keys(self, file_path: Path) -> Dict[str, Set[str]]:
        """Extract config keys from a Python file."""
        results = defaultdict(set)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return results
        
        # Extract keys using various patterns
        for pattern in self.config_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                pattern_type = self._classify_pattern(pattern)
                for match in matches:
                    if isinstance(match, tuple):
                        # Some patterns return tuples
                        match = match[0] if match[0] else match[1]
                    results[pattern_type].add(match)
        
        return results

    def _classify_pattern(self, pattern: str) -> str:
        """Classify the type of pattern for reporting."""
        if "add_argument" in pattern:
            return "CLI_argument"
        elif "config[" in pattern or "config.get" in pattern:
            return "config_dict_access"
        elif "args[" in pattern or "args.get" in pattern:
            return "args_dict_access"
        elif "config." in pattern:
            return "config_attr_access"
        elif "args." in pattern:
            return "args_attr_access"
        else:
            return "variable_assignment"

    def analyze_key_variations(self) -> Dict[str, List[str]]:
        """Analyze variations in similar config keys."""
        all_keys = set()
        for file_findings in self.findings.values():
            for pattern_type, keys in file_findings.items():
                all_keys.update(keys)
        
        # Group similar keys
        variations = defaultdict(list)
        for category, keywords in self.key_categories.items():
            category_keys = []
            for key in all_keys:
                key_lower = key.lower().replace('-', '_')
                if any(keyword in key_lower for keyword in keywords):
                    category_keys.append(key)
            if category_keys:
                variations[category] = sorted(list(set(category_keys)))
        
        return dict(variations)

    def scan_project(self) -> Dict:
        """Perform complete project scan."""
        print("Scanning Python files for config keys...")
        
        python_files = self.scan_python_files()
        print(f"Found {len(python_files)} Python files to scan")
        
        for file_path in python_files:
            rel_path = file_path.relative_to(self.root_dir)
            file_findings = self.extract_config_keys(file_path)
            
            if any(file_findings.values()):
                self.findings[str(rel_path)] = file_findings
        
        print(f"Analyzed {len(self.findings)} files with config references")
        
        # Analyze for inconsistencies
        variations = self.analyze_key_variations()
        
        return {
            'files_scanned': len(python_files),
            'files_with_config': len(self.findings),
            'key_variations': variations,
            'detailed_findings': dict(self.findings)
        }

    def generate_report(self, results: Dict) -> str:
        """Generate a human-readable report."""
        report = []
        report.append("=" * 80)
        report.append("CONFIG KEY AUDIT REPORT")
        report.append("=" * 80)
        report.append(f"Files scanned: {results['files_scanned']}")
        report.append(f"Files with config references: {results['files_with_config']}")
        report.append("")
        
        # Report key variations by category
        if results['key_variations']:
            report.append("POTENTIAL INCONSISTENCIES BY CATEGORY:")
            report.append("-" * 50)
            
            for category, keys in results['key_variations'].items():
                if len(keys) > 1:  # Only show categories with potential inconsistencies
                    report.append(f"\n{category.upper()} related keys:")
                    for key in keys:
                        report.append(f"  - {key}")
        
        # Show files with the most config references
        report.append("\n\nFILES WITH MOST CONFIG REFERENCES:")
        report.append("-" * 50)
        
        file_counts = []
        for file_path, findings in results['detailed_findings'].items():
            total_keys = sum(len(keys) for keys in findings.values())
            file_counts.append((file_path, total_keys))
        
        file_counts.sort(key=lambda x: x[1], reverse=True)
        for file_path, count in file_counts[:10]:  # Top 10
            report.append(f"  {file_path}: {count} config references")
        
        # Specific recommendations
        report.append("\n\nRECOMMENDATIONS:")
        report.append("-" * 50)
        
        cleanup_keys = results['key_variations'].get('cleanup', [])
        if len(cleanup_keys) > 1:
            report.append("1. CLEANUP PROMPT STANDARDIZATION:")
            report.append("   Found variations in cleanup-related keys:")
            for key in cleanup_keys:
                report.append(f"     - {key}")
            report.append("   Recommendation: Standardize on 'custom_cleanup_prompt'")
        
        language_keys = results['key_variations'].get('language', [])
        if len(language_keys) > 1:
            report.append("\n2. LANGUAGE FIELD STANDARDIZATION:")
            report.append("   Found variations in language-related keys:")
            for key in language_keys:
                report.append(f"     - {key}")
            report.append("   Recommendation: Standardize on 'target_language'")
        
        return "\n".join(report)

    def save_detailed_json(self, results: Dict, output_path: str = "config_audit_detailed.json"):
        """Save detailed findings to JSON for further analysis."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Detailed findings saved to {output_path}")


def main():
    """Main execution function."""
    auditor = ConfigAuditor()
    results = auditor.scan_project()
    
    # Generate and display report
    report = auditor.generate_report(results)
    print(report)
    
    # Save detailed results
    auditor.save_detailed_json(results)
    
    # Check for specific known issues
    cleanup_variations = results['key_variations'].get('cleanup', [])
    if len(cleanup_variations) > 1:
        print(f"\n⚠️  WARNING: Found {len(cleanup_variations)} different cleanup-related keys!")
        print("This suggests inconsistent naming that should be resolved.")
    
    language_variations = results['key_variations'].get('language', [])
    if len(language_variations) > 1:
        print(f"\n⚠️  WARNING: Found {len(language_variations)} different language-related keys!")
        print("This suggests inconsistent naming that should be resolved.")


if __name__ == "__main__":
    main()
