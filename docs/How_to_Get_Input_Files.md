# How to Obtain Input Files for MMSplice/MTSplice

## Overview

MMSplice/MTSplice requires three types of input files. Here's what you can download publicly vs. what you need to create/obtain per project.

---

## 🌍 PUBLIC FILES (Download Once, Use for All Projects)

### 1. FASTA Files - Reference Genome

**What it is**: The standard "normal" human genome sequence that all variants are compared against.

**Who needs it**: Everyone uses the same reference genome.

**Where to download**:

#### Option A: GENCODE/Ensembl (Recommended)

```bash
# GRCh38/hg38 (Current standard - use this for new projects)
wget ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz

# GRCh37/hg19 (Older, still used for legacy data)
wget ftp://ftp.ensembl.org/pub/grch37/current/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
```

#### Option B: UCSC Genome Browser

```bash
# hg38 (equivalent to GRCh38)
wget https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz
gunzip hg38.fa.gz

# hg19 (equivalent to GRCh37)
wget https://hgdownload.soe.ucsc.edu/goldenPath/hg19/bigZips/hg19.fa.gz
gunzip hg19.fa.gz
```

**File size**: ~3 GB compressed, ~3 GB uncompressed

**How often to download**: Once per genome version. Keep both GRCh37 and GRCh38 for compatibility.

---

### 2. GTF Files - Gene Annotations

**What it is**: Defines where all human genes, exons, and transcripts are located in the genome.

**Who needs it**: Everyone uses the same annotations (but versions update as new genes are discovered).

**Where to download**:

#### Option A: GENCODE (Most Comprehensive, Recommended)

```bash
# GENCODE v45 for GRCh38/hg38
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip gencode.v45.annotation.gtf.gz

# GENCODE v19 for GRCh37/hg19
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gtf.gz
gunzip gencode.v19.annotation.gtf.gz
```

#### Option B: Ensembl

```bash
# Ensembl release 110 (GRCh38)
wget ftp://ftp.ensembl.org/pub/release-110/gtf/homo_sapiens/Homo_sapiens.GRCh38.110.gtf.gz
gunzip Homo_sapiens.GRCh38.110.gtf.gz
```

**File size**: ~50 MB compressed, ~1.5 GB uncompressed

**How often to download**:
- Once per project (versions are stable)
- Update when you need newer gene annotations (e.g., newly discovered genes)
- **Important**: GTF version must match FASTA genome version!

---

## 📋 VCF FILES - Multiple Sources Depending on Use Case

VCF files contain genetic variants. **How you obtain them depends on your purpose:**

### Use Case 1: ASO Design (Create Your Own)

**Purpose**: Testing how your designed ASO oligonucleotides will affect splicing.

**How to obtain**: **You create these VCF files yourself** based on your ASO designs.

**Method**: Represent each ASO's predicted effect as a variant (SNP or small deletion).

#### Example: Creating VCF for ASO Candidates

```bash
# Create a simple VCF file for DMD exon 51 ASO candidates
cat > aso_dmd_exon51.vcf << 'EOF'
##fileformat=VCFv4.2
##reference=GRCh38
##INFO=<ID=ASO_ID,Number=1,Type=String,Description="ASO identifier">
##INFO=<ID=TARGET,Number=1,Type=String,Description="ASO target site">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chrX	31791568	ASO_acceptor_ex51	A	T	60	PASS	ASO_ID=DMD_Ex51_Acc;TARGET=acceptor_site
chrX	31791715	ASO_donor_ex51	G	A	60	PASS	ASO_ID=DMD_Ex51_Don;TARGET=donor_site
chrX	31791650	ASO_ESE_ex51	C	T	60	PASS	ASO_ID=DMD_Ex51_ESE;TARGET=ESE_blocker
EOF

# Compress and index
bgzip aso_dmd_exon51.vcf
tabix -p vcf aso_dmd_exon51.vcf.gz
```

**Tools for VCF creation**:
- Manual editing (for small sets)
- Python scripts with `pysam` or `cyvcf2`
- Excel → TSV → VCF conversion scripts

---

### Use Case 2: Patient Variants (Person-Specific)

**Purpose**: Analyzing disease-causing variants in individual patients.

**How to obtain**: These are **DIFFERENT for each person** and come from sequencing.

#### Source A: Clinical Sequencing Labs

If you're working with patient data:

```
Patient DNA → Sequencing Lab → VCF file with patient variants
                ↓
        (Whole Genome Sequencing or
         Whole Exome Sequencing)
```

**Companies/Services**:
- Illumina sequencing
- 23andMe (consumer genetics)
- Hospital sequencing facilities
- Research genomics centers

**Privacy**: Patient VCF files are **confidential medical records** - handle with appropriate IRB approval and data security.

---

#### Source B: Public Variant Databases (Research Use)

For research without patient data, you can download **known disease variants**:

**ClinVar** - Clinically relevant variants:
```bash
# Download all ClinVar variants
wget https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz
wget https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz.tbi

# Filter for specific gene (e.g., BRCA1)
bcftools view -r 17:43044295-43125483 clinvar.vcf.gz > brca1_clinvar.vcf
```

**gnomAD** - Population variation database:
```bash
# Download gnomAD (all human genetic variation)
# WARNING: Very large files (100+ GB)
wget https://storage.googleapis.com/gcp-public-data--gnomad/release/4.0/vcf/genomes/gnomad.genomes.v4.0.sites.chr17.vcf.bgz
```

**Other databases**:
- **COSMIC** - Cancer variants
- **HGMD** - Human Gene Mutation Database (subscription)
- **dbSNP** - All known SNPs
- **1000 Genomes** - Population diversity

---

### Use Case 3: Simulated/Test Variants (Research/Development)

**Purpose**: Testing your pipeline or exploring hypothetical scenarios.

**How to obtain**: Create synthetic VCF files.

#### Example: Random Variants in a Gene

```python
# Python script to create test VCF
import random

vcf_header = """##fileformat=VCFv4.2
##reference=GRCh38
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
"""

# Generate 10 random SNPs in BRCA1 gene region
variants = []
bases = ['A', 'T', 'G', 'C']
for i in range(10):
    pos = random.randint(43044295, 43125483)  # BRCA1 region
    ref = random.choice(bases)
    alt = random.choice([b for b in bases if b != ref])
    variants.append(f"17\t{pos}\ttest_var_{i}\t{ref}\t{alt}\t60\tPASS\t.")

with open('test_variants.vcf', 'w') as f:
    f.write(vcf_header)
    f.write('\n'.join(variants))
```

---

## 📊 Summary Table

| File Type | Public or Private? | Download or Create? | How Often? | Size |
|-----------|-------------------|---------------------|------------|------|
| **FASTA** | ✅ Public | **Download** | Once per genome version | ~3 GB |
| **GTF** | ✅ Public | **Download** | Once per annotation version | ~50 MB |
| **VCF (ASO design)** | N/A | **Create yourself** | Per ASO project | Small (KB) |
| **VCF (Patient)** | 🔒 Private | Get from sequencing lab | Per patient | Varies |
| **VCF (Public DB)** | ✅ Public | **Download** | Periodically updated | Large (GB) |

---

## 🔧 Complete Setup Example

Here's a complete workflow to set up your reference files:

```bash
# Create directory structure
mkdir -p ~/mmsplice_data/{reference,annotations,variants}
cd ~/mmsplice_data

# 1. Download Reference Genome (GRCh38)
cd reference
wget ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
mv Homo_sapiens.GRCh38.dna.primary_assembly.fa GRCh38.fa

# Index the FASTA file (required for MMSplice)
samtools faidx GRCh38.fa

# 2. Download Gene Annotations (GENCODE v45)
cd ../annotations
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_45/gencode.v45.annotation.gtf.gz
gunzip gencode.v45.annotation.gtf.gz
mv gencode.v45.annotation.gtf gencode_v45.gtf

# 3. Download Public Variant Database (ClinVar - optional)
cd ../variants
wget https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz
wget https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz.tbi

# 4. Create your own ASO VCF file
cat > my_aso_designs.vcf << 'EOF'
##fileformat=VCFv4.2
##reference=GRCh38
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
17	43044295	ASO_test_1	A	G	60	PASS	.
EOF

bgzip my_aso_designs.vcf
tabix -p vcf my_aso_designs.vcf.gz

# Done! Now you can run MMSplice
```

---

## 🎯 Typical Workflows

### Workflow 1: ASO Drug Development

```
1. Download PUBLIC files once:
   - FASTA (GRCh38.fa)
   - GTF (gencode_v45.gtf)

2. Design ASO candidates:
   - Manually design 10-50 ASO sequences

3. Create VCF file:
   - Represent each ASO as a variant
   - Create custom VCF file

4. Run MMSplice:
   - Use your VCF + public FASTA + public GTF
   - Get predictions for each ASO

5. Iterate:
   - Refine ASO designs based on predictions
   - Create new VCF, re-run predictions
```

### Workflow 2: Patient Variant Analysis

```
1. Download PUBLIC files once:
   - FASTA (GRCh38.fa)
   - GTF (gencode_v45.gtf)

2. Obtain patient VCF:
   - From clinical sequencing lab
   - Or from your own WGS/WES pipeline

3. Run MMSplice:
   - Use patient VCF + public FASTA + public GTF
   - Identify splicing-affecting variants

4. Clinical interpretation:
   - Focus on pathogenic predictions
   - Validate experimentally
```

### Workflow 3: Research/Database Screening

```
1. Download PUBLIC files once:
   - FASTA (GRCh38.fa)
   - GTF (gencode_v45.gtf)
   - ClinVar VCF (public variants)

2. Filter variants:
   - Extract variants in your gene of interest
   - Filter by variant type (missense, splice site, etc.)

3. Run MMSplice at scale:
   - Batch prediction on thousands of variants
   - Identify novel splicing-affecting variants

4. Prioritize for validation:
   - Strong predictions → experimental validation
```

---

## 💡 Key Takeaways

1. **FASTA and GTF**: Download PUBLIC files once, use for all projects
2. **VCF for ASO design**: You CREATE these based on your ASO candidates
3. **VCF for patients**: Person-specific, from sequencing labs (private)
4. **VCF for research**: Download from public databases (ClinVar, gnomAD)
5. **Always match versions**: GTF and FASTA must use the same genome build (GRCh37 vs. GRCh38)

---

## 📚 Additional Resources

### File Format Documentation
- **VCF format**: https://samtools.github.io/hts-specs/VCFv4.2.pdf
- **GTF format**: https://www.ensembl.org/info/website/upload/gff.html
- **FASTA format**: https://www.ncbi.nlm.nih.gov/genbank/fastaformat/

### Download Portals
- **GENCODE**: https://www.gencodegenes.org/
- **Ensembl**: https://www.ensembl.org/
- **UCSC Genome Browser**: https://genome.ucsc.edu/
- **ClinVar**: https://www.ncbi.nlm.nih.gov/clinvar/
- **gnomAD**: https://gnomad.broadinstitute.org/

### Tools for VCF Manipulation
- **bcftools**: http://samtools.github.io/bcftools/
- **GATK**: https://gatk.broadinstitute.org/
- **pysam (Python)**: https://pysam.readthedocs.io/
- **cyvcf2 (Python)**: https://brentp.github.io/cyvcf2/

---

**Last Updated**: 2024
**Genome Versions**: GRCh37/hg19 and GRCh38/hg38
