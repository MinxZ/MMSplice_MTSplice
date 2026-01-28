#!/bin/bash
# Fix common installation issues for MMSplice
# Usage: bash fix_installation.sh

set -e

echo "================================================================================"
echo "MMSplice Installation Fix Script"
echo "================================================================================"
echo ""

# Check if conda environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "mmsplice" ]]; then
    echo "⚠ Warning: conda environment 'mmsplice' is not activated"
    echo ""
    echo "Please activate the environment first:"
    echo "  conda activate mmsplice"
    echo ""
    read -p "Do you want me to try activating it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        eval "$(conda shell.bash hook)"
        conda activate mmsplice
    else
        exit 1
    fi
fi

echo "Conda environment: $CONDA_DEFAULT_ENV"
echo ""

# Function to check package
check_package() {
    local package=$1
    local expected_version=$2

    echo -n "Checking $package... "

    if python -c "import $package" 2>/dev/null; then
        version=$(python -c "import $package; print($package.__version__)" 2>/dev/null || echo "unknown")

        if [ -n "$expected_version" ] && [ "$version" != "$expected_version" ]; then
            echo "✗ found $version, expected $expected_version"
            return 1
        else
            echo "✓ $version"
            return 0
        fi
    else
        echo "✗ not installed"
        return 1
    fi
}

# Check current state
echo "Diagnosing installation..."
echo "----------------------------------------"

NEED_FIX=0

if ! check_package "numpy" "1.23.5"; then
    NEED_FIX=1
fi

if ! check_package "tensorflow" "2.13.1"; then
    NEED_FIX=1
fi

if ! check_package "cyvcf2"; then
    NEED_FIX=1
fi

if ! check_package "mmsplice"; then
    NEED_FIX=1
fi

echo ""

if [ $NEED_FIX -eq 0 ]; then
    echo "✅ All packages are correctly installed!"
    exit 0
fi

echo "⚠ Some packages need to be fixed"
echo ""
read -p "Do you want to fix the installation? (Y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo "================================================================================"
    echo "Fixing Installation"
    echo "================================================================================"
    echo ""

    # Fix 1: Install build dependencies
    echo "Step 1: Installing build dependencies..."
    pip install --upgrade setuptools wheel Cython "setuptools-scm>=6.2"

    # Fix 2: Install numpy first
    echo ""
    echo "Step 2: Installing numpy 1.23.5..."
    pip install numpy==1.23.5 --force-reinstall

    # Fix 3: Install tensorflow
    echo ""
    echo "Step 3: Installing tensorflow 2.13.1..."
    pip install tensorflow==2.13.1 --force-reinstall

    # Fix 4: Install sorted_nearest separately
    echo ""
    echo "Step 4: Installing sorted_nearest..."
    pip install sorted_nearest --no-build-isolation || pip install sorted_nearest==0.0.33

    # Fix 5: Install mmsplice
    echo ""
    echo "Step 5: Installing mmsplice..."
    pip install mmsplice==2.4.0

    # Fix 6: Force correct versions
    echo ""
    echo "Step 6: Forcing correct versions..."
    pip install tensorflow==2.13.1 --force-reinstall
    pip install numpy==1.23.5 --force-reinstall --no-deps

    # Fix 7: Install remaining dependencies
    echo ""
    echo "Step 7: Installing remaining dependencies..."
    pip install cyvcf2==0.30.15 kipoiseq==0.7.1

    # Verify fix
    echo ""
    echo "================================================================================"
    echo "Verifying Fix"
    echo "================================================================================"
    echo ""

    if python test_installation.py; then
        echo ""
        echo "================================================================================"
        echo "✅ Installation Fixed Successfully!"
        echo "================================================================================"
        echo ""
        echo "You can now run predictions:"
        echo "  python test_local_prediction.py"
        echo ""
    else
        echo ""
        echo "================================================================================"
        echo "⚠ Fix incomplete - please check errors above"
        echo "================================================================================"
        echo ""
        echo "For manual troubleshooting, see INSTALL.md"
        echo ""
        exit 1
    fi
else
    echo "Fix cancelled."
    exit 0
fi
