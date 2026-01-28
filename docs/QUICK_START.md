# MMSplice Quick Start - Just 3 Files!

## ✅ What You Need

```
┌─────────────────────────────────────────────────┐
│         ONLY 3 INPUT FILES REQUIRED             │
├─────────────────────────────────────────────────┤
│                                                 │
│  1️⃣  VCF File     →  Your variants/ASO designs  │
│                     (create or download)        │
│                                                 │
│  2️⃣  GTF File     →  Gene annotations           │
│                     (download once)             │
│                                                 │
│  3️⃣  FASTA File   →  Reference genome           │
│                     (download once)             │
│                                                 │
└─────────────────────────────────────────────────┘
```

## ⚙️ Everything Else is Automatic

```
┌─────────────────────────────────────────────────┐
│         AUTOMATICALLY HANDLED                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  🤖 Pre-trained models  →  Auto-download        │
│                           (~2 MB, first run)    │
│                                                 │
│  🗂️  FASTA index (.fai) →  Auto-create          │
│                           (first run)           │
│                                                 │
│  📊 Reference PSI data  →  Built-in             │
│                           (already included)    │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Test It Now (2 Minutes)

The project includes test data. Try it:

```bash
cd /Users/z/work2/dleader/MMSplice_MTSplice

# Run the quick test
python examples/quick_test.py
```

**Output you'll see:**
```
=== MMSplice Quick Test ===

✓ Using ONLY these 3 input files:

1. VCF:   tests/data/test.vcf.gz
   Size:  53.7 KB

2. GTF:   tests/data/test.gtf
   Size:  62.6 KB

3. FASTA: tests/data/hg19.nochr.chr17.fa
   Size:  78.7 MB

Loading MMSplice model...
✓ Model loaded

Running predictions...
✓ Predictions complete!

Results: 156 variant-exon pairs predicted
✅ SUCCESS - MMSplice works with just 3 files!
```

---

## 📖 Your First Real Analysis (5 Minutes)

### Step 1: Get Reference Files (One Time Setup)

```bash
# Create directory
mkdir -p ~/mmsplice_data
cd ~/mmsplice_data

# Download GTF (gene annotations) - ~50 MB
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip gencode.v45.annotation.gtf.gz

# Download FASTA (reference genome) - ~3 GB
wget ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
```

**Do this once, use forever!**

---

### Step 2: Create Your VCF (ASO Designs)

```bash
# Use the provided script for DMD exon 51 example
cd /Users/z/work2/dleader/MMSplice_MTSplice

python scripts/create_aso_vcf.py \
    --template dmd_exon51 \
    -o my_asos.vcf \
    --compress
```

---

### Step 3: Run Predictions

```python
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

# Point to your 3 files
dl = SplicingVCFDataloader(
    gtf='~/mmsplice_data/gencode.v45.annotation.gtf',
    fasta_file='~/mmsplice_data/Homo_sapiens.GRCh38.dna.primary_assembly.fa',
    vcf_file='my_asos.vcf.gz'
)

# Load and run
model = MMSplice()
predictions = predict_all_table(model, dl, pathogenicity=True)

# Save results
predictions.to_csv('my_predictions.csv', index=False)
print(f"✓ Done! {len(predictions)} predictions saved")
```

**That's it!**

---

## ❓ FAQ

### Q: Do I need to download model weights?
**A:** No - happens automatically on first run

### Q: Do I need to create FASTA index?
**A:** No - created automatically if missing

### Q: Do I need internet after setup?
**A:** No - works offline after first run (models cached locally)

### Q: What if I get "models downloading" message?
**A:** Normal! Only happens once. Subsequent runs are instant.

### Q: Do I need GPU?
**A:** No - CPU works fine (GPU optional for speed)

---

## 📦 File Sizes Reference

| File | Typical Size | Frequency |
|------|--------------|-----------|
| VCF (ASO designs) | 1-10 KB | Per project |
| VCF (patient) | 1-100 MB | Per patient |
| GTF annotations | 50 MB | Download once |
| FASTA genome | 3 GB | Download once |
| Pre-trained models | 2 MB | Auto-download once |

---

## ✅ Complete Checklist

Before first run:
- [ ] GTF file downloaded
- [ ] FASTA file downloaded
- [ ] VCF file created/ready
- [ ] `pip install mmsplice` done
- [ ] Internet connection (for model download)

After first run:
- [ ] Models cached in `~/.kipoi/`
- [ ] Can work offline
- [ ] Fast predictions!

---

## 🎯 Bottom Line

**You provide:** 3 files (VCF, GTF, FASTA)

**MMSplice handles:** Everything else automatically

**No other inputs, configs, or databases needed!**

---

## 📚 Next Steps

- Read detailed guide: [`docs/MMSplice_MTSplice_for_ASO_Design.md`](MMSplice_MTSplice_for_ASO_Design.md)
- Create custom ASOs: [`docs/Creating_VCF_for_ASO_Design.md`](Creating_VCF_for_ASO_Design.md)
- File requirements: [`docs/How_to_Get_Input_Files.md`](How_to_Get_Input_Files.md)
- Full checklist: [`docs/Input_Files_Checklist.md`](Input_Files_Checklist.md)
