# MMSplice/MTSplice Input Files Checklist

## ✅ Minimum Required Files (You Must Have)

Check that you have these 3 files before running MMSplice:

### 1. VCF File (Variants)
- [ ] I have a VCF file with my variants/ASO designs
- [ ] File is compressed with bgzip: `*.vcf.gz`
- [ ] File is indexed with tabix: `*.vcf.gz.tbi`
- [ ] VCF is left-normalized and multi-allelic sites are split

**Location:** `_____________________________`

**How to check:**
```bash
# View first few variants
gunzip -c my_variants.vcf.gz | grep -v "^##" | head -5

# Should show proper VCF format with CHROM, POS, REF, ALT columns
```

---

### 2. GTF File (Gene Annotations)
- [ ] I have a GTF file (GENCODE or Ensembl)
- [ ] GTF matches my genome version (GRCh37 vs GRCh38)
- [ ] File is uncompressed (`.gtf`, not `.gtf.gz`)

**Location:** `_____________________________`

**How to check:**
```bash
# View first few lines
head -5 my_annotations.gtf

# Should show format: CHROM SOURCE FEATURE START END SCORE STRAND FRAME ATTRIBUTES
```

**Download if needed:**
```bash
# GRCh38 (latest)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip gencode.v45.annotation.gtf.gz

# GRCh37 (older)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gtf.gz
gunzip gencode.v19.annotation.gtf.gz
```

---

### 3. FASTA File (Reference Genome)
- [ ] I have a FASTA file (reference genome)
- [ ] FASTA matches my GTF genome version (both GRCh37 or both GRCh38)
- [ ] File is uncompressed (`.fa` or `.fasta`, not `.fa.gz`)

**Location:** `_____________________________`

**How to check:**
```bash
# View first few lines
head -5 my_genome.fa

# Should show:
# >1
# NNNNN...ATCG...

# Or:
# >chr1
# NNNNN...ATCG...
```

**Download if needed:**
```bash
# GRCh38
wget ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz

# GRCh37
wget ftp://ftp.ensembl.org/pub/grch37/current/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
```

---

## ⚙️ Automatically Handled (No Action Required)

These are managed automatically by MMSplice:

### 1. Pre-trained Model Files
- [ ] ~~Download model files~~ **NOT NEEDED - downloads automatically**

**What happens automatically:**
```python
model = MMSplice()  # First time: downloads all models (~2 MB)
                    # Subsequent times: uses cached models
```

**Storage location:** `~/.kipoi/models/MMSplice/`

**Models included:**
- 5 module models (Acceptor, Donor, Exon, Introns)
- Linear model for delta_logit_psi
- Logistic model for pathogenicity
- (Optional) 8 tissue-specific models for MTSplice

---

### 2. FASTA Index File (.fai)
- [ ] ~~Create FASTA index~~ **NOT NEEDED - created automatically**

**What happens automatically:**
```python
dl = SplicingVCFDataloader(gtf, fasta, vcf)
# First time: creates genome.fa.fai automatically
# Subsequent times: uses existing index
```

**If you see errors, manually create:**
```bash
samtools faidx my_genome.fa
```

---

### 3. Reference PSI Files (for natural scale)
- [ ] ~~Download reference PSI~~ **NOT NEEDED - built-in**

**What happens automatically:**
```python
predictions = predict_all_table(model, dl,
                               natural_scale=True,
                               ref_psi_version='grch38')
# Uses built-in reference PSI values
```

**Built-in versions:** GRCh37, GRCh38

---

## 🔍 Version Compatibility Check

**CRITICAL:** GTF and FASTA must use the same genome version!

| GTF Version | FASTA Version | Compatible? |
|------------|---------------|-------------|
| GENCODE v19 (GRCh37) | GRCh37/hg19 | ✅ YES |
| GENCODE v45 (GRCh38) | GRCh38/hg38 | ✅ YES |
| GENCODE v19 (GRCh37) | GRCh38/hg38 | ❌ NO - mismatch! |
| GENCODE v45 (GRCh38) | GRCh37/hg19 | ❌ NO - mismatch! |

**How to check versions:**
```bash
# GTF version
head -5 my_annotation.gtf
# Look for "GRCh37" or "GRCh38" in comments

# FASTA version
head -1 my_genome.fa
# Check chromosome naming:
# >1 or >chr1 (both work, just need consistency)
```

---

## 🚀 Quick Setup Script

Run this to verify you have everything:

```bash
#!/bin/bash
# check_mmsplice_inputs.sh

echo "=== MMSplice Input Files Check ==="

# 1. Check VCF
if [ -f "my_variants.vcf.gz" ]; then
    echo "✓ VCF file found: my_variants.vcf.gz"
    if [ -f "my_variants.vcf.gz.tbi" ]; then
        echo "✓ VCF index found"
    else
        echo "⚠ VCF index missing - creating..."
        tabix -p vcf my_variants.vcf.gz
    fi
else
    echo "✗ VCF file not found"
fi

# 2. Check GTF
if [ -f "gencode.gtf" ]; then
    echo "✓ GTF file found: gencode.gtf"
    lines=$(wc -l < gencode.gtf)
    echo "  GTF contains $lines lines"
else
    echo "✗ GTF file not found"
fi

# 3. Check FASTA
if [ -f "GRCh38.fa" ]; then
    echo "✓ FASTA file found: GRCh38.fa"
    if [ -f "GRCh38.fa.fai" ]; then
        echo "✓ FASTA index found"
    else
        echo "⚠ FASTA index missing - creating..."
        samtools faidx GRCh38.fa
    fi
else
    echo "✗ FASTA file not found"
fi

# 4. Check model cache
if [ -d "$HOME/.kipoi/models/MMSplice" ]; then
    echo "✓ MMSplice models found in cache"
else
    echo "⚠ Models not cached yet (will download on first use)"
fi

echo ""
echo "=== Ready to run MMSplice? ==="
if [ -f "my_variants.vcf.gz" ] && [ -f "gencode.gtf" ] && [ -f "GRCh38.fa" ]; then
    echo "✓ YES - All required files present!"
else
    echo "✗ NO - Missing required files (see above)"
fi
```

---

## 📋 Minimal Working Example

Once you have the 3 files, here's the complete code:

```python
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

# 1. Specify your 3 input files
vcf_file = 'my_variants.vcf.gz'      # Your variants/ASO designs
gtf_file = 'gencode.v38.gtf'         # Gene annotations
fasta_file = 'GRCh38.fa'             # Reference genome

# 2. Create data loader (no other files needed!)
dl = SplicingVCFDataloader(
    gtf_file,
    fasta_file,
    vcf_file
)

# 3. Load model (downloads automatically if needed)
model = MMSplice()

# 4. Run predictions (that's it!)
predictions = predict_all_table(model, dl, pathogenicity=True)

# 5. Save results
predictions.to_csv('predictions.csv', index=False)

print(f"✓ Predicted {len(predictions)} variant-exon pairs")
print(predictions.head())
```

**No other files or configurations needed!**

---

## 🎓 Advanced: Alternative Input Methods

For special use cases, there are alternative input methods (but still no additional files required):

### Method 1: Direct Exon Coordinates (No VCF)

If you just want to score specific exons without variants:

```python
from mmsplice.exon_dataloader import ExonDataset

# CSV file with exon coordinates
exons_csv = 'my_exons.csv'  # Columns: chrom, start, end, strand, gene_name

dl = ExonDataset(exons_csv, fasta_file)
predictions = predict_all_table(model, dl)
```

**Still only need:** CSV file + FASTA (no VCF)

---

### Method 2: Sequence Strings (No Files!)

For testing specific sequences:

```python
from mmsplice import predict_sequence

sequence = "AGTCTGACTGCAGTCAGTCAGTCAGT"  # Your sequence
prediction = model.predict_sequence(sequence)
```

**No files needed at all!**

---

## ❓ Common Questions

### Q: Do I need to download Python packages?
**A:** Yes, but that's software installation, not input files:
```bash
pip install mmsplice
```

### Q: Do I need internet connection to run predictions?
**A:** Only for the **first run** (to download models). After that, works offline.

### Q: Do I need GPU?
**A:** No, CPU works fine (GPU optional for speed).

### Q: Do I need special file permissions?
**A:** Just read access to your 3 input files.

### Q: Do I need annotation databases?
**A:** No, GTF file contains all annotations needed.

### Q: Do I need splice site consensus sequences?
**A:** No, models learned these from training data.

---

## 📊 Summary Table

| Item | Type | Required? | How to Get |
|------|------|-----------|------------|
| **VCF file** | Input file | ✅ REQUIRED | Create for ASO design, or download ClinVar |
| **GTF file** | Input file | ✅ REQUIRED | Download from GENCODE/Ensembl |
| **FASTA file** | Input file | ✅ REQUIRED | Download from GENCODE/Ensembl |
| Pre-trained models | Weights | ✅ REQUIRED | ✨ **Auto-downloads** |
| FASTA index (.fai) | Index | Optional | ✨ **Auto-creates** |
| VCF index (.tbi) | Index | Recommended | `tabix -p vcf file.vcf.gz` |
| Reference PSI | Built-in data | Optional | ✨ **Built-in** (for natural_scale) |
| Python packages | Software | ✅ REQUIRED | `pip install mmsplice` |
| Internet | For first run | First time only | Download models once |

---

## ✅ Final Checklist

Before running MMSplice, verify:

- [ ] I have 3 files: VCF, GTF, FASTA
- [ ] All 3 files use the same genome version (all GRCh37 or all GRCh38)
- [ ] VCF is compressed and indexed (`.vcf.gz` + `.vcf.gz.tbi`)
- [ ] GTF is uncompressed (`.gtf`)
- [ ] FASTA is uncompressed (`.fa`)
- [ ] I have internet connection for first run (model download)
- [ ] I have installed mmsplice: `pip install mmsplice`

**If all checked ✅, you're ready to run MMSplice!**

---

**Bottom Line:** You only need **3 input files** (VCF, GTF, FASTA). Everything else is automatic!
