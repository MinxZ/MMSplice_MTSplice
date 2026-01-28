# Creating VCF Files for ASO Design

## The Challenge

**Antisense Oligonucleotides (ASOs)** work by binding to RNA and blocking splice sites or regulatory elements through **steric hindrance**. However, MMSplice requires **VCF files** which represent DNA sequence variants, not RNA binding events.

**Solution**: We create VCF files that use DNA variants as a **proxy** to approximate the functional effect of ASO binding.

---

## 🔬 Understanding the ASO → VCF Conversion

### What ASOs Actually Do

```
Normal Splicing:
  Exon 50    Intron       Exon 51       Intron    Exon 52
  ========].............[==========]............[========
                         ↑         ↑
                    Acceptor    Donor
                        |           |
                        └─Spliceosome binds here

With ASO Blocking Donor Site:
  Exon 50    Intron       Exon 51       Intron    Exon 52
  ========].............[==========]............[========
                                    ↑
                                  Donor
                                    |
                            🧬 ASO binds here (blocks spliceosome)
                                    ↓
                            Exon 51 gets SKIPPED
```

### How We Represent This in VCF

Since MMSplice predicts effects based on **sequence changes**, we approximate ASO blocking by introducing variants that would **disrupt the same elements**:

| ASO Target | ASO Effect | VCF Proxy Variant |
|-----------|-----------|-------------------|
| Donor site (GT) | Blocks spliceosome access | Change GT → AT (disrupts consensus) |
| Acceptor site (AG) | Blocks spliceosome access | Change AG → AA (disrupts consensus) |
| ESE (Exonic Splicing Enhancer) | Blocks SR protein binding | SNP in ESE motif |
| ISS (Intronic Splicing Silencer) | Blocks repressor binding | SNP in ISS motif |

**Important**: The VCF variant is an **approximation**. The actual ASO effect may differ slightly, but the **direction** (skipping vs. inclusion) should be similar.

---

## 📝 Step-by-Step: Creating ASO VCF Files

### Step 1: Identify Your Target Exon

First, determine which exon you want to skip or include.

**Example: DMD Exon 51 (Duchenne Muscular Dystrophy)**

```bash
# Look up exon coordinates in GTF file
grep "ENSG00000198947" gencode.gtf | grep "exon_number \"51\""
```

**Result**:
```
chrX  protein_coding  exon  31791568  31791719  .  -  .  gene_name "DMD"; exon_number "51"
```

**Key Information**:
- **Chromosome**: chrX
- **Start**: 31,791,568
- **End**: 31,791,719
- **Strand**: - (minus strand)
- **Length**: 152 bp

### Step 2: Identify Splice Sites

For **minus strand** genes (like DMD), coordinates are reversed:

```
Minus Strand (-):
┌─────────────────────────────────────────────────┐
│  Genomic DNA (5' → 3'):                         │
│  ...intron... [EXON 51] ...intron...            │
│               ↑        ↑                         │
│            END(51)  START(51)                    │
│           31791568  31791719                     │
│                                                  │
│  RNA direction (3' ← 5'):                       │
│  ...intron... [EXON 51] ...intron...            │
│               ↑        ↑                         │
│           Acceptor  Donor                        │
└─────────────────────────────────────────────────┘

Splice Sites:
- Donor (5' splice site in RNA): Near position 31,791,719
- Acceptor (3' splice site in RNA): Near position 31,791,568
```

**For plus strand** genes, it's straightforward:
- Donor = end of exon
- Acceptor = start of exon

### Step 3: Design ASO Binding Sites

**Common ASO Targets** for exon skipping:

#### Target A: Donor Splice Site
```
Sequence around donor (minus strand):
Position: 31791715-31791720
Sequence: ...CAG|GT.... (exon|intron boundary)
           ↑     ↑
         Exon  Donor consensus (GT)

ASO Strategy: Design 18-25mer ASO covering the GT dinucleotide
ASO sequence: 5'-ACTTGAGTCAGGGTACTTG-3' (example)
```

#### Target B: Acceptor Splice Site
```
Sequence around acceptor (minus strand):
Position: 31791565-31791570
Sequence: ...AG|GCT... (intron|exon boundary)
           ↑   ↑
    Acceptor   Exon
    (AG)

ASO Strategy: Design 18-25mer ASO covering the AG dinucleotide
ASO sequence: 5'-CTTAGGCTAGCAGATCTTG-3' (example)
```

#### Target C: Exonic Splicing Enhancer (ESE)
```
Exon sequence scan for ESE motifs:
Position: 31791600-31791610
Sequence: ...GAAGAAGAC... (potential SR protein binding site)

ASO Strategy: Design ASO to block this enhancer
ASO sequence: 5'-GTCTTCTTCAGGCTAAGGA-3' (example)
```

### Step 4: Create VCF Variants as Proxies

Now we represent each ASO as a VCF variant:

#### Method 1: Single Nucleotide Substitution (SNP)

**Simplest approach** - change one critical nucleotide at the ASO binding site:

```vcf
##fileformat=VCFv4.2
##reference=GRCh38
##contig=<ID=chrX,length=156040895>
##INFO=<ID=ASO_NAME,Number=1,Type=String,Description="ASO identifier">
##INFO=<ID=TARGET_TYPE,Number=1,Type=String,Description="Target element type">
##INFO=<ID=ASO_SEQ,Number=1,Type=String,Description="ASO sequence (5' to 3')">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chrX	31791719	ASO_DMD_Ex51_Donor	G	A	60	PASS	ASO_NAME=DMD_Ex51_Donor_v1;TARGET_TYPE=donor_site;ASO_SEQ=ACTTGAGTCAGGGTACTTG
chrX	31791568	ASO_DMD_Ex51_Acceptor	A	T	60	PASS	ASO_NAME=DMD_Ex51_Acc_v1;TARGET_TYPE=acceptor_site;ASO_SEQ=CTTAGGCTAGCAGATCTTG
chrX	31791605	ASO_DMD_Ex51_ESE	G	C	60	PASS	ASO_NAME=DMD_Ex51_ESE_v1;TARGET_TYPE=ESE_blocker;ASO_SEQ=GTCTTCTTCAGGCTAAGGA
```

**Rationale**:
- Donor site: G→A disrupts GT consensus (GT becomes AT)
- Acceptor site: A→T disrupts AG consensus (AG becomes TG)
- ESE: G→C disrupts enhancer motif

#### Method 2: Small Deletion

**More aggressive** - delete the critical dinucleotide:

```vcf
##fileformat=VCFv4.2
##reference=GRCh38
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chrX	31791718	ASO_DMD_Ex51_Donor_del	CGT	C	60	PASS	ASO_NAME=DMD_Ex51_Donor_del;TARGET_TYPE=donor_site
chrX	31791567	ASO_DMD_Ex51_Acc_del	AAG	A	60	PASS	ASO_NAME=DMD_Ex51_Acc_del;TARGET_TYPE=acceptor_site
```

**Rationale**:
- Deletes the critical GT (donor) or AG (acceptor) dinucleotide
- Stronger disruption, may better approximate complete ASO blocking

#### Method 3: Representing the ASO Binding Footprint

**Most realistic** - multiple SNPs across ASO binding region:

```vcf
##fileformat=VCFv4.2
##reference=GRCh38
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chrX	31791710	ASO_DMD_Ex51_Donor_pos1	A	T	60	PASS	ASO_NAME=DMD_Ex51_Donor_multi;ASO_POS=1
chrX	31791714	ASO_DMD_Ex51_Donor_pos5	C	G	60	PASS	ASO_NAME=DMD_Ex51_Donor_multi;ASO_POS=5
chrX	31791719	ASO_DMD_Ex51_Donor_pos10	G	A	60	PASS	ASO_NAME=DMD_Ex51_Donor_multi;ASO_POS=10
```

**Rationale**: Multiple variants across the ASO binding site simulate the full blocking effect

---

## 🛠️ Practical Tools & Scripts

### Python Script: Automated VCF Creation for ASOs

```python
#!/usr/bin/env python3
"""
Create VCF file for ASO design targets
"""
import sys
from datetime import date

def create_aso_vcf(aso_targets, genome_version='GRCh38', output_file='aso_designs.vcf'):
    """
    Create VCF file from ASO target list

    Args:
        aso_targets: List of dicts with keys:
            - chrom: chromosome (e.g., 'chrX')
            - pos: genomic position (1-based)
            - id: variant ID
            - ref: reference allele
            - alt: alternative allele
            - info: INFO field (optional)
    """

    # VCF header
    vcf_header = f"""##fileformat=VCFv4.2
##fileDate={date.today().strftime('%Y%m%d')}
##source=ASO_Design_Pipeline
##reference={genome_version}
##INFO=<ID=ASO_NAME,Number=1,Type=String,Description="ASO identifier">
##INFO=<ID=TARGET_TYPE,Number=1,Type=String,Description="Target element: donor_site, acceptor_site, ESE, ISS">
##INFO=<ID=ASO_SEQ,Number=1,Type=String,Description="ASO oligonucleotide sequence 5' to 3'">
##INFO=<ID=ASO_LENGTH,Number=1,Type=Integer,Description="ASO length in nucleotides">
##INFO=<ID=GENE,Number=1,Type=String,Description="Target gene symbol">
##INFO=<ID=EXON,Number=1,Type=String,Description="Target exon number">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
"""

    with open(output_file, 'w') as f:
        f.write(vcf_header)

        for target in aso_targets:
            chrom = target['chrom']
            pos = target['pos']
            var_id = target['id']
            ref = target['ref']
            alt = target['alt']
            qual = target.get('qual', '60')
            filt = target.get('filter', 'PASS')
            info = target.get('info', '.')

            line = f"{chrom}\t{pos}\t{var_id}\t{ref}\t{alt}\t{qual}\t{filt}\t{info}\n"
            f.write(line)

    print(f"✓ VCF file created: {output_file}")
    print(f"  Total ASO targets: {len(aso_targets)}")

# Example usage
if __name__ == "__main__":

    # Define ASO targets for DMD exon 51
    dmd_exon51_asos = [
        {
            'chrom': 'chrX',
            'pos': 31791719,
            'id': 'ASO_DMD_Ex51_Donor_v1',
            'ref': 'G',
            'alt': 'A',
            'info': 'ASO_NAME=DMD_Ex51_Donor_v1;TARGET_TYPE=donor_site;GENE=DMD;EXON=51;ASO_SEQ=ACTTGAGTCAGGGTACTTG;ASO_LENGTH=19'
        },
        {
            'chrom': 'chrX',
            'pos': 31791568,
            'id': 'ASO_DMD_Ex51_Acceptor_v1',
            'ref': 'A',
            'alt': 'T',
            'info': 'ASO_NAME=DMD_Ex51_Acc_v1;TARGET_TYPE=acceptor_site;GENE=DMD;EXON=51;ASO_SEQ=CTTAGGCTAGCAGATCTTG;ASO_LENGTH=19'
        },
        {
            'chrom': 'chrX',
            'pos': 31791605,
            'id': 'ASO_DMD_Ex51_ESE_v1',
            'ref': 'G',
            'alt': 'C',
            'info': 'ASO_NAME=DMD_Ex51_ESE_v1;TARGET_TYPE=ESE_blocker;GENE=DMD;EXON=51;ASO_SEQ=GTCTTCTTCAGGCTAAGGA;ASO_LENGTH=19'
        },
        {
            'chrom': 'chrX',
            'pos': 31791650,
            'id': 'ASO_DMD_Ex51_ESE_v2',
            'ref': 'C',
            'alt': 'T',
            'info': 'ASO_NAME=DMD_Ex51_ESE_v2;TARGET_TYPE=ESE_blocker;GENE=DMD;EXON=51;ASO_SEQ=CTAGGCTAAGCTTGAGTCA;ASO_LENGTH=19'
        },
    ]

    # Create VCF file
    create_aso_vcf(dmd_exon51_asos, output_file='dmd_exon51_asos.vcf')

    print("\n✓ Next steps:")
    print("  1. Compress: bgzip dmd_exon51_asos.vcf")
    print("  2. Index: tabix -p vcf dmd_exon51_asos.vcf.gz")
    print("  3. Run MMSplice on this VCF file")
```

### Running the Script

```bash
# 1. Create the Python script
python3 create_aso_vcf.py

# 2. Compress and index
bgzip dmd_exon51_asos.vcf
tabix -p vcf dmd_exon51_asos.vcf.gz

# 3. Run MMSplice
python3 -c "
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

dl = SplicingVCFDataloader(
    'gencode.v38.gtf',
    'GRCh38.fa',
    'dmd_exon51_asos.vcf.gz'
)

model = MMSplice()
predictions = predict_all_table(model, dl, pathogenicity=True)
predictions.to_csv('dmd_exon51_predictions.csv', index=False)
print('Predictions saved!')
"
```

---

## 📊 Real-World Example: Complete Workflow

### Scenario: Design ASOs for SMN2 Exon 7 Inclusion (SMA Therapy)

**Goal**: Increase SMN2 exon 7 inclusion by blocking ISS-N1 silencer

#### Step 1: Find ISS-N1 Location

```bash
# SMN2 exon 7 is at chr5:70,247,724-70,247,807 (GRCh38)
# ISS-N1 is at positions 10-21 within exon 7
# Genomic position: chr5:70,247,773-70,247,784
```

#### Step 2: Design ASOs Targeting ISS-N1

ISS-N1 sequence: `CCTTTCATAAA`

**ASO Design Strategy**:
- **ASO-1**: Cover positions 1-6 of ISS-N1
- **ASO-2**: Cover positions 6-11 of ISS-N1
- **ASO-3**: Cover entire ISS-N1

```python
# create_smn2_aso_vcf.py
from create_aso_vcf import create_aso_vcf

smn2_exon7_asos = [
    # ASO-1: Disrupt start of ISS-N1
    {
        'chrom': 'chr5',
        'pos': 70247773,
        'id': 'ASO_SMN2_Ex7_ISS_N1_pos1',
        'ref': 'C',
        'alt': 'T',
        'info': 'ASO_NAME=Nusinersen_like_pos1;TARGET_TYPE=ISS_blocker;GENE=SMN2;EXON=7;ASO_SEQ=ATTCACTTTCATAATGCTGG;ASO_LENGTH=20'
    },
    # ASO-2: Disrupt middle of ISS-N1
    {
        'chrom': 'chr5',
        'pos': 70247778,
        'id': 'ASO_SMN2_Ex7_ISS_N1_pos6',
        'ref': 'C',
        'alt': 'G',
        'info': 'ASO_NAME=Nusinersen_like_pos6;TARGET_TYPE=ISS_blocker;GENE=SMN2;EXON=7;ASO_SEQ=ATGCTGGATTCACTTTCATA;ASO_LENGTH=20'
    },
    # ASO-3: Disrupt end of ISS-N1
    {
        'chrom': 'chr5',
        'pos': 70247783,
        'id': 'ASO_SMN2_Ex7_ISS_N1_pos11',
        'ref': 'A',
        'alt': 'G',
        'info': 'ASO_NAME=Nusinersen_like_pos11;TARGET_TYPE=ISS_blocker;GENE=SMN2;EXON=7;ASO_SEQ=GCTGGATTCACTTTCATAATGC;ASO_LENGTH=22'
    },
]

create_aso_vcf(smn2_exon7_asos, output_file='smn2_exon7_asos.vcf')
```

#### Step 3: Run MMSplice with Tissue-Specific Predictions

```python
from mmsplice.vcf_dataloader import SplicingVCFDataloader
from mmsplice import MMSplice, predict_all_table

# Tissue-specific predictions (important for CNS-targeted therapy)
dl = SplicingVCFDataloader(
    'gencode.v38.gtf',
    'GRCh38.fa',
    'smn2_exon7_asos.vcf.gz',
    tissue_specific=True
)

model = MMSplice()
predictions = predict_all_table(
    model, dl,
    pathogenicity=True,
    natural_scale=True,
    ref_psi_version='grch38'
)

# Filter for strong inclusion effects
inclusion_asos = predictions[
    (predictions['gene_name'] == 'SMN2') &
    (predictions['delta_logit_psi'] > 2)  # Strong inclusion
].copy()

# Check brain/spinal cord specificity
if 'Brain - Cortex' in predictions.columns:
    inclusion_asos['brain_effect'] = predictions['Brain - Cortex']
    inclusion_asos['spinal_effect'] = predictions['Brain - Spinal cord']

print("Top ASO Candidates for SMN2 Exon 7 Inclusion:")
print(inclusion_asos[['ID', 'delta_logit_psi', 'brain_effect', 'spinal_effect']])

# Expected output:
# ASO_SMN2_Ex7_ISS_N1_pos6 should show strong positive delta_logit_psi
# (similar to clinical ASO Nusinersen)
```

---

## 🎯 Best Practices for ASO → VCF Conversion

### 1. Choose the Right Proxy Method

| Goal | Recommended Method | Rationale |
|------|-------------------|-----------|
| **Quick screening** | Single SNP at critical position | Fast, simple |
| **Accurate prediction** | Small deletion of critical motif | Better approximates blocking |
| **Conservative estimate** | Multiple SNPs across binding site | Captures distributed effects |

### 2. Position Selection Strategy

**For Donor Site ASOs** (exon skipping):
```
Priority 1: Disrupt GT dinucleotide (positions +1, +2 of intron)
Priority 2: Disrupt exonic portion (positions -3 to -1 of exon)
Priority 3: Disrupt intronic enhancers
```

**For Acceptor Site ASOs** (exon skipping):
```
Priority 1: Disrupt AG dinucleotide (positions -2, -1 of exon)
Priority 2: Disrupt polypyrimidine tract (positions -20 to -3)
Priority 3: Disrupt branch point (positions -18 to -40)
```

**For ISS Blocking ASOs** (exon inclusion):
```
Priority 1: Disrupt repressor binding motif center
Priority 2: Disrupt motif boundaries
Priority 3: Multiple positions across entire motif
```

### 3. Multiple Variants per ASO

For robustness, create **multiple VCF variants** for each ASO:

```python
# Example: 3 different representations of the same ASO
aso_variants = [
    # Variant 1: SNP at position 1
    {'pos': 31791719, 'ref': 'G', 'alt': 'A', 'id': 'ASO_v1_SNP_pos1'},
    # Variant 2: SNP at position 5
    {'pos': 31791715, 'ref': 'C', 'alt': 'T', 'id': 'ASO_v1_SNP_pos5'},
    # Variant 3: Deletion of GT
    {'pos': 31791718, 'ref': 'CGT', 'alt': 'C', 'id': 'ASO_v1_del_GT'},
]

# Compare predictions across all three
# Consensus prediction is more reliable
```

### 4. Validate with Known ASOs

Test your VCF creation method on **approved ASO drugs**:

| Drug | Disease | Target | Expected MMSplice Result |
|------|---------|--------|-------------------------|
| Eteplirsen | DMD | Exon 51 donor | delta_logit_psi < -2 |
| Nusinersen | SMA | SMN2 exon 7 ISS-N1 | delta_logit_psi > 2 |
| Golodirsen | DMD | Exon 53 donor | delta_logit_psi < -2 |

If your VCF representation predicts the correct direction for these, it's likely valid.

---

## ⚠️ Important Caveats

### 1. VCF is an Approximation

**Reality**:
```
ASO → Binds RNA → Steric blocking → Prevents protein binding
```

**VCF Proxy**:
```
Variant → Changes DNA → Alters RNA sequence → Changes protein binding
```

**These are DIFFERENT mechanisms**, so predictions are directional guides, not exact quantifications.

### 2. ASO Chemistry Not Modeled

VCF variants don't capture:
- ASO modifications (2'-MOE, PMO, etc.)
- Binding affinity differences
- Off-target hybridization
- Pharmacokinetics/delivery

### 3. Context-Dependent Effects

The same VCF variant might give different predictions than an actual ASO because:
- ASOs can cause local RNA structure changes
- ASOs might recruit RNase H (depends on chemistry)
- Cellular ASO concentration varies

---

## 📈 Interpreting MMSplice Results for ASOs

After running MMSplice on your ASO VCF file:

### Strong Candidates
```
delta_logit_psi < -2  (for exon skipping ASOs)
delta_logit_psi > +2  (for exon inclusion ASOs)
```

### Module Analysis
Check which splice module drives the effect:
- `alt_donor - ref_donor` very negative → Donor-targeting ASO is effective
- `alt_exon - ref_exon` very positive → ESE-blocking ASO works

### Tissue Specificity
For therapeutic ASOs, check tissue-specific predictions:
- DMD: Strong effect in `Muscle - Skeletal`
- SMA: Strong effect in `Brain - Spinal cord`
- Minimal effects in off-target tissues

---

## 🔬 Next Steps After VCF Creation

1. **Run MMSplice predictions**
2. **Rank ASO candidates** by predicted effect strength
3. **Filter by tissue specificity** (if using MTSplice)
4. **Synthesize top 3-5 ASOs** for experimental validation
5. **Test in vitro** (minigene assays, patient cells)
6. **Iterate**: Refine ASO designs based on experimental results

---

## 📚 Example VCF Files

I've included several example VCF files in this repository:

- `examples/dmd_exon51_asos.vcf` - DMD exon 51 skipping ASOs
- `examples/smn2_exon7_asos.vcf` - SMA exon 7 inclusion ASOs
- `examples/multi_target_asos.vcf` - Multiple genes/exons

See the `examples/` directory for complete, ready-to-use VCF files with different ASO design strategies.

---

**Key Takeaway**: Creating VCF files for ASO design requires mapping your ASO binding sites to proxy DNA variants that approximate the functional blocking effect. While not perfect, this approach provides valuable directional predictions for ASO efficacy.
