# Modal API Debug Report - DMD ASO Prediction

## Summary

The Modal API has been partially fixed but continues to have issues with the predict endpoint. File uploads now work correctly, but the MMSplice prediction processing fails.

## What Works ✅

1. **Modal Deployment**: Successfully deployed to Modal
2. **Health Endpoint**: https://dleader-lab--mmsplice-api-health.modal.run
   - Returns correct status
   - Shows GRCh38 references are available
3. **List Genomes Endpoint**: https://dleader-lab--mmsplice-api-list-genomes.modal.run
   - Lists available genomes correctly
4. **File Upload**: Test endpoint proves file uploads work
   - Successfully receives VCF files
   - Can read file contents
   - Proper async handling

## What Doesn't Work ❌

**Predict Endpoint**: https://dleader-lab--mmsplice-api-predict.modal.run
- Returns "Internal Server Error" for all VCF files
- Fails for both DMD ASO design VCF and test.vcf.gz
- Error occurs during MMSplice processing, not file upload

## Fixes Applied

### Fix #1: FastAPI File Upload Annotation
**Changed:**
```python
# Before
async def predict(vcf_file: UploadFile, ...):

# After
async def predict(vcf_file: UploadFile = File(...), ...):
```

**Result**: Deployment succeeds, but predict still fails

### Fix #2: Added Test Upload Endpoint
**Added:**
```python
@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
async def test_upload(vcf_file: UploadFile = File(...)) -> dict:
    content = await vcf_file.read()
    return {"status": "success", "filename": vcf_file.filename, "size": len(content)}
```

**Result**: ✅ Works perfectly - proves file upload mechanism is functional

## Likely Root Cause

Based on testing:
1. ✅ File upload works (test_upload endpoint succeeds)
2. ✅ Reference files exist (health check confirms)
3. ❌ Prediction fails (Internal Server Error)

**Hypothesis**: The error occurs in one of these steps:
- VCF file decompression/indexing
- SplicingVCFDataloader initialization
- MMSplice model loading
- predict_all_table execution
- JSON serialization of results

The enhanced logging should show the error, but logs are not accessible via CLI.

## Recommended Actions

### Option 1: Check Modal Web Dashboard (Recommended)
Visit: https://modal.com/apps/dleader-lab/main/deployed/mmsplice-api

Click on recent "predict" function calls to see:
- Full error traceback
- Console output with [INFO]/[ERROR] messages
- Exact line where failure occurs

### Option 2: Use Local Conda Environment (Working Now)
The local environment works perfectly:

```bash
conda activate mmsplice
cd /Users/z/work2/dleader/MMSplice_MTSplice

# Run predictions
python examples/predict_dmd_local.py

# Results: ✅ 2,033 predictions successfully generated
```

### Option 3: Simplify Modal Prediction Function
Try processing step-by-step with error handling:

```python
@modal.fastapi_endpoint(method="POST")
async def predict(vcf_file: UploadFile = File(...), ...):
    print("[STEP 1] Received file upload")
    content = await vcf_file.read()
    print(f"[STEP 2] Read {len(content)} bytes")

    # Save to temp file
    vcf_path = f"/tmp/{vcf_file.filename}"
    with open(vcf_path, 'wb') as f:
        f.write(content)
    print(f"[STEP 3] Saved to {vcf_path}")

    # Try to load with cyvcf2
    import cyvcf2
    try:
        vcf = cyvcf2.VCF(vcf_path)
        print(f"[STEP 4] Loaded VCF with cyvcf2")
        variant_count = len(list(vcf))
        print(f"[STEP 5] Found {variant_count} variants")
    except Exception as e:
        return {"error": f"VCF loading failed: {str(e)}"}

    # Continue with dataloader...
```

## API Endpoints Status

| Endpoint | URL | Status |
|----------|-----|--------|
| Health | https://dleader-lab--mmsplice-api-health.modal.run | ✅ Working |
| List Genomes | https://dleader-lab--mmsplice-api-list-genomes.modal.run | ✅ Working |
| Test Upload | https://dleader-lab--mmsplice-api-test-upload.modal.run | ✅ Working |
| Predict | https://dleader-lab--mmsplice-api-predict.modal.run | ❌ Internal Server Error |

## Files

- Working version: [deployment/modal_app_v2.py](../deployment/modal_app_v2.py)
- DMD ASO VCF: [examples/dmd_aso_design.vcf.gz](dmd_aso_design.vcf.gz)
- Test upload result: File upload succeeds (493 bytes received)

## Next Steps

1. **Immediate**: Use local conda environment for predictions (fully functional)
2. **Short-term**: Check Modal web dashboard for actual error message
3. **Medium-term**: Add step-by-step debugging in predict function
4. **Long-term**: Consider if Modal's ephemeral containers are suitable for 4GB reference files

## Local Workaround (Recommended)

Since local execution works perfectly, use this approach:

```bash
# Download GRCh38 references (one-time, ~4GB)
mkdir -p ~/references/GRCh38
cd ~/references/GRCh38

# GTF
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip gencode.v45.annotation.gtf.gz

# FASTA
wget ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
samtools faidx Homo_sapiens.GRCh38.dna.primary_assembly.fa

# Run DMD predictions
conda activate mmsplice
cd /Users/z/work2/dleader/MMSplice_MTSplice

python -c "
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table
import pandas as pd

dl = SplicingVCFDataloader(
    '~/references/GRCh38/gencode.v45.annotation.gtf',
    '~/references/GRCh38/Homo_sapiens.GRCh38.dna.primary_assembly.fa',
    'examples/dmd_aso_design.vcf.gz'
)

model = MMSplice()
predictions = predict_all_table(model, dl, pathogenicity=True, splicing_efficiency=True)

# Filter for DMD
dmd = predictions[predictions['gene_name'] == 'DMD'].sort_values('delta_logit_psi')
print(dmd[['ID', 'delta_logit_psi', 'pathogenicity']].head(10))

predictions.to_csv('examples/dmd_predictions_final.csv', index=False)
print(f'\n✓ Saved {len(predictions)} predictions to dmd_predictions_final.csv')
"
```

## Conclusion

**Recommendation**: Use the local conda environment for now. It provides:
- ✅ Full functionality (all features work)
- ✅ Better debugging (can see all errors directly)
- ✅ No API rate limits or timeouts
- ✅ Already validated with test data (2,033 predictions)

The Modal API can be revisited once the actual error is identified from the web dashboard.

---

**Report Generated**: 2026-01-27
**Status**: Local environment working, Modal API debugging in progress
