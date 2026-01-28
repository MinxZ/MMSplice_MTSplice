#!/usr/bin/env python3
"""
Test Modal API with DMD ASO design VCF
"""
import requests
import json
import time

# Read VCF content
with open('dmd_aso_design.vcf', 'r') as f:
    vcf_content = f.read()

print("="*80)
print("Testing Modal API with DMD ASO Design VCF")
print("="*80)

# Prepare request
api_url = "https://dleader-lab--mmsplice-api-predict.modal.run"
payload = {
    "vcf_content": vcf_content,
    "genome": "GRCh38",
    "pathogenicity": True,
    "splicing_efficiency": True,
    "tissue_specific": False
}

print(f"\nAPI URL: {api_url}")
print(f"VCF size: {len(vcf_content)} bytes")
variant_count = vcf_content.count('X\t31')
print(f"Number of variants: {variant_count}")

# Send request
print(f"\nSending request... (may take 2-3 minutes for cold start)")
start_time = time.time()

try:
    response = requests.post(
        api_url,
        json=payload,
        timeout=600  # 10 minute timeout
    )

    elapsed = time.time() - start_time
    print(f"Response received in {elapsed:.1f} seconds")
    print(f"HTTP Status: {response.status_code}")

    # Save response
    with open('dmd_predictions.json', 'w') as f:
        json.dump(response.json(), f, indent=2)

    # Display results
    if response.status_code == 200:
        data = response.json()

        if data.get('status') == 'success':
            print(f"\n✅ SUCCESS!")
            print(f"   Genome: {data.get('genome')}")
            print(f"   Predictions: {data.get('num_predictions')}")
            print(f"   Strong skipping: {data['summary']['strong_skipping']}")
            print(f"   Strong inclusion: {data['summary']['strong_inclusion']}")
            print(f"   Genes: {', '.join(data['summary']['genes'])}")

            # Show top predictions
            predictions = data.get('predictions', [])
            if predictions:
                print(f"\n{'-'*80}")
                print("Top 10 Predictions (sorted by delta_logit_psi):")
                print(f"{'-'*80}")

                sorted_preds = sorted(predictions, key=lambda x: x.get('delta_logit_psi', 0))
                for i, pred in enumerate(sorted_preds[:10], 1):
                    print(f"{i:2d}. {pred.get('ID', 'N/A'):30s} "
                          f"delta_logit_psi={pred.get('delta_logit_psi', 0):7.3f}  "
                          f"pathogenicity={pred.get('pathogenicity', 0):.3f}")

            print(f"\n✓ Full predictions saved to: dmd_predictions.json")
        else:
            print(f"\n❌ API Error:")
            print(json.dumps(data, indent=2))
    else:
        print(f"\n❌ HTTP Error {response.status_code}:")
        print(response.text[:500])

except requests.exceptions.Timeout:
    print(f"\n❌ Request timed out after 10 minutes")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
