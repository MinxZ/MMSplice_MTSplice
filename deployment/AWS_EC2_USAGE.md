# Using MMSplice API from AWS EC2

## Quick Start (No Authentication Required)

Your Modal API endpoints are public HTTPS URLs. You can use them directly from AWS EC2 without any setup!

### Method 1: Using cURL

```bash
# SSH into your AWS EC2 instance
ssh -i your-key.pem ec2-user@your-instance.amazonaws.com

# Make a prediction
curl -X POST https://dleader-lab--mmsplice-api-predict.modal.run \
  -F "vcf_file=@variants.vcf.gz" \
  -F "genome=GRCh38" \
  -F "pathogenicity=true" \
  > predictions.json

# Check results
cat predictions.json | jq '.summary'
```

### Method 2: Using Python

```python
import requests

# Your Modal API URL
API_URL = "https://dleader-lab--mmsplice-api-predict.modal.run"

# Upload VCF and get predictions
with open("variants.vcf.gz", "rb") as f:
    files = {"vcf_file": f}
    data = {
        "genome": "GRCh38",
        "pathogenicity": "true",
        "splicing_efficiency": "true"
    }

    response = requests.post(API_URL, files=files, data=data)
    predictions = response.json()

# Save results
import pandas as pd
df = pd.DataFrame(predictions['predictions'])
df.to_csv('predictions.csv', index=False)

print(f"Made {predictions['num_predictions']} predictions")
print(f"Strong skipping: {predictions['summary']['strong_skipping']}")
print(f"Strong inclusion: {predictions['summary']['strong_inclusion']}")
```

### Method 3: Using Bash Script

Create a script `predict.sh`:

```bash
#!/bin/bash
# predict.sh - Run MMSplice predictions

API_URL="https://dleader-lab--mmsplice-api-predict.modal.run"
VCF_FILE="$1"
GENOME="${2:-GRCh38}"
OUTPUT="${3:-predictions.json}"

if [ -z "$VCF_FILE" ]; then
    echo "Usage: ./predict.sh <vcf_file> [genome] [output_file]"
    exit 1
fi

echo "Running MMSplice prediction..."
echo "  VCF: $VCF_FILE"
echo "  Genome: $GENOME"
echo "  Output: $OUTPUT"

curl -X POST "$API_URL" \
  -F "vcf_file=@$VCF_FILE" \
  -F "genome=$GENOME" \
  -F "pathogenicity=true" \
  -F "splicing_efficiency=true" \
  -o "$OUTPUT"

echo "Done! Results saved to $OUTPUT"
```

Usage:
```bash
chmod +x predict.sh
./predict.sh variants.vcf.gz GRCh38 results.json
```

---

## Optional: Add API Key Authentication

If you want to secure your API (recommended for production), use the secured version:

### 1. Set Up API Key

Create a Modal secret:
```bash
modal secret create mmsplice-api-key MMSPLICE_API_KEY=your-secret-key-here
```

### 2. Deploy Secured Version

```bash
modal deploy deployment/modal_app_secured.py
```

### 3. Use with API Key from EC2

```bash
# Set your API key
export API_KEY="your-secret-key-here"

# Make authenticated request
curl -X POST https://your-secured-endpoint.modal.run/predict \
  -H "X-API-Key: $API_KEY" \
  -F "vcf_file=@variants.vcf.gz" \
  -F "genome=GRCh38" \
  > predictions.json
```

Python with API key:
```python
import requests

API_URL = "https://your-secured-endpoint.modal.run/predict"
API_KEY = "your-secret-key-here"

headers = {"X-API-Key": API_KEY}

with open("variants.vcf.gz", "rb") as f:
    files = {"vcf_file": f}
    data = {"genome": "GRCh38"}

    response = requests.post(API_URL, headers=headers, files=files, data=data)
    predictions = response.json()
```

---

## AWS EC2 Setup

### Install Dependencies

```bash
# Update system
sudo yum update -y  # Amazon Linux
# or
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python and pip
sudo yum install python3 python3-pip -y  # Amazon Linux
# or
sudo apt install python3 python3-pip -y  # Ubuntu

# Install required packages
pip3 install requests pandas
```

### Upload VCF Files to EC2

```bash
# From your local machine
scp -i your-key.pem variants.vcf.gz ec2-user@your-instance:/home/ec2-user/

# Or download from S3
aws s3 cp s3://your-bucket/variants.vcf.gz .
```

---

## Integration Examples

### Example 1: Batch Processing

Process multiple VCF files:

```python
import os
import requests
import pandas as pd
from pathlib import Path

API_URL = "https://dleader-lab--mmsplice-api-predict.modal.run"

# Directory with VCF files
vcf_dir = Path("/data/vcf_files")
output_dir = Path("/data/results")
output_dir.mkdir(exist_ok=True)

# Process each VCF
for vcf_file in vcf_dir.glob("*.vcf.gz"):
    print(f"Processing {vcf_file.name}...")

    with open(vcf_file, "rb") as f:
        files = {"vcf_file": f}
        data = {"genome": "GRCh38"}

        response = requests.post(API_URL, files=files, data=data)

        if response.status_code == 200:
            predictions = response.json()

            # Save results
            output_file = output_dir / f"{vcf_file.stem}_predictions.csv"
            df = pd.DataFrame(predictions['predictions'])
            df.to_csv(output_file, index=False)

            print(f"  ✓ {predictions['num_predictions']} predictions saved to {output_file}")
        else:
            print(f"  ✗ Error: {response.text}")
```

### Example 2: AWS Lambda Function

Deploy as Lambda function to process S3 uploads:

```python
import json
import boto3
import requests
from io import BytesIO

s3 = boto3.client('s3')
API_URL = "https://dleader-lab--mmsplice-api-predict.modal.run"

def lambda_handler(event, context):
    # Get S3 object
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Download VCF from S3
    vcf_obj = s3.get_object(Bucket=bucket, Key=key)
    vcf_content = vcf_obj['Body'].read()

    # Send to MMSplice API
    files = {"vcf_file": ("file.vcf.gz", BytesIO(vcf_content))}
    data = {"genome": "GRCh38"}

    response = requests.post(API_URL, files=files, data=data)
    predictions = response.json()

    # Save results back to S3
    result_key = key.replace('.vcf.gz', '_predictions.json')
    s3.put_object(
        Bucket=bucket,
        Key=result_key,
        Body=json.dumps(predictions)
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {key}',
            'predictions': predictions['num_predictions']
        })
    }
```

### Example 3: Nextflow Pipeline

Integrate into Nextflow workflow:

```groovy
process MMSPLICE_PREDICT {
    publishDir "${params.outdir}/mmsplice", mode: 'copy'

    input:
    path vcf_file

    output:
    path "${vcf_file.baseName}_predictions.json"

    script:
    """
    curl -X POST https://dleader-lab--mmsplice-api-predict.modal.run \
      -F "vcf_file=@${vcf_file}" \
      -F "genome=GRCh38" \
      > ${vcf_file.baseName}_predictions.json
    """
}

workflow {
    Channel
        .fromPath(params.vcf_files)
        .set { vcf_ch }

    MMSPLICE_PREDICT(vcf_ch)
}
```

---

## Performance Considerations

### Cold Start
- First request: ~10-20 seconds (model loading)
- Subsequent requests: ~2-10 seconds

### Throughput
- Small VCF (< 100 variants): ~5-10 seconds
- Medium VCF (100-1000 variants): ~10-60 seconds
- Large VCF (> 1000 variants): ~1-5 minutes

### Optimization Tips

1. **Batch requests**: Process multiple VCFs in parallel
2. **Keep-alive**: Reuse HTTP connections
3. **Compress VCF**: Always use .vcf.gz format
4. **Filter variants**: Only send relevant variants

```python
import requests
from concurrent.futures import ThreadPoolExecutor

def predict(vcf_file):
    with open(vcf_file, "rb") as f:
        files = {"vcf_file": f}
        data = {"genome": "GRCh38"}
        return requests.post(API_URL, files=files, data=data).json()

# Process 5 VCFs in parallel
vcf_files = ["file1.vcf.gz", "file2.vcf.gz", "file3.vcf.gz", "file4.vcf.gz", "file5.vcf.gz"]

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(predict, vcf_files))
```

---

## Cost Estimation

**Modal Costs (per 1000 predictions):**
- CPU: ~$0.50 - $2.00
- Memory: ~$0.10 - $0.50
- Storage (GRCh38): $0.61/month

**AWS EC2 Egress (to Modal):**
- First 1 GB/month: Free
- Next 10 TB/month: $0.09/GB
- VCF upload cost: ~$0.01 per 100 MB

---

## Troubleshooting

### Issue: Connection timeout

```python
# Increase timeout
response = requests.post(API_URL, files=files, data=data, timeout=300)  # 5 min
```

### Issue: Large VCF fails

```bash
# Check VCF size
ls -lh variants.vcf.gz

# If > 100 MB, split it
bcftools view -r chr1 variants.vcf.gz -Oz -o chr1.vcf.gz
```

### Issue: Invalid VCF format

```bash
# Validate VCF
bcftools view variants.vcf.gz | head

# Compress and index
bgzip variants.vcf
tabix -p vcf variants.vcf.gz
```

---

## Security Best Practices

1. **Use HTTPS**: Modal endpoints are HTTPS by default ✓
2. **Add API key**: Use secured version for production
3. **Rotate keys**: Change API keys regularly
4. **IAM roles**: Use EC2 IAM roles, not hardcoded credentials
5. **VPC endpoints**: Consider AWS PrivateLink for private connectivity

---

## Complete Example Script

Save as `ec2_mmsplice.py`:

```python
#!/usr/bin/env python3
"""
MMSplice Prediction Script for AWS EC2
Usage: python3 ec2_mmsplice.py variants.vcf.gz
"""

import sys
import requests
import pandas as pd
from pathlib import Path

API_URL = "https://dleader-lab--mmsplice-api-predict.modal.run"

def predict_splicing(vcf_file, genome="GRCh38"):
    """Run MMSplice prediction"""
    print(f"Processing {vcf_file}...")

    with open(vcf_file, "rb") as f:
        files = {"vcf_file": f}
        data = {
            "genome": genome,
            "pathogenicity": "true",
            "splicing_efficiency": "true"
        }

        print("Uploading to MMSplice API...")
        response = requests.post(API_URL, files=files, data=data, timeout=300)

    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None

    predictions = response.json()

    if "error" in predictions:
        print(f"Error: {predictions['error']}")
        return None

    return predictions

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ec2_mmsplice.py <vcf_file> [genome]")
        sys.exit(1)

    vcf_file = sys.argv[1]
    genome = sys.argv[2] if len(sys.argv) > 2 else "GRCh38"

    # Run prediction
    predictions = predict_splicing(vcf_file, genome)

    if not predictions:
        sys.exit(1)

    # Display summary
    print("\n" + "="*60)
    print("Results Summary")
    print("="*60)
    print(f"Status: {predictions['status']}")
    print(f"Genome: {predictions['genome']}")
    print(f"Total predictions: {predictions['num_predictions']}")
    print(f"Strong skipping effects: {predictions['summary']['strong_skipping']}")
    print(f"Strong inclusion effects: {predictions['summary']['strong_inclusion']}")
    print(f"Genes affected: {len(predictions['summary']['genes'])}")
    print("="*60)

    # Save results
    output_file = Path(vcf_file).stem + "_predictions.csv"
    df = pd.DataFrame(predictions['predictions'])
    df.to_csv(output_file, index=False)

    print(f"\n✓ Results saved to: {output_file}")

    # Show top predictions
    print("\nTop 10 predictions by |delta_logit_psi|:")
    top_df = df.nlargest(10, 'delta_logit_psi', keep='all')[
        ['ID', 'gene_name', 'delta_logit_psi', 'pathogenicity']
    ]
    print(top_df.to_string(index=False))

if __name__ == "__main__":
    main()
```

Usage on EC2:
```bash
python3 ec2_mmsplice.py variants.vcf.gz
```

---

## Support

- **API Issues**: Check https://modal.com/docs
- **MMSplice Issues**: https://github.com/gagneurlab/MMSplice
- **AWS EC2**: https://docs.aws.amazon.com/ec2/

---

**Your API Endpoints:**
- Predict: https://dleader-lab--mmsplice-api-predict.modal.run
- Health: https://dleader-lab--mmsplice-api-health.modal.run
- Genomes: https://dleader-lab--mmsplice-api-list-genomes.modal.run
