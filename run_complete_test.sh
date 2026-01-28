#!/bin/bash
# Complete end-to-end test workflow for MMSplice
# This script runs all tests and verifies the complete pipeline

set -e  # Exit on error

echo "================================================================================"
echo "MMSplice Complete Test Workflow"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Verify conda environment"
echo "  2. Test package imports"
echo "  3. Check reference files"
echo "  4. Run local predictions"
echo "  5. Generate summary report"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name=$1
    local test_command=$2

    echo ""
    echo "----------------------------------------"
    echo "TEST: $test_name"
    echo "----------------------------------------"

    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED${NC}: $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}: $test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Start tests
echo ""
echo "================================================================================"
echo "Starting Tests"
echo "================================================================================"

# Test 1: Check conda
run_test "Conda Installation" "command -v conda &> /dev/null"

# Test 2: Check if environment exists
if conda env list | grep -q "^mmsplice "; then
    echo -e "${GREEN}✓${NC} Found conda environment: mmsplice"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗${NC} Conda environment 'mmsplice' not found"
    echo ""
    echo "Please create the environment first:"
    echo "  bash install_conda.sh"
    echo ""
    exit 1
fi

# Activate environment
echo ""
echo "Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate mmsplice

# Test 3: Python version
run_test "Python Version" "python -c 'import sys; assert sys.version_info >= (3, 10)'"

# Test 4: Package imports
echo ""
echo "----------------------------------------"
echo "TEST: Package Imports"
echo "----------------------------------------"
python test_installation.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC}: Package Imports"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAILED${NC}: Package Imports"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test 5: Reference files
echo ""
echo "----------------------------------------"
echo "TEST: Reference Files"
echo "----------------------------------------"

GENOME=${GENOME:-GRCh38}
REF_DIR="reference_data"
GTF_FILE="$REF_DIR/$GENOME.gtf"
FASTA_FILE="$REF_DIR/$GENOME.fa"
FAI_FILE="$REF_DIR/$GENOME.fa.fai"

if [ -f "$GTF_FILE" ] && [ -f "$FASTA_FILE" ] && [ -f "$FAI_FILE" ]; then
    echo -e "${GREEN}✓ PASSED${NC}: Reference files found"
    echo "  GTF:   $GTF_FILE ($(du -h "$GTF_FILE" | cut -f1))"
    echo "  FASTA: $FASTA_FILE ($(du -h "$FASTA_FILE" | cut -f1))"
    echo "  Index: $FAI_FILE ($(du -h "$FAI_FILE" | cut -f1))"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ WARNING${NC}: Reference files not found"
    echo ""
    echo "Downloading reference files for $GENOME..."
    if bash download_references.sh "$GENOME"; then
        echo -e "${GREEN}✓ PASSED${NC}: Reference files downloaded"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}: Reference file download"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

# Test 6: Local predictions
echo ""
echo "----------------------------------------"
echo "TEST: Local Predictions"
echo "----------------------------------------"

VCF_FILE="examples/dmd_aso_design.vcf"
OUTPUT_FILE="examples/dmd_predictions_local.json"

if [ ! -f "$VCF_FILE" ]; then
    echo -e "${RED}✗ FAILED${NC}: VCF file not found: $VCF_FILE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
else
    echo "Running predictions on $VCF_FILE..."
    if python test_local_prediction.py "$VCF_FILE" "$OUTPUT_FILE"; then
        echo -e "${GREEN}✓ PASSED${NC}: Local predictions"
        TESTS_PASSED=$((TESTS_PASSED + 1))

        # Check output file
        if [ -f "$OUTPUT_FILE" ]; then
            echo "  Output file: $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"

            # Show summary from JSON
            if command -v jq &> /dev/null; then
                echo ""
                echo "  Prediction Summary:"
                jq -r '.summary | to_entries | .[] | "    \(.key): \(.value)"' "$OUTPUT_FILE" 2>/dev/null || true
            fi
        fi
    else
        echo -e "${RED}✗ FAILED${NC}: Local predictions"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
fi

# Test 7: Output file validation
if [ -f "$OUTPUT_FILE" ]; then
    run_test "Output File Validation" "python -c 'import json; json.load(open(\"$OUTPUT_FILE\"))'"
fi

# Summary
echo ""
echo "================================================================================"
echo "Test Summary"
echo "================================================================================"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo "Total Tests:    $TOTAL_TESTS"
echo -e "Tests Passed:   ${GREEN}$TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "Tests Failed:   ${RED}$TESTS_FAILED${NC}"
else
    echo -e "Tests Failed:   ${GREEN}$TESTS_FAILED${NC}"
fi
echo "Success Rate:   $SUCCESS_RATE%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}================================================================================"
    echo "✅ ALL TESTS PASSED!"
    echo -e "================================================================================${NC}"
    echo ""
    echo "Your MMSplice installation is working correctly!"
    echo ""
    echo "Generated files:"
    echo "  • $OUTPUT_FILE"
    echo "  • ${OUTPUT_FILE%.json}.csv"
    echo ""
    echo "Next steps:"
    echo "  1. Review prediction results: cat $OUTPUT_FILE"
    echo "  2. Read ASO design guide: docs/MMSplice_MTSplice_for_ASO_Design.md"
    echo "  3. Create your own VCF: docs/Creating_VCF_for_ASO_Design.md"
    echo "  4. Run predictions on your data: python test_local_prediction.py your.vcf"
    echo ""
    exit 0
else
    echo -e "${RED}================================================================================"
    echo "⚠ SOME TESTS FAILED"
    echo -e "================================================================================${NC}"
    echo ""
    echo "Please check the errors above and:"
    echo "  1. Review installation: python test_installation.py"
    echo "  2. Check documentation: INSTALL.md"
    echo "  3. Verify reference files: ls -lh reference_data/"
    echo ""
    exit 1
fi
