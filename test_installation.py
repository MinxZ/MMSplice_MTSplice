#!/usr/bin/env python
"""
Test script to verify MMSplice installation
Run this after installation to ensure everything is working correctly.
"""

import sys

def test_imports():
    """Test all critical package imports"""
    print("="*80)
    print("Testing MMSplice Installation")
    print("="*80)

    all_ok = True

    # Test numpy
    print("\n1. Testing numpy...")
    try:
        import numpy as np
        print(f"   ✓ numpy version: {np.__version__}")

        if np.__version__ != "1.23.5":
            print(f"   ⚠ Warning: Expected numpy 1.23.5, got {np.__version__}")
            print("   This may cause cyvcf2 binary incompatibility issues")
            all_ok = False
    except ImportError as e:
        print(f"   ✗ numpy import failed: {e}")
        all_ok = False
        return False

    # Test tensorflow
    print("\n2. Testing tensorflow...")
    try:
        import tensorflow as tf
        print(f"   ✓ tensorflow version: {tf.__version__}")

        if not tf.__version__.startswith("2.13"):
            print(f"   ⚠ Warning: Expected tensorflow 2.13.x, got {tf.__version__}")
            print("   This may cause numpy compatibility issues")
            all_ok = False
    except ImportError as e:
        print(f"   ✗ tensorflow import failed: {e}")
        all_ok = False
        return False

    # Test cyvcf2
    print("\n3. Testing cyvcf2...")
    try:
        import cyvcf2
        print(f"   ✓ cyvcf2 version: {cyvcf2.__version__}")
    except ImportError as e:
        print(f"   ✗ cyvcf2 import failed: {e}")
        print("   Try: pip install cyvcf2==0.30.15")
        all_ok = False
        return False
    except ValueError as e:
        print(f"   ✗ cyvcf2 binary incompatibility: {e}")
        print("   Fix: pip install numpy==1.23.5 --force-reinstall --no-deps")
        all_ok = False
        return False

    # Test mmsplice
    print("\n4. Testing mmsplice...")
    try:
        from mmsplice import MMSplice
        print(f"   ✓ MMSplice imported")

        from mmsplice.vcf_dataloader import SplicingVCFDataloader
        print(f"   ✓ SplicingVCFDataloader imported")

        from mmsplice import predict_all_table
        print(f"   ✓ predict_all_table imported")

        import mmsplice
        print(f"   ✓ mmsplice version: {mmsplice.__version__}")
    except ImportError as e:
        print(f"   ✗ mmsplice import failed: {e}")
        print("   Try: pip install mmsplice==2.4.0")
        all_ok = False
        return False

    # Test additional packages
    print("\n5. Testing additional packages...")

    packages = [
        ('pandas', 'pandas'),
        ('pysam', 'pysam'),
        ('kipoiseq', 'kipoiseq'),
    ]

    for module_name, package_name in packages:
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"   ✓ {package_name}: {version}")
        except ImportError:
            print(f"   ⚠ {package_name} not installed (optional)")

    print("\n" + "="*80)
    if all_ok:
        print("✅ ALL TESTS PASSED! Your installation is ready.")
        print("\nNext steps:")
        print("1. Download reference genomes (see INSTALL.md)")
        print("2. Run predictions: python examples/predict_brca1.py")
        print("3. Read documentation: docs/QUICK_START.md")
    else:
        print("⚠ SOME TESTS FAILED! Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. pip install tensorflow==2.13.1 --force-reinstall")
        print("2. pip install numpy==1.23.5 --force-reinstall --no-deps")
        print("3. See INSTALL.md for detailed troubleshooting")
    print("="*80)

    return all_ok

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
