#!/usr/bin/env python3
"""
Local prediction script for DMD ASO design using MMSplice
"""
import os
import sys
import pandas as pd
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

def main():
    # File paths - using test data since we don't have full GRCh38 locally
    print("="*80)
    print("DMD ASO Design - MMSplice Predictions (Local)")
    print("="*80)

    base_dir = '/Users/z/work2/dleader/MMSplice_MTSplice'
    test_data_dir = os.path.join(base_dir, 'tests', 'data')
    examples_dir = os.path.join(base_dir, 'examples')

    # Using test data (chr17/BRCA1 region from hg19) for demonstration
    vcf_file = os.path.join(test_data_dir, 'test.vcf.gz')
    gtf_file = os.path.join(test_data_dir, 'test.gtf')
    fasta_file = os.path.join(test_data_dir, 'hg19.nochr.chr17.fa')

    print(f"\nInput files:")
    print(f"  VCF:   {vcf_file}")
    print(f"  GTF:   {gtf_file}")
    print(f"  FASTA: {fasta_file}")

    # Verify files exist
    for f in [vcf_file, gtf_file, fasta_file]:
        if not os.path.exists(f):
            print(f"\n✗ Error: File not found: {f}")
            return 1

    print("\n" + "-"*80)
    print("Step 1: Creating dataloader...")
    print("-"*80)

    try:
        dl = SplicingVCFDataloader(
            gtf_file,
            fasta_file,
            vcf_file,
            tissue_specific=False  # Set to True for MTSplice tissue predictions
        )
        print("✓ Dataloader created successfully")
    except Exception as e:
        print(f"✗ Failed to create dataloader: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "-"*80)
    print("Step 2: Loading MMSplice model...")
    print("-"*80)
    print("(This may download pre-trained weights on first run)")

    try:
        model = MMSplice()
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "-"*80)
    print("Step 3: Running predictions...")
    print("-"*80)
    print("(This may take a few moments)")

    try:
        predictions = predict_all_table(
            model,
            dl,
            pathogenicity=True,
            splicing_efficiency=True,
            natural_scale=False  # Keep in logit scale
        )
        print(f"✓ Predictions complete: {len(predictions)} variant-exon pairs")
    except Exception as e:
        print(f"✗ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "-"*80)
    print("Step 4: Analyzing predictions...")
    print("-"*80)

    # Display columns available
    print(f"\nAvailable columns: {list(predictions.columns)}")

    # Basic statistics
    print(f"\nPrediction Summary:")
    print(f"  Total predictions: {len(predictions)}")
    print(f"  Unique genes: {predictions['gene_name'].nunique() if 'gene_name' in predictions.columns else 'N/A'}")
    print(f"  Unique variants: {predictions['ID'].nunique() if 'ID' in predictions.columns else 'N/A'}")

    if 'delta_logit_psi' in predictions.columns:
        print(f"\n  Delta Logit PSI statistics:")
        print(f"    Mean: {predictions['delta_logit_psi'].mean():.3f}")
        print(f"    Median: {predictions['delta_logit_psi'].median():.3f}")
        print(f"    Min: {predictions['delta_logit_psi'].min():.3f}")
        print(f"    Max: {predictions['delta_logit_psi'].max():.3f}")
        print(f"\n  Strong exon skipping (delta_logit_psi < -2): {(predictions['delta_logit_psi'] < -2).sum()}")
        print(f"  Strong exon inclusion (delta_logit_psi > 2): {(predictions['delta_logit_psi'] > 2).sum()}")

    # Sort by delta_logit_psi
    if 'delta_logit_psi' in predictions.columns:
        predictions_sorted = predictions.sort_values('delta_logit_psi')

        print(f"\n" + "="*80)
        print("Top 10 Exon Skipping Candidates (most negative delta_logit_psi):")
        print("="*80)

        columns_to_show = ['ID', 'gene_name', 'exon_id', 'delta_logit_psi']
        if 'pathogenicity' in predictions.columns:
            columns_to_show.append('pathogenicity')
        if 'delta_psi5' in predictions.columns:
            columns_to_show.append('delta_psi5')
        if 'delta_psi3' in predictions.columns:
            columns_to_show.append('delta_psi3')

        available_columns = [c for c in columns_to_show if c in predictions.columns]
        print(predictions_sorted[available_columns].head(10).to_string())

        print(f"\n" + "="*80)
        print("Top 10 Exon Inclusion Candidates (most positive delta_logit_psi):")
        print("="*80)
        print(predictions_sorted[available_columns].tail(10).to_string())

    # Save results
    output_file = os.path.join(examples_dir, 'test_predictions_local.csv')
    predictions.to_csv(output_file, index=False)
    print(f"\n" + "-"*80)
    print(f"✓ Full predictions saved to: {output_file}")
    print("-"*80)

    print("\n" + "="*80)
    print("✅ Prediction pipeline completed successfully!")
    print("="*80)

    print("\n📝 Note: This demo used test data (chr17/BRCA1). For DMD exon 51 predictions,")
    print("   you would need full GRCh38 reference files (GTF + FASTA) which are ~4GB.")
    print("   The Modal API has these files cached and can process DMD variants once")
    print("   the API issues are resolved.")

    return 0

if __name__ == '__main__':
    sys.exit(main())
