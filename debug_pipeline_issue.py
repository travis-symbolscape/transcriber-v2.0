#!/usr/bin/env python3
"""
Debug script to reproduce the specific pipeline issue:
- Starting from existing transcripts
- Running cleanup operations
- Requesting FCPXML final output
- Only produces cleaned JSON files instead of progressing to final output

This script will:
1. Create a minimal test environment
2. Generate sample transcript data
3. Run the problematic pipeline configuration
4. Analyze where the pipeline stops and why
"""

import os
import sys
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import logging

# Setup logging for detailed debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_sample_transcript(output_path: str) -> None:
    """Create a sample transcript JSON file for testing."""
    sample_segments = [
        {
            "id": 0,
            "seek": 0,
            "start": 0.0,
            "end": 3.5,
            "text": " Hello, this is a test transcript for debugging the pipeline.",
            "tokens": [50364, 2425, 11, 341, 307, 257, 1500, 24444, 329, 27428, 262, 11523, 13, 50540],
            "temperature": 0.0,
            "avg_logprob": -0.34567,
            "compression_ratio": 1.234,
            "no_speech_prob": 0.001
        },
        {
            "id": 1,
            "seek": 3500,
            "start": 3.5,
            "end": 7.2,
            "text": " We need to make sure all stages execute properly.",
            "tokens": [50540, 775, 761, 284, 787, 1654, 477, 9539, 12260, 6105, 13, 50722],
            "temperature": 0.0,
            "avg_logprob": -0.45678,
            "compression_ratio": 1.345,
            "no_speech_prob": 0.002
        },
        {
            "id": 2,
            "seek": 7200,
            "start": 7.2,
            "end": 11.8,
            "text": " Including the final output generation for FCPXML format.",
            "tokens": [50722, 9061, 262, 2457, 5072, 5270, 329, 376, 8697, 55, 10970, 5794, 13, 50952],
            "temperature": 0.0,
            "avg_logprob": -0.23456,
            "compression_ratio": 1.456,
            "no_speech_prob": 0.001
        }
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_segments, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Created sample transcript: {output_path}")

def create_test_environment(base_dir: Path) -> Dict[str, Path]:
    """Create a test environment with necessary directories and files."""
    test_dirs = {
        'input': base_dir / 'input',
        'existing_transcripts': base_dir / 'existing_transcripts',
        'output': base_dir / 'output',
        'cleaned_transcripts': base_dir / 'cleaned_transcripts',
        'final_fcpxml': base_dir / 'final_fcpxml'
    }
    
    # Create directories
    for dir_path in test_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    # Create sample transcript in existing_transcripts
    transcript_file = test_dirs['existing_transcripts'] / 'test_sample.json'
    create_sample_transcript(str(transcript_file))
    
    return test_dirs

def run_pipeline_stage(script_name: str, args: List[str], stage_name: str) -> bool:
    """Run a specific pipeline stage and log results."""
    cmd = ['python', f'scripts/{script_name}'] + args
    logger.info(f"Running {stage_name}: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=Path.cwd(),
            check=False
        )
        
        logger.info(f"{stage_name} - Return code: {result.returncode}")
        
        if result.stdout:
            logger.info(f"{stage_name} - STDOUT:\n{result.stdout}")
        
        if result.stderr:
            logger.warning(f"{stage_name} - STDERR:\n{result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"{stage_name} failed with return code {result.returncode}")
            return False
        
        logger.info(f"{stage_name} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Exception running {stage_name}: {e}")
        return False

def check_output_files(directory: Path, expected_extension: str) -> List[Path]:
    """Check what files were actually created in a directory."""
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = list(directory.glob(f"*{expected_extension}"))
    logger.info(f"Found {len(files)} {expected_extension} files in {directory}")
    
    for file in files:
        logger.info(f"  - {file.name} ({file.stat().st_size} bytes)")
    
    return files

def test_problematic_pipeline() -> bool:
    """Test the specific problematic pipeline configuration."""
    logger.info("Starting problematic pipeline test")
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory(prefix='pipeline_debug_') as temp_dir:
        temp_path = Path(temp_dir)
        logger.info(f"Using temporary directory: {temp_path}")
        
        # Setup test environment
        test_dirs = create_test_environment(temp_path)
        
        # Verify initial state
        initial_transcripts = check_output_files(test_dirs['existing_transcripts'], '.json')
        if not initial_transcripts:
            logger.error("No initial transcripts found - test setup failed")
            return False
        
        success = True
        
        # Stage 1: Context correction (cleanup) - this should work
        logger.info("\n=== STAGE 1: Context Correction (Cleanup) ===")
        
        # We need to mock an API key for this test
        os.environ['OPENAI_API_KEY'] = 'test-key-for-debugging'
        
        cleanup_args = [
            '--input-dir', str(test_dirs['existing_transcripts']),
            '--output-dir', str(test_dirs['cleaned_transcripts']),
            '--api-key', 'test-key-for-debugging',
            '--cleanup-level', 'standard'
        ]
        
        # Since we don't have a real API key, let's copy files to simulate cleanup
        logger.info("Simulating cleanup stage (copying files)")
        for transcript in initial_transcripts:
            cleaned_path = test_dirs['cleaned_transcripts'] / transcript.name
            shutil.copy2(transcript, cleaned_path)
            logger.info(f"Simulated cleanup: {transcript.name} -> {cleaned_path}")
        
        # Check cleanup results
        cleaned_files = check_output_files(test_dirs['cleaned_transcripts'], '.json')
        if not cleaned_files:
            logger.error("Cleanup stage produced no output files")
            success = False
        
        # Stage 2: FCPXML generation - this is where the issue likely occurs
        logger.info("\n=== STAGE 2: FCPXML Generation ===")
        
        fcpxml_args = [
            '--input-dir', str(test_dirs['cleaned_transcripts']),
            '--output-dir', str(test_dirs['final_fcpxml'])
        ]
        
        fcpxml_success = run_pipeline_stage(
            'generate_fcpxml.py', 
            fcpxml_args,
            'FCPXML Generation'
        )
        
        if not fcpxml_success:
            logger.error("FCPXML generation stage failed")
            success = False
        
        # Check final output
        fcpxml_files = check_output_files(test_dirs['final_fcpxml'], '.fcpxml')
        if not fcpxml_files:
            logger.error("FCPXML generation produced no output files")
            success = False
        
        # Analysis: Check what actually happened
        logger.info("\n=== ANALYSIS ===")
        
        # Check if cleaned transcripts exist (should exist)
        logger.info(f"Cleaned transcripts directory: {test_dirs['cleaned_transcripts']}")
        cleaned_count = len(check_output_files(test_dirs['cleaned_transcripts'], '.json'))
        logger.info(f"Cleaned JSON files: {cleaned_count}")
        
        # Check if final FCPXML files exist (this is what fails)
        logger.info(f"Final FCPXML directory: {test_dirs['final_fcpxml']}")
        fcpxml_count = len(check_output_files(test_dirs['final_fcpxml'], '.fcpxml'))
        logger.info(f"Final FCPXML files: {fcpxml_count}")
        
        if cleaned_count > 0 and fcpxml_count == 0:
            logger.error("CONFIRMED ISSUE: Pipeline stops after cleanup, doesn't generate final output")
            
            # Try to understand why FCPXML generation failed
            logger.info("Investigating FCPXML generation failure...")
            
            # Check if the script exists
            fcpxml_script = Path('scripts/generate_fcpxml.py')
            if not fcpxml_script.exists():
                logger.error(f"FCPXML script not found: {fcpxml_script}")
            else:
                logger.info(f"FCPXML script exists: {fcpxml_script}")
                
                # Try running with verbose output
                test_cmd = [
                    'python', str(fcpxml_script), '--help'
                ]
                try:
                    help_result = subprocess.run(test_cmd, capture_output=True, text=True)
                    logger.info(f"FCPXML script help output:\n{help_result.stdout}")
                    if help_result.stderr:
                        logger.warning(f"FCPXML script help stderr:\n{help_result.stderr}")
                except Exception as e:
                    logger.error(f"Failed to get help from FCPXML script: {e}")
        
        elif cleaned_count > 0 and fcpxml_count > 0:
            logger.info("Pipeline appears to work correctly")
        
        else:
            logger.error("Pipeline failed at cleanup stage")
        
        return success

def test_pipeline_orchestrator_logic():
    """Test the main pipeline orchestrator logic to identify issues."""
    logger.info("\n=== Testing Pipeline Orchestrator Logic ===")
    
    # Check if the main orchestrator exists
    main_script = Path('run_transcription_pipeline_v2.py')
    if not main_script.exists():
        logger.error(f"Main pipeline script not found: {main_script}")
        return False
    
    logger.info(f"Main pipeline script found: {main_script}")
    
    # Try to understand the flow by examining the key parts
    try:
        with open(main_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for specific patterns that might cause issues
        patterns_to_check = [
            "generate_fcpxml.py",
            "final_output_dir",
            "subprocess.run(cmd, check=True)",
            "config['output_format'] == 'fcpxml'",
            "current_transcript_dir"
        ]
        
        for pattern in patterns_to_check:
            if pattern in content:
                logger.info(f"Found pattern in orchestrator: {pattern}")
            else:
                logger.warning(f"Pattern NOT found in orchestrator: {pattern}")
        
        # Count lines to understand script size
        lines = content.split('\n')
        logger.info(f"Main script has {len(lines)} lines")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to analyze main script: {e}")
        return False

def main():
    """Main debug function."""
    logger.info("=== Starting Pipeline Debug Session ===")
    logger.info(f"Working directory: {Path.cwd()}")
    logger.info(f"Python executable: {sys.executable}")
    
    # Check if we're in the right directory
    required_files = [
        'scripts/generate_fcpxml.py',
        'scripts/context_correct_transcript.py',
        'run_transcription_pipeline_v2.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        logger.error("Make sure you're running this from the transcriber-v2.0 root directory")
        return False
    
    logger.info("All required files found")
    
    # Test 1: Reproduce the problematic pipeline
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Reproducing Problematic Pipeline")
    logger.info("="*60)
    
    test1_success = test_problematic_pipeline()
    
    # Test 2: Analyze orchestrator logic
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Analyzing Orchestrator Logic")  
    logger.info("="*60)
    
    test2_success = test_pipeline_orchestrator_logic()
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("DEBUG SESSION SUMMARY")
    logger.info("="*60)
    
    logger.info(f"Test 1 (Pipeline Reproduction): {'PASS' if test1_success else 'FAIL'}")
    logger.info(f"Test 2 (Orchestrator Analysis): {'PASS' if test2_success else 'FAIL'}")
    
    if not test1_success:
        logger.error("The pipeline issue has been reproduced.")
        logger.info("Next steps:")
        logger.info("1. Check the main orchestrator's stage execution logic")
        logger.info("2. Verify that the final output generation is actually called")
        logger.info("3. Add debug logging to the orchestrator")
        logger.info("4. Check for early termination conditions")
    
    logger.info("Debug session complete. Check debug_pipeline.log for full details.")
    
    return test1_success and test2_success

if __name__ == '__main__':
    main()
