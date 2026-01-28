#!/usr/bin/env python3
"""Test that all MMSplice imports work correctly"""

import sys

print("=" * 60)
print("Testing MMSplice Installation - Import Verification")
print("=" * 60)
print()

# Test core MMSplice imports
print("Testing MMSplice core imports...")
try:
    from mmsplice import MMSplice
    print("✓ MMSplice imported successfully")
except ImportError as e:
    print(f"✗ Failed to import MMSplice: {e}")
    sys.exit(1)

try:
    from mmsplice.vcf_dataloader import SplicingVCFDataloader
    print("✓ SplicingVCFDataloader imported successfully")
except ImportError as e:
    print(f"✗ Failed to import SplicingVCFDataloader: {e}")
    sys.exit(1)

try:
    from mmsplice import predict_all_table
    print("✓ predict_all_table imported successfully")
except ImportError as e:
    print(f"✗ Failed to import predict_all_table: {e}")
    sys.exit(1)

print()

# Test dependencies
print("Testing key dependencies...")
try:
    import tensorflow as tf
    print(f"✓ TensorFlow {tf.__version__} imported successfully")
except ImportError as e:
    print(f"✗ Failed to import TensorFlow: {e}")
    sys.exit(1)

try:
    import pandas as pd
    print(f"✓ Pandas {pd.__version__} imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Pandas: {e}")
    sys.exit(1)

try:
    import cyvcf2
    print(f"✓ cyvcf2 {cyvcf2.__version__} imported successfully")
except ImportError as e:
    print(f"✗ Failed to import cyvcf2: {e}")
    sys.exit(1)

try:
    import kipoiseq
    print(f"✓ kipoiseq imported successfully")
except ImportError as e:
    print(f"✗ Failed to import kipoiseq: {e}")
    sys.exit(1)

try:
    import pyfaidx
    print(f"✓ pyfaidx imported successfully")
except ImportError as e:
    print(f"✗ Failed to import pyfaidx: {e}")
    sys.exit(1)

try:
    import pyranges
    print(f"✓ pyranges imported successfully")
except ImportError as e:
    print(f"✗ Failed to import pyranges: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✅ SUCCESS - All imports completed successfully!")
print("=" * 60)
print()
print("MMSplice is installed and ready to use.")
print()
