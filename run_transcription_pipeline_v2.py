#!/usr/bin/env python3
"""
Transcriber v2.0+ - Unified Pipeline Interface

Goal-centric modular transcription pipeline with flexible user choices.
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Enhanced input handling
try:
    import readline
    # Enable better line editing and history
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

# Load environment variables
load_dotenv()

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.NC}")
    print("=" * len(text))

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.NC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}💡 {text}{Colors.NC}")

def ask_yes_no(prompt: str, explanation: str = "", default: str = "n") -> bool:
    """Ask a yes/no question with optional explanation"""
    if explanation:
        print_info(explanation)
    
    if default.lower() == "y":
        response = input(f"{prompt} [Y/n]: ").strip().lower() or "y"
    else:
        response = input(f"{prompt} [y/N]: ").strip().lower() or "n"
    
    return response in ['y', 'yes']

def check_api_keys() -> Dict[str, Optional[str]]:
    """Check for required API keys and offer to set them"""
    print_header("🔐 API Key Configuration")
    
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'HUGGINGFACE_TOKEN': os.getenv('HUGGINGFACE_TOKEN')
    }
    
    missing_keys = []
    for key, value in api_keys.items():
        if value:
            print_success(f"{key} found")
        else:
            missing_keys.append(key)
            print_warning(f"{key} not found")
    
    if missing_keys:
        print()
        print_info("Some AI features require API keys:")
        print("• Context Correction: Fixes grammar and homophone errors using GPT-4")
        print("• Translation: Translates content to other languages using GPT-4")
        print()
        
        if ask_yes_no("Would you like to set up API keys now?", 
                     "This will create/update your .env file"):
            
            env_path = Path(".env")
            env_content = ""
            
            # Read existing .env if it exists
            if env_path.exists():
                with open(env_path, 'r') as f:
                    env_content = f.read()
            
            for key in missing_keys:
                if key == 'OPENAI_API_KEY':
                    print(f"\n{Colors.YELLOW}Setting up OpenAI API Key:{Colors.NC}")
                    print("• Get your API key from: https://platform.openai.com/api-keys")
                    print("• Required for context correction and translation features")
                    
                    api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
                    
                    if api_key:
                        # Update or add the key
                        if f"{key}=" in env_content:
                            lines = env_content.split('\n')
                            updated_lines = []
                            for line in lines:
                                if line.startswith(f"{key}="):
                                    updated_lines.append(f"{key}={api_key}")
                                else:
                                    updated_lines.append(line)
                            env_content = '\n'.join(updated_lines)
                        else:
                            env_content += f"\n{key}={api_key}"
                        
                        api_keys[key] = api_key
                        print_success(f"{key} configured")
                
                elif key == 'HUGGINGFACE_TOKEN':
                    print(f"\n{Colors.YELLOW}Setting up Hugging Face Token:{Colors.NC}")
                    print("• Get your token from: https://huggingface.co/settings/tokens")
                    print("• Required for advanced speaker diarization using pyannote.audio")
                    print("• Creates a free account at https://huggingface.co if you don't have one")
                    
                    hf_token = input("Enter your Hugging Face token (or press Enter to skip): ").strip()
                    
                    if hf_token:
                        # Update or add the key
                        if f"{key}=" in env_content:
                            lines = env_content.split('\n')
                            updated_lines = []
                            for line in lines:
                                if line.startswith(f"{key}="):
                                    updated_lines.append(f"{key}={hf_token}")
                                else:
                                    updated_lines.append(line)
                            env_content = '\n'.join(updated_lines)
                        else:
                            env_content += f"\n{key}={hf_token}"
                        
                        api_keys[key] = hf_token
                        print_success(f"{key} configured")
            
            # Save updated .env file
            if any(api_keys.values()):
                with open(env_path, 'w') as f:
                    f.write(env_content.strip())
                print_success(".env file updated")
                
                # Reload environment
                load_dotenv(override=True)
    
    return api_keys

def select_output_format() -> str:
    """Select the desired output format"""
    print_header("🎯 Output Format Selection")
    print("Choose your desired output format:\n")
    
    formats = [
        ("FCPXML", "Professional subtitle files for Final Cut Pro", 
         "Video editors, professional content creation", "~2-5 minutes"),
        ("ITT", "Standard subtitle files for video players", 
         "General video distribution, streaming platforms", "~2-5 minutes"),
        ("Markdown", "Human-readable transcripts with speaker identification", 
         "Interview analysis, meeting notes, content research", "~5-10 minutes"),
        ("JSON", "Raw transcript data with precise timing", 
         "Developers, further processing, custom applications", "~1-3 minutes")
    ]
    
    for i, (name, desc, use_case, time) in enumerate(formats, 1):
        print(f"{Colors.BOLD}{i}. {name}{Colors.NC}")
        print(f"   {desc}")
        print(f"   {Colors.CYAN}Best for:{Colors.NC} {use_case}")
        print(f"   {Colors.YELLOW}Time estimate:{Colors.NC} {time}")
        print()
    
    print_info("Not sure which to choose?")
    print("• For video editing: Choose FCPXML or ITT")
    print("• For reading/analysis: Choose Markdown")
    print("• For technical use: Choose JSON")
    print()
    
    while True:
        try:
            choice = int(input("Select output format [1-4]: "))
            if 1 <= choice <= 4:
                return ['fcpxml', 'itt', 'markdown', 'json'][choice - 1]
            else:
                print("Please select 1-4.")
        except ValueError:
            print("Please enter a number.")

def clean_path_input(path_input: str) -> str:
    """Clean and normalize path input for copy/paste robustness"""
    # Remove leading/trailing whitespace
    cleaned = path_input.strip()
    
    # Remove surrounding quotes (single or double)
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1]
    elif cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1]
    
    # Handle escaped quotes
    cleaned = cleaned.replace('\"', '"').replace("\''", "'")
    
    # Use standard Python method for path expansion (handles ~ properly)
    cleaned = os.path.expanduser(cleaned)
    
    return cleaned

def parse_file_selection(selection: str, max_files: int) -> List[int]:
    """Parse file selection input robustly"""
    selection = selection.strip().lower()
    
    # Handle 'all' case
    if selection in ['all', 'a', '*']:
        return list(range(max_files))
    
    indices = []
    
    # Split by comma and process each part
    for part in selection.split(','):
        part = part.strip()
        
        if not part:
            continue
            
        try:
            if '-' in part:
                # Handle ranges like "2-5" or "2 - 5"
                range_parts = [p.strip() for p in part.split('-')]
                if len(range_parts) == 2:
                    start = int(range_parts[0]) - 1  # Convert to 0-based
                    end = int(range_parts[1]) - 1    # Convert to 0-based
                    
                    # Validate range
                    if start < 0 or end >= max_files or start > end:
                        raise ValueError(f"Invalid range: {part}")
                    
                    indices.extend(range(start, end + 1))
                else:
                    raise ValueError(f"Invalid range format: {part}")
            else:
                # Single number
                num = int(part) - 1  # Convert to 0-based
                if num < 0 or num >= max_files:
                    raise ValueError(f"Number out of range: {part}")
                indices.append(num)
                
        except ValueError as e:
            raise ValueError(f"Invalid selection '{part}': {str(e)}")
    
    # Remove duplicates and sort
    return sorted(list(set(indices)))

def scan_existing_transcripts(input_dir: Path) -> List[Dict[str, any]]:
    """Scan for existing transcript directories and return metadata"""
    existing_transcripts = []
    
    # Look for transcript directories in potential output locations
    potential_locations = [
        input_dir / "output" / "transcripts",
        input_dir / "transcripts", 
        input_dir.parent / "output" / "transcripts",
    ]
    
    for location in potential_locations:
        if location.exists():
            for transcript_dir in location.iterdir():
                if transcript_dir.is_dir():
                    # Parse directory name for metadata
                    # Format: language_stage_date_model
                    parts = transcript_dir.name.split('_')
                    if len(parts) >= 3:
                        try:
                            language = parts[0]
                            stage = parts[1]  # raw, cleaned, translated
                            date = parts[2]
                            model = parts[3] if len(parts) > 3 else "unknown"
                            
                            # Count JSON files to verify it's a real transcript directory
                            json_files = list(transcript_dir.glob("*.json"))
                            if json_files:
                                existing_transcripts.append({
                                    'path': str(transcript_dir),
                                    'language': language,
                                    'stage': stage,
                                    'date': date,
                                    'model': model,
                                    'file_count': len(json_files),
                                    'description': f"{language.title()} {stage} transcripts ({date}, {model} model, {len(json_files)} files)"
                                })
                        except (IndexError, ValueError):
                            continue
    
    return sorted(existing_transcripts, key=lambda x: x['date'], reverse=True)

def select_existing_transcript_operations(existing: List[Dict[str, any]], input_dir: Path) -> Dict[str, any]:
    """Select existing transcript and operation to perform"""
    print_header("🔧 Existing Transcript Operations")
    
    if existing:
        print("Select which transcript to work with:\n")
        
        for i, transcript in enumerate(existing, 1):
            print(f"  {i}. {transcript['description']}")
        
        print(f"\n  {len(existing) + 1}. Browse for transcripts in a different location")
        print()
        
        while True:
            try:
                choice = int(input(f"Select transcript [1-{len(existing) + 1}]: "))
                if 1 <= choice <= len(existing):
                    selected_transcript = existing[choice - 1]
                    break
                elif choice == len(existing) + 1:
                    selected_transcript = select_transcript_directory()
                    if not selected_transcript:
                        return select_transcript_source(input_dir)  # Go back to main menu
                    break
                else:
                    print(f"Please select 1-{len(existing) + 1}.")
            except ValueError:
                print("Please enter a number.")
    else:
        # No existing transcripts found in standard locations
        selected_transcript = select_transcript_directory()
        if not selected_transcript:
            return select_transcript_source(input_dir)  # Go back to main menu
    
    print_success(f"Selected: {selected_transcript['description']}")
    
    # Show README information if available
    transcript_path = Path(selected_transcript['path'])
    readme_path = transcript_path / "README.md"
    if readme_path.exists():
        print(f"\n{Colors.CYAN}📋 Processing Details:{Colors.NC}")
        try:
            with open(readme_path, 'r') as f:
                readme_content = f.read()
            
            # Extract key details for display
            import re
            
            # Show processing type and key details
            processing_match = re.search(r'\*\*Processing:\*\* ([^\n]+)', readme_content)
            if processing_match:
                print(f"• Processing: {processing_match.group(1)}")
            
            created_match = re.search(r'\*\*Created:\*\* ([^\n]+)', readme_content)
            if created_match:
                print(f"• Created: {created_match.group(1)}")
            
            # Show custom instructions if present
            custom_match = re.search(r'\*\*Custom Instructions:\*\* ([^\n]+)', readme_content)
            if custom_match:
                print(f"• Instructions: {custom_match.group(1)}")
            
            # Show cleanup level if present
            cleanup_match = re.search(r'\*\*Cleanup Level:\*\* ([^\n]+)', readme_content)
            if cleanup_match:
                print(f"• Cleanup Level: {cleanup_match.group(1)}")
            
            # Show language info if translation
            source_lang_match = re.search(r'\*\*Source Language:\*\* ([^\n]+)', readme_content)
            target_lang_match = re.search(r'\*\*Target Language:\*\* ([^\n]+)', readme_content)
            if source_lang_match and target_lang_match:
                print(f"• Translation: {source_lang_match.group(1)} → {target_lang_match.group(1)}")
                
        except Exception:
            pass  # If README parsing fails, just continue
    
    # Intelligent operation suggestions based on transcript stage
    stage = selected_transcript.get('stage', 'unknown').lower()
    
    print("\n🎯 What would you like to do with this transcript?\n")
    
    # Base operations
    operations = [
        ("translate", "Translate to another language", "Create translated version"),
        ("cleanup", "AI cleanup with improved context", "Enhance readability and accuracy"),
        ("custom", "Apply custom AI instructions", "Experimental processing with your rules")
    ]
    
    # Add intelligent suggestions based on stage
    suggestions = []
    if 'raw' in stage:
        suggestions.append("💡 Recommended: Try cleanup first to improve readability, then translate if needed")
    elif 'clean' in stage:
        suggestions.append("💡 Recommended: This transcript is already cleaned - perfect for translation")
    elif 'translat' in stage:
        suggestions.append("💡 Note: This is already a translated transcript - consider custom processing for refinements")
    
    for i, (op, desc, explanation) in enumerate(operations, 1):
        print(f"{Colors.BOLD}{i}. {desc.title()}{Colors.NC}")
        print(f"   {explanation}")
        
        # Add specific suggestions for each operation
        if op == "cleanup" and 'raw' in stage:
            print(f"   {Colors.GREEN}✨ Perfect choice for raw transcripts{Colors.NC}")
        elif op == "translate" and 'clean' in stage:
            print(f"   {Colors.GREEN}✨ Ideal for cleaned transcripts{Colors.NC}")
        elif op == "custom" and 'translat' in stage:
            print(f"   {Colors.GREEN}✨ Good for refining translations{Colors.NC}")
        
        print()
    
    # Show general suggestions
    for suggestion in suggestions:
        print(f"{Colors.YELLOW}{suggestion}{Colors.NC}")
    
    if suggestions:
        print()
    
    while True:
        try:
            op_choice = int(input("Select operation [1-3]: "))
            if 1 <= op_choice <= 3:
                operation = operations[op_choice - 1][0]
                break
            else:
                print("Please select 1, 2, or 3.")
        except ValueError:
            print("Please enter a number.")
    
    print_success(f"Operation: {operations[op_choice - 1][1]}")
    
    return {
        'mode': 'existing_operations',
        'transcript_dir': selected_transcript['path'],
        'language': selected_transcript['language'],
        'stage': selected_transcript['stage'],
        'model': selected_transcript['model'],
        'operation': operation,
        'input_dir': str(input_dir)
    }

def browse_for_transcript_directory() -> Optional[Dict[str, any]]:
    """Allow user to browse for a transcript directory manually"""
    print("\n📁 Browse for Transcript Directory")
    print("💡 Enter the path to a directory containing transcript JSON files")
    print("Example: /Users/workspace/output/transcripts/english_raw_20241202_base")
    print()
    
    while True:
        path_input = input("Enter transcript directory path (or press Enter to cancel): ").strip()
        
        if not path_input:
            print_info("Cancelled - returning to main menu")
            return None
        
        # Validate input doesn't contain command-like text
        if any(phrase in path_input.lower() for phrase in ['select option', 'select transcript', 'operation', 'select operation']):
            print_error("Invalid path input detected. Please enter a valid directory path.")
            continue
        
        try:
            cleaned_path = clean_path_input(path_input)
            transcript_dir = Path(cleaned_path)
            
            if not transcript_dir.exists():
                print_error(f"Directory does not exist: {transcript_dir}")
                continue
            
            if not transcript_dir.is_dir():
                print_error(f"Path is not a directory: {transcript_dir}")
                continue
            
            # Use smart scanning to find transcript directories (same as other routes)
            transcript_dirs = smart_scan_for_transcripts(transcript_dir)
            
            if not transcript_dirs:
                print_error(f"No transcript directories found in: {transcript_dir}")
                if not ask_yes_no("Try a different directory?", "", "y"):
                    return None
                continue
            
            print_success(f"Found {len(transcript_dirs)} transcript directories")
            
            # Let user select from found transcript directories (same as other routes)
            selected_transcript = select_from_found_transcripts(transcript_dirs, transcript_dir)
            if selected_transcript:
                return selected_transcript
            
        except Exception as e:
            print_error(f"Invalid path: {e}")
            continue

def select_transcript_directory() -> Optional[Dict[str, any]]:
    """Select transcript directory with smart scanning like input file selection"""
    print_header("📁 Transcript Directory Selection")
    
    # Default directories to check
    default_dirs = [
        Path.cwd() / "output",
        Path.cwd() / "transcripts",
        Path.cwd()
    ]
    
    print("Where are your transcript files located?\n")
    
    # Show default options with smart scanning
    option_num = 1
    found_transcripts = {}
    
    for default_dir in default_dirs:
        if default_dir.exists():
            transcripts_found = smart_scan_for_transcripts(default_dir)
            if transcripts_found:
                print(f"{option_num}. {default_dir} ({len(transcripts_found)} transcript directories found)")
                found_transcripts[option_num] = (default_dir, transcripts_found)
                option_num += 1
            else:
                print(f"{option_num}. {default_dir} (no transcripts found)")
                found_transcripts[option_num] = (default_dir, [])
                option_num += 1
    
    print(f"{option_num}. Specify custom directory")
    custom_option = option_num
    print()
    
    # Show found transcripts
    if any(transcripts for _, transcripts in found_transcripts.values()):
        print(f"{Colors.GREEN}✨ Found transcript directories:{Colors.NC}")
        for opt_num, (dir_path, transcripts) in found_transcripts.items():
            if transcripts:
                print(f"  In {dir_path}:")
                for transcript in transcripts[:3]:  # Show first 3
                    print(f"    • {transcript['description']}")
                if len(transcripts) > 3:
                    print(f"    • ... and {len(transcripts) - 3} more")
        print()
    
    while True:
        try:
            choice = int(input(f"Select option [1-{custom_option}]: "))
            
            if choice in found_transcripts:
                selected_dir, transcripts = found_transcripts[choice]
                if transcripts:
                    # Let user choose specific transcript from this directory
                    return select_from_found_transcripts(transcripts, selected_dir)
                else:
                    print_info(f"No transcripts in {selected_dir}. Try a different option.")
                    continue
                    
            elif choice == custom_option:
                return browse_for_custom_transcript_directory()
            else:
                print(f"Please select 1-{custom_option}.")
                
        except ValueError:
            print("Please enter a number.")

def smart_scan_for_transcripts(base_dir: Path) -> List[Dict[str, any]]:
    """Intelligently scan directory for transcript folders with JSON files and README metadata"""
    transcript_dirs = []
    
    # Look for directories with JSON files
    for item in base_dir.rglob("*"):
        if item.is_dir():
            # Check for JSON files
            json_files = list(item.glob("*.json"))
            if json_files:
                # Try to extract metadata from README if it exists
                readme_path = item / "README.md"
                metadata = extract_metadata_from_readme(readme_path) if readme_path.exists() else {}
                
                # Parse directory name for metadata
                dir_metadata = parse_directory_name(item.name)
                
                # Combine metadata (README takes precedence)
                combined_metadata = {**dir_metadata, **metadata}
                
                # Try to infer language from JSON file names (for translated transcripts)
                if combined_metadata.get('language') == 'unknown':
                    combined_metadata['language'] = infer_language_from_files(json_files)
                
                # Validate JSON files contain transcript data
                if validate_transcript_json_files(json_files[:2]):  # Check first 2 files
                    transcript_dirs.append({
                        'path': str(item),
                        'language': combined_metadata.get('language', 'unknown'),
                        'stage': combined_metadata.get('stage', 'unknown'),
                        'date': combined_metadata.get('date', 'unknown'),
                        'model': combined_metadata.get('model', 'unknown'),
                        'file_count': len(json_files),
                        'description': create_transcript_description(combined_metadata, len(json_files), str(item)),
                        'base_dir': str(base_dir)
                    })
    
    # Sort by date (newest first) and then by file count
    return sorted(transcript_dirs, key=lambda x: (x['date'], x['file_count']), reverse=True)

def extract_metadata_from_readme(readme_path: Path) -> Dict[str, str]:
    """Extract metadata from README.md file"""
    metadata = {}
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
            
        # Look for metadata patterns
        import re
        
        # Extract stage from title or processing line
        stage_match = re.search(r'Stage \d+: ([^\n]+)', content)
        if stage_match:
            stage_text = stage_match.group(1).lower()
            if 'raw' in stage_text or 'whisper' in stage_text:
                metadata['stage'] = 'raw'
            elif 'clean' in stage_text or 'corrected' in stage_text:
                metadata['stage'] = 'cleaned'
            elif 'translat' in stage_text:
                metadata['stage'] = 'translated'
        
        # Extract processing info
        processing_match = re.search(r'\*\*Processing:\*\* ([^\n]+)', content)
        if processing_match:
            processing = processing_match.group(1).lower()
            if 'raw' in processing:
                metadata['stage'] = 'raw'
            elif 'clean' in processing:
                metadata['stage'] = 'cleaned'
                
        # Extract model info
        model_match = re.search(r"'([^']+)' model", content)
        if model_match:
            metadata['model'] = model_match.group(1)
            
        # Extract date
        date_match = re.search(r'\*\*Created:\*\* ([^\n]+)', content)
        if date_match:
            date_str = date_match.group(1)
            # Convert to simple date format
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                metadata['date'] = dt.strftime('%Y%m%d')
            except:
                pass
                
    except Exception:
        pass  # If README parsing fails, just return empty metadata
    
    return metadata

def parse_directory_name(dir_name: str) -> Dict[str, str]:
    """Parse directory name for metadata (format: language_stage_date_model)"""
    metadata = {}
    parts = dir_name.split('_')
    
    # Handle standard format: language_stage_date_model
    if len(parts) >= 3 and parts[0].isalpha():
        metadata['language'] = parts[0]
        metadata['stage'] = parts[1]
        metadata['date'] = parts[2]
        if len(parts) > 3:
            metadata['model'] = parts[3]
    # Handle numbered stage format: 1_raw_whisper
    elif len(parts) >= 2 and parts[0].isdigit():
        metadata['stage'] = parts[1] if len(parts) > 1 else 'unknown'
        if len(parts) > 2:
            metadata['stage'] = f"{parts[1]}_{parts[2]}"  # e.g., "raw_whisper"
    # Handle descriptive names: translated_transcripts, final_fcpxml
    elif 'translat' in dir_name.lower():
        metadata['stage'] = 'translated'
    elif 'clean' in dir_name.lower() or 'corrected' in dir_name.lower():
        metadata['stage'] = 'cleaned'
    elif 'raw' in dir_name.lower():
        metadata['stage'] = 'raw'
    elif 'final' in dir_name.lower():
        metadata['stage'] = 'final'
    elif 'diariz' in dir_name.lower():
        metadata['stage'] = 'diarized'
    
    return metadata

def validate_transcript_json_files(json_files: List[Path]) -> bool:
    """Validate that JSON files contain transcript data"""
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Check for transcript-like structure
            if isinstance(data, list):
                # Check if it has transcript segment structure
                if data and isinstance(data[0], dict):
                    first_segment = data[0]
                    # Look for common transcript fields
                    if any(key in first_segment for key in ['text', 'start', 'end', 'timestamp']):
                        return True
            elif isinstance(data, dict):
                # Check for other transcript formats
                if any(key in data for key in ['segments', 'text', 'transcript']):
                    return True
                    
        except (json.JSONDecodeError, OSError):
            continue
    
    return False

def infer_language_from_files(json_files: List[Path]) -> str:
    """Infer language from JSON file names (especially for translated files)"""
    for json_file in json_files:
        filename = json_file.stem.lower()
        
        # Check for language indicators in filename
        if '_chinese_' in filename or '_chinese(' in filename:
            if 'traditional' in filename:
                return 'Chinese (Traditional)'
            elif 'simplified' in filename:
                return 'Chinese (Simplified)'
            else:
                return 'Chinese'
        elif '_spanish_' in filename or '_spanish(' in filename:
            return 'Spanish'
        elif '_french_' in filename or '_french(' in filename:
            return 'French'
        elif '_german_' in filename or '_german(' in filename:
            return 'German'
        elif '_japanese_' in filename or '_japanese(' in filename:
            return 'Japanese'
        elif '_korean_' in filename or '_korean(' in filename:
            return 'Korean'
        elif '_portuguese_' in filename or '_portuguese(' in filename:
            return 'Portuguese'
        elif '_italian_' in filename or '_italian(' in filename:
            return 'Italian'
        elif '_arabic_' in filename or '_arabic(' in filename:
            return 'Arabic'
        elif '_english_' in filename or '_english(' in filename:
            return 'English'
    
    return 'unknown'

def create_transcript_description(metadata: Dict[str, str], file_count: int, directory_path: str = None) -> str:
    """Create a human-readable description of the transcript directory"""
    language = metadata.get('language', 'Unknown').title()
    stage = metadata.get('stage', 'unknown')
    date = metadata.get('date', 'unknown')
    model = metadata.get('model', 'unknown')
    
    # Handle different date formats
    if date != 'unknown':
        if len(date) == 8:  # YYYYMMDD format
            try:
                from datetime import datetime
                dt = datetime.strptime(date, '%Y%m%d')
                date = dt.strftime('%b %d, %Y')
            except:
                pass
        elif '-' in date and len(date) == 10:  # YYYY-MM-DD format
            try:
                from datetime import datetime
                dt = datetime.strptime(date, '%Y-%m-%d')
                date = dt.strftime('%b %d, %Y')
            except:
                pass
    
    # Clean up display values
    if language.lower() == 'unknown':
        language = 'Unspecified'
    if stage == 'unknown':
        stage = 'processed'
    if model == 'unknown':
        model = 'unspecified'
    
    # Check if this has unknown specifications (all critical metadata is unknown/unspecified)
    is_unknown_specs = (language == 'Unspecified' and stage == 'processed' and 
                       date == 'unknown' and model == 'unspecified')
    
    # Get directory name for display
    dir_name = ""
    if directory_path:
        from pathlib import Path
        dir_name = Path(directory_path).name
    
    if is_unknown_specs and dir_name:
        return f"Unknown specifications - {dir_name} ({file_count} files)"
    elif dir_name:
        return f"{language} {stage} transcripts ({date}, {model} model, {file_count} files) - {dir_name}"
    else:
        return f"{language} {stage} transcripts ({date}, {model} model, {file_count} files)"

def select_from_found_transcripts(transcripts: List[Dict[str, any]], base_dir: Path) -> Optional[Dict[str, any]]:
    """Let user select from found transcripts in a directory"""
    print(f"\n📁 Select Transcript from {base_dir}")
    print(f"Found {len(transcripts)} transcript directories:\n")
    
    for i, transcript in enumerate(transcripts, 1):
        print(f"  {i}. {transcript['description']}")
    
    print(f"\n  {len(transcripts) + 1}. Browse for a different directory")
    print()
    
    while True:
        try:
            choice = int(input(f"Select transcript [1-{len(transcripts) + 1}]: "))
            if 1 <= choice <= len(transcripts):
                selected = transcripts[choice - 1]
                print_success(f"Selected: {selected['description']}")
                return selected
            elif choice == len(transcripts) + 1:
                return browse_for_custom_transcript_directory()
            else:
                print(f"Please select 1-{len(transcripts) + 1}.")
        except ValueError:
            print("Please enter a number.")

def browse_for_custom_transcript_directory() -> Optional[Dict[str, any]]:
    """Browse for custom transcript directory with enhanced scanning"""
    print("\n📁 Custom Transcript Directory")
    print("💡 Enter the path to a directory - we'll scan it for transcript files")
    print("Examples:")
    print("  /Users/workspace/Desktop/project/output")
    print("  ~/Documents/transcripts")
    print()
    
    while True:
        path_input = input("Enter directory path (or press Enter to cancel): ").strip()
        
        if not path_input:
            print_info("Cancelled")
            return None
        
        # Validate input doesn't contain command-like text
        if any(phrase in path_input.lower() for phrase in ['select option', 'select transcript', 'operation', 'select operation']):
            print_error("Invalid path input detected. Please enter a valid directory path.")
            continue
        
        try:
            cleaned_path = clean_path_input(path_input)
            search_dir = Path(cleaned_path)
            
            if not search_dir.exists():
                print_error(f"Directory does not exist: {search_dir}")
                continue
            
            if not search_dir.is_dir():
                print_error(f"Path is not a directory: {search_dir}")
                continue
            
            # Smart scan for transcripts
            print(f"\n🔍 Scanning {search_dir} for transcript directories...")
            found_transcripts = smart_scan_for_transcripts(search_dir)
            
            if found_transcripts:
                print_success(f"Found {len(found_transcripts)} transcript directories")
                return select_from_found_transcripts(found_transcripts, search_dir)
            else:
                # Check if this directory itself contains JSON files
                json_files = list(search_dir.glob("*.json"))
                if json_files and validate_transcript_json_files(json_files[:2]):
                    print_success(f"Found {len(json_files)} transcript files in directory")
                    
                    # Parse metadata from directory
                    readme_metadata = extract_metadata_from_readme(search_dir / "README.md") if (search_dir / "README.md").exists() else {}
                    dir_metadata = parse_directory_name(search_dir.name)
                    metadata = {**dir_metadata, **readme_metadata}
                    
                    transcript_info = {
                        'path': str(search_dir),
                        'language': metadata.get('language', 'unknown'),
                        'stage': metadata.get('stage', 'unknown'),
                        'date': metadata.get('date', 'unknown'),
                        'model': metadata.get('model', 'unknown'),
                        'file_count': len(json_files),
                        'description': create_transcript_description(metadata, len(json_files), str(search_dir))
                    }
                    
                    print(f"Directory: {transcript_info['description']}")
                    
                    if ask_yes_no("Use this transcript directory?", "", "y"):
                        return transcript_info
                else:
                    print_error(f"No transcript files found in {search_dir} or its subdirectories")
                    if not ask_yes_no("Try a different directory?", "", "y"):
                        return None
            
        except Exception as e:
            print_error(f"Error accessing directory: {e}")
            continue

def select_transcript_source(input_dir: Path) -> Dict[str, any]:
    """Let user choose between existing transcripts or creating new ones"""
    print_header("📁 Transcript Source Selection")
    
    print("How do you want to create your transcript?\n")
    
    # Check for existing transcripts in common locations
    existing = scan_existing_transcripts(input_dir)
    
    print("1. Create new transcripts from audio/video files")
    print("2. Use existing transcripts for final output")
    print("3. Work with existing transcripts (translate, cleanup, custom operations)")
    
    if existing:
        print(f"\n{Colors.GREEN}✨ Found {len(existing)} existing transcript(s) in standard locations:{Colors.NC}")
        for i, transcript in enumerate(existing, 1):
            print(f"  • {transcript['description']}")
        print()
    else:
        print(f"\n{Colors.YELLOW}💡 No transcripts found in standard locations.{Colors.NC}")
        print("Don't worry - you can browse for transcripts in any location with options 2 or 3.")
        print()
    
    print(f"{Colors.CYAN}💡 Options explained:{Colors.NC}")
    print("• Option 1: Fresh transcription from your media files")
    print("• Option 2: Convert existing transcripts to your chosen format (browse for location)")
    print("• Option 3: Enhance existing transcripts (translation, AI cleanup, etc.) (browse for location)")
    print()
    
    while True:
        try:
            choice = int(input("Select option [1-3]: "))
            if choice == 1:
                print_info("Creating new transcripts from audio/video files")
                return select_input_files()
            elif choice == 2:
                return select_existing_transcript_for_output(existing, input_dir)
            elif choice == 3:
                return select_existing_transcript_operations(existing, input_dir)
            else:
                print("Please select 1, 2, or 3.")
        except ValueError:
            print("Please enter a number.")

def select_existing_transcript_for_output(existing: List[Dict[str, any]], input_dir: Path) -> Dict[str, any]:
    """Select existing transcript to use for final output generation"""
    print_header("📋 Select Existing Transcript")
    
    if existing:
        print("Which transcript would you like to use for output generation?\n")
        
        for i, transcript in enumerate(existing, 1):
            print(f"  {i}. {transcript['description']}")
        
        # Option to browse for a different transcript directory
        print(f"\n  {len(existing) + 1}. Browse for a different transcript directory")
        print()
        
        while True:
            try:
                choice = int(input(f"Select transcript [1-{len(existing) + 1}]: "))
                if 1 <= choice <= len(existing):
                    selected = existing[choice - 1]
                    print_success(f"Using: {selected['description']}")
                    return {
                        'mode': 'reuse',
                        'transcript_dir': selected['path'],
                        'language': selected['language'],
                        'stage': selected['stage'],
                        'model': selected['model'],
                        'input_dir': str(input_dir)
                    }
                elif choice == len(existing) + 1:
                    break  # Go to smart directory scanning
                else:
                    print(f"Please select 1-{len(existing) + 1}.")
            except ValueError:
                print("Please enter a number.")
    
    # Smart directory scanning (same logic as existing operations)
    print_header("📁 Transcript Directory Selection")
    print("Where are your transcript files located?\n")
    
    # Smart parent directory suggestions
    parent_dir = input_dir.parent
    suggestions = []
    
    # Look for potential transcript directories in common locations
    potential_dirs = [
        input_dir / "output",
        input_dir,
        parent_dir
    ]
    
    for i, dir_path in enumerate(potential_dirs, 1):
        if dir_path.exists():
            transcript_dirs = smart_scan_for_transcripts(dir_path)
            if transcript_dirs:
                suggestions.append((dir_path, f"{len(transcript_dirs)} transcript directories found"))
            else:
                suggestions.append((dir_path, "no transcripts found"))
        else:
            suggestions.append((dir_path, "directory not found"))
    
    # Display options
    for i, (dir_path, status) in enumerate(suggestions, 1):
        print(f"{i}. {dir_path} ({status})")
    
    print(f"{len(suggestions) + 1}. Specify custom directory")
    print()
    
    while True:
        try:
            choice = int(input(f"Select option [1-{len(suggestions) + 1}]: "))
            
            if 1 <= choice <= len(suggestions):
                selected_dir = suggestions[choice - 1][0]
                transcript_dirs = smart_scan_for_transcripts(selected_dir)
                
                if not transcript_dirs:
                    print_error(f"No transcript directories found in {selected_dir}")
                    continue
                
                # Let user select from found transcript directories
                selected_transcript = select_from_found_transcripts(transcript_dirs, selected_dir)
                if selected_transcript:
                    return {
                        'mode': 'reuse',
                        'transcript_dir': selected_transcript['path'],
                        'language': selected_transcript['language'],
                        'stage': selected_transcript['stage'],
                        'model': selected_transcript['model'],
                        'input_dir': str(input_dir)
                    }
                    
            elif choice == len(suggestions) + 1:
                # Browse for custom transcript directory
                selected_transcript = browse_for_transcript_directory()
                if selected_transcript:
                    return {
                        'mode': 'reuse',
                        'transcript_dir': selected_transcript['path'],
                        'language': selected_transcript['language'],
                        'stage': selected_transcript['stage'],
                        'model': selected_transcript['model'],
                        'input_dir': str(input_dir)
                    }
            else:
                print(f"Please select 1-{len(suggestions) + 1}.")
                
        except ValueError:
            print("Please enter a number.")

def select_input_files() -> Dict[str, any]:
    """Select input files and directory"""
    print_header("📁 Input File Selection")
    
    # Default directory
    default_dir = Path.cwd() / "sample_inputs"
    
    print("Where are your video/audio files located?")
    print(f"1. Use current directory: {Path.cwd()}")
    print(f"2. Use sample inputs: {default_dir}")
    print("3. Specify custom directory")
    print()
    
    while True:
        choice_input = input("Select option [1-3]: ").strip()
        
        if choice_input in ['1', '']:
            input_dir = Path.cwd()
            break
        elif choice_input == '2':
            input_dir = default_dir
            break
        elif choice_input == '3':
            while True:
                print("\n💡 You can paste a directory path directly (quotes will be handled automatically)")
                path_input = input("Enter directory path: ")
                
                if not path_input.strip():
                    print_error("Please enter a path or press Ctrl+C to cancel")
                    continue
                
                try:
                    cleaned_path = clean_path_input(path_input)
                    input_dir = Path(cleaned_path)
                    
                    if not input_dir.exists():
                        print_error(f"Directory does not exist: {input_dir}")
                        retry = input("Try again? [Y/n]: ").strip().lower()
                        if retry in ['n', 'no']:
                            return select_input_files()  # Start over
                        continue
                    
                    if not input_dir.is_dir():
                        print_error(f"Path is not a directory: {input_dir}")
                        continue
                    
                    break
                    
                except Exception as e:
                    print_error(f"Invalid path: {e}")
                    continue
            break
        else:
            print("Please select 1, 2, or 3.")
    
    # Check for media files
    media_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4a', '.wav', '.mp3', '.flac']
    media_files = []
    
    for ext in media_extensions:
        media_files.extend(list(input_dir.glob(f"*{ext}")))
        media_files.extend(list(input_dir.glob(f"*{ext.upper()}")))
    
    if not media_files:
        # Check for recursive search
        if ask_yes_no("No media files found in directory. Search subdirectories?", 
                     "This will search all subdirectories for media files"):
            for ext in media_extensions:
                media_files.extend(list(input_dir.rglob(f"*{ext}")))
                media_files.extend(list(input_dir.rglob(f"*{ext.upper()}")))
    
    if not media_files:
        print_error("No media files found.")
        sys.exit(1)
    
    media_files = sorted(media_files)
    print_success(f"Found {len(media_files)} media file(s)")
    
    # Show files and get selection
    print("\nFound files:")
    for i, file in enumerate(media_files, 1):
        print(f"  {i}. {file.name}")
    
    if len(media_files) > 1:
        if ask_yes_no(f"Process ALL {len(media_files)} files?", "y"):
            selected_files = media_files
        else:
            print("\n📋 File Selection Options:")
            print("• Individual files: 1,3,5")
            print("• Ranges: 2-8 or 1-3,7-10")
            print("• All files: 'all' or 'a'")
            print("• Mixed: 1,3-5,9")
            print()
            
            while True:
                selection = input("Enter your selection: ").strip()
                
                if not selection:
                    print_error("Please enter a selection or 'all'")
                    continue
                
                try:
                    indices = parse_file_selection(selection, len(media_files))
                    
                    if not indices:
                        print_error("No valid files selected")
                        continue
                    
                    selected_files = [media_files[i] for i in indices]
                    
                    # Confirm selection
                    print(f"\n✅ Selected {len(selected_files)} file(s):")
                    for file in selected_files:
                        print(f"  • {file.name}")
                    
                    if ask_yes_no("Proceed with these files?", "", "y"):
                        break
                    else:
                        print("Please make a new selection:")
                        continue
                        
                except ValueError as e:
                    print_error(str(e))
                    print("Please try again with a valid selection.")
                    continue
    else:
        selected_files = media_files
    
    return {
        'mode': 'new',
        'input_dir': str(input_dir),
        'selected_files': [str(f) for f in selected_files],
        'recursive': input_dir in [f.parent for f in Path(input_dir).rglob("*") if f in selected_files]
    }

def select_transcription_options() -> Dict[str, any]:
    """Select transcription model and options"""
    print_header("🧠 Transcription Configuration")
    
    # Model selection
    print("Whisper Model Selection:")
    print("💡 Model choice affects quality and speed:")
    print()
    
    models = [
        ("tiny", "Fastest, lowest quality", "Quick tests"),
        ("base", "Balanced speed/quality", "Most use cases"),
        ("small", "Better quality, moderate speed", "Important content"),
        ("medium", "High quality, slower", "Professional use"),
        ("large", "Best quality, slowest", "Critical accuracy")
    ]
    
    for i, (model, desc, use) in enumerate(models, 1):
        print(f"{Colors.BOLD}{i}. {model}{Colors.NC} - {desc} (good for {use})")
    
    print(f"\n{Colors.CYAN}For your first test, we recommend 'base' for good results quickly.{Colors.NC}")
    
    while True:
        choice = input("\nSelect model [1-5] or press Enter for base: ").strip()
        if not choice:
            model = "base"
            break
        try:
            choice = int(choice)
            if 1 <= choice <= 5:
                model = ["tiny", "base", "small", "medium", "large"][choice - 1]
                break
            else:
                print("Please select 1-5 or press Enter for default.")
        except ValueError:
            print("Please enter a number.")
    
    print_success(f"Selected: {model} model")
    
    # Audio preprocessing option
    print("\n🔊 Audio Preprocessing:")
    print("💡 STRONGLY RECOMMENDED - Enhances audio quality before transcription:")
    print("• Removes background noise and unwanted frequencies")
    print("• Optimizes audio sample rate for Whisper (16kHz)")
    print("• Improves transcription accuracy for ALL audio types")
    print("• Works for: studio recordings, interviews, phone calls, video conferences")
    print("• Requires FFmpeg (automatically falls back if not available)")
    print()
    print(f"{Colors.YELLOW}⚠️  Only disable if you have very specific technical requirements{Colors.NC}")
    print(f"{Colors.GREEN}✅ Recommended for 99% of use cases{Colors.NC}")
    print()
    
    preprocessing = ask_yes_no("Enable audio preprocessing?", 
                              "RECOMMENDED: Improves quality for virtually all audio sources", "y")
    
    enhancement_level = "standard"  # Default
    if preprocessing:
        print_success("Audio preprocessing enabled")
        
        # Ask for enhancement level
        print("\n🎚️ Audio Enhancement Level:")
        print("Choose enhancement strength based on your audio quality:")
        print()
        print("1. Minimal - Basic cleanup only (good quality audio)")
        print("   • Bandpass filter + volume normalization")
        print("   • Fastest processing, minimal artifacts")
        print()
        print("2. Standard - Balanced enhancement (most audio types)")
        print("   • Noise reduction + dynamic range compression")
        print("   • Good balance of quality vs artifacts")
        print()
        print("3. Aggressive - Maximum enhancement (poor quality audio)")
        print("   • Heavy noise reduction + compression + EQ boost")
        print("   • Best for difficult audio, may introduce artifacts")
        print()
        print(f"{Colors.CYAN}💡 Recommendation:{Colors.NC}")
        print("• Studio/professional recordings: Minimal")
        print("• Phone calls, video conferences: Standard")
        print("• Noisy environments, low quality: Aggressive")
        print()
        
        while True:
            choice = input("Select enhancement level [1-3] or press Enter for Standard: ").strip()
            if not choice or choice == '2':
                enhancement_level = "standard"
                break
            elif choice == '1':
                enhancement_level = "minimal"
                break
            elif choice == '3':
                enhancement_level = "aggressive"
                break
            else:
                print("Please select 1, 2, or 3.")
        
        print_success(f"Enhancement level: {enhancement_level}")
    else:
        print_info("Using original audio (faster processing)")
    
    return {
        'model': model,
        'preprocessing': preprocessing,
        'enhancement_level': enhancement_level,
        'recursive': False  # Will be set based on input selection
    }

def select_processing_options(output_format: str, api_keys: Dict[str, str]) -> Dict[str, any]:
    """Select processing options based on output format"""
    print_header("⚙️ Processing Options")
    
    options = {
        'diarization': False,
        'context_correction': False,
        'translation': False,
        'target_language': None
    }
    
    # Diarization (for all formats except JSON)
    if output_format != 'json':
        print("🎭 Speaker Diarization:")
        print("💡 Adds speaker labels (Speaker 1, Speaker 2, etc.) to identify who is speaking")
        print("• Useful for interviews, meetings, conversations")
        print("• Based on timing gaps and voice characteristics")
        print()
        
        options['diarization'] = ask_yes_no("Enable speaker diarization?", 
                                           "Adds speaker identification to transcripts")
        if options['diarization']:
            print_success("Speaker diarization enabled")
    
    # AI transcript enhancement (if API key available)
    if api_keys.get('OPENAI_API_KEY'):
        print("\n🧽 AI Transcript Enhancement (Optional)")
        print("="*45)
        print(f"{Colors.CYAN}💡 What this does:{Colors.NC}")
        print("In addition to the raw transcript, we can create an AI-enhanced")
        print("transcript that cleans up the text using contextual information.")
        print()
        print(f"{Colors.GREEN}✨ How it helps:{Colors.NC}")
        print("• Fixes words Whisper misheard (e.g., 'there' → 'their')")
        print("• Corrects basic grammar and punctuation")
        print("• Removes filler words like 'um', 'uh' (if you want)")
        print("• Makes transcripts easier to read and use")
        print()
        print(f"{Colors.YELLOW}🗂️ What you'll get:{Colors.NC}")
        print("• Original raw transcript (exactly what Whisper heard)")
        print("• Enhanced transcript (cleaned up version)")
        print("• Both saved in separate folders with clear labels")
        print()
        print(f"{Colors.CYAN}💰 Expected Cost:{Colors.NC}")
        print("• ~$0.01-0.03 per minute of video (sent to OpenAI for processing)")
        print(f"{Colors.YELLOW}• You can always add this enhancement later if you skip it now{Colors.NC}")
        print()
        
        # Custom yes/no prompt with specific options
        print("🔄 Would you like to create an AI-enhanced transcript?")
        print("1. Yes, add enhancement now")
        print("2. No, not right now (you can do this later if needed)")
        print()
        
        while True:
            choice = input("Select option [1-2]: ").strip()
            if choice == '1':
                options['context_correction'] = True
                break
            elif choice == '2':
                options['context_correction'] = False
                break
            else:
                print("Please select 1 or 2.")
        if options['context_correction']:
            print_success("AI context correction enabled")
            
            # AI Cleanup Configuration
            print("\n🧽 AI Transcript Cleanup Configuration")
            print("="*50)
            print(f"{Colors.CYAN}💡 Configure post-transcription cleanup:{Colors.NC}")
            print("After Whisper creates the transcript, AI can clean it up based on your needs.")
            print()
            print(f"{Colors.YELLOW}🎯 Cleanup levels:{Colors.NC}")
            print("1. Minimal - Fix obvious errors only (homophones, basic grammar)")
            print("2. Standard - Light cleanup + remove some filler words")
            print("3. Aggressive - Comprehensive cleanup for readability")
            print("4. Custom - Specify your own cleanup instructions")
            print()
            print(f"{Colors.GREEN}📝 Choose based on your use case:{Colors.NC}")
            print("• Video subtitles: Minimal (preserve speaker's exact words)")
            print("• Meeting notes: Standard (balance accuracy and readability)")
            print("• Article transcripts: Aggressive (polished, readable text)")
            print("• Special requirements: Custom (your specific instructions)")
            print()
            
            while True:
                cleanup_choice = input("Select cleanup level [1-4]: ").strip()
                if cleanup_choice in ['1', '2', '3', '4']:
                    break
                print("Please select 1, 2, 3, or 4.")
            
            cleanup_levels = ['minimal', 'standard', 'aggressive', 'custom']
            options['cleanup_level'] = cleanup_levels[int(cleanup_choice) - 1]
            
            if options['cleanup_level'] == 'custom':
                print(f"\n{Colors.CYAN}🎨 Custom Cleanup Instructions:{Colors.NC}")
                print("💡 Describe what you want the AI to do with your transcript:")
                print("• Examples: 'Remove all um and uh, fix grammar but keep informal tone'")
                print("•          'Only fix obvious errors, preserve all speech exactly'")
                print("•          'Make it very formal and remove all casual language'")
                print()
                
                user_cleanup_description = input("Enter your cleanup instructions: ").strip()
                
                if user_cleanup_description:
                    # Clean description input
                    if user_cleanup_description.startswith('"') and user_cleanup_description.endswith('"'):
                        user_cleanup_description = user_cleanup_description[1:-1]
                    elif user_cleanup_description.startswith("'") and user_cleanup_description.endswith("'"):
                        user_cleanup_description = user_cleanup_description[1:-1]
                    
                    # Iterative cleanup prompt refinement loop
                    current_cleanup_prompt = None
                    while True:
                        print(f"\n{Colors.CYAN}🤖 Optimizing cleanup instructions...{Colors.NC}")
                        
                        try:
                            # Generate optimized cleanup prompt using OpenAI
                            import openai
                            client = openai.OpenAI(api_key=api_keys['OPENAI_API_KEY'])
                            
                            cleanup_response = client.chat.completions.create(
                                model="gpt-4",
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are an expert at creating precise transcript cleanup instructions for AI. Convert user descriptions into clear, actionable cleanup prompts that preserve important speech characteristics while achieving the user's goals. Be specific about what to remove, fix, or preserve. Keep instructions under 100 words and focus on concrete actions."
                                    },
                                    {
                                        "role": "user",
                                        "content": f"Convert this cleanup description into optimal AI cleanup instructions: {user_cleanup_description}"
                                    }
                                ],
                                max_tokens=150,
                                temperature=0.3
                            )
                            
                            current_cleanup_prompt = cleanup_response.choices[0].message.content.strip()
                            
                            # Remove quotes if the AI added them
                            if current_cleanup_prompt.startswith('"') and current_cleanup_prompt.endswith('"'):
                                current_cleanup_prompt = current_cleanup_prompt[1:-1]
                            
                            print(f"\n{Colors.BOLD}📋 AI-Optimized Cleanup Instructions:{Colors.NC}")
                            print(f"{Colors.GREEN}'{current_cleanup_prompt}'{Colors.NC}")
                            print()
                            print(f"{Colors.CYAN}💡 This will guide the AI to:{Colors.NC}")
                            print("• Apply consistent cleanup rules across all transcript segments")
                            print("• Preserve important speech characteristics as specified")
                            print("• Balance accuracy with your readability requirements")
                            print()
                            
                            # Get user approval
                            if ask_yes_no("Use these cleanup instructions?", 
                                         "This will guide how AI cleans up your transcript", "y"):
                                options['custom_cleanup_prompt'] = current_cleanup_prompt
                                print_success(f"✅ Approved cleanup: '{current_cleanup_prompt}'")
                                break
                            
                            # Ask if they want to modify their description
                            print(f"\n{Colors.YELLOW}🔄 Let's refine your cleanup instructions{Colors.NC}")
                            print("💡 Try being more specific about what to keep vs. what to remove")
                            
                            new_cleanup_description = input(f"\nRevised cleanup description (or Enter to use original): ").strip()
                            if new_cleanup_description:
                                # Clean new description
                                if new_cleanup_description.startswith('"') and new_cleanup_description.endswith('"'):
                                    new_cleanup_description = new_cleanup_description[1:-1]
                                elif new_cleanup_description.startswith("'") and new_cleanup_description.endswith("'"):
                                    new_cleanup_description = new_cleanup_description[1:-1]
                                user_cleanup_description = new_cleanup_description
                            
                            # Option to use their original description
                            if ask_yes_no("Or use your original description as-is?", 
                                         f"This would use: '{user_cleanup_description}'"):
                                options['custom_cleanup_prompt'] = user_cleanup_description
                                print_success(f"✅ Using your description: '{user_cleanup_description}'")
                                break
                                
                        except Exception as e:
                            print_warning(f"Could not generate optimized cleanup instructions: {str(e)}")
                            print_info(f"Using your description as cleanup prompt: '{user_cleanup_description}'")
                            options['custom_cleanup_prompt'] = user_cleanup_description
                            break
                else:
                    print_error("Please enter cleanup instructions or select a different level")
                    # Go back to level selection - restart the cleanup level selection
                    options['cleanup_level'] = 'standard'  # Default fallback
            else:
                cleanup_descriptions = {
                    'minimal': 'Fix obvious transcription errors only',
                    'standard': 'Fix errors + light cleanup (remove some filler words)',
                    'aggressive': 'Comprehensive cleanup (remove most filler words, improve readability)'
                }
                print_success(f"✅ Cleanup level: {options['cleanup_level']} - {cleanup_descriptions[options['cleanup_level']]}")
    else:
        print_warning("AI context correction not available (no OpenAI API key)")
    
    # Translation (if API key available)
    if api_keys.get('OPENAI_API_KEY'):
        print("\n🌐 Translation Options (Optional)")
        print("="*35)
        print(f"{Colors.CYAN}💡 What this does:{Colors.NC}")
        print("The transcript will be created in the original language of your content.")
        print("We can then create an additional translated version in another language.")
        print()
        print(f"{Colors.GREEN}✨ How it works:{Colors.NC}")
        print("• Preserves exact timing data for subtitles")
        print("• Uses GPT-4 for natural, context-aware translation")
        print("• Creates separate files for original and translated versions")
        print()
        
        # Ask for original language identification
        print(f"{Colors.YELLOW}🗣️ What language is spoken in your content?{Colors.NC}")
        original_languages = [
            "English", "Spanish", "French", "German", "Chinese (Mandarin)", 
            "Japanese", "Portuguese", "Italian", "Korean", "Arabic"
        ]
        
        for i, lang in enumerate(original_languages, 1):
            print(f"  {i}. {lang}")
        print(f"  {len(original_languages) + 1}. Other (specify)")
        
        while True:
            try:
                choice = int(input(f"Select original language [1-{len(original_languages) + 1}]: "))
                if 1 <= choice <= len(original_languages):
                    options['original_language'] = original_languages[choice - 1]
                    break
                elif choice == len(original_languages) + 1:
                    custom = input("Enter the original language: ").strip()
                    if custom:
                        if custom.startswith('"') and custom.endswith('"'):
                            custom = custom[1:-1]
                        elif custom.startswith("'") and custom.endswith("'"):
                            custom = custom[1:-1]
                        options['original_language'] = custom.strip().title()
                        break
                    else:
                        print_error("Please enter a language name")
                else:
                    print(f"Please select 1-{len(original_languages) + 1}.")
            except ValueError:
                print("Please enter a number.")
        
        print_success(f"Original language: {options['original_language']}")
        
        print(f"\n{Colors.CYAN}💰 Expected Cost:{Colors.NC}")
        print("• ~$0.05-0.15 per minute of video (sent to OpenAI for translation)")
        print(f"{Colors.YELLOW}• You can always add translation later if you skip it now{Colors.NC}")
        print()
        
        # Custom yes/no prompt with specific options
        print("🔄 Would you like to create a translated version?")
        print("1. Yes, add translation now")
        print("2. No, not right now (you can do this later if needed)")
        print()
        
        while True:
            choice = input("Select option [1-2]: ").strip()
            if choice == '1':
                options['translation'] = True
                break
            elif choice == '2':
                options['translation'] = False
                break
            else:
                print("Please select 1 or 2.")
        
        if options['translation']:
            print("\nSelect target language for translation:")
            target_languages = [
                "Spanish", "French", "German", "Chinese (Simplified)", 
                "Chinese (Traditional)", "Japanese", "Portuguese", "Italian", "Korean", "Arabic"
            ]
            
            for i, lang in enumerate(target_languages, 1):
                print(f"  {i}. {lang}")
            print(f"  {len(target_languages) + 1}. Other (specify)")
            
            while True:
                try:
                    choice = int(input(f"Select target language [1-{len(target_languages) + 1}]: "))
                    if 1 <= choice <= len(target_languages):
                        options['target_language'] = target_languages[choice - 1]
                        break
                    elif choice == len(target_languages) + 1:
                        print("💡 Enter the target language name (e.g., 'Hindi', 'Russian', 'Thai')")
                        custom = input("Target language: ").strip()
                        
                        # Clean language input
                        if custom:
                            # Remove quotes if present
                            if custom.startswith('"') and custom.endswith('"'):
                                custom = custom[1:-1]
                            elif custom.startswith("'") and custom.endswith("'"):
                                custom = custom[1:-1]
                            
                            options['target_language'] = custom.strip().title()
                            break
                        else:
                            print_error("Please enter a language name")
                    else:
                        print(f"Please select 1-{len(target_languages) + 1}.")
                except ValueError:
                    print("Please enter a number.")
            
            print_success(f"Will translate from {options['original_language']} to {options['target_language']}")
    else:
        print_warning("Translation not available (no OpenAI API key)")
    
    return options

def select_format_specific_options(output_format: str, has_speakers: bool) -> Dict[str, any]:
    """Select format-specific options"""
    options = {}
    
    if output_format == 'markdown':
        print_header("📝 Markdown Format Options")
        
        print("Markdown formatting options:")
        print("💡 Choose what information to include in your transcript")
        print()
        
        # Timecode option
        print("🕒 Timecodes:")
        print("• Shows timestamp for each segment (e.g., **02:45**: Hello there)")
        print("• Useful for referencing specific moments")
        print()
        options['include_timecodes'] = ask_yes_no("Include timecodes in markdown?", 
                                                 "Adds timestamps to help locate specific moments")
        
        # Speaker option (only if diarization was enabled)
        if has_speakers:
            print("\n👥 Speaker Labels:")
            print("• Shows who is speaking (e.g., **Speaker 1**: Hello there)")
            print("• Requires speaker diarization to be enabled")
            print()
            options['include_speakers'] = ask_yes_no("Include speaker labels?", 
                                                   "Shows who is speaking for each segment")
        else:
            options['include_speakers'] = False
        
        # Custom title
        print("\n📋 Custom Title:")
        print("💡 Enter a custom title for your transcript (optional)")
        custom_title = input("Custom title (or press Enter for auto-generated): ").strip()
        
        # Clean title input
        if custom_title:
            # Remove quotes if present
            if custom_title.startswith('"') and custom_title.endswith('"'):
                custom_title = custom_title[1:-1]
            elif custom_title.startswith("'") and custom_title.endswith("'"):
                custom_title = custom_title[1:-1]
            
            options['title'] = custom_title.strip()
    
    elif output_format == 'fcpxml':
        print_header("🎬 FCPXML Format Options")
        
        print("Final Cut Pro XML options:")
        print("💡 Customize the FCPXML project settings")
        print()
        
        # Project name
        print("💡 Enter a custom project name for your FCPXML file (optional)")
        custom_name = input("Project name (or press Enter for auto-generated): ").strip()
        
        # Clean project name input
        if custom_name:
            # Remove quotes if present
            if custom_name.startswith('"') and custom_name.endswith('"'):
                custom_name = custom_name[1:-1]
            elif custom_name.startswith("'") and custom_name.endswith("'"):
                custom_name = custom_name[1:-1]
            
            options['project_name'] = custom_name.strip()
    
    return options

def select_cleanup_level() -> str:
    """Select cleanup level for iterative refinement"""
    print("🎯 Cleanup levels:")
    print("1. Minimal - Fix obvious errors only (homophones, basic grammar)")
    print("2. Standard - Light cleanup + remove some filler words")
    print("3. Aggressive - Comprehensive cleanup for readability")
    print("4. Custom - Specify your own cleanup instructions")
    print()
    
    while True:
        cleanup_choice = input("Select cleanup level [1-4]: ").strip()
        if cleanup_choice in ['1', '2', '3', '4']:
            cleanup_levels = ['minimal', 'standard', 'aggressive', 'custom']
            return cleanup_levels[int(cleanup_choice) - 1]
        print("Please select 1, 2, 3, or 4.")

def select_ai_cleanup_options(api_keys: Dict[str, str]) -> Dict[str, str]:
    """Select AI cleanup options for existing transcript operations"""
    while True:
        print("🎯 AI Cleanup Levels:")
        print()
        print(f"{Colors.YELLOW}💰 Cost Information:{Colors.NC}")
        print("• AI cleanup uses OpenAI GPT-4 for processing")
        print("• Estimated cost: ~$0.01-0.03 per minute of transcript content")
        print("• You'll see a cost estimate before processing begins")
        print("• All API usage is transparent and shown upfront")
        print()
        
        print("1. Minimal - Fix obvious homophone errors (there/their, your/you're) and basic")
        print("   grammar mistakes. Preserve all filler words and informal speech.")
        print("   Maintain speaker's exact style and tone.")
        print()
        print("2. Standard - Fix homophone and grammar errors. Remove some filler words")
        print("   (um, uh) while preserving authenticity. Improve basic punctuation")
        print("   and capitalization. Preserve informal language and speaking style.")
        print()
        print("3. Aggressive - Fix all grammar, punctuation, and homophone errors.")
        print("   Remove most filler words and speech disfluencies. Improve sentence")
        print("   structure for readability. Enhanced text for publication-ready quality.")
        print()
        print("4. Custom - Specify your own cleanup instructions. OpenAI will help refine")
        print("   your instructions through an interactive process to ensure optimal results.")
        print("   Additional cost: ~$0.01 for instruction optimization.")
        print()
        
        while True:
            cleanup_choice = input("Select cleanup level [1-4]: ").strip()
            if cleanup_choice in ['1', '2', '3', '4']:
                cleanup_levels = ['minimal', 'standard', 'aggressive', 'custom']
                cleanup_level = cleanup_levels[int(cleanup_choice) - 1]
                break
            print("Please select 1, 2, 3, or 4.")
        
        config = {'cleanup_level': cleanup_level}
        
        if cleanup_level == 'custom':
            custom_instructions = get_custom_cleanup_prompt(api_keys)
            if custom_instructions is None:
                # User chose to go back to cleanup level selection
                print(f"\n{Colors.YELLOW}🔄 Restarting cleanup level selection{Colors.NC}")
                continue
            config['custom_cleanup_prompt'] = custom_instructions
        
        return config

def select_target_language() -> str:
    """Select target language for translation"""
    print("\nSelect target language for translation:")
    target_languages = [
        "Spanish", "French", "German", "Chinese (Simplified)", 
        "Chinese (Traditional)", "Japanese", "Portuguese", "Italian", "Korean", "Arabic"
    ]
    
    for i, lang in enumerate(target_languages, 1):
        print(f"  {i}. {lang}")
    print(f"  {len(target_languages) + 1}. Other (specify)")
    
    while True:
        try:
            choice = int(input(f"Select target language [1-{len(target_languages) + 1}]: "))
            if 1 <= choice <= len(target_languages):
                return target_languages[choice - 1]
            elif choice == len(target_languages) + 1:
                print("💡 Enter the target language name (e.g., 'Hindi', 'Russian', 'Thai')")
                custom = input("Target language: ").strip()
                
                if custom:
                    if custom.startswith('"') and custom.endswith('"'):
                        custom = custom[1:-1]
                    elif custom.startswith("'") and custom.endswith("'"):
                        custom = custom[1:-1]
                    return custom.strip().title()
                else:
                    print_error("Please enter a language name")
            else:
                print(f"Please select 1-{len(target_languages) + 1}.")
        except ValueError:
            print("Please enter a number.")

def get_custom_ai_instructions() -> str:
    """Get custom AI instructions from user"""
    print("🎨 Custom AI Instructions:")
    print("💡 Describe what you want the AI to do with your transcript:")
    print("• Examples: 'Summarize key points from each speaker'")
    print("•          'Extract action items and decisions made'")
    print("•          'Convert to formal business language'")
    print()
    
    instructions = input("Enter your custom instructions: ").strip()
    
    if not instructions:
        return "Apply custom processing while preserving meaning and timing"
    
    # Clean input
    if instructions.startswith('"') and instructions.endswith('"'):
        instructions = instructions[1:-1]
    elif instructions.startswith("'") and instructions.endswith("'"):
        instructions = instructions[1:-1]
    
    return instructions.strip()
def get_custom_cleanup_prompt(api_keys: Dict[str, str]) -> str:
    """Get custom cleanup prompt from user with AI optimization"""
    while True:
        print("🎨 Help OpenAI Understand Your Content Context:")
        print("💡 Describe the context of your content so OpenAI can make better correction decisions:")
        print("• Examples: 'Business meeting with technical jargon and some industry acronyms'")
        print("•          'Casual interview with Taiwan English accents, some Mandarin names'")
        print("•          'Educational lecture about software development with coding terms'")
        print("•          'Medical conference with pharmaceutical terminology'")
        print()
        
        user_description = input("Enter context description: ").strip()
        
        if not user_description:
            print_error("Please provide a context description or go back to select a different cleanup level.")
            if ask_yes_no("Go back to cleanup level selection?", "", "y"):
                return None  # Signal to restart cleanup level selection
            continue
        
        # Clean input
        if user_description.startswith('"') and user_description.endswith('"'):
            user_description = user_description[1:-1]
        elif user_description.startswith("'") and user_description.endswith("'"):
            user_description = user_description[1:-1]
        
        try:
            import openai
            client = openai.OpenAI(api_key=api_keys['OPENAI_API_KEY'])
            
            print(f"\n{Colors.CYAN}🤖 AI is creating optimized cleanup instructions...{Colors.NC}")
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are helping a user improve an audio transcript created by Whisper AI. The user is describing the context of their content to help you create better transcript cleanup instructions. Your job is to provide clear, actionable instructions for AI transcript cleanup that takes this context into account. Focus on: 1) What errors to fix (homophones, grammar, technical terms), 2) What to preserve (speaking style, specific terminology, names), 3) How to handle context-specific elements (accents, technical jargon, proper nouns). Keep instructions under 100 words and be specific."
                    },
                    {
                        "role": "user",
                        "content": f"Context: {user_description}\n\nPlease provide optimized cleanup instructions for AI transcript processing that takes this context into account."
                    }
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            optimized = response.choices[0].message.content.strip()
            if optimized.startswith('"') and optimized.endswith('"'):
                optimized = optimized[1:-1]
            
            print(f"\n{Colors.BOLD}📋 AI-Optimized Cleanup Instructions:{Colors.NC}")
            print(f"{Colors.GREEN}'{optimized}'{Colors.NC}")
            print()
            print(f"{Colors.CYAN}💡 These instructions will help AI better understand your content context.{Colors.NC}")
            print()
            
            # User decision loop
            while True:
                print("What would you like to do?")
                print("1. ✅ Use these optimized instructions")
                print("2. ✏️  Refine the context description")
                print("3. 📝 Use your original description as-is")
                print("4. 🔙 Go back to cleanup level selection")
                print()
                
                choice = input("Select option [1-4]: ").strip()
                
                if choice == '1':
                    print_success(f"Using AI-optimized instructions: '{optimized}'")
                    return optimized
                elif choice == '2':
                    print(f"\n{Colors.YELLOW}🔄 Let's refine your context description{Colors.NC}")
                    print("💡 Try being more specific about accents, technical terms, or speaking style")
                    break  # Break inner loop to restart context input
                elif choice == '3':
                    print_success(f"Using your original description: '{user_description}'")
                    return user_description
                elif choice == '4':
                    return None  # Signal to restart cleanup level selection
                else:
                    print("Please select 1, 2, 3, or 4.")
                    
        except Exception as e:
            print_warning(f"Could not optimize instructions: {e}")
            print(f"\n{Colors.YELLOW}Using your original description: '{user_description}'{Colors.NC}")
            return user_description

def select_output_directory(config: Dict[str, any] = None) -> str:
    """Select output directory with smart defaults based on source"""
    print_header("📤 Output Directory")
    
    # Determine source directory for smart suggestions
    source_dir = None
    if config and config.get('input'):
        if config['input'].get('input_dir'):
            source_dir = Path(config['input']['input_dir'])
        elif config['input'].get('transcript_dir'):
            # For existing transcripts, use the parent directory to create sibling output
            transcript_path = Path(config['input']['transcript_dir'])
            source_dir = transcript_path.parent
    
    # Option 1: Next to source directory (recommended)
    if source_dir and source_dir.exists():
        # Create a sibling directory with _output suffix
        source_output = source_dir.parent / f"{source_dir.name}_output"
        option1_text = f"Next to source: {source_output}"
        option1_path = source_output
    else:
        # Fallback to current directory
        option1_path = Path.cwd() / "output"
        option1_text = f"Current directory: {option1_path}"
    
    # Option 2: Desktop or app default
    desktop_path = Path.home() / "Desktop" / "transcription_output"
    app_default = Path.cwd() / "output"
    
    print("Where should the results be saved?")
    print(f"1. {option1_text} ✨ Recommended")
    print(f"2. Desktop: {desktop_path}")
    print(f"3. App default: {app_default}")
    print("4. Custom location")
    print()
    
    while True:
        choice_input = input("Select option [1-4]: ").strip()
        
        if choice_input in ['1', '']:
            output_dir = option1_path
            break
        elif choice_input == '2':
            output_dir = desktop_path
            break
        elif choice_input == '3':
            output_dir = app_default
            break
        elif choice_input == '4':
            while True:
                print("\n💡 You can paste a directory path directly (will be created if it doesn't exist)")
                path_input = input("Enter output directory path: ")
                
                if not path_input.strip():
                    print_error("Please enter a path or select option 1-3")
                    continue
                
                # Validate input doesn't contain command-like text
                if any(phrase in path_input.lower() for phrase in ['select option', 'select transcript', 'operation']):
                    print_error("Invalid path input detected. Please enter a valid directory path.")
                    continue
                
                try:
                    cleaned_path = clean_path_input(path_input)
                    output_dir = Path(cleaned_path)
                    
                    # Try to create the directory to test if path is valid
                    try:
                        output_dir.mkdir(parents=True, exist_ok=True)
                        break
                    except Exception as e:
                        print_error(f"Cannot create directory: {e}")
                        continue
                        
                except Exception as e:
                    print_error(f"Invalid path: {e}")
                    continue
            break
        else:
            print("Please select 1, 2, 3, or 4.")
    
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Output directory: {output_dir}")
    
    return str(output_dir)

def create_stage_directory(output_dir: Path, stage_num: int, stage_name: str, description: str) -> Path:
    """Create a numbered stage directory with documentation"""
    stage_dir = output_dir / f"{stage_num}_{stage_name}"
    stage_dir.mkdir(exist_ok=True)
    
    # Create README with stage description
    readme_path = stage_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(f"# Stage {stage_num}: {stage_name.replace('_', ' ').title()}\n\n")
        f.write(f"{description}\n\n")
        f.write(f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Processing:** {stage_name}\n")
    
    return stage_dir

def run_pipeline(config: Dict[str, any]) -> bool:
    """Execute the transcription pipeline with staged directories"""
    print_header("🚀 Executing Pipeline")
    
    print("Configuration Summary:")
    print(f"• Output format: {config['output_format']}")
    
    # Only show transcription details for new transcripts
    if config['input'].get('mode') not in ['reuse', 'existing_operations']:
        print(f"• Model: {config['transcription']['model']}")
        print(f"• Audio preprocessing: {config['transcription']['preprocessing']}")
        print(f"• Input files: {len(config['input']['selected_files'])}")
    else:
        print(f"• Using existing transcripts from: {config['input']['transcript_dir']}")
        if config['input'].get('operation'):
            print(f"• Operation: {config['input']['operation']}")
    
    print(f"• Diarization: {config['processing']['diarization']}")
    print(f"• Context correction: {config['processing']['context_correction']}")
    print(f"• Translation: {config['processing']['translation']}")
    if config['processing']['translation']:
        print(f"• Target language: {config['processing']['target_language']}")
    print(f"• Output directory: {config['output_dir']}")
    print()
    
    if not ask_yes_no("Proceed with transcription?", "", "y"):
        print("Pipeline cancelled by user.")
        return False
    
    try:
        import datetime
        output_base = Path(config['output_dir'])
        stage_counter = 1
        
        # Determine processing path based on input mode
        input_mode = config['input'].get('mode', 'new')
        
        # For existing operations, use the provided transcript directory
        if input_mode in ['existing_operations', 'reuse']:
            current_transcript_dir = Path(config['input']['transcript_dir'])
            print_success(f"Using existing transcripts from: {current_transcript_dir}")
            
            # Skip transcription stage for existing transcripts
            print(f"Skipping transcription stage (working with existing files)")
            
        else:
            # Stage 1: Raw Whisper Transcription (for new transcripts)
            print_header("📝 Stage 1: Raw Whisper Transcription")
            raw_description = f"Raw Whisper transcription using '{config['transcription']['model']}' model."
            if config['transcription']['preprocessing']:
                raw_description += " Audio preprocessing (noise reduction, 16kHz resampling) applied."
            
            current_transcript_dir = create_stage_directory(
                output_base, stage_counter, "raw_whisper", raw_description
            )
            stage_counter += 1
            
            cmd = [
                "python", "scripts/transcribe.py",
                "--input-dir", config['input']['input_dir'],
                "--output-dir", str(current_transcript_dir),
                "--model", config['transcription']['model']
            ]
            
            if config['input'].get('recursive'):
                cmd.append("--recursive")
            
            if config['transcription'].get('preprocessing'):
                cmd.append("--preprocessing")
                # Pass enhancement level if specified
                enhancement_level = config['transcription'].get('enhancement_level', 'standard')
                cmd.extend(["--enhancement-level", enhancement_level])
            
            # No initial prompt - let Whisper transcribe naturally
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
            print_success("Transcription complete")
        
        # Stage 2: AI Cleanup (if enabled)
        if config['processing']['context_correction']:
            print_header("🤖 Stage 2: AI Transcript Cleanup")
            
            # Iterative cleanup loop
            while True:
                cleanup_level = config['processing'].get('cleanup_level', 'standard')
                custom_prompt = config['processing'].get('custom_cleanup_prompt')
                
                cleanup_description = {
                    'minimal': 'Minimal cleanup (homophones, basic grammar)',
                    'standard': 'Standard cleanup (light filler word removal)',
                    'aggressive': 'Aggressive cleanup (heavy filler word removal)',
                    'custom': f'Custom cleanup: \'{custom_prompt}\''
                }.get(cleanup_level, 'Standard cleanup')
                
                print(f"Applying: {cleanup_description}")
                
                cleaned_dir = create_stage_directory(
                    output_base, stage_counter, f"cleaned_{cleanup_level}", cleanup_description
                )
                
                cmd = [
                    "python", "scripts/context_correct_transcript.py",
                    "--input-dir", str(current_transcript_dir),
                    "--output-dir", str(cleaned_dir),
                    "--api-key", config['api_keys']['OPENAI_API_KEY'],
                    "--cleanup-level", cleanup_level
                ]
                
                if custom_prompt:
                    cmd.extend(["--custom-cleanup-prompt", custom_prompt])
                
                print(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True)
                print_success("AI cleanup complete")
                
                current_transcript_dir = cleaned_dir
                
                # Ask if user wants to refine cleanup
                if ask_yes_no("\nWould you like to refine the cleanup?", 
                             "This will create a new cleaned version with different instructions"):
                    # Re-run cleanup options with refined instructions
                    print("\n🧽 Refining AI Transcript Cleanup")
                    print("="*50)
                    
                    # Get new cleanup level
                    new_cleanup_level = select_cleanup_level()
                    config['processing']['cleanup_level'] = new_cleanup_level
                    
                    # Get new custom prompt if needed
                    if new_cleanup_level == 'custom':
                        new_custom_prompt = get_custom_cleanup_prompt(config['api_keys'])
                        config['processing']['custom_cleanup_prompt'] = new_custom_prompt
                    else:
                        config['processing']['custom_cleanup_prompt'] = None
                    
                    stage_counter += 1
                    continue
                else:
                    break
            
            stage_counter += 1
        
        # For reuse mode, skip all processing and go directly to final output
        if input_mode == 'reuse':
            print_info("Reuse mode: Skipping all processing stages - proceeding directly to final output")
        
        # For existing operations mode, check if we should skip to final output
        elif (input_mode == 'existing_operations' and 
              config['input'].get('operation') not in ['translate']):
            print_info(f"Existing operations mode: Completed {config['input']['operation']} operation - proceeding to final output")
        
        # Step 3: Translation (if enabled)
        if config['processing']['translation'] and input_mode != 'reuse':
            print_header("🌐 Step 3: Translation")
            translated_dir = Path(config['output_dir']) / "translated_transcripts"
            translated_dir.mkdir(exist_ok=True)
            
            cmd = [
                "python", "scripts/translate_transcript.py",
                "--transcript-dir", str(current_transcript_dir),
                "--output-dir", str(translated_dir),
                "--target-language", config['processing']['target_language'],
                "--api-key", config['api_keys']['OPENAI_API_KEY'],
                "--skip-confirm"
            ]
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
            print_success("Translation complete")
            current_transcript_dir = translated_dir
        
        # Step 4: Diarization (if enabled and not in skip modes)
        if (config['processing']['diarization'] and 
            input_mode not in ['reuse', 'existing_operations']):
            print_header("🎭 Step 4: Speaker Diarization")
            diarized_dir = Path(config['output_dir']) / "diarized_transcripts"
            diarized_dir.mkdir(exist_ok=True)
            
            cmd = [
                "python", "scripts/diarize_transcript.py",
                "--input-dir", str(current_transcript_dir),
                "--output-dir", str(diarized_dir)
            ]
            
            # Add Hugging Face token if available
            if config['api_keys'].get('HUGGINGFACE_TOKEN'):
                cmd.extend(["--hf-token", config['api_keys']['HUGGINGFACE_TOKEN']])
                print("💡 Using advanced diarization with pyannote.audio")
            else:
                print("💡 Using simple timing-based speaker detection (no HF token)")
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
            print_success("Diarization complete")
            current_transcript_dir = diarized_dir
        
        # Step 5: Generate Final Output
        print_header(f"📄 Step 5: Generating {config['output_format'].upper()}")
        final_output_dir = Path(config['output_dir']) / f"final_{config['output_format']}"
        final_output_dir.mkdir(exist_ok=True)
        
        if config['output_format'] == 'markdown':
            cmd = [
                "python", "scripts/generate_markdown.py",
                "--input-dir", str(current_transcript_dir),
                "--output-dir", str(final_output_dir)
            ]
            
            if config['format_options'].get('include_timecodes'):
                cmd.append("--include-timecodes")
            if config['format_options'].get('include_speakers'):
                cmd.append("--include-speakers")
            if config['format_options'].get('title'):
                cmd.extend(["--title", config['format_options']['title']])
        
        elif config['output_format'] == 'fcpxml':
            cmd = [
                "python", "scripts/generate_fcpxml.py",
                "--input-dir", str(current_transcript_dir),
                "--output-dir", str(final_output_dir)
            ]
            
            if config['format_options'].get('project_name'):
                cmd.extend(["--project-name", config['format_options']['project_name']])
        
        elif config['output_format'] == 'itt':
            cmd = [
                "python", "scripts/generate_itt.py",
                "--input-dir", str(current_transcript_dir),
                "--output-dir", str(final_output_dir)
            ]
        
        elif config['output_format'] == 'json':
            # For JSON, just copy the final transcripts
            import shutil
            for json_file in current_transcript_dir.glob("*.json"):
                shutil.copy2(json_file, final_output_dir)
            print_success("JSON files copied")
        
        if config['output_format'] != 'json':
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
        
        print_success(f"{config['output_format'].upper()} generation complete")
        
        # Show results
        print_header("🎉 Pipeline Complete!")
        print(f"📁 Results saved to: {final_output_dir}")
        
        # List generated files
        output_files = list(final_output_dir.iterdir())
        if output_files:
            print(f"\n📄 Generated {len(output_files)} file(s):")
            for file in output_files:
                print(f"  • {file.name}")
        
        if ask_yes_no("Open output directory?", "", "y"):
            subprocess.run(["open", str(final_output_dir)])
        
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Pipeline failed: {e}")
        return False
    except KeyboardInterrupt:
        print_error("Pipeline cancelled by user")
        return False

def main():
    """Main execution function"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🎯 Transcriber v2.0 - Unified Pipeline")
    print("=====================================")
    print(f"{Colors.NC}")
    print(f"{Colors.CYAN}Goal-Centric Modular Transcription Pipeline{Colors.NC}")
    print()
    
    # Check API keys first
    api_keys = check_api_keys()
    
    # Gather configuration
    config = {
        'api_keys': api_keys
    }
    
    # Step 1: Select output format (goal-first approach)
    config['output_format'] = select_output_format()
    
    # Step 2: Select transcript source based on goal
    print(f"\n{Colors.CYAN}📁 Working with {config['output_format'].upper()} format{Colors.NC}")
    config['input'] = select_transcript_source(Path.cwd())
    
    if config['input']['mode'] == 'reuse':
        # Directly process existing transcript operations
        config['processing'] = {
            'diarization': False,
            'context_correction': False,
            'translation': False,
            'target_language': None,
        }
        config['format_options'] = {}
    elif config['input']['mode'] == 'existing_operations':
        # Handle the selected operation for existing transcripts
        operation = config['input']['operation']
        
        if operation == 'cleanup':
            # AI cleanup operation - need to get cleanup configuration
            print(f"\n{Colors.CYAN}🧹 AI Cleanup Configuration{Colors.NC}")
            cleanup_config = select_ai_cleanup_options(config['api_keys'])
            config['processing'] = {
                'diarization': False,
                'context_correction': True,
                'translation': False,
                'target_language': None,
                'cleanup_level': cleanup_config['cleanup_level'],
                'custom_cleanup_prompt': cleanup_config.get('custom_cleanup_prompt')
            }
            
            # Set dummy transcription config for existing operations
            config['transcription'] = {
                'model': 'existing',
                'preprocessing': False
            }
            
            # Ensure transcript_dir is properly set for output directory calculation
            config['input']['transcript_dir'] = config['input'].get('transcript_dir')
            
        elif operation == 'translate':
            # Translation operation - need to get target language
            print(f"\n{Colors.CYAN}🌐 Translation Configuration{Colors.NC}")
            target_language = select_target_language()
            config['processing'] = {
                'diarization': False,
                'context_correction': False,
                'translation': True,
                'target_language': target_language,
            }
            
            # Set dummy transcription config for existing operations
            config['transcription'] = {
                'model': 'existing',
                'preprocessing': False
            }
            
            # Ensure transcript_dir is properly set for output directory calculation
            config['input']['transcript_dir'] = config['input'].get('transcript_dir')
            
        elif operation == 'custom':
            # Custom AI instructions operation
            print(f"\n{Colors.CYAN}🔧 Custom AI Instructions{Colors.NC}")
            custom_instructions = get_custom_ai_instructions()
            config['processing'] = {
                'diarization': False,
                'context_correction': True,  # Use context correction with custom instructions
                'translation': False,
                'target_language': None,
                'cleanup_level': 'custom',
                'custom_cleanup_prompt': custom_instructions
            }
            
            # Set dummy transcription config for existing operations
            config['transcription'] = {
                'model': 'existing',
                'preprocessing': False
            }
        
        config['format_options'] = {}
    else:
        # Step 3: Select transcription options
        config['transcription'] = select_transcription_options()
        
        # Step 4: Select processing options
        config['processing'] = select_processing_options(config['output_format'], api_keys)
        
        # Step 5: Select format-specific options
        config['format_options'] = select_format_specific_options(
            config['output_format'], 
            config['processing']['diarization']
        )
    
    # Step 6: Select output directory
    config['output_dir'] = select_output_directory(config)
    
    # Step 7: Execute pipeline
    success = run_pipeline(config)
    
    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Transcription pipeline completed successfully!{Colors.NC}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Pipeline failed. Check the output above for details.{Colors.NC}")
        sys.exit(1)

if __name__ == '__main__':
    main()
