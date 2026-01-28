"""
Test imports to diagnose numpy/cyvcf2 issue in Modal
"""
import modal

app = modal.App("test-imports")

# Use same image as modal_app_v2.py
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install(
        "wget", "curl", "git", "build-essential",
        "zlib1g-dev", "libbz2-dev", "liblzma-dev",
        "libcurl4-openssl-dev", "libssl-dev",
        "samtools", "tabix",
    )
    .pip_install("numpy==1.23.5")
    .pip_install(
        "fastapi[standard]==0.115.0",
        "python-multipart",
        "pydantic==2.8.2",
        "pyyaml==6.0.1",
        "mmsplice==2.4.0",
    )
    .run_commands(
        "pip install tensorflow==2.13.1 --force-reinstall",
        "pip install numpy==1.23.5 --force-reinstall --no-deps"
    )
)

@app.function(image=image)
def test_imports():
    """Test all critical imports"""
    import sys
    import subprocess

    print("="*80)
    print("DIAGNOSTIC TEST - Import Check")
    print("="*80)

    # Check installed packages
    print("\n0. Checking installed package versions...")
    result = subprocess.run(['pip', 'list', '--format=freeze'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if any(pkg in line.lower() for pkg in ['numpy', 'tensorflow', 'mmsplice', 'cyvcf2']):
            print(f"   {line}")
    print()

    # Test numpy version
    print("\n1. Testing numpy...")
    try:
        import numpy as np
        print(f"   ✓ numpy version: {np.__version__}")
        print(f"   ✓ numpy.dtype size: {np.dtype('float64').itemsize}")

        # Check dtype structure size (the critical part for cyvcf2)
        import numpy
        dt = numpy.dtype('float64')
        print(f"   ✓ dtype object size: {sys.getsizeof(dt)} bytes")
    except Exception as e:
        print(f"   ✗ numpy import failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test cyvcf2 import
    print("\n2. Testing cyvcf2...")
    try:
        from cyvcf2 import VCF
        print(f"   ✓ cyvcf2 imported successfully")

        import cyvcf2
        print(f"   ✓ cyvcf2 version: {cyvcf2.__version__}")
    except Exception as e:
        print(f"   ✗ cyvcf2 import failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Check tensorflow version before importing mmsplice
    print("\n3. Checking tensorflow version...")
    try:
        import tensorflow as tf
        print(f"   ✓ tensorflow version: {tf.__version__}")
    except Exception as e:
        print(f"   ✗ tensorflow import failed: {e}")
        import traceback
        traceback.print_exc()

    # Test mmsplice imports
    print("\n4. Testing mmsplice...")
    try:
        from mmsplice import MMSplice
        print(f"   ✓ MMSplice imported")

        from mmsplice.vcf_dataloader import SplicingVCFDataloader
        print(f"   ✓ SplicingVCFDataloader imported")

        from mmsplice import predict_all_table
        print(f"   ✓ predict_all_table imported")
    except Exception as e:
        print(f"   ✗ mmsplice import failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test tensorflow
    print("\n4. Testing tensorflow...")
    try:
        import tensorflow as tf
        print(f"   ✓ tensorflow version: {tf.__version__}")
    except Exception as e:
        print(f"   ✗ tensorflow import failed: {e}")

    print("\n" + "="*80)
    print("✅ ALL IMPORTS SUCCESSFUL!")
    print("="*80)


@app.local_entrypoint()
def main():
    """Run the import test"""
    test_imports.remote()
