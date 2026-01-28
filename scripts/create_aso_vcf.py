#!/usr/bin/env python3
"""
Create VCF files for ASO design
Converts ASO binding sites to VCF variants for MMSplice prediction

Usage:
    python create_aso_vcf.py --help
    python create_aso_vcf.py examples/dmd_exon51.yaml
"""

import argparse
import sys
from datetime import date
from typing import List, Dict
import yaml


def create_aso_vcf(aso_targets: List[Dict],
                   genome_version: str = 'GRCh38',
                   output_file: str = 'aso_designs.vcf') -> None:
    """
    Create VCF file from ASO target list

    Args:
        aso_targets: List of dicts with keys:
            - chrom: chromosome (e.g., 'chrX')
            - pos: genomic position (1-based)
            - id: variant ID
            - ref: reference allele
            - alt: alternative allele
            - info: INFO field dict (optional)
        genome_version: Reference genome version
        output_file: Output VCF filename
    """

    # VCF header
    vcf_header = f"""##fileformat=VCFv4.2
##fileDate={date.today().strftime('%Y%m%d')}
##source=ASO_Design_Pipeline_v1.0
##reference={genome_version}
##INFO=<ID=ASO_NAME,Number=1,Type=String,Description="ASO identifier">
##INFO=<ID=TARGET_TYPE,Number=1,Type=String,Description="Target element: donor_site, acceptor_site, ESE, ISS, ESS, ISE">
##INFO=<ID=ASO_SEQ,Number=1,Type=String,Description="ASO oligonucleotide sequence 5' to 3'">
##INFO=<ID=ASO_LENGTH,Number=1,Type=Integer,Description="ASO length in nucleotides">
##INFO=<ID=GENE,Number=1,Type=String,Description="Target gene symbol">
##INFO=<ID=EXON,Number=1,Type=String,Description="Target exon number">
##INFO=<ID=DESIGN_GOAL,Number=1,Type=String,Description="ASO goal: skip_exon or include_exon">
##INFO=<ID=CHEMISTRY,Number=1,Type=String,Description="ASO chemistry: 2MOE, PMO, PNA, etc.">
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

            # Build INFO field
            info_dict = target.get('info', {})
            if info_dict:
                info_parts = [f"{k}={v}" for k, v in info_dict.items()]
                info = ';'.join(info_parts)
            else:
                info = '.'

            line = f"{chrom}\t{pos}\t{var_id}\t{ref}\t{alt}\t{qual}\t{filt}\t{info}\n"
            f.write(line)

    print(f"✓ VCF file created: {output_file}")
    print(f"  Total ASO targets: {len(aso_targets)}")
    print(f"\n✓ Next steps:")
    print(f"  1. Compress: bgzip {output_file}")
    print(f"  2. Index: tabix -p vcf {output_file}.gz")
    print(f"  3. Run MMSplice predictions")


def load_aso_config(config_file: str) -> List[Dict]:
    """
    Load ASO targets from YAML configuration file

    Example YAML format:
    ---
    genome_version: GRCh38
    targets:
      - chrom: chrX
        pos: 31791719
        id: ASO_DMD_Ex51_Donor
        ref: G
        alt: A
        info:
          ASO_NAME: DMD_Ex51_Donor_v1
          TARGET_TYPE: donor_site
          GENE: DMD
          EXON: "51"
          ASO_SEQ: ACTTGAGTCAGGGTACTTG
          ASO_LENGTH: 19
          DESIGN_GOAL: skip_exon
    """
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    return config.get('targets', []), config.get('genome_version', 'GRCh38')


# Predefined ASO design templates
DMD_EXON51_ASOS = [
    {
        'chrom': 'chrX',
        'pos': 31791719,
        'id': 'ASO_DMD_Ex51_Donor_v1',
        'ref': 'G',
        'alt': 'A',
        'info': {
            'ASO_NAME': 'DMD_Ex51_Donor_v1',
            'TARGET_TYPE': 'donor_site',
            'GENE': 'DMD',
            'EXON': '51',
            'ASO_SEQ': 'ACTTGAGTCAGGGTACTTG',
            'ASO_LENGTH': '19',
            'DESIGN_GOAL': 'skip_exon',
            'CHEMISTRY': '2MOE'
        }
    },
    {
        'chrom': 'chrX',
        'pos': 31791568,
        'id': 'ASO_DMD_Ex51_Acceptor_v1',
        'ref': 'A',
        'alt': 'T',
        'info': {
            'ASO_NAME': 'DMD_Ex51_Acc_v1',
            'TARGET_TYPE': 'acceptor_site',
            'GENE': 'DMD',
            'EXON': '51',
            'ASO_SEQ': 'CTTAGGCTAGCAGATCTTG',
            'ASO_LENGTH': '19',
            'DESIGN_GOAL': 'skip_exon',
            'CHEMISTRY': '2MOE'
        }
    },
    {
        'chrom': 'chrX',
        'pos': 31791605,
        'id': 'ASO_DMD_Ex51_ESE_v1',
        'ref': 'G',
        'alt': 'C',
        'info': {
            'ASO_NAME': 'DMD_Ex51_ESE_v1',
            'TARGET_TYPE': 'ESE_blocker',
            'GENE': 'DMD',
            'EXON': '51',
            'ASO_SEQ': 'GTCTTCTTCAGGCTAAGGA',
            'ASO_LENGTH': '19',
            'DESIGN_GOAL': 'skip_exon',
            'CHEMISTRY': '2MOE'
        }
    },
]


SMN2_EXON7_ASOS = [
    {
        'chrom': 'chr5',
        'pos': 70247773,
        'id': 'ASO_SMN2_Ex7_ISS_N1_pos1',
        'ref': 'C',
        'alt': 'T',
        'info': {
            'ASO_NAME': 'Nusinersen_like_pos1',
            'TARGET_TYPE': 'ISS_blocker',
            'GENE': 'SMN2',
            'EXON': '7',
            'ASO_SEQ': 'ATTCACTTTCATAATGCTGG',
            'ASO_LENGTH': '20',
            'DESIGN_GOAL': 'include_exon',
            'CHEMISTRY': '2MOE'
        }
    },
    {
        'chrom': 'chr5',
        'pos': 70247778,
        'id': 'ASO_SMN2_Ex7_ISS_N1_pos6',
        'ref': 'C',
        'alt': 'G',
        'info': {
            'ASO_NAME': 'Nusinersen_like_pos6',
            'TARGET_TYPE': 'ISS_blocker',
            'GENE': 'SMN2',
            'EXON': '7',
            'ASO_SEQ': 'ATGCTGGATTCACTTTCATA',
            'ASO_LENGTH': '20',
            'DESIGN_GOAL': 'include_exon',
            'CHEMISTRY': '2MOE'
        }
    },
    {
        'chrom': 'chr5',
        'pos': 70247783,
        'id': 'ASO_SMN2_Ex7_ISS_N1_pos11',
        'ref': 'A',
        'alt': 'G',
        'info': {
            'ASO_NAME': 'Nusinersen_like_pos11',
            'TARGET_TYPE': 'ISS_blocker',
            'GENE': 'SMN2',
            'EXON': '7',
            'ASO_SEQ': 'GCTGGATTCACTTTCATAATGC',
            'ASO_LENGTH': '22',
            'DESIGN_GOAL': 'include_exon',
            'CHEMISTRY': '2MOE'
        }
    },
]


def main():
    parser = argparse.ArgumentParser(
        description='Create VCF files for ASO design',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use predefined template for DMD exon 51
  python create_aso_vcf.py --template dmd_exon51 -o dmd_ex51.vcf

  # Use predefined template for SMN2 exon 7
  python create_aso_vcf.py --template smn2_exon7 -o smn2_ex7.vcf

  # Load custom ASO designs from YAML file
  python create_aso_vcf.py --config my_asos.yaml -o my_asos.vcf

  # Create from YAML and auto-compress
  python create_aso_vcf.py --config my_asos.yaml -o my_asos.vcf --compress
        """
    )

    parser.add_argument('--template', '-t',
                       choices=['dmd_exon51', 'smn2_exon7'],
                       help='Use predefined ASO template')

    parser.add_argument('--config', '-c',
                       help='YAML configuration file with ASO targets')

    parser.add_argument('--output', '-o',
                       default='aso_designs.vcf',
                       help='Output VCF filename (default: aso_designs.vcf)')

    parser.add_argument('--genome', '-g',
                       default='GRCh38',
                       choices=['GRCh37', 'GRCh38', 'hg19', 'hg38'],
                       help='Reference genome version (default: GRCh38)')

    parser.add_argument('--compress',
                       action='store_true',
                       help='Auto-compress and index VCF file (requires bgzip and tabix)')

    args = parser.parse_args()

    # Determine ASO targets
    if args.template == 'dmd_exon51':
        print("Using DMD Exon 51 template (3 ASO designs)")
        targets = DMD_EXON51_ASOS
        genome_version = args.genome
    elif args.template == 'smn2_exon7':
        print("Using SMN2 Exon 7 template (3 ASO designs)")
        targets = SMN2_EXON7_ASOS
        genome_version = args.genome
    elif args.config:
        print(f"Loading ASO designs from: {args.config}")
        targets, genome_version = load_aso_config(args.config)
        if args.genome != 'GRCh38':  # Override if specified
            genome_version = args.genome
    else:
        parser.error("Must specify either --template or --config")

    # Create VCF
    create_aso_vcf(targets, genome_version=genome_version, output_file=args.output)

    # Optionally compress and index
    if args.compress:
        import subprocess
        try:
            print("\nCompressing VCF file...")
            subprocess.run(['bgzip', '-f', args.output], check=True)
            print(f"✓ Compressed: {args.output}.gz")

            print("Indexing VCF file...")
            subprocess.run(['tabix', '-p', 'vcf', f'{args.output}.gz'], check=True)
            print(f"✓ Indexed: {args.output}.gz.tbi")

            print(f"\n✓ Ready to use: {args.output}.gz")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error during compression/indexing: {e}")
            print("  Make sure bgzip and tabix are installed")
        except FileNotFoundError:
            print("✗ bgzip or tabix not found in PATH")
            print("  Install with: conda install -c bioconda htslib")


if __name__ == "__main__":
    main()
