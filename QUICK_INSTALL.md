# Quick Installation Guide (Conda)

Quick start guide for setting up MMSplice/MTSplice using conda on Ubuntu/Debian.

## Prerequisites

- Ubuntu 20.04+ or Debian 11+
- Miniconda or Anaconda installed

## Installation (5 steps)

### 1. Create Conda Environment

```bash
cd /path/to/MMSplice_MTSplice
conda create -n mmsplice python=3.10 -y
conda activate mmsplice
```

### 2. Install System Tools

```bash
conda install -c bioconda -c conda-forge samtools htslib tabix -y
```

### 3. Install Python Packages

```bash
# Install numpy via conda
conda install -c conda-forge numpy=1.23.5 -y

# Install scientific packages
conda install -c conda-forge pandas scipy scikit-learn pysam -y

# Install TensorFlow via pip
pip install tensorflow==2.13.1

# Install MMSplice
pip install mmsplice==2.4.0

# Force correct versions (CRITICAL!)
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps

# Install remaining packages
pip install cyvcf2==0.30.15 kipoiseq==0.7.1
```

### 4. Verify Installation

```bash
python test_installation.py
```

Expected output:
```
✅ ALL TESTS PASSED! Your installation is ready.
```

### 5. Download Reference Genome

```bash
mkdir -p reference_data && cd reference_data

# Download GRCh38 GTF
wget -O GRCh38.gtf.gz https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip GRCh38.gtf.gz

# Download GRCh38 FASTA
wget -O GRCh38.fa.gz ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip GRCh38.fa.gz

# Index FASTA
samtools faidx GRCh38.fa

cd ..
```

## Test Run

```bash
conda activate mmsplice
python examples/predict_brca1.py
```

## Alternative: One-Command Install

```bash
# Create environment from file
conda env create -f environment.yml
conda activate mmsplice

# Force correct versions (IMPORTANT!)
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps

# Test installation
python test_installation.py
```

## Troubleshooting

### Error: `numpy.dtype size changed`
**Fix:**
```bash
pip install numpy==1.23.5 --force-reinstall --no-deps
```

### Error: `module 'numpy' has no attribute 'dtypes'`
**Fix:**
```bash
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps
```

### cyvcf2 import fails
**Fix:**
```bash
conda install -c conda-forge numpy=1.23.5 -y
pip install cyvcf2==0.30.15 --force-reinstall
```

## Why These Specific Versions?

- **numpy 1.23.5**: Required for cyvcf2 binary compatibility (96-byte dtype structure)
- **tensorflow 2.13.1**: Last version compatible with numpy 1.23.5
- **Python 3.10**: Optimal compatibility with all dependencies

## Next Steps

- Full documentation: [INSTALL.md](INSTALL.md)
- Quick start guide: [docs/QUICK_START.md](docs/QUICK_START.md)
- ASO design guide: [docs/MMSplice_MTSplice_for_ASO_Design.md](docs/MMSplice_MTSplice_for_ASO_Design.md)
