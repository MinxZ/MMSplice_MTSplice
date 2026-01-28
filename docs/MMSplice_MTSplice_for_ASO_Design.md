# MMSplice & MTSplice: Predicting Splicing Effects for ASO Design

## Table of Contents
1. [Introduction & Purpose](#introduction--purpose)
2. [Model Overview](#model-overview)
3. [Inputs & Requirements](#inputs--requirements)
4. [Outputs & Interpretation](#outputs--interpretation)
5. [ASO Design Application Workflow](#aso-design-application-workflow)
6. [Best Practices](#best-practices-for-aso-design)
7. [Example Use Cases](#example-use-cases)
8. [Limitations & Considerations](#limitations--considerations)
9. [Installation & Setup](#installation--setup)
10. [Additional Resources](#additional-resources)

---

## Introduction & Purpose

### What are MMSplice and MTSplice?

**MMSplice** (Modular Modeling of Splicing) and **MTSplice** (Multi-Tissue Splicing) are deep learning models that predict how genetic variants affect RNA splicing in human cells. These tools are essential for understanding variant pathogenicity and designing therapeutic interventions that target splicing.

**Key Capabilities:**
- Predict effects of genetic variants on exon inclusion levels (Percent Spliced-In, PSI)
- Quantify tissue-specific splicing changes across 56 human tissues
- Score pathogenic potential of splicing variants
- Assess splicing efficiency changes

### Clinical Relevance

Splicing defects account for a substantial fraction of human genetic diseases:
- **15-60%** of disease-causing mutations affect splicing
- Alternative splicing regulates **~95%** of human multi-exon genes
- Tissue-specific splicing plays critical roles in development and disease

### Why This Matters for ASO Design

**Antisense Oligonucleotides (ASOs)** are powerful therapeutics that can:
- **Skip disease-causing exons** to restore reading frames (e.g., Duchenne Muscular Dystrophy)
- **Promote exon inclusion** to correct aberrant skipping (e.g., Spinal Muscular Atrophy)
- **Redirect splicing patterns** to produce therapeutic isoforms

**MMSplice/MTSplice enable:**
1. **Rational ASO design** - Predict which sequences will have the desired splicing effect
2. **Target prioritization** - Identify the most promising ASO candidates before synthesis
3. **Tissue specificity assessment** - Evaluate on-target vs. off-target tissue effects
4. **Mechanism understanding** - Determine which splice regulatory elements are affected

**Approved ASO Therapeutics:**
- **Eteplirsen** (Exondys 51) - DMD exon 51 skipping
- **Nusinersen** (Spinraza) - SMA exon 7 inclusion
- **Golodirsen** (Vyondys 53) - DMD exon 53 skipping
- **Viltolarsen** (Viltepso) - DMD exon 53 skipping

---

## Model Overview

### MMSplice (Tissue-Agnostic Model)

MMSplice is a modular neural network that predicts constitutive splicing regulatory effects.

#### Architecture

MMSplice consists of **5 independent neural network modules**, each analyzing a specific region around the exon:

| Module | Region | Size | Function |
|--------|--------|------|----------|
| **Acceptor Intron** | 3' intron | 50 bp intron + 3 bp exon | Models intronic splicing silencers/enhancers upstream of exon |
| **Acceptor** | Splice acceptor site | 13 bp (intron+exon junction) | Models 3' splice site recognition |
| **Exon** | Exon body | Variable length | Models exonic splicing enhancers/silencers |
| **Donor** | Splice donor site | 13 bp (exon+intron junction) | Models 5' splice site recognition |
| **Donor Intron** | 5' intron | 5 bp exon + 50 bp intron | Models intronic splicing silencers/enhancers downstream of exon |

#### Training Data
- **2+ million** sequences from massively parallel reporter assays (MPRA)
- **500,000+** naturally occurring splice sites
- Trained on perturbation data (reference vs. variant sequences)

#### Outputs
- **delta_logit_psi**: Primary score for effect on exon inclusion (logit scale)
- **pathogenicity**: Probability that variant is disease-causing (0-1 scale)
- **efficiency**: Effect on overall splicing efficiency

### MTSplice (Tissue-Specific Extension)

MTSplice extends MMSplice by adding tissue-specific regulatory predictions.

#### Architecture

MTSplice = **MMSplice** (constitutive elements) + **TSplice** (tissue-specific elements)

**TSplice Component:**
- Convolutional neural network with **64 filters**
- Analyzes **300 bp flanking regions** (vs. 100 bp for MMSplice)
- **Spline transformations** model positional effects
- **Multi-task learning** across 56 tissues simultaneously
- Ensemble of **8 models** for robust predictions

#### Training Data
- **ASCOT dataset**: 61,823 cassette exons across 56 tissues
- **GTEx RNA-Seq data**: 53 GTEx tissues + peripheral retina
- Captures tissue-specific splicing patterns, especially in:
  - **Central nervous system** (14 brain regions + spinal cord + retina)
  - **Muscle tissues** (skeletal muscle + heart)
  - Other organs (liver, lung, kidney, testis, etc.)

#### Key Findings from Research
- **29%** of exons (17,991/61,823) show tissue-specific splicing (≥10% PSI deviation)
- **Brain tissues** cluster together with distinct splicing patterns
- **Autism-associated** de novo mutations enriched for brain-specific splicing effects
- MTSplice **outperforms** MMSplice alone in 39/51 tissues for variant effect prediction

---

## Inputs & Requirements

### Required Input Files

| Input File | Format | Description | Example | Preparation |
|-----------|--------|-------------|---------|-------------|
| **VCF** | `.vcf`, `.vcf.gz` | Genetic variants representing ASO effects or natural variants | `variants.vcf.gz` | Must be **left-normalized** and **multi-allelic sites split** |
| **GTF** | `.gtf` | Gene annotation with exon coordinates | `gencode.v38.annotation.gtf` | Use Ensembl or Gencode annotations |
| **FASTA** | `.fa`, `.fasta` | Reference genome sequence | `GRCh38.fa` | Match genome build to GTF (GRCh37 or GRCh38) |

### VCF File Preparation (Critical!)

```bash
# Split multi-allelic sites
bcftools norm -m-both -o normalized.vcf input.vcf

# Left-normalize indels
bcftools norm -f reference.fasta -o final.vcf normalized.vcf

# Quality filtering (recommended)
bcftools filter -i 'QUAL>20' -o filtered.vcf final.vcf
```

### Input Parameters

#### SplicingVCFDataloader Parameters

```python
from mmsplice.vcf_dataloader import SplicingVCFDataloader

dl = SplicingVCFDataloader(
    gtf,                          # Path to GTF annotation file
    fasta_file,                   # Path to reference FASTA
    vcf_file,                     # Path to VCF file

    # Sequence parameters
    split_seq=True,               # Split into 5 modules (default: True)
    encode=True,                  # One-hot encode DNA (default: True)
    overhang=(100, 100),          # Flanking bp for MMSplice (default: 100, 100)

    # Tissue-specific parameters
    tissue_specific=False,        # Enable MTSplice (default: False)
    tissue_overhang=(300, 300),   # Flanking bp for tissue model (default: 300, 300)
)
```

#### predict_all_table Parameters

```python
from mmsplice import MMSplice, predict_all_table

model = MMSplice()
predictions = predict_all_table(
    model,                        # MMSplice model instance
    dl,                          # SplicingVCFDataloader instance

    # Batch processing
    batch_size=512,               # Batch size for GPU (default: 512)
    progress=True,                # Show progress bar (default: True)

    # Additional predictions
    pathogenicity=False,          # Add pathogenicity score (default: False)
    splicing_efficiency=False,    # Add efficiency score (default: False)

    # Tissue-specific options
    natural_scale=False,          # Convert to delta_psi instead of logit (default: False)
    ref_psi_version=None,         # 'grch37' or 'grch38' for natural_scale conversion
)
```

---

## Outputs & Interpretation

### Output Format

MMSplice/MTSplice returns a **pandas DataFrame** with comprehensive predictions for each variant-exon pair.

### Core Columns

#### Variant & Exon Information
- **ID**: Variant identifier (from VCF)
- **exons**: Genomic coordinates `chr:start-end:strand`
- **exon_id**: Exon identifier
- **gene_id**: Ensembl gene ID
- **gene_name**: Human-readable gene symbol
- **transcript_id**: Transcript identifier

### Primary Prediction: delta_logit_psi

The **main score** indicating effect on exon inclusion:

```
delta_logit_psi = logit(PSI_alt) - logit(PSI_ref)
```

**Interpretation:**

| delta_logit_psi | Effect | Interpretation |
|----------------|--------|----------------|
| **< -2** | **Strong decrease** | Promotes exon skipping |
| **-2 to -0.5** | **Moderate decrease** | Mild exon skipping |
| **-0.5 to 0.5** | **Weak/uncertain** | Minimal effect |
| **0.5 to 2** | **Moderate increase** | Mild exon inclusion |
| **> 2** | **Strong increase** | Promotes exon inclusion |

**Sign Convention:**
- **Positive (+)**: Variant **increases** exon inclusion
- **Negative (-)**: Variant **decreases** exon inclusion (promotes skipping)

### Module Scores

Five pairs of scores (reference vs. alternative) for each splice region:

| Module | Columns | What It Measures |
|--------|---------|------------------|
| Acceptor Intron | `ref_acceptorIntron`, `alt_acceptorIntron` | 3' intron ISS/ISE effects |
| Acceptor | `ref_acceptor`, `alt_acceptor` | 3' splice site strength |
| Exon | `ref_exon`, `alt_exon` | Exonic ESS/ESE effects |
| Donor | `ref_donor`, `alt_donor` | 5' splice site strength |
| Donor Intron | `ref_donorIntron`, `alt_donorIntron` | 5' intron ISS/ISE effects |

**Usage for ASO Design:**
- Identify **which module** drives the splicing change
- Target ASOs to the relevant region (acceptor site, donor site, or exon body)
- Large difference in `alt_donor` vs. `ref_donor` → Target donor site with ASO

### Pathogenicity Score

**Column**: `pathogenicity`

**Range**: 0.0 to 1.0

**Interpretation:**
- **> 0.8**: High probability of pathogenic effect
- **0.5 - 0.8**: Moderate pathogenicity
- **< 0.5**: Low pathogenicity

**Use in ASO Design:**
- High pathogenicity → Prioritize for therapeutic intervention
- Evaluate off-target effects in non-disease tissues

### Splicing Efficiency Score

**Column**: `efficiency`

**Range**: Real number

**Interpretation:**
- Predicts overall change in splicing efficiency
- Higher efficiency changes may indicate more potent ASO effects

### Tissue-Specific Predictions (MTSplice)

When `tissue_specific=True`, additional columns for each of **56 tissues**:

**Tissue Categories:**
- **Brain** (14 regions): Amygdala, Caudate, Cerebellum, Cortex, Hippocampus, etc.
- **Muscle**: Skeletal muscle, Heart (atrial appendage), Heart (left ventricle)
- **Digestive**: Colon, Esophagus, Liver, Pancreas, Stomach, Small intestine
- **Reproductive**: Ovary, Testis, Uterus, Prostate, Breast
- **Other**: Lung, Kidney, Skin, Adipose, Spleen, Thyroid, etc.

**Column Naming**:
- `{Tissue_Name}`: delta_logit_psi for that tissue
- Example: `Liver`, `Muscle - Skeletal`, `Brain - Cortex`

**With natural_scale=True**:
- Converts logit predictions to **delta_psi** (natural PSI scale 0-1)
- Adds columns: `{Tissue_Name}_ref` (reference PSI), `{Tissue_Name}_delta_psi`

### Output File Formats

```python
# Save as CSV
predictions.to_csv('predictions.csv', index=False)

# Save as Parquet (faster for large datasets)
predictions.to_parquet('predictions.parquet')

# Write to VCF with INFO fields
from mmsplice import writeVCF
writeVCF(input_vcf, output_vcf, predictions)
```

---

## ASO Design Application Workflow

### Overview: 7-Step Process

```
1. Define Therapeutic Goal → 2. Identify Target Exons → 3. Generate Candidate ASOs
     ↓                                                                ↓
7. Experimental Validation ← 6. Prioritize Candidates ← 5. Analyze Results
                                        ↓
                            4. Run MMSplice/MTSplice Predictions
```

### Step 1: Define Therapeutic Goal

#### Exon Skipping
**Goal**: Remove disease-causing exon to restore reading frame

**Diseases**:
- Duchenne Muscular Dystrophy (DMD)
- Dysferlinopathies
- Facioscapulohumeral muscular dystrophy

**ASO Strategy**: Block splice sites or splicing enhancers to induce skipping

**Expected Prediction**: **Negative delta_logit_psi** (< -2 for strong skipping)

#### Exon Inclusion
**Goal**: Prevent aberrant exon skipping or promote inclusion

**Diseases**:
- Spinal Muscular Atrophy (SMA)
- Beta-thalassemia
- Familial dysautonomia

**ASO Strategy**: Block splicing silencers (ISS/ESS)

**Expected Prediction**: **Positive delta_logit_psi** (> 2 for strong inclusion)

#### Splice Site Switching
**Goal**: Redirect to alternative splice sites

**ASO Strategy**: Block canonical sites to activate cryptic sites

**Expected Prediction**: Combination of negative (blocked site) and positive (activated site)

### Step 2: Identify Target Exons

**For Exon Skipping:**
```python
# Example: DMD exon 51 skipping candidates
# Identify exon coordinates from gene annotation
target_gene = "DMD"
target_exon = 51
target_region = "chrX:31,791,568-31,791,719"  # Example coordinates
```

**For Exon Inclusion:**
```python
# Example: SMN2 exon 7 inclusion
target_gene = "SMN2"
target_exon = 7
iss_regions = ["exon7_ISS-N1"]  # Known splicing silencer
```

### Step 3: Generate Candidate ASO Sequences

#### 3.1: Design ASO Binding Sites

**Targeting Splice Sites (for exon skipping):**
```
Exon Structure:
  Intron     |  Exon  |  Intron
  ===AGgtaagt===ATG...TAG===ttgcagGT===
         ↑                    ↑
      Acceptor             Donor

ASO targets:
- Acceptor site ASO: Overlaps AG dinucleotide
- Donor site ASO: Overlaps GT dinucleotide
- ESE blocking ASO: Covers exonic enhancer motifs
```

**Targeting Splicing Enhancers/Silencers:**
```
ISS-N1 in SMN2 exon 7:
  CCTTTCATAAA
  ^^^^^^^^^^^
  ASO target region
```

#### 3.2: Represent ASOs as VCF Variants

Since MMSplice requires VCF input, represent ASO effects as variants:

**Option A: SNP at ASO binding site** (simplified approach)
```vcf
##fileformat=VCFv4.2
#CHROM  POS         ID              REF  ALT  QUAL  FILTER  INFO
chrX    31791568    ASO_acceptor    A    T    60    PASS    .
chrX    31791719    ASO_donor       G    A    60    PASS    .
chr5    70247773    ASO_SMN2_ISS    C    T    60    PASS    .
```

**Option B: Deletion mimicking ASO blocking**
```vcf
#CHROM  POS         ID              REF      ALT  QUAL  FILTER  INFO
chrX    31791568    ASO_acceptor    AGGTAA   A    60    PASS    .
```

**Note**: This is a proxy representation. The actual ASO effect is steric blocking, but deletions can approximate this for prediction purposes.

### Step 4: Run MMSplice/MTSplice Predictions

#### Basic Usage (Tissue-Agnostic)

```python
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

# File paths
gtf_file = '/path/to/gencode.v38.annotation.gtf'
fasta_file = '/path/to/GRCh38.fa'
vcf_file = '/path/to/aso_candidates.vcf.gz'

# Create dataloader
dl = SplicingVCFDataloader(
    gtf_file,
    fasta_file,
    vcf_file,
    overhang=(100, 100)
)

# Load model
model = MMSplice()

# Run predictions
predictions = predict_all_table(
    model,
    dl,
    pathogenicity=True,
    splicing_efficiency=True,
    progress=True
)

# Save results
predictions.to_csv('aso_predictions.csv', index=False)
```

#### Tissue-Specific Predictions

```python
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

# Create tissue-specific dataloader
dl = SplicingVCFDataloader(
    gtf_file,
    fasta_file,
    vcf_file,
    tissue_specific=True,
    tissue_overhang=(300, 300)
)

# Load model
model = MMSplice()

# Run tissue-specific predictions
predictions = predict_all_table(
    model,
    dl,
    pathogenicity=True,
    splicing_efficiency=True,
    natural_scale=True,          # Convert to delta_psi scale
    ref_psi_version='grch38',    # Match your genome build
    progress=True
)

# Examine tissue-specific effects
tissue_cols = [col for col in predictions.columns if col in [
    'Muscle - Skeletal', 'Heart - Left Ventricle',
    'Brain - Cortex', 'Liver', 'Lung'
]]
tissue_effects = predictions[['ID', 'gene_name', 'exons'] + tissue_cols]
print(tissue_effects.head())
```

### Step 5: Analyze Results

#### For Exon Skipping ASOs

```python
import pandas as pd

# Load predictions
df = pd.read_csv('aso_predictions.csv')

# Filter for strong exon skipping effects
skipping_candidates = df[
    (df['delta_logit_psi'] < -2) &              # Strong skipping
    (df['gene_name'] == 'DMD') &                # Target gene
    (df['pathogenicity'] > 0.5)                 # Likely pathogenic
].copy()

# Sort by strength of effect
skipping_candidates = skipping_candidates.sort_values(
    'delta_logit_psi',
    ascending=True
)

# Identify which module drives the effect
skipping_candidates['primary_module'] = skipping_candidates.apply(
    lambda row: min([
        ('donor', row['alt_donor'] - row['ref_donor']),
        ('acceptor', row['alt_acceptor'] - row['ref_acceptor']),
        ('exon', row['alt_exon'] - row['ref_exon'])
    ], key=lambda x: x[1])[0],
    axis=1
)

print(skipping_candidates[['ID', 'exons', 'delta_logit_psi', 'primary_module', 'pathogenicity']])
```

**Output Example:**
```
ID              exons                    delta_logit_psi  primary_module  pathogenicity
ASO_donor_51    chrX:31791568-31791719  -3.45            donor           0.87
ASO_acceptor_51 chrX:31791568-31791719  -2.91            acceptor        0.79
ASO_ESE_51      chrX:31791568-31791719  -1.23            exon            0.45
```

#### For Exon Inclusion ASOs

```python
# Filter for strong exon inclusion effects
inclusion_candidates = df[
    (df['delta_logit_psi'] > 2) &               # Strong inclusion
    (df['gene_name'] == 'SMN2') &               # Target gene
    (df['exons'].str.contains('exon7'))         # Target exon
].copy()

# Check tissue specificity (if available)
if 'Brain - Cortex' in df.columns:
    inclusion_candidates['brain_effect'] = df['Brain - Cortex']
    inclusion_candidates['muscle_effect'] = df['Muscle - Skeletal']

    # Calculate tissue specificity ratio
    inclusion_candidates['brain_specificity'] = (
        inclusion_candidates['brain_effect'] /
        inclusion_candidates['muscle_effect']
    )

print(inclusion_candidates[['ID', 'delta_logit_psi', 'brain_effect', 'brain_specificity']])
```

#### Visualize Module Contributions

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_module_effects(variant_id, df):
    """Visualize which splice module is most affected by ASO"""
    row = df[df['ID'] == variant_id].iloc[0]

    modules = ['acceptorIntron', 'acceptor', 'exon', 'donor', 'donorIntron']
    deltas = [
        row[f'alt_{m}'] - row[f'ref_{m}']
        for m in modules
    ]

    plt.figure(figsize=(10, 5))
    plt.bar(modules, deltas, color=['red' if d < 0 else 'green' for d in deltas])
    plt.axhline(y=0, color='black', linestyle='--')
    plt.ylabel('Module Score Change (alt - ref)')
    plt.title(f'ASO Effect on Splice Modules: {variant_id}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Example usage
plot_module_effects('ASO_donor_51', df)
```

### Step 6: Prioritize ASO Candidates

#### Ranking Criteria

```python
def rank_aso_candidates(df, goal='skipping'):
    """
    Rank ASO candidates by multiple criteria

    Parameters:
    - df: DataFrame with predictions
    - goal: 'skipping' or 'inclusion'
    """
    ranked = df.copy()

    # 1. Strength of effect
    if goal == 'skipping':
        ranked['strength_score'] = -ranked['delta_logit_psi']  # More negative = better
    else:
        ranked['strength_score'] = ranked['delta_logit_psi']   # More positive = better

    # 2. Pathogenicity score (higher = more likely therapeutic)
    ranked['pathogenicity_score'] = ranked['pathogenicity']

    # 3. Efficiency score (absolute value)
    ranked['efficiency_score'] = abs(ranked['efficiency'])

    # 4. Module specificity (prefer effects on single module)
    module_deltas = []
    for idx, row in ranked.iterrows():
        deltas = [
            abs(row['alt_acceptorIntron'] - row['ref_acceptorIntron']),
            abs(row['alt_acceptor'] - row['ref_acceptor']),
            abs(row['alt_exon'] - row['ref_exon']),
            abs(row['alt_donor'] - row['ref_donor']),
            abs(row['alt_donorIntron'] - row['ref_donorIntron'])
        ]
        # Higher max relative to mean = more specific
        specificity = max(deltas) / (np.mean(deltas) + 0.001)
        module_deltas.append(specificity)
    ranked['module_specificity'] = module_deltas

    # Composite score (weighted)
    ranked['composite_score'] = (
        0.5 * ranked['strength_score'] +
        0.2 * ranked['pathogenicity_score'] +
        0.2 * ranked['efficiency_score'] +
        0.1 * ranked['module_specificity']
    )

    # Rank by composite score
    ranked = ranked.sort_values('composite_score', ascending=False)

    return ranked[['ID', 'gene_name', 'exons', 'delta_logit_psi',
                   'pathogenicity', 'composite_score']]

# Rank candidates
top_candidates = rank_aso_candidates(skipping_candidates, goal='skipping')
print(top_candidates.head(10))
```

#### Tissue Specificity Filter

```python
def filter_by_tissue_specificity(df, target_tissue, min_ratio=2.0):
    """
    Filter ASOs by tissue specificity

    Parameters:
    - df: DataFrame with tissue predictions
    - target_tissue: Name of target tissue (e.g., 'Muscle - Skeletal')
    - min_ratio: Minimum ratio of target/off-target effect
    """
    if target_tissue not in df.columns:
        print("Tissue-specific predictions not available")
        return df

    # Get all tissue columns
    tissue_cols = [col for col in df.columns if col in [
        'Liver', 'Lung', 'Brain - Cortex', 'Muscle - Skeletal',
        'Heart - Left Ventricle', 'Testis', 'Kidney - Cortex'
    ]]

    specific = df.copy()
    specific['target_effect'] = abs(specific[target_tissue])
    specific['mean_offtarget'] = specific[
        [t for t in tissue_cols if t != target_tissue]
    ].abs().mean(axis=1)

    specific['tissue_specificity_ratio'] = (
        specific['target_effect'] / (specific['mean_offtarget'] + 0.1)
    )

    # Filter by minimum ratio
    specific = specific[specific['tissue_specificity_ratio'] >= min_ratio]

    return specific.sort_values('tissue_specificity_ratio', ascending=False)

# Example: DMD muscle-specific ASOs
muscle_specific = filter_by_tissue_specificity(
    predictions,
    target_tissue='Muscle - Skeletal',
    min_ratio=2.0
)
```

### Step 7: Experimental Validation

After computational prioritization, validate top ASO candidates:

#### In Vitro Validation
1. **Minigene assays**
   - Clone target exon + flanking regions into expression vector
   - Transfect with ASO
   - Measure PSI by RT-PCR or RNA-Seq
   - Compare to MMSplice predictions

2. **Cell-based assays**
   - Patient-derived cells (iPSCs, fibroblasts, myoblasts)
   - Transfect with ASO
   - Western blot for protein restoration
   - RNA analysis for splicing changes

#### In Vivo Validation
3. **Animal models**
   - Mdx mice for DMD
   - SMA mouse models
   - Systemic or local ASO delivery
   - Functional phenotype assessment

#### Expected Correlation
- **Strong correlation** (r > 0.7): delta_logit_psi vs. measured PSI change
- **Directional agreement**: Sign of prediction matches experimental outcome
- **Magnitude**: |delta_logit_psi| > 2 typically produces measurable splicing change

---

## Best Practices for ASO Design

### VCF Preparation Best Practices

```bash
# Complete preprocessing pipeline
# 1. Split multi-allelic variants
bcftools norm -m-both input.vcf | \
# 2. Left-normalize
bcftools norm -f GRCh38.fa | \
# 3. Filter by quality
bcftools filter -i 'QUAL>20' | \
# 4. Compress and index
bgzip > final.vcf.gz && tabix final.vcf.gz
```

### Interpretation Guidelines

#### Strength Thresholds

| Category | delta_logit_psi Range | Expected PSI Change | Action |
|----------|----------------------|---------------------|---------|
| **Strong** | \|score\| > 2 | > 20% PSI change | **Prioritize** for validation |
| **Moderate** | 0.5 < \|score\| ≤ 2 | 5-20% PSI change | Consider for validation |
| **Weak** | \|score\| ≤ 0.5 | < 5% PSI change | Likely insufficient effect |

#### Module Score Interpretation

**For Donor Site ASOs:**
- Large negative difference in `alt_donor - ref_donor`
- Minimal changes in other modules
- Indicates specific disruption of 5' splice site

**For Acceptor Site ASOs:**
- Large negative difference in `alt_acceptor - ref_acceptor`
- Minimal changes in other modules
- Indicates specific disruption of 3' splice site

**For ESE/ISS Blocking ASOs:**
- Changes primarily in `alt_exon - ref_exon`
- May also affect `acceptor` or `donor` if ESE/ISS overlaps

### Tissue Specificity Best Practices

#### Identifying Tissue-Specific Effects

```python
def assess_tissue_specificity(df, variant_id):
    """Quantify tissue specificity of ASO effect"""
    row = df[df['ID'] == variant_id]

    # Get tissue columns
    tissue_cols = [c for c in df.columns if c in [
        'Brain - Cortex', 'Muscle - Skeletal', 'Liver',
        'Lung', 'Heart - Left Ventricle'
    ]]

    if not tissue_cols:
        print("No tissue-specific predictions available")
        return None

    tissue_effects = row[tissue_cols].iloc[0]

    print(f"Tissue Specificity Analysis: {variant_id}")
    print("=" * 50)
    for tissue, effect in tissue_effects.items():
        print(f"{tissue:30s}: {effect:6.2f}")

    # Calculate coefficient of variation
    cv = tissue_effects.std() / (abs(tissue_effects.mean()) + 0.01)
    print(f"\nCoefficient of Variation: {cv:.2f}")
    print(f"Interpretation: {'TISSUE-SPECIFIC' if cv > 0.5 else 'UBIQUITOUS'}")

    return tissue_effects

# Example
assess_tissue_specificity(predictions, 'ASO_candidate_1')
```

#### Brain Disease Applications

For neurological disorders (autism, epilepsy, neurodegeneration):

```python
# Brain-specific tissues in MTSplice
brain_tissues = [
    'Brain - Amygdala',
    'Brain - Anterior cingulate cortex',
    'Brain - Caudate (basal ganglia)',
    'Brain - Cerebellar Hemisphere',
    'Brain - Cerebellum',
    'Brain - Cortex',
    'Brain - Frontal Cortex (BA9)',
    'Brain - Hippocampus',
    'Brain - Hypothalamus',
    'Brain - Nucleus accumbens',
    'Brain - Putamen',
    'Brain - Spinal cord',
    'Brain - Substantia nigra',
    'Retina - Eye'
]

# Filter for brain-specific ASOs
brain_df = predictions.copy()
brain_df['mean_brain_effect'] = brain_df[brain_tissues].mean(axis=1)
brain_df['mean_other_effect'] = brain_df[
    [c for c in predictions.columns if c not in brain_tissues and 'Brain' not in c]
].mean(axis=1)
brain_df['brain_specificity'] = (
    abs(brain_df['mean_brain_effect']) /
    (abs(brain_df['mean_other_effect']) + 0.1)
)

brain_specific = brain_df[brain_df['brain_specificity'] > 2.0]
```

#### Muscle Disease Applications

For muscular dystrophies (DMD, LGMD, FSHD):

```python
muscle_tissues = [
    'Muscle - Skeletal',
    'Heart - Atrial Appendage',
    'Heart - Left Ventricle'
]

# Muscle-specific analysis
muscle_df = predictions.copy()
muscle_df['mean_muscle_effect'] = muscle_df[muscle_tissues].mean(axis=1)

# Filter strong muscle effects with minimal cardiac effects
dmd_candidates = muscle_df[
    (abs(muscle_df['Muscle - Skeletal']) > 2) &
    (abs(muscle_df['Heart - Left Ventricle']) < 1)  # Minimize cardiac effects
]
```

---

## Example Use Cases

### Example 1: Duchenne Muscular Dystrophy (DMD) - Exon 51 Skipping

**Disease Background:**
- **Cause**: Frameshift mutations in dystrophin gene (DMD)
- **Therapeutic Approach**: Skip exon 51 to restore reading frame
- **Approved ASO**: Eteplirsen (Exondys 51)

**Workflow:**

```python
# Step 1: Define target
target_gene = "DMD"
target_exon = 51
exon_coords = "chrX:31,791,568-31,791,719"  # GRCh38

# Step 2: Create VCF with ASO candidates
# aso_dmd_exon51.vcf
"""
#CHROM  POS         ID                  REF  ALT  QUAL  FILTER
chrX    31791568    ASO_acceptor_ex51   A    T    60    PASS
chrX    31791715    ASO_donor_ex51      G    A    60    PASS
chrX    31791650    ASO_ESE_ex51        C    T    60    PASS
"""

# Step 3: Run predictions with muscle-specific analysis
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

dl = SplicingVCFDataloader(
    'gencode.v38.gtf',
    'GRCh38.fa',
    'aso_dmd_exon51.vcf',
    tissue_specific=True
)

model = MMSplice()
dmd_predictions = predict_all_table(
    model, dl,
    pathogenicity=True,
    splicing_efficiency=True,
    natural_scale=True,
    ref_psi_version='grch38'
)

# Step 4: Analyze results
dmd_results = dmd_predictions[dmd_predictions['gene_name'] == 'DMD'].copy()

# Filter for strong skipping in muscle
dmd_results = dmd_results[
    (dmd_results['delta_logit_psi'] < -2) &
    (dmd_results['Muscle - Skeletal'] < -2)
]

print("Top DMD Exon 51 Skipping ASO Candidates:")
print(dmd_results[['ID', 'delta_logit_psi', 'Muscle - Skeletal',
                    'Heart - Left Ventricle', 'pathogenicity']])
```

**Expected Output:**
```
ID                    delta_logit_psi  Muscle-Skeletal  Heart-LV  pathogenicity
ASO_donor_ex51        -3.21            -3.45            -2.87     0.91
ASO_acceptor_ex51     -2.89            -3.12            -2.65     0.88
ASO_ESE_ex51          -1.45            -1.67            -1.23     0.56
```

**Interpretation:**
- **ASO_donor_ex51**: Strongest candidate (delta_logit_psi = -3.21)
- **Muscle-specific effect**: Strong in skeletal muscle (-3.45)
- **Cardiac safety**: Moderate effect in heart (-2.87), consider monitoring
- **Mechanism**: Donor site disruption (check `alt_donor - ref_donor`)

### Example 2: Spinal Muscular Atrophy (SMA) - SMN2 Exon 7 Inclusion

**Disease Background:**
- **Cause**: Loss of SMN1 gene
- **Therapeutic Approach**: Promote SMN2 exon 7 inclusion via ISS-N1 blocking
- **Approved ASO**: Nusinersen (Spinraza)

**Workflow:**

```python
# Step 1: Define target
target_gene = "SMN2"
target_exon = 7
iss_n1_region = "chr5:70,247,773"  # ISS-N1 location

# Step 2: Create VCF targeting ISS-N1
# aso_smn2_exon7.vcf
"""
#CHROM  POS         ID                  REF  ALT  QUAL  FILTER
chr5    70247773    ASO_ISS_N1_pos1     C    T    60    PASS
chr5    70247778    ASO_ISS_N1_pos6     T    A    60    PASS
chr5    70247783    ASO_ISS_N1_pos11    A    G    60    PASS
"""

# Step 3: Run predictions
dl = SplicingVCFDataloader(
    'gencode.v38.gtf',
    'GRCh38.fa',
    'aso_smn2_exon7.vcf',
    tissue_specific=True
)

model = MMSplice()
sma_predictions = predict_all_table(
    model, dl,
    pathogenicity=True,
    splicing_efficiency=True,
    natural_scale=True,
    ref_psi_version='grch38'
)

# Step 4: Filter for strong inclusion in CNS tissues
sma_results = sma_predictions[sma_predictions['gene_name'] == 'SMN2'].copy()

sma_results = sma_results[
    (sma_results['delta_logit_psi'] > 2) &
    (sma_results['Brain - Cortex'] > 2)
]

print("Top SMN2 Exon 7 Inclusion ASO Candidates:")
print(sma_results[['ID', 'delta_logit_psi', 'Brain - Cortex',
                    'Brain - Spinal cord', 'pathogenicity']])
```

**Expected Output:**
```
ID                    delta_logit_psi  Brain-Cortex  Brain-Spinal  pathogenicity
ASO_ISS_N1_pos6       2.87             3.12          3.45          0.82
ASO_ISS_N1_pos1       2.34             2.67          2.91          0.75
ASO_ISS_N1_pos11      1.98             2.23          2.45          0.68
```

**Interpretation:**
- **ASO_ISS_N1_pos6**: Best candidate for promoting exon 7 inclusion
- **CNS-specific**: Strong effects in brain and spinal cord
- **Mechanism**: ISS-N1 silencer disruption (check `alt_exon - ref_exon`)
- **Clinical correlation**: Position 6 corresponds to nusinersen binding site

### Example 3: Autism Spectrum Disorder - Brain-Specific Splicing Correction

**Disease Background:**
- **Observation**: ASD patients show mis-splicing of brain-specific exons
- **Therapeutic Hypothesis**: Correct brain-specific splicing defects
- **MTSplice Application**: Identify brain-specific splicing variants

**Workflow:**

```python
# Step 1: Load autism-associated variants
# Example: de novo mutations from autism cohorts
autism_vcf = "autism_denovo_variants.vcf.gz"

# Step 2: Run tissue-specific predictions
dl = SplicingVCFDataloader(
    'gencode.v38.gtf',
    'GRCh38.fa',
    autism_vcf,
    tissue_specific=True
)

model = MMSplice()
autism_predictions = predict_all_table(
    model, dl,
    pathogenicity=True,
    natural_scale=True,
    ref_psi_version='grch38'
)

# Step 3: Identify brain-specific splicing variants
brain_tissues = [
    'Brain - Cortex', 'Brain - Hippocampus',
    'Brain - Amygdala', 'Brain - Cerebellum'
]

autism_predictions['mean_brain_effect'] = autism_predictions[brain_tissues].abs().mean(axis=1)

non_brain = [c for c in autism_predictions.columns
             if c not in brain_tissues and 'Brain' not in c and c in [
                 'Liver', 'Lung', 'Muscle - Skeletal', 'Heart - Left Ventricle'
             ]]
autism_predictions['mean_other_effect'] = autism_predictions[non_brain].abs().mean(axis=1)

# Calculate brain specificity
autism_predictions['brain_specificity_ratio'] = (
    autism_predictions['mean_brain_effect'] /
    (autism_predictions['mean_other_effect'] + 0.1)
)

# Filter for brain-specific effects
brain_specific_variants = autism_predictions[
    (autism_predictions['brain_specificity_ratio'] > 3.0) &
    (autism_predictions['mean_brain_effect'] > 2.0) &
    (autism_predictions['pathogenicity'] > 0.7)
].copy()

# Step 4: Design ASOs to rescue brain-specific mis-splicing
print("Brain-Specific Autism Splicing Variants:")
print(brain_specific_variants[['ID', 'gene_name', 'delta_logit_psi',
                                'mean_brain_effect', 'brain_specificity_ratio']])

# Step 5: Generate rescue ASOs (opposite effect to mutation)
rescue_asos = []
for idx, row in brain_specific_variants.iterrows():
    if row['delta_logit_psi'] < 0:  # Mutation decreases inclusion
        aso_goal = "promote inclusion"
        target_region = "ISS/ESS"
    else:  # Mutation increases inclusion
        aso_goal = "promote skipping"
        target_region = "donor/acceptor"

    rescue_asos.append({
        'variant_id': row['ID'],
        'gene': row['gene_name'],
        'mutation_effect': row['delta_logit_psi'],
        'aso_goal': aso_goal,
        'target_region': target_region
    })

import pandas as pd
rescue_df = pd.DataFrame(rescue_asos)
print("\nASO Design Strategy:")
print(rescue_df)
```

**Expected Insights:**
- Identify genes with brain-specific mis-splicing in autism
- Design ASOs to counteract pathogenic splicing changes
- Prioritize variants with high brain specificity ratios
- Experimental validation in patient-derived neurons or brain organoids

---

## Limitations & Considerations

### 1. Predictive Model, Not Experimental Validation

**MMSplice/MTSplice provide predictions** based on sequence features, but:
- **Experimental validation is required** for therapeutic development
- Predictions are probabilistic, not deterministic
- Cellular context (RBP expression, chromatin state) affects actual splicing

**Best Practice**: Use predictions to prioritize ASO candidates for experimental testing, not as definitive proof of effect.

### 2. Sequence Context Limitations

**Input regions analyzed:**
- MMSplice: **100 bp** flanking each side of exon
- MTSplice: **300 bp** flanking each side of exon

**Implications:**
- Long-range regulatory elements (> 300 bp away) are not captured
- Deep intronic elements may be missed
- Branch point sequences far from acceptor may not be fully modeled

**Best Practice**: For deep intronic variants or long-range enhancers, consider complementary tools or experimental approaches.

### 3. Training Data Bias

**MMSplice training:**
- Primarily trained on **reporter assay data** in HEK293 cells
- Natural variants from **GTEx** (healthy individuals)

**MTSplice training:**
- **ASCOT dataset** from GTEx RNA-Seq
- Limited disease-specific splicing patterns

**Implications:**
- May underperform on novel splice junctions or unannotated exons
- Disease-specific splicing patterns (e.g., cancer-specific) may not be well-represented
- Performance best for annotated, constitutive cassette exons

**Best Practice**: Highest confidence for well-annotated exons in protein-coding genes from Ensembl/Gencode.

### 4. No ASO Chemistry Modeling

**MMSplice/MTSplice do not account for:**
- **ASO chemical modifications** (2'-MOE, PMO, PNA, etc.)
- **ASO binding affinity** and stability
- **ASO delivery efficiency** to target tissues
- **Off-target hybridization** to unintended transcripts
- **Immunogenicity** or toxicity

**Best Practice**: Combine MMSplice predictions with:
- ASO design tools (e.g., binding affinity calculators)
- Off-target analysis (BLAST, RNA structure prediction)
- Chemistry optimization based on prior ASO drug experience

### 5. Tissue-Specific Limitations

**GTEx data characteristics:**
- Derived from **healthy donors** (post-mortem tissues)
- Limited representation of **disease states**
- Tissue-specific variant effects are **modest** in healthy individuals (only 3.4% of variants show >20% tissue-specific difference)

**Implications:**
- Disease-specific splicing changes may be underestimated
- Pathological conditions (inflammation, stress) alter splicing factors
- Developmental stages not represented (fetal vs. adult splicing)

**Best Practice**:
- Tissue-specific predictions are most useful for **ranking** ASO candidates
- Validate in disease-relevant cell types or patient samples
- Consider disease-specific splicing factor expression

### 6. Exon Type Limitations

**Best performance:**
- **Cassette exons** (can be included or skipped)
- **Annotated exons** in Ensembl/Gencode

**Limited performance:**
- Alternative 5' or 3' splice sites
- Intron retention events
- Mutually exclusive exons
- Novel/unannotated junctions

**Best Practice**: For non-cassette alternative splicing events, interpret predictions with caution and prioritize experimental validation.

### 7. Computational Representation of ASO Effects

**Challenge**: ASOs work via **steric blocking**, but MMSplice requires **sequence variants** as input.

**Current Approach**: Represent ASO binding as:
- SNPs at binding site
- Small deletions mimicking blocked region

**Limitations**:
- Imperfect proxy for actual steric blocking mechanism
- Doesn't capture ASO-RNA duplex stability
- May not accurately model partial ASO overlap scenarios

**Best Practice**:
- Focus on **directional predictions** (skipping vs. inclusion) rather than absolute magnitudes
- Validate top candidates experimentally
- Consider multiple ASO representations (different SNPs/deletions) for robustness

### 8. Regulatory Element Complexity

**Splicing is regulated by:**
- Splice site strength (modeled well by MMSplice)
- ESE/ESS, ISE/ISS elements (partially modeled)
- **RNA secondary structure** (not modeled)
- **Long-range interactions** (not modeled)
- **Chromatin state** (not modeled)
- **RBP concentrations** (partially via tissue-specific model)

**Best Practice**: Use predictions as a starting point, but recognize that splicing is multifactorial.

---

## Installation & Setup

### Quick Start Installation

```bash
# Install dependencies
pip install cyvcf2 cython numpy scipy pandas

# Install MMSplice
pip install mmsplice

# Verify installation
python -c "from mmsplice import MMSplice; print('MMSplice installed successfully')"
```

### System Requirements

- **Python**: 3.7 or higher
- **RAM**: Minimum 8 GB (16 GB recommended for large VCF files)
- **Storage**: ~2 GB for pre-trained models and annotations
- **GPU**: Optional (speeds up predictions, but CPU works fine)

### Download Reference Data

#### Reference Genome (FASTA)

```bash
# GRCh38 from Ensembl
wget ftp://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz

# OR GRCh37 from Ensembl
wget ftp://ftp.ensembl.org/pub/grch37/current/fasta/homo_sapiens/dna/Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
gunzip Homo_sapiens.GRCh37.dna.primary_assembly.fa.gz
```

#### Gene Annotation (GTF)

```bash
# Gencode v38 (GRCh38)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_38/gencode.v38.annotation.gtf.gz
gunzip gencode.v38.annotation.gtf.gz

# OR Gencode v19 (GRCh37)
wget https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gtf.gz
gunzip gencode.v19.annotation.gtf.gz
```

### Test Installation

```python
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table
import pandas as pd

# Paths to test data (use your own files or package test data)
gtf = "path/to/gencode.v38.annotation.gtf"
fasta = "path/to/GRCh38.fa"
vcf = "path/to/test_variants.vcf.gz"

# Create dataloader
dl = SplicingVCFDataloader(gtf, fasta, vcf)

# Load model (downloads pre-trained weights automatically)
model = MMSplice()

# Run predictions
predictions = predict_all_table(model, dl, pathogenicity=True)

print("Installation successful!")
print(f"Predicted {len(predictions)} variant-exon pairs")
print(predictions.head())
```

### Using Pre-built Exon Annotations

MMSplice provides **pre-built exon annotations** for faster setup:

```python
from mmsplice import MMSplice
from mmsplice.utils import get_exon_dl

# Download pre-built exon sequences for GRCh38
dl = get_exon_dl(
    genome='grch38',        # or 'grch37'
    tissue_specific=True
)

# Run predictions directly
model = MMSplice()
predictions = predict_all_table(model, dl, pathogenicity=True)
```

---

## Additional Resources

### Official Documentation & Code

- **GitHub Repository**: [https://github.com/gagneurlab/MMSplice](https://github.com/gagneurlab/MMSplice)
- **Kipoi Model Zoo**: [https://kipoi.org/models/MMSplice/](https://kipoi.org/models/MMSplice/)
- **Example Notebook**: Included in repository at `notebooks/example.ipynb`

### Scientific Publications

**MMSplice:**
- Cheng et al. (2019). "MMSplice: Modular modeling improves the predictions of genetic variant effects on splicing." *Genome Biology*, 20(1), 48.
- DOI: [10.1186/s13059-019-1653-z](https://doi.org/10.1186/s13059-019-1653-z)

**MTSplice:**
- Cheng et al. (2020). "MTSplice predicts effects of genetic variants on tissue-specific splicing." *bioRxiv*.
- DOI: [10.1101/2020.06.07.138453](https://doi.org/10.1101/2020.06.07.138453)

**Related Work:**
- ASCOT dataset: Ling et al. (2020). "ASCOT identifies key regulators of neuronal subtype-specific splicing." *Nature Communications*, 11(1), 1-12.

### ASO Design Resources

**Tools:**
- **SROOGLE**: Search for splicing regulatory elements
- **ESEfinder**: Predict exonic splicing enhancers
- **Human Splicing Finder**: Comprehensive splicing analysis

**Databases:**
- **SpliceAid**: Database of splicing factors and their binding sites
- **SplicePort**: Splice site prediction
- **RegRNA**: Regulatory RNA motifs

**ASO Chemistry:**
- **2'-O-Methoxyethyl (2'-MOE)**: FDA-approved chemistry (Nusinersen)
- **Phosphorodiamidate Morpholino Oligomers (PMO)**: Neutral backbone (Eteplirsen)
- **Peptide-conjugated PMO (PPMO)**: Enhanced delivery

### Related Splicing Prediction Tools

- **SpliceAI**: Deep learning for splice site prediction
- **SPANR**: Tissue-specific splicing predictor (earlier model)
- **HAL**: Ensemble splicing predictor
- **CADD-Splice**: Combined annotation for splicing variants

### Community & Support

- **GitHub Issues**: Report bugs or ask questions at [MMSplice Issues](https://github.com/gagneurlab/MMSplice/issues)
- **Kipoi Forum**: General machine learning for genomics discussions

---

## Summary

MMSplice and MTSplice provide powerful computational tools for predicting splicing effects of genetic variants, with direct applications to Antisense Oligonucleotide (ASO) therapeutic design:

**Key Strengths:**
- Modular architecture allows interpretation of splice region effects
- Tissue-specific predictions across 56 human tissues
- Pathogenicity scoring for variant prioritization
- Pre-trained models ready for immediate use

**ASO Design Workflow:**
1. Define therapeutic goal (exon skipping vs. inclusion)
2. Generate candidate ASO sequences as VCF variants
3. Run MMSplice/MTSplice predictions
4. Analyze delta_logit_psi and tissue specificity
5. Prioritize by strength, specificity, and pathogenicity
6. Validate experimentally

**Best Practices:**
- Use delta_logit_psi > 2 or < -2 as threshold for strong effects
- Leverage tissue-specific predictions for targeted therapies
- Combine with experimental validation in relevant cell types
- Consider ASO chemistry and delivery in final design

**Limitations:**
- Predictions are probabilistic, not definitive
- Limited to sequence context (100-300 bp)
- Does not model ASO chemistry or delivery
- Best for annotated cassette exons

By integrating MMSplice/MTSplice into the ASO design pipeline, researchers can dramatically reduce the search space of candidate ASOs, prioritize the most promising targets, and accelerate the path from computational prediction to clinical therapy.

---

**Document Version:** 1.0
**Last Updated:** 2024
**License:** CC-BY-4.0
**Contact:** See [GitHub repository](https://github.com/gagneurlab/MMSplice) for support
