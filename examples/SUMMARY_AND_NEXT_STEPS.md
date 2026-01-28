# DMD ASO Design Project - Summary & Next Steps

## ✅ What We Successfully Completed

### 1. **Local Prediction Pipeline** ✅
- **Status**: Fully functional
- **Environment**: conda environment "mmsplice" with Python 3.8
- **Validated**: Successfully ran predictions on 2,033 variant-exon pairs (BRCA1 test data)
- **Results**: Generated comprehensive analysis with delta_logit_psi scores, pathogenicity, and module scores

### 2. **DMD Exon 51 ASO Design VCF** ✅
- **File**: [examples/dmd_aso_design.vcf](dmd_aso_design.vcf)
- **Variants**: 6 ASO candidates targeting:
  - 3 donor site positions (X:31,791,718-720)
  - 2 acceptor site positions (X:31,791,625-626)
  - 1 ESE blocker (X:31,791,500)
- **Format**: Corrected chromosome naming from "chrX" to "X" for Ensembl/GRCh38 compatibility
- **Reference Drug**: Based on Eteplirsen (FDA-approved DMD exon 51 skipping therapy)

### 3. **Documentation** ✅
Created comprehensive guides:
- [ASO_DESIGN_ANALYSIS_REPORT.md](ASO_DESIGN_ANALYSIS_REPORT.md) - Complete analysis of MMSplice for ASO design
- [MMSplice_MTSplice_for_ASO_Design.md](../docs/MMSplice_MTSplice_for_ASO_Design.md) - Technical guide
- [QUICK_START.md](../docs/QUICK_START.md) - Getting started guide
- [Creating_VCF_for_ASO_Design.md](../docs/Creating_VCF_for_ASO_Design.md) - VCF preparation guide

### 4. **Modal API Deployment** ✅ (with issues)
- **Status**: Deployed but experiencing runtime errors
- **Health Endpoint**: ✅ Working - https://dleader-lab--mmsplice-api-health.modal.run
- **Prediction Endpoint**: ⚠️  Returns "Internal Server Error" (debugging in progress)
- **Reference Files**: ✅ GRCh38 GTF + FASTA cached in Modal Volume

---

## ⚠️  Current Issue: Modal API Internal Error

### Problem
The Modal API `/predict` endpoint returns "Internal Server Error" for all VCF file uploads, including known-good test files.

### Investigation Steps Taken
1. **Enhanced error logging**: Added comprehensive logging and traceback reporting
2. **Redeployed API**: Latest version includes detailed error messages
3. **Tested with multiple VCFs**: Both DMD ASO design and test.vcf.gz fail
4. **Verified reference files**: GRCh38 GTF and FASTA exist and are accessible

### Potential Causes
1. **Async file handling issue**: The `await vcf_file.read()` may have compatibility issues with FastAPI version
2. **VCF processing error**: SplicingVCFDataloader might fail silently during initialization
3. **Memory/timeout**: Large reference files (4GB) might cause initialization delays
4. **Dependency conflict**: MMSplice 2.4.0 + FastAPI 0.115.0 + Python 3.10 combination

### Next Debugging Steps
1. Check Modal web dashboard logs directly at: https://modal.com/apps/dleader-lab/main/deployed/mmsplice-api
2. Test with minimal VCF (single variant)
3. Add health check for MMSplice model loading
4. Test synchronous file upload instead of async

---

## ✅ Working Solution: Local Execution

Since the Modal API has issues, use the local conda environment which **works perfectly**:

### Setup (One-Time)

```bash
# Activate environment
conda activate mmsplice

# Verify installation
python -c "from mmsplice import MMSplice; print('✓ MMSplice ready')"
```

### Run Predictions

#### Option A: Use the Prediction Script

```bash
cd /Users/z/work2/dleader/MMSplice_MTSplice

# Run predictions (currently uses test data)
python examples/predict_dmd_local.py
```

**Output**:
```
================================================================================
DMD ASO Design - MMSplice Predictions (Local)
================================================================================

Prediction Summary:
  Total predictions: 2,033
  Delta Logit PSI statistics:
    Min: -13.142 (strongest exon skipping)
    Max: +6.428 (strongest exon inclusion)
  Strong exon skipping candidates: 475
  Strong exon inclusion candidates: 9

Top 10 Exon Skipping Candidates: [displays results]

✓ Full predictions saved to: examples/test_predictions_local.csv
```

#### Option B: Custom Python Script

```python
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table
import pandas as pd

# Input files
gtf_file = "path/to/GRCh38.gtf"      # ~1.5 GB
fasta_file = "path/to/GRCh38.fa"     # ~3 GB
vcf_file = "examples/dmd_aso_design.vcf.gz"

# Create dataloader
dl = SplicingVCFDataloader(gtf_file, fasta_file, vcf_file)

# Load model
model = MMSplice()

# Run predictions
predictions = predict_all_table(
    model,
    dl,
    pathogenicity=True,
    splicing_efficiency=True
)

# Analyze exon skipping candidates
skipping = predictions[predictions['delta_logit_psi'] < -2].sort_values('delta_logit_psi')

print("Top ASO Candidates for Exon Skipping:")
print(skipping[['ID', 'gene_name', 'delta_logit_psi', 'pathogenicity']].head(10))

# Save results
predictions.to_csv('dmd_aso_predictions.csv', index=False)
```

---

## 📊 Expected Results for DMD Exon 51

When full GRCh38 reference files are used with the DMD ASO design VCF, you should see:

### Strong Skipping Candidates (delta_logit_psi < -2)

| Variant ID | Position | Target | Expected delta_logit_psi | Interpretation |
|-----------|----------|---------|--------------------------|----------------|
| ASO_DMD_Ex51_Donor_v1 | X:31,791,718 | Donor GT | < -3 | Strong exon 51 skipping |
| ASO_DMD_Ex51_Donor_v2 | X:31,791,719 | Donor GT | < -3 | Strong exon 51 skipping |
| ASO_DMD_Ex51_Acceptor_v1 | X:31,791,625 | Acceptor AG | -2 to -4 | Moderate-strong skipping |

### Analysis Criteria

**Tier 1 Candidates (Highest Priority)**:
- delta_logit_psi < -3
- pathogenicity > 0.9
- Strong module scores at donor/acceptor

**Tier 2 Candidates (Good)**:
- -3 < delta_logit_psi < -2
- pathogenicity > 0.7

**Not Recommended**:
- delta_logit_psi > -0.5 (weak effect)

---

## 📥 Getting Full GRCh38 Reference Files

The test data only covers chr17/BRCA1. For DMD (chromosome X), you need full GRCh38:

### Download GRCh38 Files

```bash
# Create reference directory
mkdir -p ~/references/GRCh38
cd ~/references/GRCh38

# Download GTF (~1.5 GB compressed, ~8 GB uncompressed)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip gencode.v45.annotation.gtf.gz

# Download FASTA (~900 MB compressed, ~3 GB uncompressed)
wget ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz

# Create FASTA index (required)
samtools faidx Homo_sapiens.GRCh38.dna.primary_assembly.fa

echo "✓ GRCh38 references ready at: $(pwd)"
```

### Update Prediction Script

```python
# Use full genome references
gtf_file = "/Users/z/references/GRCh38/gencode.v45.annotation.gtf"
fasta_file = "/Users/z/references/GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa"
vcf_file = "examples/dmd_aso_design.vcf.gz"
```

---

## 🔬 Next Steps for ASO Development

### 1. Run Full Predictions (1-2 hours first time)

```bash
conda activate mmsplice

# Create prediction script for DMD
cat > examples/predict_dmd_full.py << 'EOF'
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table
import pandas as pd

print("Loading MMSplice for DMD exon 51 predictions...")

dl = SplicingVCFDataloader(
    "/Users/z/references/GRCh38/gencode.v45.annotation.gtf",
    "/Users/z/references/GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa",
    "examples/dmd_aso_design.vcf.gz",
    tissue_specific=True  # Enable 56-tissue predictions
)

model = MMSplice()
predictions = predict_all_table(model, dl, pathogenicity=True, splicing_efficiency=True)

# Filter for DMD exon 51
dmd_predictions = predictions[predictions['gene_name'] == 'DMD']
dmd_sorted = dmd_predictions.sort_values('delta_logit_psi')

print(f"\n{'='*80}")
print(f"DMD Exon 51 ASO Predictions - Top Candidates")
print(f"{'='*80}\n")

print(dmd_sorted[['ID', 'delta_logit_psi', 'pathogenicity', 'delta_psi5', 'delta_psi3']].head(10))

# Check muscle-specific effects
muscle_cols = [c for c in dmd_sorted.columns if 'Muscle' in c or 'Heart' in c]
if muscle_cols:
    print(f"\nMuscle/Heart Tissue-Specific Predictions:")
    print(dmd_sorted[['ID'] + muscle_cols[:3]].head())

dmd_predictions.to_csv('examples/dmd_exon51_predictions_full.csv', index=False)
print(f"\n✓ Full predictions saved to: examples/dmd_exon51_predictions_full.csv")
EOF

# Run it
python examples/predict_dmd_full.py
```

### 2. Rank ASO Candidates

Based on predictions, select top 3-5 candidates for:
1. **In vitro validation**: Minigene assays (2-4 weeks)
2. **Cell-based validation**: Patient myoblasts (4-8 weeks)
3. **Chemistry optimization**: Test different ASO modifications

### 3. Tissue-Specific Analysis

```python
# Analyze muscle vs other tissues
muscle_effect = predictions['tissue_Muscle_Skeletal_delta_logit_psi']
brain_effect = predictions['tissue_Brain_Cortex_delta_logit_psi']

# Ideal: strong in muscle, weak elsewhere
selectivity = muscle_effect / (brain_effect + 1e-6)
```

### 4. Experimental Validation Pipeline

| Stage | Time | Cost | Goal |
|-------|------|------|------|
| **Minigene assay** | 2 weeks | $5K | Confirm exon skipping |
| **Patient cells** | 1 month | $20K | Test dystrophin restoration |
| **Mouse model** | 3 months | $100K | In vivo efficacy |
| **Clinical trial** | 5-7 years | $50M+ | FDA approval |

---

## 🚀 Alternative: Fix Modal API (Advanced)

If you want to debug the Modal API:

### 1. Access Modal Dashboard

Visit https://modal.com/apps/dleader-lab/main/deployed/mmsplice-api

Click on recent "predict" function calls to see full logs and tracebacks.

### 2. Potential Fixes

**Fix A: Simplify file handling**
```python
# Try non-async file reading
@modal.fastapi_endpoint(method="POST")
def predict(vcf_file: UploadFile, ...):  # Remove async
    vcf_content = vcf_file.file.read()    # Remove await
    ...
```

**Fix B: Increase resources**
```python
@app.function(
    timeout=1200,     # Increase from 600s
    memory=16384,     # Increase from 8GB
    cpu=8.0,          # Increase from 4 cores
)
```

**Fix C: Test model loading separately**
```python
@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def test_model():
    from mmsplice import MMSplice
    try:
        model = MMSplice()
        return {"status": "Model loaded successfully"}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
```

### 3. Redeploy & Test

```bash
modal deploy deployment/modal_app_v2.py
curl https://dleader-lab--mmsplice-api-test-model.modal.run
```

---

## 📚 Key Resources

### Documentation
- [ASO_DESIGN_ANALYSIS_REPORT.md](ASO_DESIGN_ANALYSIS_REPORT.md) - Complete workflow guide
- [MMSplice Paper](../2020.06.07.138453v1.full.pdf) - MTSplice preprint
- [GitHub Repository](https://github.com/gagneurlab/MMSplice)

### Files
- ✅ [dmd_aso_design.vcf](dmd_aso_design.vcf) - DMD exon 51 ASO variants
- ✅ [predict_dmd_local.py](predict_dmd_local.py) - Working prediction script
- ✅ [test_predictions_local.csv](test_predictions_local.csv) - Example results

### API Endpoints (Health working, Predict has issues)
- Health: https://dleader-lab--mmsplice-api-health.modal.run ✅
- Predict: https://dleader-lab--mmsplice-api-predict.modal.run ⚠️
- Genomes: https://dleader-lab--mmsplice-api-list-genomes.modal.run ✅

---

## ✅ Final Checklist

- [x] Conda environment "mmsplice" created and validated
- [x] DMD exon 51 ASO design VCF created (6 variants)
- [x] Local prediction pipeline working perfectly
- [x] Modal API deployed (health endpoint working)
- [x] Comprehensive documentation created
- [x] Test predictions completed (2,033 variant-exon pairs)
- [ ] Download full GRCh38 references (user action required)
- [ ] Run DMD predictions with full genome
- [ ] Fix Modal API internal error (debugging needed)
- [ ] Experimental validation of top ASO candidates

---

## 💡 Recommendations

1. **Immediate**: Use local conda environment with test data to validate workflow
2. **Short-term** (this week): Download GRCh38 and run full DMD predictions
3. **Medium-term** (1-2 weeks): Debug Modal API or accept local-only workflow
4. **Long-term** (months): Validate top ASO candidates experimentally

---

**Generated**: 2026-01-27
**Status**: Local pipeline fully functional, Modal API needs debugging
**Conda Environment**: mmsplice (Python 3.8)
**Contact**: For Modal API issues, check https://modal.com/apps/dleader-lab
