#!/usr/bin/env python3
"""
Quick test of MMSplice with the included test data
Demonstrates that you only need 3 input files: VCF, GTF, FASTA
"""

from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table
import os

# Get the test data directory
script_dir = os.path.dirname(os.path.abspath(__file__))
test_data = os.path.join(os.path.dirname(script_dir), 'tests', 'data')

print("=== MMSplice Quick Test ===")
print("\n✓ Using ONLY these 3 input files:\n")

# 1. VCF file (variants)
vcf_file = os.path.join(test_data, 'test.vcf.gz')
print(f"1. VCF:   {vcf_file}")
print(f"   Size:  {os.path.getsize(vcf_file) / 1024:.1f} KB")

# 2. GTF file (gene annotations)
gtf_file = os.path.join(test_data, 'test.gtf')
print(f"\n2. GTF:   {gtf_file}")
print(f"   Size:  {os.path.getsize(gtf_file) / 1024:.1f} KB")

# 3. FASTA file (reference genome)
fasta_file = os.path.join(test_data, 'hg19.nochr.chr17.fa')
print(f"\n3. FASTA: {fasta_file}")
print(f"   Size:  {os.path.getsize(fasta_file) / (1024*1024):.1f} MB")

print("\n" + "="*50)
print("Running MMSplice predictions...")
print("="*50 + "\n")

# Create data loader - ONLY need those 3 files!
dl = SplicingVCFDataloader(
    gtf_file,
    fasta_file,
    vcf_file
)

# Load model (downloads pre-trained weights automatically on first run)
print("Loading MMSplice model...")
model = MMSplice()
print("✓ Model loaded (pre-trained weights downloaded if needed)\n")

# Run predictions
print("Running predictions...")
predictions = predict_all_table(
    model,
    dl,
    pathogenicity=True,      # Add pathogenicity scores
    splicing_efficiency=True # Add efficiency scores
)
print(f"✓ Predictions complete!\n")

# Show results
print("="*50)
print("Results Summary")
print("="*50)
print(f"Total predictions: {len(predictions)}")
print(f"\nColumns in output: {list(predictions.columns)}\n")

# Show first few predictions
print("First 3 predictions:")
print(predictions[['ID', 'gene_name', 'delta_logit_psi', 'pathogenicity']].head(3))

# Count strong effects
strong_skipping = (predictions['delta_logit_psi'] < -2).sum()
strong_inclusion = (predictions['delta_logit_psi'] > 2).sum()

print(f"\n✓ Strong exon skipping effects (delta_logit_psi < -2): {strong_skipping}")
print(f"✓ Strong exon inclusion effects (delta_logit_psi > 2): {strong_inclusion}")

# Save results
output_file = os.path.join(script_dir, 'test_predictions.csv')
predictions.to_csv(output_file, index=False)
print(f"\n✓ Results saved to: {output_file}")

print("\n" + "="*50)
print("✅ SUCCESS - MMSplice works with just 3 files!")
print("="*50)
print("\nNo other inputs needed:")
print("  ✓ Pre-trained models: Downloaded automatically")
print("  ✓ FASTA index (.fai): Created automatically")
print("  ✓ Reference data: Built-in")
