"""
Python client library for MMSplice Modal API

Usage:
    from mmsplice_client import MMSpliceClient

    client = MMSpliceClient(api_url="https://your-endpoint.modal.run")
    results = client.predict("variants.vcf.gz")
    results.to_csv("predictions.csv")
"""

import requests
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd


class MMSpliceClient:
    """Client for MMSplice Modal API"""

    def __init__(self, api_url: str, timeout: int = 300):
        """
        Initialize MMSplice API client

        Args:
            api_url: Base URL of the Modal API predict endpoint
            timeout: Request timeout in seconds (default: 300)
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout

    def predict(
        self,
        vcf_file: str | Path,
        genome: str = "GRCh38",
        pathogenicity: bool = True,
        splicing_efficiency: bool = True,
        tissue_specific: bool = False,
    ) -> pd.DataFrame:
        """
        Run MMSplice predictions on a VCF file

        Args:
            vcf_file: Path to VCF file (.vcf or .vcf.gz)
            genome: Reference genome (GRCh38 or GRCh37)
            pathogenicity: Include pathogenicity scores
            splicing_efficiency: Include splicing efficiency
            tissue_specific: Enable tissue-specific predictions

        Returns:
            DataFrame with predictions

        Raises:
            FileNotFoundError: If VCF file doesn't exist
            RuntimeError: If prediction fails
        """
        vcf_path = Path(vcf_file)
        if not vcf_path.exists():
            raise FileNotFoundError(f"VCF file not found: {vcf_file}")

        # Prepare request
        with open(vcf_path, 'rb') as f:
            files = {'vcf_file': f}
            data = {
                'genome': genome,
                'pathogenicity': str(pathogenicity).lower(),
                'splicing_efficiency': str(splicing_efficiency).lower(),
                'tissue_specific': str(tissue_specific).lower(),
            }

            response = requests.post(
                self.api_url,
                files=files,
                data=data,
                timeout=self.timeout
            )

        response.raise_for_status()
        result = response.json()

        if 'error' in result:
            raise RuntimeError(f"Prediction failed: {result['error']}")

        # Convert to DataFrame
        df = pd.DataFrame(result['predictions'])
        return df

    def predict_batch(
        self,
        vcf_files: list[str | Path],
        genome: str = "GRCh38",
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Run predictions on multiple VCF files

        Args:
            vcf_files: List of VCF file paths
            genome: Reference genome
            **kwargs: Additional arguments for predict()

        Returns:
            Dictionary mapping file names to DataFrames
        """
        results = {}
        for vcf_file in vcf_files:
            vcf_path = Path(vcf_file)
            print(f"Processing {vcf_path.name}...")
            try:
                df = self.predict(vcf_file, genome=genome, **kwargs)
                results[vcf_path.name] = df
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                results[vcf_path.name] = None

        return results

    def health(self) -> Dict[str, Any]:
        """
        Check API health status

        Returns:
            Health status dictionary
        """
        # Extract base URL by removing /predict
        base_url = self.api_url.replace('/predict', '')
        response = requests.get(f"{base_url}/health", timeout=10)
        response.raise_for_status()
        return response.json()

    def list_genomes(self) -> Dict[str, Any]:
        """
        List available reference genomes

        Returns:
            Dictionary of available genomes
        """
        base_url = self.api_url.replace('/predict', '')
        response = requests.get(f"{base_url}/list-genomes", timeout=10)
        response.raise_for_status()
        return response.json()


class PredictionResult:
    """Helper class for working with prediction results"""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def filter_strong_effects(self, threshold: float = 2.0) -> pd.DataFrame:
        """Get variants with strong splicing effects"""
        return self.df[abs(self.df['delta_logit_psi']) > threshold]

    def filter_pathogenic(self, threshold: float = 0.8) -> pd.DataFrame:
        """Get likely pathogenic variants"""
        return self.df[self.df['pathogenicity'] > threshold]

    def by_gene(self, gene_name: str) -> pd.DataFrame:
        """Filter by gene name"""
        return self.df[self.df['gene_name'] == gene_name]

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            'total_predictions': len(self.df),
            'genes': self.df['gene_name'].nunique(),
            'strong_skipping': (self.df['delta_logit_psi'] < -2).sum(),
            'strong_inclusion': (self.df['delta_logit_psi'] > 2).sum(),
            'mean_pathogenicity': self.df['pathogenicity'].mean(),
            'affected_genes': self.df['gene_name'].unique().tolist(),
        }


# Convenience functions
def predict_vcf(
    api_url: str,
    vcf_file: str | Path,
    **kwargs
) -> pd.DataFrame:
    """
    Quick prediction function

    Args:
        api_url: Modal API URL
        vcf_file: VCF file path
        **kwargs: Additional arguments for predict()

    Returns:
        DataFrame with predictions
    """
    client = MMSpliceClient(api_url)
    return client.predict(vcf_file, **kwargs)


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python mmsplice_client.py API_URL VCF_FILE [GENOME]")
        sys.exit(1)

    api_url = sys.argv[1]
    vcf_file = sys.argv[2]
    genome = sys.argv[3] if len(sys.argv) > 3 else "GRCh38"

    # Create client
    client = MMSpliceClient(api_url)

    # Check health
    print("Checking API health...")
    health = client.health()
    print(f"Status: {health['status']}")

    # Run prediction
    print(f"\nRunning prediction on {vcf_file}...")
    df = client.predict(vcf_file, genome=genome)

    # Show results
    print(f"\n{len(df)} predictions made")
    print("\nSample predictions:")
    print(df[['ID', 'gene_name', 'delta_logit_psi', 'pathogenicity']].head())

    # Save
    output_file = Path(vcf_file).with_suffix('.predictions.csv')
    df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")
