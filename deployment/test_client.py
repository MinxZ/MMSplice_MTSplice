#!/usr/bin/env python3
"""
Test client for MMSplice Modal API

Usage:
    python test_client.py --url YOUR_API_URL --vcf my_variants.vcf.gz
    python test_client.py --url YOUR_API_URL --vcf my_variants.vcf.gz --tissue-specific
    python test_client.py --health
"""

import argparse
import requests
import json
import sys
from pathlib import Path
import pandas as pd


def check_health(base_url: str):
    """Check API health status"""
    print("Checking API health...")
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        health = response.json()

        print("\n" + "=" * 60)
        print("API Health Status")
        print("=" * 60)
        print(f"Status: {health['status']}")
        print(f"Service: {health['service']}")
        print(f"Version: {health['version']}")
        print("\nGenomes Available:")
        for genome, status in health['genomes_available'].items():
            gtf_status = "✓" if status['gtf_exists'] else "✗"
            fasta_status = "✓" if status['fasta_exists'] else "✗"
            ready = "READY" if (status['gtf_exists'] and status['fasta_exists']) else "NOT READY"
            print(f"  {genome}: GTF {gtf_status}  FASTA {fasta_status}  [{ready}]")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def list_genomes(base_url: str):
    """List available genomes with details"""
    print("Fetching genome information...")
    try:
        response = requests.get(f"{base_url}/list-genomes")
        response.raise_for_status()
        genomes = response.json()

        print("\n" + "=" * 60)
        print("Available Reference Genomes")
        print("=" * 60)
        for genome, info in genomes.items():
            print(f"\n{genome}:")
            print(f"  GTF:   {info['gtf']}")
            if info['gtf_size_mb']:
                print(f"         Size: {info['gtf_size_mb']} MB")
            print(f"  FASTA: {info['fasta']}")
            if info['fasta_size_mb']:
                print(f"         Size: {info['fasta_size_mb']} MB")
            print(f"  Status: {'✓ READY' if info['ready'] else '✗ NOT READY'}")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"✗ Failed to list genomes: {e}")
        return False


def predict(
    base_url: str,
    vcf_file: Path,
    genome: str = "GRCh38",
    pathogenicity: bool = True,
    splicing_efficiency: bool = True,
    tissue_specific: bool = False,
    output_file: str = None
):
    """Make prediction request"""
    print(f"\nRunning MMSplice prediction on {vcf_file}...")
    print(f"Genome: {genome}")
    print(f"Pathogenicity: {pathogenicity}")
    print(f"Splicing efficiency: {splicing_efficiency}")
    print(f"Tissue-specific: {tissue_specific}")

    if not vcf_file.exists():
        print(f"✗ Error: VCF file not found: {vcf_file}")
        return False

    try:
        # Prepare request
        with open(vcf_file, 'rb') as f:
            files = {'vcf_file': f}
            data = {
                'genome': genome,
                'pathogenicity': str(pathogenicity).lower(),
                'splicing_efficiency': str(splicing_efficiency).lower(),
                'tissue_specific': str(tissue_specific).lower(),
            }

            print("\nUploading VCF and running predictions...")
            response = requests.post(f"{base_url}/predict", files=files, data=data)

        response.raise_for_status()
        result = response.json()

        # Check for errors
        if 'error' in result:
            print(f"\n✗ Prediction failed: {result['error']}")
            return False

        # Display results
        print("\n" + "=" * 60)
        print("Prediction Results")
        print("=" * 60)
        print(f"Status: {result['status']}")
        print(f"Genome: {result['genome']}")
        print(f"Number of predictions: {result['num_predictions']}")
        print("\nParameters:")
        for key, value in result['parameters'].items():
            print(f"  {key}: {value}")

        print("\nSummary:")
        summary = result['summary']
        print(f"  Strong exon skipping (Δlogit(PSI) < -2): {summary['strong_skipping']}")
        print(f"  Strong exon inclusion (Δlogit(PSI) > 2): {summary['strong_inclusion']}")
        print(f"  Genes affected: {len(summary['genes'])}")
        if len(summary['genes']) <= 10:
            print(f"    {', '.join(summary['genes'])}")
        else:
            print(f"    {', '.join(summary['genes'][:10])} ... and {len(summary['genes']) - 10} more")

        # Show sample predictions
        print("\nSample Predictions (first 5):")
        predictions_df = pd.DataFrame(result['predictions'])
        print(predictions_df[['ID', 'gene_name', 'delta_logit_psi', 'pathogenicity']].head())

        # Save results
        if output_file:
            output_path = Path(output_file)
        else:
            output_path = vcf_file.with_suffix('.predictions.csv')

        predictions_df.to_csv(output_path, index=False)
        print(f"\n✓ Full results saved to: {output_path}")

        # Also save JSON
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ JSON results saved to: {json_path}")

        print("=" * 60)
        return True

    except requests.exceptions.RequestException as e:
        print(f"\n✗ Request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Test client for MMSplice Modal API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check API health
  python test_client.py --url https://your-endpoint --health

  # List available genomes
  python test_client.py --url https://your-endpoint --list-genomes

  # Run prediction
  python test_client.py --url https://your-endpoint --vcf my_variants.vcf.gz

  # Run with tissue-specific predictions
  python test_client.py --url https://your-endpoint --vcf my_variants.vcf.gz --tissue-specific

  # Use GRCh37 instead of GRCh38
  python test_client.py --url https://your-endpoint --vcf my_variants.vcf.gz --genome GRCh37

  # Save to custom output file
  python test_client.py --url https://your-endpoint --vcf my_variants.vcf.gz -o results.csv
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='Base URL of the Modal API (e.g., https://username--mmsplice-api-predict.modal.run)'
    )

    parser.add_argument(
        '--vcf',
        type=Path,
        help='VCF file to analyze'
    )

    parser.add_argument(
        '--genome',
        default='GRCh38',
        choices=['GRCh38', 'GRCh37'],
        help='Reference genome version (default: GRCh38)'
    )

    parser.add_argument(
        '--pathogenicity',
        action='store_true',
        default=True,
        help='Include pathogenicity scores (default: True)'
    )

    parser.add_argument(
        '--no-pathogenicity',
        dest='pathogenicity',
        action='store_false',
        help='Exclude pathogenicity scores'
    )

    parser.add_argument(
        '--splicing-efficiency',
        action='store_true',
        default=True,
        help='Include splicing efficiency (default: True)'
    )

    parser.add_argument(
        '--no-splicing-efficiency',
        dest='splicing_efficiency',
        action='store_false',
        help='Exclude splicing efficiency'
    )

    parser.add_argument(
        '--tissue-specific',
        action='store_true',
        default=False,
        help='Enable tissue-specific predictions (MTSplice)'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: input_file.predictions.csv)'
    )

    parser.add_argument(
        '--health',
        action='store_true',
        help='Check API health status'
    )

    parser.add_argument(
        '--list-genomes',
        action='store_true',
        help='List available reference genomes'
    )

    args = parser.parse_args()

    # Remove trailing slash from URL
    base_url = args.url.rstrip('/')

    # Handle different modes
    if args.health:
        success = check_health(base_url)
        sys.exit(0 if success else 1)

    if args.list_genomes:
        success = list_genomes(base_url)
        sys.exit(0 if success else 1)

    if not args.vcf:
        parser.error("--vcf is required for predictions (or use --health or --list-genomes)")

    # Run prediction
    success = predict(
        base_url=base_url,
        vcf_file=args.vcf,
        genome=args.genome,
        pathogenicity=args.pathogenicity,
        splicing_efficiency=args.splicing_efficiency,
        tissue_specific=args.tissue_specific,
        output_file=args.output
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
