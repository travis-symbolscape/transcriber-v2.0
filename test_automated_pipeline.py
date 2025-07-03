#!/usr/bin/env python3
"""
Automated Pipeline Testing Script

Comprehensively tests all combinations of the transcription pipeline
without requiring user interaction.
"""

import os
import sys
import json
import subprocess
import argparse
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Optional, Tuple
import datetime

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

class TestLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        
        # Print to console
        if level == "ERROR":
            print(f"{Colors.RED}{log_entry}{Colors.NC}")
        elif level == "SUCCESS":
            print(f"{Colors.GREEN}{log_entry}{Colors.NC}")
        elif level == "WARNING":
            print(f"{Colors.YELLOW}{log_entry}{Colors.NC}")
        else:
            print(f"{Colors.CYAN}{log_entry}{Colors.NC}")
        
        # Write to file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def log_error(self, message: str):
        self.log(message, "ERROR")
    
    def log_success(self, message: str):
        self.log(message, "SUCCESS")
    
    def log_warning(self, message: str):
        self.log(message, "WARNING")

class AutomatedTester:
    def __init__(self, test_dir: str, logger: TestLogger):
        self.test_dir = Path(test_dir)
        self.logger = logger
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': [],
            'test_details': []
        }
        
        # Check API keys
        self.api_keys = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'HUGGINGFACE_TOKEN': os.getenv('HUGGINGFACE_TOKEN')
        }
        
        # Find video file
        self.video_file = self.find_video_file()
        
    def find_video_file(self) -> Optional[Path]:
        """Find the video file in the test directory"""
        media_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4a', '.wav', '.mp3', '.flac']
        
        for ext in media_extensions:
            files = list(self.test_dir.glob(f"*{ext}"))
            files.extend(list(self.test_dir.glob(f"*{ext.upper()}")))
            if files:
                return files[0]
        
        return None
    
    def generate_test_configs(self) -> List[Dict]:
        """Generate all test configurations"""
        configs = []
        
        # Base configuration matrix (reduced for quick testing)
        output_formats = ['json', 'markdown']  # Start with simplest
        models = ['tiny']  # Fastest model only
        preprocessing_options = [False]  # Skip preprocessing initially 
        diarization_options = [False]  # Skip diarization initially
        
        # Context correction and translation (only if API key available)
        context_options = [False]
        translation_options = [{'enabled': False, 'language': None}]
        
        if self.api_keys.get('OPENAI_API_KEY'):
            context_options.append(True)
            translation_options.extend([
                {'enabled': True, 'language': 'Spanish'},
                {'enabled': True, 'language': 'French'},
                {'enabled': True, 'language': 'German'}
            ])
        
        # Generate base combinations
        test_id = 0
        for output_format in output_formats:
            for model in models:
                for preprocessing in preprocessing_options:
                    for diarization in diarization_options:
                        for context in context_options:
                            for translation in translation_options:
                                # Skip context correction without API key
                                if context and not self.api_keys.get('OPENAI_API_KEY'):
                                    continue
                                
                                # Skip translation without API key
                                if translation['enabled'] and not self.api_keys.get('OPENAI_API_KEY'):
                                    continue
                                
                                test_id += 1
                                config = {
                                    'test_id': test_id,
                                    'output_format': output_format,
                                    'model': model,
                                    'preprocessing': preprocessing,
                                    'diarization': diarization,
                                    'context_correction': context,
                                    'translation': translation,
                                    'format_options': self.get_format_options(output_format, diarization)
                                }
                                
                                configs.append(config)
        
        return configs
    
    def get_format_options(self, output_format: str, has_diarization: bool) -> Dict:
        """Get format-specific options"""
        if output_format == 'markdown':
            return {
                'include_timecodes': True,
                'include_speakers': has_diarization,
                'title': f'Test Transcript {time.time():.0f}'
            }
        elif output_format == 'fcpxml':
            return {
                'project_name': f'Test Project {time.time():.0f}'
            }
        else:
            return {}
    
    def generate_output_dir_name(self, config: Dict) -> str:
        """Generate descriptive output directory name"""
        parts = [
            config['output_format'],
            config['model'],
            f"preproc-{'on' if config['preprocessing'] else 'off'}",
            f"diar-{'on' if config['diarization'] else 'off'}",
            f"context-{'on' if config['context_correction'] else 'off'}",
        ]
        
        if config['translation']['enabled']:
            parts.append(f"trans-{config['translation']['language'].lower()}")
        else:
            parts.append("trans-off")
        
        # Add format-specific options
        if config['output_format'] == 'markdown':
            opts = config['format_options']
            parts.append(f"time-{'on' if opts.get('include_timecodes') else 'off'}")
            parts.append(f"speak-{'on' if opts.get('include_speakers') else 'off'}")
        elif config['output_format'] == 'fcpxml':
            parts.append("projname-custom")
        
        return '_'.join(parts)
    
    def run_single_test(self, config: Dict) -> bool:
        """Run a single test configuration"""
        test_name = self.generate_output_dir_name(config)
        self.logger.log(f"Starting test {config['test_id']}: {test_name}")
        
        try:
            # Create output directory
            output_dir = self.test_dir / "test_outputs" / test_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create input directory with video file
            input_dir = output_dir / "input"
            input_dir.mkdir(exist_ok=True)
            
            # Copy video file to input directory
            import shutil
            video_copy = input_dir / self.video_file.name
            if not video_copy.exists():
                shutil.copy2(self.video_file, video_copy)
            
            # Step 1: Transcription
            self.logger.log(f"  Running transcription with {config['model']} model...")
            transcript_dir = output_dir / "transcripts"
            transcript_dir.mkdir(exist_ok=True)
            
            cmd = [
                "python", "scripts/transcribe.py",
                "--input-dir", str(input_dir),
                "--output-dir", str(transcript_dir),
                "--model", config['model']
            ]
            
            if config['preprocessing']:
                cmd.append("--preprocessing")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            current_transcript_dir = transcript_dir
            
            # Step 2: Context Correction (if enabled)
            if config['context_correction']:
                self.logger.log(f"  Running context correction...")
                corrected_dir = output_dir / "corrected_transcripts"
                corrected_dir.mkdir(exist_ok=True)
                
                cmd = [
                    "python", "scripts/context_correct_transcript.py",
                    "--input-dir", str(current_transcript_dir),
                    "--output-dir", str(corrected_dir),
                    "--api-key", self.api_keys['OPENAI_API_KEY']
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                current_transcript_dir = corrected_dir
            
            # Step 3: Translation (if enabled)
            if config['translation']['enabled']:
                self.logger.log(f"  Running translation to {config['translation']['language']}...")
                translated_dir = output_dir / "translated_transcripts"
                translated_dir.mkdir(exist_ok=True)
                
                cmd = [
                    "python", "scripts/translate_transcript.py",
                    "--transcript-dir", str(current_transcript_dir),
                    "--output-dir", str(translated_dir),
                    "--target-language", config['translation']['language'],
                    "--api-key", self.api_keys['OPENAI_API_KEY'],
                    "--skip-confirm"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                current_transcript_dir = translated_dir
            
            # Step 4: Diarization (if enabled)
            if config['diarization']:
                self.logger.log(f"  Running speaker diarization...")
                diarized_dir = output_dir / "diarized_transcripts"
                diarized_dir.mkdir(exist_ok=True)
                
                cmd = [
                    "python", "scripts/diarize_transcript.py",
                    "--input-dir", str(current_transcript_dir),
                    "--output-dir", str(diarized_dir)
                ]
                
                # Add HF token if available, otherwise use simple mode
                if self.api_keys.get('HUGGINGFACE_TOKEN'):
                    cmd.extend(["--hf-token", self.api_keys['HUGGINGFACE_TOKEN']])
                else:
                    cmd.append("--simple-only")
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                current_transcript_dir = diarized_dir
            
            # Step 5: Generate Final Output
            self.logger.log(f"  Generating {config['output_format']} output...")
            final_output_dir = output_dir / f"final_{config['output_format']}"
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
            
            if config['output_format'] != 'json':
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Verify output files were created
            output_files = list(final_output_dir.iterdir())
            if not output_files:
                raise Exception("No output files generated")
            
            self.logger.log_success(f"Test {config['test_id']} completed: {len(output_files)} files generated")
            
            # Store test details
            self.results['test_details'].append({
                'test_id': config['test_id'],
                'config': config,
                'output_dir': str(output_dir),
                'files_generated': len(output_files),
                'status': 'PASSED'
            })
            
            return True
            
        except Exception as e:
            error_msg = f"Test {config['test_id']} failed: {str(e)}"
            self.logger.log_error(error_msg)
            self.logger.log_error(f"Traceback: {traceback.format_exc()}")
            
            self.results['errors'].append({
                'test_id': config['test_id'],
                'config': config,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            
            # Store test details
            self.results['test_details'].append({
                'test_id': config['test_id'],
                'config': config,
                'output_dir': str(output_dir) if 'output_dir' in locals() else 'N/A',
                'files_generated': 0,
                'status': 'FAILED',
                'error': str(e)
            })
            
            return False
    
    def run_all_tests(self):
        """Run all test configurations"""
        if not self.video_file:
            self.logger.log_error("No video file found in test directory")
            return
        
        self.logger.log(f"Found video file: {self.video_file.name}")
        
        # Generate test configurations
        configs = self.generate_test_configs()
        self.results['total_tests'] = len(configs)
        
        self.logger.log(f"Generated {len(configs)} test configurations")
        
        # API key status
        if self.api_keys.get('OPENAI_API_KEY'):
            self.logger.log("OpenAI API key found - testing advanced features")
        else:
            self.logger.log_warning("OpenAI API key not found - skipping context correction and translation")
        
        if self.api_keys.get('HUGGINGFACE_TOKEN'):
            self.logger.log("HuggingFace token found - testing advanced diarization")
        else:
            self.logger.log_warning("HuggingFace token not found - using simple diarization")
        
        # Run tests
        start_time = time.time()
        for i, config in enumerate(configs, 1):
            self.logger.log(f"\n{'='*60}")
            self.logger.log(f"TEST {i}/{len(configs)} - Progress: {i/len(configs)*100:.1f}%")
            
            if self.run_single_test(config):
                self.results['passed'] += 1
            else:
                self.results['failed'] += 1
            
            # Progress estimate
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(configs) - i) * avg_time
            self.logger.log(f"Elapsed: {elapsed/60:.1f}m, Estimated remaining: {remaining/60:.1f}m")
        
        # Generate final report
        self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        self.logger.log(f"\n{'='*60}")
        self.logger.log("FINAL TEST REPORT")
        self.logger.log(f"{'='*60}")
        
        self.logger.log(f"Total tests: {self.results['total_tests']}")
        self.logger.log_success(f"Passed: {self.results['passed']}")
        if self.results['failed'] > 0:
            self.logger.log_error(f"Failed: {self.results['failed']}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100
        self.logger.log(f"Success rate: {success_rate:.1f}%")
        
        # Save detailed report
        report_file = self.test_dir / "test_outputs" / "test_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.log(f"Detailed report saved to: {report_file}")
        
        if self.results['failed'] > 0:
            self.logger.log("\nFAILED TESTS:")
            for error in self.results['errors']:
                self.logger.log_error(f"Test {error['test_id']}: {error['error']}")

def main():
    parser = argparse.ArgumentParser(description="Automated pipeline testing")
    parser.add_argument('--test-dir', required=True, help='Test directory path')
    args = parser.parse_args()
    
    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        print(f"Error: Test directory does not exist: {test_dir}")
        sys.exit(1)
    
    # Set up logging
    log_file = test_dir / "test_outputs" / "test_log.txt"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear previous log
    if log_file.exists():
        log_file.unlink()
    
    logger = TestLogger(str(log_file))
    logger.log("Starting automated pipeline testing")
    logger.log(f"Test directory: {test_dir}")
    
    # Run tests
    tester = AutomatedTester(str(test_dir), logger)
    tester.run_all_tests()

if __name__ == '__main__':
    main()
