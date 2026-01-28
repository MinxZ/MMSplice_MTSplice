# Custom Genome Support Guide

MMSplice Modal deployment now supports **any custom genome**! You can easily add and use different species, assemblies, or custom reference files.

## Quick Start

### Using Pre-configured Genomes

The deployment comes with 8+ pre-configured genomes ready to download:

```bash
# Deploy the v2 app (with custom genome support)
modal deploy deployment/modal_app_v2.py

# Download any genome from genomes_config.yaml
modal run deployment/modal_app_v2.py::download_genome --genome GRCh38  # Human GRCh38
modal run deployment/modal_app_v2.py::download_genome --genome GRCh37  # Human GRCh37
modal run deployment/modal_app_v2.py::download_genome --genome GRCm39  # Mouse
modal run deployment/modal_app_v2.py::download_genome --genome GRCz11  # Zebrafish
modal run deployment/modal_app_v2.py::download_genome --genome BDGP6.32  # Drosophila
```

### Pre-configured Genomes

See [genomes_config.yaml](genomes_config.yaml) for the full list:

| Genome | Species | Description |
|--------|---------|-------------|
| **GRCh38** | Human | GENCODE v45, primary assembly |
| **GRCh37** | Human | GENCODE v19 (hg19), primary assembly |
| **GRCm39** | Mouse | GENCODE vM33, primary assembly |
| **GRCm38** | Mouse | GENCODE vM25 (mm10), primary assembly |
| **Rnor_6.0** | Rat | Ensembl release 110 |
| **GRCz11** | Zebrafish | Ensembl release 110 |
| **BDGP6.32** | Drosophila | Ensembl release 110 (dm6) |
| **WBcel235** | C. elegans | Ensembl release 110 (ce11) |

## Adding Custom Genomes

### Method 1: Edit genomes_config.yaml (Recommended)

1. Edit [genomes_config.yaml](genomes_config.yaml):

```yaml
genomes:
  MyGenome:
    gtf_url: "https://your-server.com/annotations.gtf.gz"
    fasta_url: "https://your-server.com/genome.fa.gz"
    description: "My custom genome assembly v1.0"

  Mmul_10:  # Example: Rhesus macaque
    gtf_url: "ftp://ftp.ensembl.org/pub/release-110/gtf/macaca_mulatta/Macaca_mulatta.Mmul_10.110.gtf.gz"
    fasta_url: "ftp://ftp.ensembl.org/pub/release-110/fasta/macaca_mulatta/dna/Macaca_mulatta.Mmul_10.dna.toplevel.fa.gz"
    description: "Rhesus macaque genome Mmul_10"
```

2. Download your custom genome:

```bash
modal run deployment/modal_app_v2.py::download_genome --genome MyGenome
```

### Method 2: Add via Command Line

Add a genome without editing the config file:

```bash
modal run deployment/modal_app_v2.py::add_custom_genome \
  --name MyGenome \
  --gtf-url "https://your-server.com/annotations.gtf.gz" \
  --fasta-url "https://your-server.com/genome.fa.gz" \
  --description "My custom genome"
```

Then download it:

```bash
modal run deployment/modal_app_v2.py::download_genome --genome MyGenome
```

## Finding Genome URLs

### Ensembl

Browse: https://ftp.ensembl.org/pub/

Example URLs:
```
# GTF
ftp://ftp.ensembl.org/pub/release-110/gtf/[species]/[Species].[assembly].110.gtf.gz

# FASTA
ftp://ftp.ensembl.org/pub/release-110/fasta/[species]/dna/[Species].[assembly].dna.primary_assembly.fa.gz
```

### GENCODE (Human & Mouse)

- Human: https://www.gencodegenes.org/human/
- Mouse: https://www.gencodegenes.org/mouse/

Example URLs:
```
# Human GRCh38
https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz

# Mouse GRCm39
https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_mouse/release_M33/gencode.vM33.annotation.gtf.gz
ftp://ftp.ensembl.org/pub/release-110/fasta/mus_musculus/dna/Mus_musculus.GRCm39.dna.primary_assembly.fa.gz
```

### UCSC Genome Browser

Browse: https://hgdownload.soe.ucsc.edu/downloads.html

Convert UCSC files to Ensembl format (GTF may need conversion).

## Using Custom Genomes

Once downloaded, use them in API calls:

### cURL

```bash
curl -X POST https://your-endpoint/predict \
  -F "vcf_file=@variants.vcf.gz" \
  -F "genome=MyGenome" \
  > predictions.json
```

### Python

```python
from mmsplice_client import MMSpliceClient

client = MMSpliceClient(api_url="https://your-endpoint")
predictions = client.predict("variants.vcf.gz", genome="MyGenome")
```

### Test Client

```bash
python deployment/test_client.py \
  --url https://your-endpoint \
  --vcf variants.vcf.gz \
  --genome MyGenome
```

## Listing Available Genomes

### Check what's configured

```bash
# Via API
curl https://your-endpoint/list-genomes

# Via health check
curl https://your-endpoint/health
```

### Check what's downloaded

```bash
modal volume ls mmsplice-reference-data
```

## Example: Adding Rhesus Macaque

1. Add to [genomes_config.yaml](genomes_config.yaml):

```yaml
genomes:
  Mmul_10:
    gtf_url: "ftp://ftp.ensembl.org/pub/release-110/gtf/macaca_mulatta/Macaca_mulatta.Mmul_10.110.gtf.gz"
    fasta_url: "ftp://ftp.ensembl.org/pub/release-110/fasta/macaca_mulatta/dna/Macaca_mulatta.Mmul_10.dna.toplevel.fa.gz"
    description: "Rhesus macaque genome Mmul_10 (Ensembl 110)"
```

2. Download:

```bash
modal run deployment/modal_app_v2.py::download_genome --genome Mmul_10
```

3. Use:

```bash
curl -X POST https://your-endpoint/predict \
  -F "vcf_file=@macaque_variants.vcf.gz" \
  -F "genome=Mmul_10" \
  > macaque_predictions.json
```

## Example: Adding Custom Assembly

If you have your own GTF and FASTA files hosted somewhere:

```bash
modal run deployment/modal_app_v2.py::add_custom_genome \
  --name MyPlant_v2 \
  --gtf-url "https://mylab.edu/genomes/myplant_v2.gtf.gz" \
  --fasta-url "https://mylab.edu/genomes/myplant_v2.fa.gz" \
  --description "My plant genome assembly v2.0"

modal run deployment/modal_app_v2.py::download_genome --genome MyPlant_v2
```

## File Requirements

### GTF Format

- Must be valid GTF format (tab-separated)
- Required features: `gene`, `transcript`, `exon`
- Can be compressed (.gz)

Example GTF line:
```
chr1	HAVANA	gene	11869	14409	.	+	.	gene_id "ENSG00000223972"; gene_name "DDX11L1";
```

### FASTA Format

- Standard FASTA format
- Can be compressed (.gz)
- Should match chromosome names in GTF

Example FASTA:
```
>chr1
ATCGATCGATCG...
>chr2
GCTAGCTAGCTA...
```

## Storage & Costs

### File Sizes (Approximate)

| Genome | GTF | FASTA | Total | Cost/month |
|--------|-----|-------|-------|------------|
| Human GRCh38 | 50 MB | 3.0 GB | 3.05 GB | $0.61 |
| Human GRCh37 | 40 MB | 3.0 GB | 3.04 GB | $0.61 |
| Mouse GRCm39 | 35 MB | 2.7 GB | 2.73 GB | $0.55 |
| Rat Rnor_6.0 | 30 MB | 2.8 GB | 2.83 GB | $0.57 |
| Zebrafish GRCz11 | 25 MB | 1.4 GB | 1.42 GB | $0.28 |
| Drosophila BDGP6.32 | 15 MB | 143 MB | 158 MB | $0.03 |
| C. elegans WBcel235 | 10 MB | 100 MB | 110 MB | $0.02 |

Modal Volume pricing: $0.20/GB/month

### Download Times

Depends on file size and internet speed:

- Small genomes (< 500 MB): 2-5 minutes
- Medium genomes (500 MB - 2 GB): 5-10 minutes
- Large genomes (> 2 GB): 10-20 minutes

## Troubleshooting

### Issue: "Genome not found in config"

**Cause:** Genome not in genomes_config.yaml

**Solution:**
```bash
# Check available genomes
cat deployment/genomes_config.yaml

# Or list via API
curl https://your-endpoint/list-genomes
```

### Issue: Download fails with 404

**Cause:** Invalid URL in config

**Solution:** Verify URLs are accessible:
```bash
curl -I "YOUR_GTF_URL"
curl -I "YOUR_FASTA_URL"
```

### Issue: GTF/FASTA format error

**Cause:** Invalid file format

**Solution:** Validate files locally:
```bash
# Check GTF
zcat annotations.gtf.gz | head -20

# Check FASTA
zcat genome.fa.gz | head -20
```

### Issue: Chromosome name mismatch

**Cause:** GTF and FASTA use different chr naming (chr1 vs 1)

**Solution:** Ensure consistent naming or convert:
```bash
# Add "chr" prefix to FASTA
sed 's/^>/chr>/g' genome.fa > genome_chr.fa

# Or remove "chr" from GTF
sed 's/chr//g' annotations.gtf > annotations_nochr.gtf
```

## Best Practices

1. **Use primary assemblies**: Prefer `primary_assembly.fa` over `toplevel.fa` when available
2. **Match releases**: Use same Ensembl release for GTF and FASTA
3. **Compress files**: Always use .gz compression for faster uploads
4. **Test locally first**: Download a small region and test before full deployment
5. **Document versions**: Include version info in description field
6. **Backup config**: Keep a copy of genomes_config.yaml in version control

## Migration from v1

If you're using the old modal_app.py:

1. **Deploy v2:**
   ```bash
   modal deploy deployment/modal_app_v2.py
   ```

2. **Re-download genomes:**
   ```bash
   modal run deployment/modal_app_v2.py::download_genome --genome GRCh38
   ```

3. **Update API URLs** in your code to point to v2 endpoints

The old genomes will remain in the volume but v2 uses a new naming scheme (GRCh38.gtf instead of gencode.v45.annotation.gtf).

## Advanced: Multiple Assemblies

You can have multiple versions of the same genome:

```yaml
genomes:
  GRCh38_v45:
    gtf_url: "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz"
    fasta_url: "ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz"
    description: "Human GRCh38 with GENCODE v45"

  GRCh38_v44:
    gtf_url: "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/gencode.v44.annotation.gtf.gz"
    fasta_url: "ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz"
    description: "Human GRCh38 with GENCODE v44"
```

## Next Steps

- See [README_MODAL.md](README_MODAL.md) for general deployment info
- Check [genomes_config.yaml](genomes_config.yaml) for pre-configured genomes
- Browse [Ensembl FTP](https://ftp.ensembl.org/pub/) for more species

---

**Ready to add your genome?**

```bash
# Edit config
vim deployment/genomes_config.yaml

# Deploy
modal deploy deployment/modal_app_v2.py

# Download
modal run deployment/modal_app_v2.py::download_genome --genome YourGenome
```
