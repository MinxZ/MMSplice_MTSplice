"""
MMSplice Serverless Deployment on Modal - v2 with Custom Genome Support

This Modal app provides a serverless API for MMSplice predictions.
Supports VCF file uploads and any custom genome via genomes_config.yaml.

Usage:
    # Deploy
    modal deploy deployment/modal_app_v2.py

    # Setup any genome from config
    modal run deployment/modal_app_v2.py::download_genome --genome GRCh38
    modal run deployment/modal_app_v2.py::download_genome --genome GRCm39
    modal run deployment/modal_app_v2.py::download_genome --genome MyCustomGenome

    # Add custom genome on-the-fly
    modal run deployment/modal_app_v2.py::add_custom_genome \
        --name MyGenome \
        --gtf-url "https://example.com/annotations.gtf.gz" \
        --fasta-url "https://example.com/genome.fa.gz" \
        --description "My custom genome"

API Endpoints:
    POST /predict - Upload VCF file and get predictions
    GET /health - Health check
    GET /genomes - List available reference genomes
"""

import modal
import os
from pathlib import Path
from typing import Optional, Dict
import tempfile
from pydantic import BaseModel

# Request model for predict endpoint
class PredictRequest(BaseModel):
    vcf_content: str
    genome: str = "GRCh38"
    pathogenicity: bool = True
    splicing_efficiency: bool = True
    tissue_specific: bool = False

# Create Modal app
app = modal.App("mmsplice-api")

# Create a persistent volume for reference files (FASTA, GTF)
volume = modal.Volume.from_name("mmsplice-reference-data", create_if_missing=True)

# Define the container image with all dependencies
# Key constraint: cyvcf2 0.30.15 (binary) requires numpy 1.23.x (96-byte dtype)
# TensorFlow 2.16+ requires numpy 1.26+ (has dtypes attribute)
# Solution: Use TensorFlow 2.13 which is compatible with numpy 1.23.5
# Problem: mmsplice requires 'tensorflow' with no version constraint, pip upgrades to latest
# Fix: Force downgrade tensorflow and numpy AFTER all packages are installed
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
    # Install numpy first
    .pip_install("numpy==1.23.5")
    # Install all packages (tensorflow will be latest 2.20+)
    .pip_install(
        "fastapi[standard]==0.115.0",
        "python-multipart",
        "pydantic==2.8.2",
        "pyyaml==6.0.1",
        "mmsplice==2.4.0",  # Installs tensorflow 2.20+ as dependency
    )
    # Force downgrade to compatible versions AFTER mmsplice installation
    .run_commands(
        "pip install tensorflow==2.13.1 --force-reinstall",  # Downgrade tensorflow
        "pip install numpy==1.23.5 --force-reinstall --no-deps"  # Force numpy for cyvcf2
    )
)

# Volume mount path
REFERENCE_VOLUME_PATH = "/reference_data"
GENOMES_CONFIG_PATH = f"{REFERENCE_VOLUME_PATH}/genomes_config.yaml"


def load_genome_config() -> Dict:
    """Load genome configuration from YAML file or return default"""
    import yaml

    # Try to load from volume
    if os.path.exists(GENOMES_CONFIG_PATH):
        try:
            with open(GENOMES_CONFIG_PATH, 'r') as f:
                config = yaml.safe_load(f)
                return config if config else {"genomes": {}}
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")

    # Return empty default
    return {"genomes": {}}


def get_available_genomes() -> Dict[str, Dict[str, str]]:
    """Get available genomes and their local file paths"""
    config = load_genome_config()
    genomes = {}

    for name in config.get("genomes", {}).keys():
        genomes[name] = {
            "gtf": f"{REFERENCE_VOLUME_PATH}/{name}.gtf",
            "fasta": f"{REFERENCE_VOLUME_PATH}/{name}.fa",
        }

    # Add defaults if config is empty
    if not genomes:
        genomes = {
            "GRCh38": {
                "gtf": f"{REFERENCE_VOLUME_PATH}/GRCh38.gtf",
                "fasta": f"{REFERENCE_VOLUME_PATH}/GRCh38.fa",
            },
            "GRCh37": {
                "gtf": f"{REFERENCE_VOLUME_PATH}/GRCh37.gtf",
                "fasta": f"{REFERENCE_VOLUME_PATH}/GRCh37.fa",
            },
        }

    return genomes


@app.function(
    image=image,
    volumes={REFERENCE_VOLUME_PATH: volume},
    timeout=1200,  # Increased from 600s
    memory=16384,  # Increased from 8GB to 16GB
    cpu=8.0,       # Increased from 4 to 8 cores
)
@modal.fastapi_endpoint(method="POST")
async def predict(request: PredictRequest) -> dict:
    """
    Predict splicing effects from VCF content (passed as text).

    Args:
        request: PredictRequest containing VCF content and parameters

    Returns:
        JSON with predictions and metadata

    Note: For files > 1MB, use S3 URL instead (coming soon)
    """
    import pandas as pd
    from mmsplice.vcf_dataloader import SplicingVCFDataloader
    from mmsplice import MMSplice, predict_all_table
    import gzip
    import traceback

    # Extract parameters from request
    vcf_content = request.vcf_content
    genome = request.genome
    pathogenicity = request.pathogenicity
    splicing_efficiency = request.splicing_efficiency
    tissue_specific = request.tissue_specific

    # Top-level error handling to catch any unexpected errors
    try:
        print(f"[INFO] Received prediction request for genome: {genome}")
        print(f"[INFO] VCF content size: {len(vcf_content)} bytes")

        AVAILABLE_GENOMES = get_available_genomes()
        print(f"[INFO] Available genomes: {list(AVAILABLE_GENOMES.keys())}")

        # Validate genome selection
        if genome not in AVAILABLE_GENOMES:
            return {
                "error": f"Invalid genome '{genome}'. Available: {list(AVAILABLE_GENOMES.keys())}. "
                         f"Run 'modal run deployment/modal_app_v2.py::download_genome --genome {genome}' to add it."
            }

        # Get reference file paths
        ref_files = AVAILABLE_GENOMES[genome]
        gtf_file = ref_files["gtf"]
        fasta_file = ref_files["fasta"]
        print(f"[INFO] GTF file: {gtf_file}")
        print(f"[INFO] FASTA file: {fasta_file}")

        # Check if reference files exist
        if not os.path.exists(gtf_file):
            return {
                "error": f"GTF file not found: {gtf_file}. Run: modal run deployment/modal_app_v2.py::download_genome --genome {genome}"
            }
        if not os.path.exists(fasta_file):
            return {
                "error": f"FASTA file not found: {fasta_file}. Run: modal run deployment/modal_app_v2.py::download_genome --genome {genome}"
            }
        print("[INFO] Reference files validated")

        # Create temporary directory for VCF file
        with tempfile.TemporaryDirectory() as tmp_dir:
            print(f"[INFO] Created temp directory: {tmp_dir}")

            # Save VCF content to file and compress
            vcf_path = os.path.join(tmp_dir, "input.vcf.gz")
            with gzip.open(vcf_path, 'wt') as f:
                f.write(vcf_content)
            print(f"[INFO] Saved and compressed VCF to: {vcf_path}")

            # Index VCF file if needed
            print("[INFO] Attempting to index VCF with tabix...")
            import subprocess
            try:
                result = subprocess.run(['tabix', '-p', 'vcf', vcf_path], check=True, capture_output=True)
                print(f"[INFO] Tabix indexing successful")
            except subprocess.CalledProcessError as e:
                print(f"[WARN] Tabix indexing failed (this may be okay): {e}")
                pass

            # Create dataloader
            print("[INFO] Creating SplicingVCFDataloader...")
            try:
                dl = SplicingVCFDataloader(
                    gtf_file,
                    fasta_file,
                    vcf_path,
                    tissue_specific=tissue_specific
                )
                print(f"[INFO] Dataloader created successfully")
            except Exception as e:
                error_msg = f"Failed to load VCF file: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] Traceback:\n{error_traceback}")
                return {"error": error_msg, "traceback": error_traceback}

            # Load MMSplice model
            print("[INFO] Loading MMSplice model...")
            try:
                model = MMSplice()
                print("[INFO] MMSplice model loaded")
            except Exception as e:
                error_msg = f"Failed to load MMSplice model: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] Traceback:\n{error_traceback}")
                return {"error": error_msg, "traceback": error_traceback}

            # Run predictions
            print("[INFO] Running predictions...")
            try:
                predictions = predict_all_table(
                    model,
                    dl,
                    pathogenicity=pathogenicity,
                    splicing_efficiency=splicing_efficiency
                )
                print(f"[INFO] Predictions complete: {len(predictions)} rows")
            except Exception as e:
                error_msg = f"Prediction failed: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] Traceback:\n{error_traceback}")
                return {"error": error_msg, "traceback": error_traceback}

        # Convert to JSON-serializable format
        print(f"[INFO] Predictions complete: {len(predictions)} rows")
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

    except Exception as e:
        # Catch any unhandled exceptions
        error_msg = f"Unexpected error: {str(e)}"
        error_traceback = traceback.format_exc()
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Traceback:\n{error_traceback}")
        return {
            "error": error_msg,
            "traceback": error_traceback,
            "type": type(e).__name__
        }


@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
async def test_vcf_text(vcf_content: str) -> dict:
    """Test VCF text input endpoint"""
    try:
        return {
            "status": "success",
            "size": len(vcf_content),
            "lines": vcf_content.count('\n'),
            "first_200_chars": vcf_content[:200]
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.function(image=image, volumes={REFERENCE_VOLUME_PATH: volume})
@modal.fastapi_endpoint(method="GET")
def health() -> dict:
    """Health check endpoint"""
    AVAILABLE_GENOMES = get_available_genomes()

    # Check reference files
    genomes_available = {}
    for genome, paths in AVAILABLE_GENOMES.items():
        genomes_available[genome] = {
            "gtf_exists": os.path.exists(paths["gtf"]),
            "fasta_exists": os.path.exists(paths["fasta"]),
        }

    config = load_genome_config()

    return {
        "status": "healthy",
        "service": "MMSplice API v2 (Custom Genome Support)",
        "version": "2.4.0",
        "config_loaded": os.path.exists(GENOMES_CONFIG_PATH),
        "total_genomes_configured": len(config.get("genomes", {})),
        "genomes_available": genomes_available,
    }


@app.function(image=image, volumes={REFERENCE_VOLUME_PATH: volume})
@modal.fastapi_endpoint(method="GET")
def list_genomes() -> dict:
    """List available reference genomes with details"""
    AVAILABLE_GENOMES = get_available_genomes()
    config = load_genome_config()

    genomes = {}
    for genome, paths in AVAILABLE_GENOMES.items():
        gtf_exists = os.path.exists(paths["gtf"])
        fasta_exists = os.path.exists(paths["fasta"])

        genome_info = config.get("genomes", {}).get(genome, {})

        genomes[genome] = {
            "gtf": paths["gtf"],
            "fasta": paths["fasta"],
            "ready": gtf_exists and fasta_exists,
            "gtf_size_mb": round(os.path.getsize(paths["gtf"]) / 1024 / 1024, 2) if gtf_exists else None,
            "fasta_size_mb": round(os.path.getsize(paths["fasta"]) / 1024 / 1024, 2) if fasta_exists else None,
            "description": genome_info.get("description", "No description"),
            "gtf_url": genome_info.get("gtf_url", "Unknown"),
            "fasta_url": genome_info.get("fasta_url", "Unknown"),
        }

    return genomes


@app.function(
    image=image,
    volumes={REFERENCE_VOLUME_PATH: volume},
    timeout=3600,  # 1 hour for large file downloads
)
def download_genome(genome: str):
    """
    Download and setup reference files for any genome from genomes_config.yaml

    Args:
        genome: Genome name from genomes_config.yaml (e.g., GRCh38, GRCm39, etc.)

    Usage:
        modal run deployment/modal_app_v2.py::download_genome --genome GRCh38
        modal run deployment/modal_app_v2.py::download_genome --genome GRCm39
    """
    import subprocess
    import yaml

    # First, upload config if not present
    if not os.path.exists(GENOMES_CONFIG_PATH):
        print("Config not found in volume. Creating default config...")
        import yaml

        # Create default config with pre-configured genomes
        default_config = {
            "genomes": {
                "GRCh38": {
                    "gtf_url": "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz",
                    "fasta_url": "ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz",
                    "description": "Human genome GRCh38/hg38 (GENCODE v45)"
                },
                "GRCh37": {
                    "gtf_url": "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gtf.gz",
                    "fasta_url": "ftp://ftp.ensembl.org/pub/grch37/current/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz",
                    "description": "Human genome GRCh37/hg19 (GENCODE v19)"
                },
                "GRCm39": {
                    "gtf_url": "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M33/gencode.vM33.annotation.gtf.gz",
                    "fasta_url": "ftp://ftp.ensembl.org/pub/release-110/fasta/mus_musculus/dna/Mus_musculus.GRCm39.dna.primary_assembly.fa.gz",
                    "description": "Mouse genome GRCm39 (GENCODE vM33)"
                }
            }
        }

        os.makedirs(REFERENCE_VOLUME_PATH, exist_ok=True)
        with open(GENOMES_CONFIG_PATH, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        print(f"✓ Config created at {GENOMES_CONFIG_PATH}")

    # Load config
    config = load_genome_config()
    genomes_config = config.get("genomes", {})

    if genome not in genomes_config:
        print(f"✗ Error: Genome '{genome}' not found in config")
        print(f"Available genomes: {list(genomes_config.keys())}")
        return

    genome_info = genomes_config[genome]
    gtf_url = genome_info.get("gtf_url")
    fasta_url = genome_info.get("fasta_url")

    if not gtf_url or not fasta_url:
        print(f"✗ Error: Genome '{genome}' missing gtf_url or fasta_url")
        return

    print(f"Downloading genome: {genome}")
    print(f"Description: {genome_info.get('description', 'N/A')}")

    # Create directory
    os.makedirs(REFERENCE_VOLUME_PATH, exist_ok=True)

    # Download GTF
    gtf_path = f"{REFERENCE_VOLUME_PATH}/{genome}.gtf"
    if not os.path.exists(gtf_path):
        print(f"\nDownloading GTF from {gtf_url}...")
        subprocess.run(["wget", "-O", gtf_path + ".gz", gtf_url], check=True)
        print("Decompressing GTF...")
        subprocess.run(["gunzip", "-f", gtf_path + ".gz"], check=True)
        print(f"✓ GTF downloaded: {gtf_path}")
    else:
        print(f"✓ GTF already exists: {gtf_path}")

    # Download FASTA
    fasta_path = f"{REFERENCE_VOLUME_PATH}/{genome}.fa"
    if not os.path.exists(fasta_path):
        print(f"\nDownloading FASTA from {fasta_url}...")
        subprocess.run(["wget", "-O", fasta_path + ".gz", fasta_url], check=True)
        print("Decompressing FASTA (this may take a while)...")
        subprocess.run(["gunzip", "-f", fasta_path + ".gz"], check=True)
        print(f"✓ FASTA downloaded: {fasta_path}")

        # Create FASTA index
        print("\nCreating FASTA index...")
        subprocess.run(["samtools", "faidx", fasta_path], check=True)
        print(f"✓ FASTA indexed: {fasta_path}.fai")
    else:
        print(f"✓ FASTA already exists: {fasta_path}")
        # Check if index exists
        if not os.path.exists(fasta_path + ".fai"):
            print("Creating FASTA index...")
            subprocess.run(["samtools", "faidx", fasta_path], check=True)
            print(f"✓ FASTA indexed: {fasta_path}.fai")

    # Commit volume changes
    volume.commit()

    # Show file sizes
    gtf_size = os.path.getsize(gtf_path) / 1024 / 1024
    fasta_size = os.path.getsize(fasta_path) / 1024 / 1024
    print(f"\n✅ Reference files for {genome} are ready!")
    print(f"   GTF:   {gtf_size:.2f} MB")
    print(f"   FASTA: {fasta_size:.2f} MB")


@app.function(
    image=image,
    volumes={REFERENCE_VOLUME_PATH: volume},
    timeout=600,
)
def add_custom_genome(
    name: str,
    gtf_url: str,
    fasta_url: str,
    description: str = "Custom genome"
):
    """
    Add a custom genome to the configuration and download it

    Args:
        name: Unique name for the genome (e.g., MyGenome)
        gtf_url: URL to GTF file (can be .gz)
        fasta_url: URL to FASTA file (can be .gz)
        description: Human-readable description

    Usage:
        modal run deployment/modal_app_v2.py::add_custom_genome \
            --name MyGenome \
            --gtf-url "https://example.com/annotations.gtf.gz" \
            --fasta-url "https://example.com/genome.fa.gz" \
            --description "My custom genome"
    """
    import yaml

    # Create config directory if needed
    os.makedirs(REFERENCE_VOLUME_PATH, exist_ok=True)

    # Load existing config or create new
    config = load_genome_config()
    if "genomes" not in config:
        config["genomes"] = {}

    # Add new genome
    config["genomes"][name] = {
        "gtf_url": gtf_url,
        "fasta_url": fasta_url,
        "description": description,
    }

    # Save config
    with open(GENOMES_CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    volume.commit()

    print(f"✓ Added {name} to configuration")
    print(f"\nTo download: modal run deployment/modal_app_v2.py::download_genome --genome {name}")


# Local entrypoint
@app.local_entrypoint()
def main(genome: str = "GRCh38"):
    """
    Setup reference files for a genome

    Usage:
        modal run deployment/modal_app_v2.py  # Downloads GRCh38
        modal run deployment/modal_app_v2.py --genome GRCm39  # Downloads mouse genome
    """
    print(f"Setting up reference files for {genome}...")
    download_genome.remote(genome=genome)

    print("\nChecking health...")
    health_status = health.remote()
    print(health_status)
