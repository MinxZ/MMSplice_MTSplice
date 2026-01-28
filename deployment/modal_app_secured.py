"""
MMSplice API with API Key Authentication

This version adds simple API key authentication for production use.
"""

import modal
import os
from pathlib import Path
from typing import Optional, Dict
import tempfile
from fastapi import UploadFile, Header, HTTPException

# Create Modal app
app = modal.App("mmsplice-api-secured")

# API Key - Set this as a Modal secret
API_KEY = os.environ.get("MMSPLICE_API_KEY", "your-secret-key-here")

# Create a persistent volume for reference files
volume = modal.Volume.from_name("mmsplice-reference-data", create_if_missing=True)

# Define the container image
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install(
        "wget",
        "curl",
        "git",
        "build-essential",
        "zlib1g-dev",
        "libbz2-dev",
        "liblzma-dev",
        "libcurl4-openssl-dev",
        "libssl-dev",
        "samtools",
        "tabix",
    )
    .pip_install(
        "mmsplice==2.4.0",
        "fastapi[standard]==0.115.0",
        "python-multipart",
        "pydantic==2.8.2",
        "pyyaml==6.0.1",
    )
)

REFERENCE_VOLUME_PATH = "/reference_data"
GENOMES_CONFIG_PATH = f"{REFERENCE_VOLUME_PATH}/genomes_config.yaml"


def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Include 'X-API-Key' header."
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )


def load_genome_config() -> Dict:
    """Load genome configuration"""
    import yaml
    if os.path.exists(GENOMES_CONFIG_PATH):
        try:
            with open(GENOMES_CONFIG_PATH, 'r') as f:
                config = yaml.safe_load(f)
                return config if config else {"genomes": {}}
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
    return {"genomes": {}}


def get_available_genomes() -> Dict[str, Dict[str, str]]:
    """Get available genomes"""
    config = load_genome_config()
    genomes = {}
    for name in config.get("genomes", {}).keys():
        genomes[name] = {
            "gtf": f"{REFERENCE_VOLUME_PATH}/{name}.gtf",
            "fasta": f"{REFERENCE_VOLUME_PATH}/{name}.fa",
        }
    if not genomes:
        genomes = {
            "GRCh38": {
                "gtf": f"{REFERENCE_VOLUME_PATH}/GRCh38.gtf",
                "fasta": f"{REFERENCE_VOLUME_PATH}/GRCh38.fa",
            },
        }
    return genomes


@app.function(
    image=image,
    volumes={REFERENCE_VOLUME_PATH: volume},
    timeout=600,
    memory=8192,
    cpu=4.0,
)
@modal.fastapi_endpoint(method="POST")
async def predict(
    vcf_file: UploadFile,
    genome: str = "GRCh38",
    pathogenicity: bool = True,
    splicing_efficiency: bool = True,
    tissue_specific: bool = False,
    x_api_key: str = Header(None),
) -> dict:
    """
    Predict splicing effects (requires API key)

    Headers:
        X-API-Key: Your API key
    """
    # Verify API key
    verify_api_key(x_api_key)

    import pandas as pd
    from mmsplice.vcf_dataloader import SplicingVCFDataloader
    from mmsplice import MMSplice, predict_all_table
    import gzip

    AVAILABLE_GENOMES = get_available_genomes()

    if genome not in AVAILABLE_GENOMES:
        return {
            "error": f"Invalid genome '{genome}'. Available: {list(AVAILABLE_GENOMES.keys())}"
        }

    ref_files = AVAILABLE_GENOMES[genome]
    gtf_file = ref_files["gtf"]
    fasta_file = ref_files["fasta"]

    if not os.path.exists(gtf_file) or not os.path.exists(fasta_file):
        return {
            "error": f"Reference files not found. Run download_genome for {genome}"
        }

    with tempfile.TemporaryDirectory() as tmp_dir:
        vcf_content = await vcf_file.read()
        vcf_filename = vcf_file.filename or "uploaded.vcf"

        if vcf_filename.endswith('.vcf.gz'):
            vcf_path = os.path.join(tmp_dir, vcf_filename)
            with open(vcf_path, 'wb') as f:
                f.write(vcf_content)
        elif vcf_filename.endswith('.vcf'):
            vcf_path = os.path.join(tmp_dir, vcf_filename + '.gz')
            with gzip.open(vcf_path, 'wb') as f:
                f.write(vcf_content)
        else:
            return {"error": "VCF file must have .vcf or .vcf.gz extension"}

        import subprocess
        try:
            subprocess.run(['tabix', '-p', 'vcf', vcf_path], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            pass

        try:
            dl = SplicingVCFDataloader(
                gtf_file,
                fasta_file,
                vcf_path,
                tissue_specific=tissue_specific
            )
        except Exception as e:
            return {"error": f"Failed to load VCF file: {str(e)}"}

        try:
            model = MMSplice()
        except Exception as e:
            return {"error": f"Failed to load MMSplice model: {str(e)}"}

        try:
            predictions = predict_all_table(
                model,
                dl,
                pathogenicity=pathogenicity,
                splicing_efficiency=splicing_efficiency
            )
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}

        result = {
            "status": "success",
            "genome": genome,
            "num_predictions": len(predictions),
            "parameters": {
                "pathogenicity": pathogenicity,
                "splicing_efficiency": splicing_efficiency,
                "tissue_specific": tissue_specific,
            },
            "predictions": predictions.to_dict(orient="records"),
            "summary": {
                "strong_skipping": int((predictions['delta_logit_psi'] < -2).sum()),
                "strong_inclusion": int((predictions['delta_logit_psi'] > 2).sum()),
                "genes": predictions['gene_name'].unique().tolist() if 'gene_name' in predictions.columns else [],
            }
        }

        return result


@app.function(image=image, volumes={REFERENCE_VOLUME_PATH: volume})
@modal.fastapi_endpoint(method="GET")
def health() -> dict:
    """Health check (no auth required)"""
    AVAILABLE_GENOMES = get_available_genomes()
    config = load_genome_config()

    genomes_available = {}
    for genome, paths in AVAILABLE_GENOMES.items():
        genomes_available[genome] = {
            "gtf_exists": os.path.exists(paths["gtf"]),
            "fasta_exists": os.path.exists(paths["fasta"]),
        }

    return {
        "status": "healthy",
        "service": "MMSplice API (Secured)",
        "version": "2.4.0",
        "authentication": "API key required for /predict endpoint",
        "config_loaded": os.path.exists(GENOMES_CONFIG_PATH),
        "total_genomes_configured": len(config.get("genomes", {})),
        "genomes_available": genomes_available,
    }
