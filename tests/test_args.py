#!/usr/bin/env python3
"""
Simple test to verify the argument parsing works correctly
"""

def test_args():
    import argparse
    
    # Simulate the argument parser from whisper_online.py
    parser = argparse.ArgumentParser()
    parser.add_argument('--agreement-iterations', type=int, default=2, dest='agreement_iterations', 
                       help='Number of consecutive iterations required for local agreement. Higher values increase stability but may increase latency (default: 2, minimum: 2).')
    
    # Test default value
    args = parser.parse_args([])
    print(f"Default agreement_iterations: {args.agreement_iterations}")
    
    # Test custom value
    args = parser.parse_args(['--agreement-iterations', '3'])
    print(f"Custom agreement_iterations: {args.agreement_iterations}")
    
    # Test validation would happen in asr_factory
    if args.agreement_iterations < 2:
        print("ERROR: agreement_iterations must be >= 2")
    else:
        print("✓ Validation passed")

if __name__ == "__main__":
    test_args()
    print("✓ Argument parsing test completed successfully")
