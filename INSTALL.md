# Installation Guide - MMSplice/MTSplice on Ubuntu

This guide covers installation on Ubuntu/Debian systems using conda for running MMSplice predictions locally.

## System Requirements

- Ubuntu 20.04+ or Debian 11+
- Miniconda or Anaconda
- 8GB+ RAM (16GB recommended for large VCF files)
- ~5GB disk space for reference genomes

## Installation Steps

### 1. Install Miniconda (if not already installed)

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Run installer
bash Miniconda3-latest-Linux-x86_64.sh

# Follow prompts, then restart your shell or run:
source ~/.bashrc

# Verify installation
conda --version
```

### 2. Create Conda Environment

```bash
# Navigate to project directory
cd /path/to/MMSplice_MTSplice

# Create conda environment with Python 3.10 and basic packages
conda create -n mmsplice python=3.10 -y

# Activate environment
conda activate mmsplice
```

### 3. Install System Tools via Conda

```bash
# Install bioinformatics tools (samtools, tabix, etc.)
conda install -c bioconda -c conda-forge samtools htslib tabix -y

# Install build tools
conda install -c conda-forge gcc_linux-64 gxx_linux-64 make cmake -y
```

### 4. Install Python Packages in Correct Order

**CRITICAL:** Install packages in this specific order to avoid dependency conflicts:

```bash
# Ensure conda environment is activated
conda activate mmsplice

# Step 1: Install numpy 1.23.5 via conda (required for cyvcf2 binary compatibility)
conda install -c conda-forge numpy=1.23.5 -y

# Step 2: Install other scientific packages via conda
conda install -c conda-forge pandas scipy scikit-learn matplotlib seaborn pysam -y

# Step 3: Install TensorFlow 2.13.1 via pip (compatible with numpy 1.23.5)
pip install tensorflow==2.13.1

# Step 4: Install MMSplice (may try to upgrade tensorflow, we'll fix this next)
pip install mmsplice==2.4.0

# Step 5: Force downgrade back to compatible versions
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps

# Step 6: Install remaining dependencies
pip install cyvcf2==0.30.15 kipoiseq==0.7.1

# Step 7: Install API dependencies (optional - only if using Modal/FastAPI)
pip install fastapi[standard]==0.115.0 python-multipart pydantic==2.8.2 pyyaml==6.0.1 requests

# Step 8: Install Jupyter (optional)
conda install -c conda-forge jupyter ipython -y
```

## Alternative: One-Command Installation (Recommended)

You can use the provided `environment.yml` file for easier installation:

```bash
# Create environment from file
conda env create -f environment.yml

# Activate environment
conda activate mmsplice

# IMPORTANT: After conda installation, force correct versions
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps
```

This installs all dependencies automatically, but you still need to force the correct tensorflow and numpy versions at the end.

## Verify Installation

```bash
# Ensure environment is activated
conda activate mmsplice

# Test imports
python << 'EOF'
import numpy as np
import tensorflow as tf
from mmsplice import MMSplice
from mmsplice.vcf_dataloader import SplicingVCFDataloader
import cyvcf2

print(f"✓ numpy: {np.__version__}")
print(f"✓ tensorflow: {tf.__version__}")
print(f"✓ cyvcf2: {cyvcf2.__version__}")
print(f"✓ mmsplice: OK")
print("\n✅ All imports successful!")
EOF
```

Expected output:
```
✓ numpy: 1.23.5
✓ tensorflow: 2.13.1
✓ cyvcf2: 0.30.15
✓ mmsplice: OK

✅ All imports successful!
```

## Download Reference Genomes

```bash
# Ensure conda environment is activated
conda activate mmsplice

# Create reference data directory
mkdir -p reference_data
cd reference_data

# Download GRCh38 GTF (GENCODE v45)
wget -O GRCh38.gtf.gz https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip GRCh38.gtf.gz

# Download GRCh38 FASTA (Ensembl release 110)
wget -O GRCh38.fa.gz ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip GRCh38.fa.gz

# Index FASTA file (samtools installed via conda)
samtools faidx GRCh38.fa

cd ..
```

## Quick Test

Test with the DMD ASO design example:

```bash
# Activate conda environment
conda activate mmsplice

# Run prediction
python << 'EOF'
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

# Setup
gtf_file = "reference_data/GRCh38.gtf"
fasta_file = "reference_data/GRCh38.fa"
vcf_file = "examples/dmd_aso_design.vcf"

# Create dataloader
dl = SplicingVCFDataloader(gtf_file, fasta_file, vcf_file)

# Load model and predict
model = MMSplice()
predictions = predict_all_table(model, dl, pathogenicity=True, splicing_efficiency=True)

# Show results
print(f"\n✅ Predictions: {len(predictions)} variants")
print(predictions[['ID', 'delta_logit_psi', 'pathogenicity']].to_string())
EOF
```

## Troubleshooting

### Issue: `numpy.dtype size changed` error

**Cause:** Binary incompatibility between numpy and cyvcf2

**Fix:**
```bash
pip install numpy==1.23.5 --force-reinstall --no-deps
```

### Issue: `module 'numpy' has no attribute 'dtypes'`

**Cause:** TensorFlow 2.16+ requires numpy 1.26+, but cyvcf2 requires numpy 1.23.5

**Fix:**
```bash
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps
```

### Issue: Out of memory during prediction

**Fix:** Reduce batch size or process VCF in chunks
```python
# Process in smaller batches
dl = SplicingVCFDataloader(gtf_file, fasta_file, vcf_file, batch_size=32)
```

## Managing Your Conda Environment

```bash
# Activate environment
conda activate mmsplice

# Deactivate environment
conda deactivate

# List all packages in environment
conda list

# Update a specific package
conda update <package_name>

# Remove environment (if needed)
conda env remove -n mmsplice

# Export environment to share with others
conda env export > my_environment.yml
```

## Next Steps

- See [QUICK_START.md](docs/QUICK_START.md) for usage examples
- See [MMSplice_MTSplice_for_ASO_Design.md](docs/MMSplice_MTSplice_for_ASO_Design.md) for ASO design workflow
- Check [examples/](examples/) for VCF examples and prediction scripts
