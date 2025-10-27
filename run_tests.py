#!/usr/bin/env python3
"""
Comprehensive test runner for Bricks Manager application.
Provides easy commands for running different test suites and generating coverage reports.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Bricks Manager Test Runner")
    parser.add_argument(
        'test_type', 
        choices=['all', 'unit', 'integration', 'models', 'services', 'routes', 'coverage', 'quick'],
        help='Type of tests to run'
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-coverage', action='store_true', help='Skip coverage reporting')
    parser.add_argument('--html', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--fail-fast', '-x', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add verbosity
    if args.verbose:
        cmd.append('-v')
    
    # Add fail-fast
    if args.fail_fast:
        cmd.append('-x')
    
    # Test type specific configuration
    if args.test_type == 'all':
        cmd.extend(['brick_manager/tests/'])
    elif args.test_type == 'unit':
        cmd.extend(['-m', 'unit', 'brick_manager/tests/'])
    elif args.test_type == 'integration':
        cmd.extend(['-m', 'integration', 'brick_manager/tests/'])
    elif args.test_type == 'models':
        cmd.extend(['brick_manager/tests/test_models.py'])
    elif args.test_type == 'services':
        cmd.extend([
            'brick_manager/tests/test_cache_service.py',
            'brick_manager/tests/test_part_lookup_service.py',
            'brick_manager/tests/test_brickognize_service.py',
            'brick_manager/tests/test_label_service.py',
            'brick_manager/tests/test_rebrickable_service.py'
        ])
    elif args.test_type == 'routes':
        cmd.extend([
            'brick_manager/tests/test_main_routes.py',
            'brick_manager/tests/test_routes.py'
        ])
    elif args.test_type == 'quick':
        cmd.extend(['-m', 'not slow', 'brick_manager/tests/'])
    elif args.test_type == 'coverage':
        # Just run coverage report without tests
        coverage_cmd = ['python', '-m', 'coverage', 'report']
        return run_command(coverage_cmd, "Coverage Report")
    
    # Add coverage if not disabled
    if not args.no_coverage and args.test_type != 'coverage':
        cmd.extend(['--cov=brick_manager', '--cov-report=term-missing'])
        
        if args.html:
            cmd.append('--cov-report=html')
    
    # Run the tests
    success = run_command(cmd, f"Running {args.test_type} tests")
    
    # Show coverage summary if HTML report was generated
    if args.html and success:
        html_path = Path("htmlcov/index.html").absolute()
        print(f"\n📊 Coverage report generated at: {html_path}")
        print("Open in browser to view detailed coverage information.")
    
    # Show next steps
    if success:
        print(f"\n🎉 Test run completed successfully!")
        print("\nNext steps:")
        print("  • View coverage report: python run_tests.py coverage")
        print("  • Run specific tests: python run_tests.py models")
        print("  • Generate HTML report: python run_tests.py all --html")
    else:
        print(f"\n❌ Test run failed!")
        print("\nTroubleshooting:")
        print("  • Check test logs above for specific errors")
        print("  • Run with --verbose for more details")
        print("  • Run individual test files to isolate issues")
        sys.exit(1)

if __name__ == "__main__":
    main()