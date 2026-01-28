#!/usr/bin/env python
"""
Test local MMSplice predictions with DMD ASO design VCF
This script verifies that your local installation works correctly.
"""

import os
import sys
import json
from pathlib import Path

def check_files(gtf_file, fasta_file, vcf_file):
    """Check if required files exist"""
    print("\n" + "="*80)
    print("Checking Required Files")
    print("="*80)

    all_exist = True

    files = {
        "GTF": gtf_file,
        "FASTA": fasta_file,
        "FASTA Index": fasta_file + ".fai",
        "VCF": vcf_file,
    }

    for name, filepath in files.items():
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / 1024 / 1024
            print(f"✓ {name:15s} {filepath} ({size_mb:.1f} MB)")
        else:
            print(f"✗ {name:15s} {filepath} - NOT FOUND")
            all_exist = False

    if not all_exist:
        print("\n❌ Missing required files!")
        print("\nTo download reference files, run:")
        print("  bash download_references.sh GRCh38")
        return False

    return True


def run_predictions(gtf_file, fasta_file, vcf_file, genome="GRCh38"):
    """Run MMSplice predictions"""
    print("\n" + "="*80)
    print(f"Running MMSplice Predictions - {genome}")
    print("="*80)

    try:
        from mmsplice.vcf_dataloader import SplicingVCFDataloader
        from mmsplice import MMSplice, predict_all_table
        import pandas as pd
    except ImportError as e:
        print(f"\n❌ Import failed: {e}")
        print("\nPlease ensure MMSplice is installed:")
        print("  conda activate mmsplice")
        print("  python test_installation.py")
        return None

    try:
        # Create dataloader
        print(f"\n1. Creating dataloader...")
        print(f"   GTF:   {gtf_file}")
        print(f"   FASTA: {fasta_file}")
        print(f"   VCF:   {vcf_file}")

        dl = SplicingVCFDataloader(
            gtf_file,
            fasta_file,
            vcf_file,
            tissue_specific=False
        )
        print(f"   ✓ Dataloader created")

        # Load model
        print(f"\n2. Loading MMSplice model...")
        model = MMSplice()
        print(f"   ✓ Model loaded")

        # Run predictions
        print(f"\n3. Running predictions...")
        print(f"   This may take 1-2 minutes...")

        predictions = predict_all_table(
            model,
            dl,
            pathogenicity=True,
            splicing_efficiency=True
        )

        print(f"   ✓ Predictions complete: {len(predictions)} variants")

        return predictions

    except Exception as e:
        print(f"\n❌ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_results(predictions, vcf_file):
    """Analyze and display prediction results"""
    print("\n" + "="*80)
    print("Analysis Results")
    print("="*80)

    # Summary statistics
    print(f"\nTotal variants analyzed: {len(predictions)}")

    if 'delta_logit_psi' in predictions.columns:
        strong_skipping = (predictions['delta_logit_psi'] < -2).sum()
        moderate_skipping = ((predictions['delta_logit_psi'] >= -2) &
                            (predictions['delta_logit_psi'] < -0.5)).sum()
        neutral = ((predictions['delta_logit_psi'] >= -0.5) &
                   (predictions['delta_logit_psi'] <= 0.5)).sum()
        moderate_inclusion = ((predictions['delta_logit_psi'] > 0.5) &
                             (predictions['delta_logit_psi'] <= 2)).sum()
        strong_inclusion = (predictions['delta_logit_psi'] > 2).sum()

        print(f"\nSplicing Effect Categories:")
        print(f"  Strong exon skipping (Δlogit(Ψ) < -2):        {strong_skipping:3d} variants")
        print(f"  Moderate exon skipping (-2 ≤ Δlogit(Ψ) < -0.5): {moderate_skipping:3d} variants")
        print(f"  Neutral (-0.5 ≤ Δlogit(Ψ) ≤ 0.5):            {neutral:3d} variants")
        print(f"  Moderate inclusion (0.5 < Δlogit(Ψ) ≤ 2):     {moderate_inclusion:3d} variants")
        print(f"  Strong exon inclusion (Δlogit(Ψ) > 2):        {strong_inclusion:3d} variants")

    # Gene information
    if 'gene_name' in predictions.columns:
        genes = predictions['gene_name'].unique()
        print(f"\nGenes affected: {', '.join(genes)}")

    # Detailed results
    print("\n" + "-"*80)
    print("Detailed Predictions (sorted by splicing effect)")
    print("-"*80)

    # Select relevant columns
    display_cols = []
    for col in ['ID', 'gene_name', 'exon_id', 'delta_logit_psi',
                'pathogenicity', 'efficiency', 'ref', 'alt']:
        if col in predictions.columns:
            display_cols.append(col)

    # Sort by delta_logit_psi (most negative = strongest skipping)
    if 'delta_logit_psi' in predictions.columns:
        sorted_preds = predictions.sort_values('delta_logit_psi')
    else:
        sorted_preds = predictions

    # Display table
    pd_options = {
        'display.max_rows': None,
        'display.max_columns': None,
        'display.width': None,
        'display.max_colwidth': 40
    }

    import pandas as pd
    with pd.option_context(*[item for pair in pd_options.items() for item in pair]):
        print(sorted_preds[display_cols].to_string(index=False))

    # ASO-specific interpretation (if this is DMD ASO VCF)
    if 'dmd_aso_design' in vcf_file.lower() or 'DMD' in str(predictions.get('gene_name', '')):
        print("\n" + "="*80)
        print("ASO Design Interpretation (DMD Exon 51 Skipping)")
        print("="*80)

        print("\nGoal: Identify variants that cause STRONG EXON SKIPPING")
        print("Target: Δlogit(Ψ) < -2 (strong skipping effect)")
        print("\nInterpretation:")
        print("  • Negative Δlogit(Ψ): Promotes exon skipping (DESIRED for ASO)")
        print("  • Positive Δlogit(Ψ): Promotes exon inclusion (undesired)")
        print("  • |Δlogit(Ψ)| > 2: Strong effect")

        if 'delta_logit_psi' in predictions.columns:
            best_candidates = sorted_preds[sorted_preds['delta_logit_psi'] < -2]

            if len(best_candidates) > 0:
                print(f"\n✅ Found {len(best_candidates)} strong ASO candidate(s):")
                for idx, row in best_candidates.iterrows():
                    variant_id = row.get('ID', 'N/A')
                    delta = row.get('delta_logit_psi', 0)
                    patho = row.get('pathogenicity', 'N/A')
                    print(f"\n  • {variant_id}")
                    print(f"    Δlogit(Ψ) = {delta:.3f} (strong skipping)")
                    print(f"    Pathogenicity = {patho:.3f}")
                    print(f"    Recommendation: EXCELLENT candidate for ASO-induced exon skipping")
            else:
                print(f"\n⚠ No variants with strong skipping effect (Δlogit(Ψ) < -2)")
                print("  Consider:")
                print("  • Testing different variant positions")
                print("  • Targeting acceptor vs donor splice sites")
                print("  • Checking ESE/ESS motif regions")


def save_results(predictions, output_file):
    """Save predictions to JSON file"""
    print("\n" + "="*80)
    print("Saving Results")
    print("="*80)

    try:
        # Convert to JSON-serializable format
        result = {
            "status": "success",
            "num_predictions": len(predictions),
            "predictions": predictions.to_dict(orient="records")
        }

        # Add summary statistics
        if 'delta_logit_psi' in predictions.columns:
            result["summary"] = {
                "strong_skipping": int((predictions['delta_logit_psi'] < -2).sum()),
                "strong_inclusion": int((predictions['delta_logit_psi'] > 2).sum()),
                "mean_delta_logit_psi": float(predictions['delta_logit_psi'].mean()),
                "min_delta_logit_psi": float(predictions['delta_logit_psi'].min()),
                "max_delta_logit_psi": float(predictions['delta_logit_psi'].max()),
            }

        if 'gene_name' in predictions.columns:
            result["summary"]["genes"] = predictions['gene_name'].unique().tolist()

        # Save to file
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"✓ Results saved to: {output_file}")

        # Also save as CSV
        csv_file = output_file.replace('.json', '.csv')
        predictions.to_csv(csv_file, index=False)
        print(f"✓ Results saved to: {csv_file}")

    except Exception as e:
        print(f"⚠ Warning: Could not save results: {e}")


def main():
    """Main function"""
    print("="*80)
    print("MMSplice Local Prediction Test")
    print("="*80)

    # Default file paths
    genome = os.environ.get("GENOME", "GRCh38")
    gtf_file = f"reference_data/{genome}.gtf"
    fasta_file = f"reference_data/{genome}.fa"
    vcf_file = "examples/dmd_aso_design.vcf"
    output_file = "examples/dmd_predictions_local.json"

    # Allow command line override
    if len(sys.argv) > 1:
        vcf_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    print(f"\nGenome: {genome}")
    print(f"VCF:    {vcf_file}")
    print(f"Output: {output_file}")

    # Check files
    if not check_files(gtf_file, fasta_file, vcf_file):
        sys.exit(1)

    # Run predictions
    predictions = run_predictions(gtf_file, fasta_file, vcf_file, genome)
    if predictions is None:
        sys.exit(1)

    # Analyze results
    analyze_results(predictions, vcf_file)

    # Save results
    save_results(predictions, output_file)

    print("\n" + "="*80)
    print("✅ Test Complete!")
    print("="*80)
    print("\nNext steps:")
    print("  • Review results in:", output_file)
    print("  • Check CSV for analysis:", output_file.replace('.json', '.csv'))
    print("  • Compare with Modal API results")
    print("  • See docs/MMSplice_MTSplice_for_ASO_Design.md for ASO design workflow")
    print("")


if __name__ == "__main__":
    main()
