"""
Test Runner for Health Monitoring System
"""
import unittest
import sys
import os


def run_all_tests():
    """Run all test suites"""
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')

    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)

    # Return success/failure
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 60)
    print("Running Health Monitoring System Tests")
    print("=" * 60)

    # Run tests
    success = run_all_tests()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)