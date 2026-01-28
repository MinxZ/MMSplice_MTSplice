# Complete Setup Guide - MMSplice/MTSplice

Quick reference guide for setting up and testing MMSplice/MTSplice on Ubuntu with conda.

## 🚀 Quick Start (4 Commands)

```bash
# 1. Install environment
bash install_conda.sh

# 2. Activate environment
conda activate mmsplice

# 3. Download reference genome
bash download_references.sh GRCh38

# 4. Test predictions
python test_local_prediction.py
```

That's it! You're ready to run predictions.

## 📋 Step-by-Step Guide

### Step 1: Install MMSplice Environment

Choose one method:

**Option A: Automated Installation (Recommended)**
```bash
bash install_conda.sh
```

**Option B: Manual Installation**
```bash
# Create environment
conda create -n mmsplice python=3.10 -y
conda activate mmsplice

# Install packages
conda install -c bioconda -c conda-forge samtools htslib tabix -y
conda install -c conda-forge numpy=1.23.5 pandas scipy scikit-learn pysam -y
pip install tensorflow==2.13.1
pip install mmsplice==2.4.0

# Force correct versions (CRITICAL!)
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps
pip install cyvcf2==0.30.15 kipoiseq==0.7.1
```

**Option C: From environment.yml**
```bash
conda env create -f environment.yml
conda activate mmsplice
pip install tensorflow==2.13.1 --force-reinstall
pip install numpy==1.23.5 --force-reinstall --no-deps
```

### Step 2: Verify Installation

```bash
conda activate mmsplice
python test_installation.py
```

Expected output:
```
✅ ALL TESTS PASSED! Your installation is ready.
```

### Step 3: Download Reference Genome

```bash
# Download GRCh38 (human, default)
bash download_references.sh GRCh38

# Or download GRCh37 (human, hg19)
bash download_references.sh GRCh37

# Or download GRCm39 (mouse)
bash download_references.sh GRCm39
```

This will:
- Download GTF annotation file (~50-100 MB compressed, 1-2 GB uncompressed)
- Download FASTA genome file (~800 MB compressed, 3-4 GB uncompressed)
- Create FASTA index (.fai file)
- Store everything in `reference_data/` directory

**Note:** Downloads can take 5-30 minutes depending on your internet speed.

### Step 4: Test Local Predictions

```bash
python test_local_prediction.py
```

This will:
- Verify reference files exist
- Load the DMD ASO design VCF (6 variants)
- Run MMSplice predictions
- Display results with ASO design interpretation
- Save results to `examples/dmd_predictions_local.json`

## 📁 Project Structure

```
MMSplice_MTSplice/
├── install_conda.sh              # Automated installation script
├── download_references.sh        # Download reference genomes
├── test_installation.py          # Verify installation
├── test_local_prediction.py      # Test local predictions
├── environment.yml               # Conda environment definition
├── requirements.txt              # Pip requirements
├── INSTALL.md                    # Detailed installation guide
├── QUICK_INSTALL.md             # Quick installation reference
├── README_SETUP.md              # This file
│
├── reference_data/              # Reference genomes (created by download script)
│   ├── GRCh38.gtf              # Human genome annotation
│   ├── GRCh38.fa               # Human genome sequence
│   └── GRCh38.fa.fai           # FASTA index
│
├── examples/                    # Example VCF files and results
│   ├── dmd_aso_design.vcf      # DMD exon 51 ASO design (6 variants)
│   ├── dmd_predictions_local.json   # Local prediction results
│   └── test_modal_api.py       # Test Modal API endpoint
│
├── docs/                        # Documentation
│   ├── QUICK_START.md
│   ├── MMSplice_MTSplice_for_ASO_Design.md
│   ├── Creating_VCF_for_ASO_Design.md
│   └── Input_Files_Checklist.md
│
└── deployment/                  # Modal serverless deployment
    ├── modal_app_v2.py         # Modal API with fixed dependencies
    └── test_imports_modal.py   # Test Modal imports
```

## 🧪 Testing Your Installation

### Test 1: Installation Verification
```bash
conda activate mmsplice
python test_installation.py
```

Should show:
- ✓ numpy 1.23.5
- ✓ tensorflow 2.13.1
- ✓ cyvcf2 0.30.15
- ✓ mmsplice 2.4.0

### Test 2: Local Predictions
```bash
python test_local_prediction.py
```

Should produce:
- Predictions for 6 DMD variants
- ASO design interpretation
- JSON and CSV output files

### Test 3: Custom VCF
```bash
python test_local_prediction.py path/to/your.vcf output.json
```

## 🔧 Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `install_conda.sh` | Install conda environment | `bash install_conda.sh` |
| `download_references.sh` | Download genome files | `bash download_references.sh GRCh38` |
| `test_installation.py` | Verify installation | `python test_installation.py` |
| `test_local_prediction.py` | Run predictions | `python test_local_prediction.py [vcf] [output]` |
| `test_modal_api.py` | Test Modal API | `python examples/test_modal_api.py` |

## 💡 Common Workflows

### Workflow 1: ASO Design for New Gene/Exon
```bash
# 1. Create VCF with candidate variants (see docs/Creating_VCF_for_ASO_Design.md)
# 2. Run predictions
python test_local_prediction.py my_aso_design.vcf results.json

# 3. Review results
cat results.json
# Look for variants with delta_logit_psi < -2 (strong skipping)
```

### Workflow 2: Batch Processing Multiple VCFs
```bash
conda activate mmsplice

for vcf in vcf_files/*.vcf; do
    output="results/$(basename $vcf .vcf)_predictions.json"
    python test_local_prediction.py "$vcf" "$output"
done
```

### Workflow 3: Compare Local vs Modal API
```bash
# Run local prediction
python test_local_prediction.py examples/dmd_aso_design.vcf local_results.json

# Run Modal API prediction
cd examples
python test_modal_api.py
cd ..

# Compare results
diff local_results.json examples/dmd_predictions.json
```

## ⚙️ Environment Management

```bash
# Activate environment
conda activate mmsplice

# Deactivate environment
conda deactivate

# List installed packages
conda list

# Update a package
conda update numpy

# Export environment
conda env export > my_environment.yml

# Remove environment
conda env remove -n mmsplice
```

## 🐛 Troubleshooting

### Issue: Installation test fails

**Check numpy version:**
```bash
conda activate mmsplice
python -c "import numpy; print(numpy.__version__)"
```

Should be `1.23.5`. If not:
```bash
pip install numpy==1.23.5 --force-reinstall --no-deps
```

### Issue: Reference download fails

**Manual download:**
```bash
cd reference_data

# GTF
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip gencode.v45.annotation.gtf.gz
mv gencode.v45.annotation.gtf GRCh38.gtf

# FASTA
wget ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
mv Homo_sapiens.GRCh38.dna.primary_assembly.fa GRCh38.fa

# Index
samtools faidx GRCh38.fa
```

### Issue: Predictions fail with "Out of Memory"

**Reduce memory usage:**
```python
# Edit test_local_prediction.py, change dataloader:
dl = SplicingVCFDataloader(
    gtf_file, fasta_file, vcf_file,
    tissue_specific=False,
    batch_size=32  # Add this line
)
```

### Issue: cyvcf2 import error

**Reinstall cyvcf2:**
```bash
conda activate mmsplice
pip uninstall cyvcf2 -y
pip install cyvcf2==0.30.15
```

## 📚 Documentation

- **Installation**: [INSTALL.md](INSTALL.md) - Detailed installation guide
- **Quick Start**: [QUICK_INSTALL.md](QUICK_INSTALL.md) - Quick reference
- **ASO Design**: [docs/MMSplice_MTSplice_for_ASO_Design.md](docs/MMSplice_MTSplice_for_ASO_Design.md)
- **VCF Creation**: [docs/Creating_VCF_for_ASO_Design.md](docs/Creating_VCF_for_ASO_Design.md)
- **API Guide**: [deployment/README.md](deployment/) - Modal serverless deployment

## 🆘 Getting Help

1. Check troubleshooting section above
2. Review [INSTALL.md](INSTALL.md) for detailed instructions
3. Run `python test_installation.py` to diagnose issues
4. Check that reference files are downloaded: `ls -lh reference_data/`

## ✅ Next Steps After Setup

Once everything is working:

1. **Read ASO Design Guide**: [docs/MMSplice_MTSplice_for_ASO_Design.md](docs/MMSplice_MTSplice_for_ASO_Design.md)
2. **Create Your VCF**: [docs/Creating_VCF_for_ASO_Design.md](docs/Creating_VCF_for_ASO_Design.md)
3. **Run Predictions**: `python test_local_prediction.py your.vcf results.json`
4. **Analyze Results**: Look for variants with strong skipping effects (Δlogit(Ψ) < -2)
5. **Deploy to Cloud** (optional): See [deployment/modal_app_v2.py](deployment/modal_app_v2.py)

Happy splicing! 🧬
