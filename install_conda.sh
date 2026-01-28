#!/bin/bash
# Automated installation script for MMSplice/MTSplice using conda
# Usage: bash install_conda.sh

set -e  # Exit on error

echo "================================================================================"
echo "MMSplice/MTSplice Installation Script (Conda)"
echo "================================================================================"
echo ""

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "❌ Error: conda is not installed or not in PATH"
    echo ""
    echo "Please install Miniconda first:"
    echo "  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    echo "  bash Miniconda3-latest-Linux-x86_64.sh"
    echo ""
    exit 1
fi

echo "✓ Conda found: $(conda --version)"
echo ""

# Check if environment already exists
if conda env list | grep -q "^mmsplice "; then
    echo "⚠ Warning: conda environment 'mmsplice' already exists"
    read -p "Do you want to remove it and reinstall? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        conda env remove -n mmsplice -y
    else
        echo "Installation cancelled."
        exit 0
    fi
fi

# Create conda environment
echo "Step 1/7: Creating conda environment with Python 3.10..."
conda create -n mmsplice python=3.10 -y

# Initialize conda for bash (if needed)
eval "$(conda shell.bash hook)"

# Activate environment
echo ""
echo "Step 2/7: Activating environment..."
conda activate mmsplice

# Install system tools
echo ""
echo "Step 3/7: Installing bioinformatics tools (samtools, tabix)..."
conda install -c bioconda -c conda-forge samtools htslib tabix -y

# Install numpy via conda
echo ""
echo "Step 4/7: Installing numpy 1.23.5 via conda..."
conda install -c conda-forge numpy=1.23.5 -y

# Install scientific packages
echo ""
echo "Step 5/7: Installing scientific packages..."
conda install -c conda-forge pandas scipy scikit-learn pysam matplotlib seaborn -y

# Install build dependencies
echo ""
echo "Step 6/8: Installing build dependencies..."
pip install setuptools wheel Cython
pip install "setuptools-scm>=6.2"

# Install TensorFlow and MMSplice via pip
echo ""
echo "Step 7/8: Installing TensorFlow and MMSplice..."
pip install tensorflow==2.13.1

# Install sorted_nearest separately (fixes build issues)
echo "Installing sorted_nearest (MMSplice dependency)..."
pip install sorted_nearest --no-build-isolation || pip install sorted_nearest==0.0.33

# Install MMSplice
pip install mmsplice==2.4.0

# Force correct versions
echo ""
echo "Step 8/8: Forcing correct package versions (critical for compatibility)..."
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps

# Install remaining packages
pip install cyvcf2==0.30.15 kipoiseq==0.7.1 requests pyyaml==6.0.1

# Optional: Install Jupyter
read -p "Do you want to install Jupyter? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    conda install -c conda-forge jupyter ipython -y
    echo "✓ Jupyter installed"
fi

# Test installation
echo ""
echo "================================================================================"
echo "Testing Installation"
echo "================================================================================"
echo ""

if python test_installation.py; then
    echo ""
    echo "================================================================================"
    echo "✅ Installation Successful!"
    echo "================================================================================"
    echo ""
    echo "To activate the environment, run:"
    echo "  conda activate mmsplice"
    echo ""
    echo "Next steps:"
    echo "  1. Download reference genomes: see INSTALL.md"
    echo "  2. Run test predictions: python examples/predict_brca1.py"
    echo "  3. Read documentation: docs/QUICK_START.md"
    echo ""
else
    echo ""
    echo "================================================================================"
    echo "⚠ Installation completed with warnings"
    echo "================================================================================"
    echo ""
    echo "Please check the errors above and see INSTALL.md for troubleshooting."
    echo ""
fi

echo "To activate the environment in the future:"
echo "  conda activate mmsplice"
echo ""
