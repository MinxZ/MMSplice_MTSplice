#!/bin/bash
# Download reference genome files for MMSplice
# Usage: bash download_references.sh [genome]
# Default genome: GRCh38

set -e  # Exit on error

GENOME=${1:-GRCh38}
REF_DIR="reference_data"

echo "================================================================================"
echo "Reference Genome Download Script"
echo "================================================================================"
echo ""
echo "Genome: $GENOME"
echo "Target directory: $REF_DIR"
echo ""

# Create reference directory
mkdir -p "$REF_DIR"
cd "$REF_DIR"

# Function to download and extract with progress
download_and_extract() {
    local url=$1
    local output_gz=$2
    local output=$3
    local description=$4

    echo "----------------------------------------"
    echo "Downloading $description..."
    echo "URL: $url"
    echo "----------------------------------------"

    if [ -f "$output" ]; then
        echo "✓ $output already exists, skipping download"
        return 0
    fi

    # Download with progress bar
    if command -v wget &> /dev/null; then
        wget --progress=bar:force -O "$output_gz" "$url" 2>&1 | \
            grep --line-buffered "%" | \
            sed -u -e "s,\.,,g" | \
            awk '{printf("\r%4s\n", $2)}'
    elif command -v curl &> /dev/null; then
        curl -L --progress-bar -o "$output_gz" "$url"
    else
        echo "❌ Error: Neither wget nor curl is available"
        exit 1
    fi

    # Extract
    echo ""
    echo "Extracting $output_gz..."
    gunzip -f "$output_gz"

    # Show file size
    size=$(du -h "$output" | cut -f1)
    echo "✓ $output extracted successfully ($size)"
    echo ""
}

# Download based on genome
case $GENOME in
    GRCh38)
        echo "Downloading Human Genome GRCh38 (hg38)"
        echo ""

        # GTF
        GTF_URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz"
        download_and_extract "$GTF_URL" "GRCh38.gtf.gz" "GRCh38.gtf" "GRCh38 GTF (GENCODE v45)"

        # FASTA
        FASTA_URL="ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz"
        download_and_extract "$FASTA_URL" "GRCh38.fa.gz" "GRCh38.fa" "GRCh38 FASTA (Ensembl 110)"

        # Index FASTA
        if [ ! -f "GRCh38.fa.fai" ]; then
            echo "----------------------------------------"
            echo "Indexing FASTA file..."
            echo "----------------------------------------"
            if command -v samtools &> /dev/null; then
                samtools faidx GRCh38.fa
                echo "✓ GRCh38.fa.fai created"
            else
                echo "⚠ Warning: samtools not found, skipping FASTA indexing"
                echo "Please run: samtools faidx GRCh38.fa"
            fi
        else
            echo "✓ GRCh38.fa.fai already exists"
        fi
        ;;

    GRCh37)
        echo "Downloading Human Genome GRCh37 (hg19)"
        echo ""

        # GTF
        GTF_URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gtf.gz"
        download_and_extract "$GTF_URL" "GRCh37.gtf.gz" "GRCh37.gtf" "GRCh37 GTF (GENCODE v19)"

        # FASTA
        FASTA_URL="ftp://ftp.ensembl.org/pub/grch37/current/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz"
        download_and_extract "$FASTA_URL" "GRCh37.fa.gz" "GRCh37.fa" "GRCh37 FASTA"

        # Index FASTA
        if [ ! -f "GRCh37.fa.fai" ]; then
            echo "----------------------------------------"
            echo "Indexing FASTA file..."
            echo "----------------------------------------"
            if command -v samtools &> /dev/null; then
                samtools faidx GRCh37.fa
                echo "✓ GRCh37.fa.fai created"
            else
                echo "⚠ Warning: samtools not found, skipping FASTA indexing"
            fi
        else
            echo "✓ GRCh37.fa.fai already exists"
        fi
        ;;

    GRCm39)
        echo "Downloading Mouse Genome GRCm39"
        echo ""

        # GTF
        GTF_URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M33/gencode.vM33.annotation.gtf.gz"
        download_and_extract "$GTF_URL" "GRCm39.gtf.gz" "GRCm39.gtf" "GRCm39 GTF (GENCODE vM33)"

        # FASTA
        FASTA_URL="ftp://ftp.ensembl.org/pub/release-110/fasta/mus_musculus/dna/Mus_musculus.GRCm39.dna.primary_assembly.fa.gz"
        download_and_extract "$FASTA_URL" "GRCm39.fa.gz" "GRCm39.fa" "GRCm39 FASTA (Ensembl 110)"

        # Index FASTA
        if [ ! -f "GRCm39.fa.fai" ]; then
            echo "----------------------------------------"
            echo "Indexing FASTA file..."
            echo "----------------------------------------"
            if command -v samtools &> /dev/null; then
                samtools faidx GRCm39.fa
                echo "✓ GRCm39.fa.fai created"
            else
                echo "⚠ Warning: samtools not found, skipping FASTA indexing"
            fi
        else
            echo "✓ GRCm39.fa.fai already exists"
        fi
        ;;

    *)
        echo "❌ Error: Unknown genome '$GENOME'"
        echo ""
        echo "Supported genomes:"
        echo "  - GRCh38 (Human, hg38, default)"
        echo "  - GRCh37 (Human, hg19)"
        echo "  - GRCm39 (Mouse)"
        echo ""
        echo "Usage: bash download_references.sh [genome]"
        exit 1
        ;;
esac

cd ..

# Summary
echo ""
echo "================================================================================"
echo "✅ Download Complete!"
echo "================================================================================"
echo ""
echo "Reference files for $GENOME:"
ls -lh "$REF_DIR/$GENOME".* 2>/dev/null || echo "  (files listed above)"
echo ""
echo "Files are ready to use with MMSplice:"
echo "  GTF:   $REF_DIR/$GENOME.gtf"
echo "  FASTA: $REF_DIR/$GENOME.fa"
echo "  Index: $REF_DIR/$GENOME.fa.fai"
echo ""
echo "Next steps:"
echo "  1. Test installation: python test_installation.py"
echo "  2. Run predictions: python test_local_prediction.py"
echo ""
