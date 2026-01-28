# MMSplice Modal Deployment - Quick Start

## 1. Install Modal

```bash
pip install modal
```

## 2. Authenticate

```bash
modal token new
```

This opens a browser for authentication.

## 3. Deploy

```bash
# Option A: Automated (recommended)
bash deployment/deploy.sh

# Option B: Manual
modal deploy deployment/modal_app.py
modal run deployment/modal_app.py  # Setup reference files
```

## 4. Get Your API URLs

After deployment, Modal will print URLs like:
```
Created web endpoint => https://username--mmsplice-api-predict.modal.run
Created web endpoint => https://username--mmsplice-api-health.modal.run
```

**Save these URLs!** You'll need them to make API calls.

## 5. Test It

```bash
# Check health
curl https://YOUR-HEALTH-URL

# Make a prediction
python deployment/test_client.py \
  --url https://YOUR-PREDICT-URL \
  --vcf tests/data/test.vcf.gz
```

## 6. Use It

### Python

```python
import requests

url = "https://YOUR-PREDICT-URL"
with open("variants.vcf.gz", "rb") as f:
    files = {"vcf_file": f}
    data = {"genome": "GRCh38"}
    response = requests.post(url, files=files, data=data)
    predictions = response.json()

print(predictions['num_predictions'])  # Number of predictions
print(predictions['predictions'])       # Array of predictions
```

### cURL

```bash
curl -X POST https://YOUR-PREDICT-URL \
  -F "vcf_file=@variants.vcf.gz" \
  -F "genome=GRCh38" \
  > predictions.json
```

## Architecture

```
┌─────────────┐
│   User      │
│             │
└──────┬──────┘
       │ Upload VCF
       │
       ▼
┌─────────────────────────────────────┐
│   Modal Serverless Function         │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  FastAPI Endpoint            │  │
│  │  /predict                    │  │
│  └──────────────┬───────────────┘  │
│                 │                   │
│                 ▼                   │
│  ┌──────────────────────────────┐  │
│  │  MMSplice Model              │  │
│  │  - Load VCF                  │  │
│  │  - Load GTF/FASTA (Volume)   │  │
│  │  - Run predictions           │  │
│  └──────────────┬───────────────┘  │
│                 │                   │
└─────────────────┼───────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │  Modal Volume    │
        │  (Persistent)    │
        │                  │
        │  - GTF (~50 MB)  │
        │  - FASTA (~3 GB) │
        │  - .fai index    │
        └──────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │  Return JSON     │
        │  {predictions,   │
        │   summary, ...}  │
        └──────────────────┘
```

## Files Created

| File | Purpose |
|------|---------|
| `modal_app.py` | Main Modal app with API endpoints |
| `README_MODAL.md` | Complete documentation |
| `test_client.py` | Python client for testing |
| `deploy.sh` | Automated deployment script |
| `requirements.txt` | Python dependencies |

## Common Issues

**Issue**: "GTF file not found"
```bash
# Solution: Setup reference files
modal run deployment/modal_app.py
```

**Issue**: VCF upload fails
```bash
# Solution: Compress and index VCF
bgzip my_variants.vcf
tabix -p vcf my_variants.vcf.gz
```

**Issue**: Timeout error
```python
# Solution: Increase timeout in modal_app.py
@app.function(timeout=1200)  # 20 minutes
```

## Next Steps

- Read full documentation: [README_MODAL.md](README_MODAL.md)
- View API docs: Visit `https://YOUR-PREDICT-URL/docs` in browser
- See example notebooks: [../docs/](../docs/)
- Add authentication: See security section in README_MODAL.md

## Cost Estimate

- **Free tier**: $30/month credit (enough for ~1000-3000 predictions)
- **Storage**: ~$1.22/month for reference files
- **Per prediction**: $0.01 - $0.50 depending on VCF size

## Support

- Modal docs: https://modal.com/docs
- MMSplice GitHub: https://github.com/gagneurlab/MMSplice
- Issues: Create an issue in this repository

---

**Ready to deploy?**

```bash
bash deployment/deploy.sh
```
