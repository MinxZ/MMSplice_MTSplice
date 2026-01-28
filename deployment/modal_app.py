"""
MMSplice Serverless Deployment on Modal

This Modal app provides a serverless API for MMSplice predictions.
Supports VCF file uploads and returns splicing predictions.

Usage:
    modal deploy deployment/modal_app.py

API Endpoints:
    POST /predict - Upload VCF file and get predictions
    GET /health - Health check
    GET /genomes - List available reference genomes
"""

import modal
import os
from pathlib import Path
from typing import Optional
import tempfile

# Create Modal app
app = modal.App("mmsplice-api")

# Create a persistent volume for reference files (FASTA, GTF)
volume = modal.Volume.from_name("mmsplice-reference-data", create_if_missing=True)

# Define the container image with all dependencies
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
    )
    .pip_install(
        "mmsplice==2.4.0",
        "fastapi[standard]==0.115.0",
        "python-multipart",
        "pydantic==2.8.2",
    )
)

# Volume mount path
REFERENCE_VOLUME_PATH = "/reference_data"

# Default reference files (users can add more)
AVAILABLE_GENOMES = {
    "GRCh38": {
        "gtf": f"{REFERENCE_VOLUME_PATH}/gencode.v45.annotation.gtf",
        "fasta": f"{REFERENCE_VOLUME_PATH}/Homo_sapiens.GRCh38.dna.primary_assembly.fa",
    },
    "GRCh37": {
        "gtf": f"{REFERENCE_VOLUME_PATH}/gencode.v19.annotation.gtf",
        "fasta": f"{REFERENCE_VOLUME_PATH}/Homo_sapiens.GRCh37.dna.primary_assembly.fa",
    },
}


@app.function(
    image=image,
    volumes={REFERENCE_VOLUME_PATH: volume},
    timeout=600,  # 10 minutes max
    memory=8192,  # 8GB RAM
    cpu=4.0,      # 4 CPUs
)
@modal.web_endpoint(method="POST", docs=True)
async def predict(
    vcf_file: modal.web.UploadFile,
    genome: str = "GRCh38",
    pathogenicity: bool = True,
    splicing_efficiency: bool = True,
    tissue_specific: bool = False,
) -> dict:
    """
    Predict splicing effects from uploaded VCF file.

    Args:
        vcf_file: VCF file (can be .vcf or .vcf.gz)
        genome: Reference genome version (GRCh38 or GRCh37)
        pathogenicity: Include pathogenicity scores
        splicing_efficiency: Include efficiency predictions
        tissue_specific: Enable tissue-specific predictions (MTSplice)

    Returns:
        JSON with predictions and metadata
    """
    import pandas as pd
    from mmsplice.vcf_dataloader import SplicingVCFDataloader
    from mmsplice import MMSplice, predict_all_table
    import gzip
    import json

    # Validate genome selection
    if genome not in AVAILABLE_GENOMES:
        return {
            "error": f"Invalid genome '{genome}'. Available: {list(AVAILABLE_GENOMES.keys())}"
        }

    # Get reference file paths
    ref_files = AVAILABLE_GENOMES[genome]
    gtf_file = ref_files["gtf"]
    fasta_file = ref_files["fasta"]

    # Check if reference files exist
    if not os.path.exists(gtf_file):
        return {
            "error": f"GTF file not found: {gtf_file}. Please run setup script to upload reference files."
        }
    if not os.path.exists(fasta_file):
        return {
            "error": f"FASTA file not found: {fasta_file}. Please run setup script to upload reference files."
        }

    # Create temporary directory for VCF file
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save uploaded VCF file
        vcf_content = await vcf_file.read()
        vcf_filename = vcf_file.filename or "uploaded.vcf"

        # Handle .vcf.gz or .vcf
        if vcf_filename.endswith('.vcf.gz'):
            vcf_path = os.path.join(tmp_dir, vcf_filename)
            with open(vcf_path, 'wb') as f:
                f.write(vcf_content)
        elif vcf_filename.endswith('.vcf'):
            # Compress with bgzip for cyvcf2
            vcf_path = os.path.join(tmp_dir, vcf_filename + '.gz')
            with gzip.open(vcf_path, 'wb') as f:
                f.write(vcf_content)
        else:
            return {"error": "VCF file must have .vcf or .vcf.gz extension"}

        # Index VCF file if needed
        import subprocess
        try:
            subprocess.run(['tabix', '-p', 'vcf', vcf_path], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Try to index anyway, some VCFs might work without it
            pass

        # Create dataloader
        try:
            dl = SplicingVCFDataloader(
                gtf_file,
                fasta_file,
                vcf_path,
                tissue_specific=tissue_specific
            )
        except Exception as e:
            return {"error": f"Failed to load VCF file: {str(e)}"}

        # Load MMSplice model
        try:
            model = MMSplice()
        except Exception as e:
            return {"error": f"Failed to load MMSplice model: {str(e)}"}

        # Run predictions
        try:
            predictions = predict_all_table(
                model,
                dl,
                pathogenicity=pathogenicity,
                splicing_efficiency=splicing_efficiency
            )
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}

        # Convert to JSON-serializable format
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
@modal.web_endpoint(method="GET")
def health() -> dict:
    """Health check endpoint"""
    import os

    # Check reference files
    genomes_available = {}
    for genome, paths in AVAILABLE_GENOMES.items():
        genomes_available[genome] = {
            "gtf_exists": os.path.exists(paths["gtf"]),
            "fasta_exists": os.path.exists(paths["fasta"]),
        }

    return {
        "status": "healthy",
        "service": "MMSplice API",
        "version": "2.4.0",
        "genomes_available": genomes_available,
    }


@app.function(image=image, volumes={REFERENCE_VOLUME_PATH: volume})
@modal.web_endpoint(method="GET")
def list_genomes() -> dict:
    """List available reference genomes"""
    import os

    genomes = {}
    for genome, paths in AVAILABLE_GENOMES.items():
        gtf_exists = os.path.exists(paths["gtf"])
        fasta_exists = os.path.exists(paths["fasta"])

        genomes[genome] = {
            "gtf": paths["gtf"],
            "fasta": paths["fasta"],
            "ready": gtf_exists and fasta_exists,
            "gtf_size_mb": round(os.path.getsize(paths["gtf"]) / 1024 / 1024, 2) if gtf_exists else None,
            "fasta_size_mb": round(os.path.getsize(paths["fasta"]) / 1024 / 1024, 2) if fasta_exists else None,
        }

    return genomes


@app.function(
    image=image,
    volumes={REFERENCE_VOLUME_PATH: volume},
    timeout=3600,  # 1 hour for large file downloads
)
def setup_reference_files(genome: str = "GRCh38"):
    """
    Download and setup reference files for a specific genome.
    Run this once to populate the Modal Volume with reference data.

    Args:
        genome: Genome version to download (GRCh38 or GRCh37)
    """
    import subprocess
    import os

    if genome not in AVAILABLE_GENOMES:
        print(f"Invalid genome: {genome}")
        return

    ref_files = AVAILABLE_GENOMES[genome]

    # Create directory if needed
    os.makedirs(REFERENCE_VOLUME_PATH, exist_ok=True)

    # Download GTF
    gtf_path = ref_files["gtf"]
    if not os.path.exists(gtf_path):
        print(f"Downloading GTF for {genome}...")
        if genome == "GRCh38":
            gtf_url = "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz"
        else:  # GRCh37
            gtf_url = "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gtf.gz"

        subprocess.run(["wget", "-O", gtf_path + ".gz", gtf_url], check=True)
        subprocess.run(["gunzip", gtf_path + ".gz"], check=True)
        print(f"✓ GTF downloaded: {gtf_path}")
    else:
        print(f"✓ GTF already exists: {gtf_path}")

    # Download FASTA
    fasta_path = ref_files["fasta"]
    if not os.path.exists(fasta_path):
        print(f"Downloading FASTA for {genome}...")
        if genome == "GRCh38":
            fasta_url = "ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz"
        else:  # GRCh37
            fasta_url = "ftp://ftp.ensembl.org/pub/grch37/current/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz"

        subprocess.run(["wget", "-O", fasta_path + ".gz", fasta_url], check=True)
        subprocess.run(["gunzip", fasta_path + ".gz"], check=True)
        print(f"✓ FASTA downloaded: {fasta_path}")

        # Create FASTA index
        print("Creating FASTA index...")
        subprocess.run(["samtools", "faidx", fasta_path], check=True)
        print(f"✓ FASTA indexed: {fasta_path}.fai")
    else:
        print(f"✓ FASTA already exists: {fasta_path}")

    # Commit volume changes
    volume.commit()
    print(f"\n✅ Reference files for {genome} are ready!")


# Local entrypoint for testing
@app.local_entrypoint()
def main():
    """Local test - setup reference files"""
    print("Setting up reference files for GRCh38...")
    setup_reference_files.remote(genome="GRCh38")

    print("\nChecking health...")
    health_status = health.remote()
    print(health_status)
