# MMSplice Serverless Deployment on Modal

This directory contains everything you need to deploy MMSplice as a serverless API on [Modal](https://modal.com/).

## Overview

The Modal deployment provides:
- **REST API** for MMSplice predictions
- **VCF file upload** support
- **Multiple reference genomes** (GRCh38, GRCh37)
- **Persistent storage** for reference files using Modal Volumes
- **Auto-scaling** serverless infrastructure
- **Optional tissue-specific predictions** (MTSplice)

## Prerequisites

### 1. Install Modal

```bash
pip install modal
```

### 2. Create Modal Account

Sign up at [modal.com](https://modal.com/) (free tier available)

### 3. Authenticate

```bash
modal token new
```

This will open a browser to authenticate and save your token.

## Deployment Steps

### Step 1: Deploy the App

```bash
# From the project root directory
modal deploy deployment/modal_app.py
```

This will:
- Build the container image with all dependencies
- Create the Modal app with API endpoints
- Create a persistent volume for reference files
- Deploy the endpoints and return URLs

**Expected output:**
```
✓ Created objects.
├── 🔨 Created mount /Users/z/work2/dleader/MMSplice_MTSplice/deployment/modal_app.py
├── 🔨 Created volume mmsplice-reference-data.
├── 🔨 Created image im-...
├── 🔨 Created function predict.
├── 🔨 Created web endpoint => https://yourusername--mmsplice-api-predict.modal.run
├── 🔨 Created function health.
├── 🔨 Created web endpoint => https://yourusername--mmsplice-api-health.modal.run
└── 🔨 Created function list_genomes.
    🔨 Created web endpoint => https://yourusername--mmsplice-api-list-genomes.modal.run
```

### Step 2: Setup Reference Files

**IMPORTANT:** You must upload reference files (FASTA and GTF) before making predictions.

```bash
# Download and setup GRCh38 reference files (default)
modal run deployment/modal_app.py

# Or setup GRCh37
modal run deployment/modal_app.py --genome GRCh37
```

**What this does:**
- Downloads GTF file (~50 MB for GRCh38, ~40 MB for GRCh37)
- Downloads FASTA file (~3 GB for GRCh38, ~3 GB for GRCh37)
- Creates FASTA index (.fai file)
- Stores everything in the Modal Volume

**Time required:** 10-15 minutes (depending on internet speed)

### Step 3: Verify Deployment

Check that reference files are ready:

```bash
curl https://yourusername--mmsplice-api-health.modal.run
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "MMSplice API",
  "version": "2.4.0",
  "genomes_available": {
    "GRCh38": {
      "gtf_exists": true,
      "fasta_exists": true
    },
    "GRCh37": {
      "gtf_exists": false,
      "fasta_exists": false
    }
  }
}
```

## API Usage

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | POST | Upload VCF and get predictions |
| `/health` | GET | Health check |
| `/list-genomes` | GET | List available genomes |

### Making Predictions

#### Using cURL

```bash
# Basic prediction
curl -X POST \
  https://yourusername--mmsplice-api-predict.modal.run \
  -F "vcf_file=@my_variants.vcf.gz" \
  -F "genome=GRCh38" \
  -F "pathogenicity=true" \
  -F "splicing_efficiency=true" \
  > predictions.json

# With tissue-specific predictions (MTSplice)
curl -X POST \
  https://yourusername--mmsplice-api-predict.modal.run \
  -F "vcf_file=@my_variants.vcf.gz" \
  -F "genome=GRCh38" \
  -F "tissue_specific=true" \
  > predictions_tissue.json
```

#### Using Python (requests)

```python
import requests

url = "https://yourusername--mmsplice-api-predict.modal.run"

with open("my_variants.vcf.gz", "rb") as f:
    files = {"vcf_file": f}
    data = {
        "genome": "GRCh38",
        "pathogenicity": "true",
        "splicing_efficiency": "true",
        "tissue_specific": "false"
    }

    response = requests.post(url, files=files, data=data)
    predictions = response.json()

print(f"Status: {predictions['status']}")
print(f"Number of predictions: {predictions['num_predictions']}")
print(f"Strong skipping effects: {predictions['summary']['strong_skipping']}")
print(f"Strong inclusion effects: {predictions['summary']['strong_inclusion']}")

# Save predictions to CSV
import pandas as pd
df = pd.DataFrame(predictions['predictions'])
df.to_csv('predictions.csv', index=False)
```

#### Using the Test Client

```bash
python deployment/test_client.py --vcf my_variants.vcf.gz --genome GRCh38
```

### API Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vcf_file` | file | *required* | VCF file (.vcf or .vcf.gz) |
| `genome` | string | `GRCh38` | Reference genome (GRCh38 or GRCh37) |
| `pathogenicity` | boolean | `true` | Include pathogenicity scores |
| `splicing_efficiency` | boolean | `true` | Include efficiency predictions |
| `tissue_specific` | boolean | `false` | Enable MTSplice tissue predictions |

### Response Format

```json
{
  "status": "success",
  "genome": "GRCh38",
  "num_predictions": 2033,
  "parameters": {
    "pathogenicity": true,
    "splicing_efficiency": true,
    "tissue_specific": false
  },
  "predictions": [
    {
      "ID": "17:41197805:ACATCTGCC>A",
      "gene_name": "BRCA1",
      "delta_logit_psi": 0.001848,
      "pathogenicity": 0.908687,
      "efficiency": 0.95,
      ...
    }
  ],
  "summary": {
    "strong_skipping": 475,
    "strong_inclusion": 9,
    "genes": ["BRCA1", "TP53", ...]
  }
}
```

## Cost Estimation

Modal pricing (as of 2024):

- **Free tier**: $30/month credit
- **CPU**: ~$0.000231/CPU-second
- **Memory**: ~$0.00003/GB-second
- **Storage**: $0.20/GB-month for volumes

**Estimated costs per prediction:**
- Small VCF (10 variants): ~$0.01 - $0.02
- Medium VCF (100 variants): ~$0.05 - $0.10
- Large VCF (1000 variants): ~$0.30 - $0.50

**Storage costs:**
- GRCh38 reference (3.05 GB): ~$0.61/month
- GRCh37 reference (3.05 GB): ~$0.61/month
- Total: ~$1.22/month for both genomes

## Performance

- **Cold start**: 10-20 seconds (first request)
- **Warm requests**: 2-10 seconds (depending on VCF size)
- **Throughput**: ~10 variants/second
- **Concurrency**: Auto-scales to handle multiple requests

## Configuration

### Adjust Resources

Edit [modal_app.py](modal_app.py:30-33) to change compute resources:

```python
@app.function(
    timeout=600,      # Max execution time (seconds)
    memory=8192,      # RAM in MB
    cpu=4.0,          # Number of CPUs
)
```

### Add More Genomes

Edit [modal_app.py](modal_app.py:46-55) to add custom genomes:

```python
AVAILABLE_GENOMES = {
    "GRCh38": {
        "gtf": f"{REFERENCE_VOLUME_PATH}/gencode.v45.annotation.gtf",
        "fasta": f"{REFERENCE_VOLUME_PATH}/Homo_sapiens.GRCh38.dna.primary_assembly.fa",
    },
    "mm10": {  # Add mouse genome
        "gtf": f"{REFERENCE_VOLUME_PATH}/gencode.vM25.annotation.gtf",
        "fasta": f"{REFERENCE_VOLUME_PATH}/GRCm38.primary_assembly.fa",
    },
}
```

## Monitoring

### View Logs

```bash
# View recent logs
modal app logs mmsplice-api

# Stream logs in real-time
modal app logs mmsplice-api --follow
```

### Check Volume Usage

```bash
modal volume ls mmsplice-reference-data
```

## Troubleshooting

### Issue: "GTF file not found"

**Cause:** Reference files not uploaded

**Solution:**
```bash
modal run deployment/modal_app.py
```

### Issue: "Failed to load VCF file"

**Cause:** VCF file is malformed or not compressed properly

**Solution:**
- Ensure VCF is valid: `bcftools view my_variants.vcf`
- Compress with bgzip: `bgzip my_variants.vcf`
- Index with tabix: `tabix -p vcf my_variants.vcf.gz`

### Issue: Timeout Error

**Cause:** Large VCF file takes too long

**Solution:** Increase timeout in [modal_app.py](modal_app.py:30):
```python
@app.function(timeout=1200)  # 20 minutes
```

### Issue: Out of Memory

**Cause:** VCF file has too many variants

**Solution:** Increase memory in [modal_app.py](modal_app.py:32):
```python
@app.function(memory=16384)  # 16GB
```

## Updating the Deployment

After making changes to [modal_app.py](modal_app.py):

```bash
modal deploy deployment/modal_app.py
```

Modal will rebuild the image and redeploy automatically.

## Stopping/Deleting

### Stop the app (remove endpoints)

```bash
modal app stop mmsplice-api
```

### Delete the app entirely

```bash
modal app delete mmsplice-api
```

**Warning:** This does NOT delete the Volume. Reference files persist.

### Delete the Volume

```bash
modal volume delete mmsplice-reference-data
```

**Warning:** This deletes all reference files. You'll need to re-download them.

## Security Considerations

1. **API Authentication**: The basic deployment has no authentication. For production, add authentication:
   ```python
   from fastapi import Header, HTTPException

   async def verify_token(authorization: str = Header(None)):
       if authorization != f"Bearer {YOUR_SECRET_TOKEN}":
           raise HTTPException(status_code=401)

   @modal.web_endpoint(method="POST")
   async def predict(
       vcf_file: modal.web.UploadFile,
       authorization: str = Header(None)
   ):
       verify_token(authorization)
       # ... rest of code
   ```

2. **Rate Limiting**: Add rate limiting to prevent abuse

3. **File Size Limits**: Limit VCF file uploads (currently no limit)

4. **CORS**: Add CORS headers if accessing from browser

## Advanced Features

### Batch Processing

For processing many VCF files, use the batch API:

```python
import modal

app = modal.App.lookup("mmsplice-api")
predict = app.function_lookup("predict")

# Process multiple files
vcf_files = ["file1.vcf.gz", "file2.vcf.gz", "file3.vcf.gz"]

with app.run():
    results = list(predict.map([
        {"vcf_file": f, "genome": "GRCh38"}
        for f in vcf_files
    ]))
```

### Custom Model Weights

To use custom pre-trained weights:

1. Upload weights to Modal Volume
2. Modify model loading in [modal_app.py](modal_app.py):
   ```python
   model = MMSplice(custom_model_path=f"{REFERENCE_VOLUME_PATH}/my_weights.h5")
   ```

## Support & Resources

- **Modal Documentation**: https://modal.com/docs
- **MMSplice GitHub**: https://github.com/gagneurlab/MMSplice
- **Project Documentation**: See [docs/](../docs/) directory

## Example Use Cases

### Use Case 1: ASO Design Pipeline

```python
# 1. Create ASO designs as VCF
python scripts/create_aso_vcf.py --template dmd_exon51 -o dmd_asos.vcf --compress

# 2. Run predictions on Modal
curl -X POST https://your-endpoint/predict \
  -F "vcf_file=@dmd_asos.vcf.gz" \
  -F "genome=GRCh38" \
  -F "tissue_specific=true" \
  > aso_predictions.json

# 3. Analyze results
python scripts/analyze_aso_predictions.py aso_predictions.json
```

### Use Case 2: Patient Variant Analysis

```python
# Upload patient VCF from whole exome sequencing
curl -X POST https://your-endpoint/predict \
  -F "vcf_file=@patient_001.vcf.gz" \
  -F "genome=GRCh38" \
  -F "pathogenicity=true" \
  > patient_001_splicing_predictions.json
```

### Use Case 3: Integration with Galaxy/Nextflow

Add MMSplice Modal API to your bioinformatics pipeline:

```groovy
// Nextflow example
process MMSPLICE_PREDICT {
    input:
    path vcf_file

    output:
    path 'predictions.json'

    script:
    """
    curl -X POST ${MMSPLICE_API_URL} \
      -F "vcf_file=@${vcf_file}" \
      -F "genome=GRCh38" \
      > predictions.json
    """
}
```

---

## Quick Reference

```bash
# Deploy
modal deploy deployment/modal_app.py

# Setup reference files
modal run deployment/modal_app.py

# Make prediction
curl -X POST YOUR_URL/predict -F "vcf_file=@file.vcf.gz" > results.json

# Check health
curl YOUR_URL/health

# View logs
modal app logs mmsplice-api

# Update deployment
modal deploy deployment/modal_app.py

# Stop app
modal app stop mmsplice-api
```

---

**Ready to deploy? Run:**

```bash
modal deploy deployment/modal_app.py
```
