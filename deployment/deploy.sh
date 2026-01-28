#!/bin/bash
# Automated deployment script for MMSplice Modal API

set -e  # Exit on error

echo "=========================================="
echo "MMSplice Modal Deployment Script"
echo "=========================================="
echo

# Check if modal is installed
if ! command -v modal &> /dev/null; then
    echo "✗ Modal CLI not found. Installing..."
    pip install modal
    echo "✓ Modal installed"
else
    echo "✓ Modal CLI found"
fi

# Check if authenticated
echo
echo "Checking Modal authentication..."
if ! modal token --help &> /dev/null; then
    echo "✗ Not authenticated. Running 'modal token new'..."
    modal token new
else
    echo "✓ Modal authentication found"
fi

# Deploy the app
echo
echo "=========================================="
echo "Deploying MMSplice API to Modal..."
echo "=========================================="
modal deploy deployment/modal_app.py

echo
echo "✓ Deployment complete!"
echo

# Ask if user wants to setup reference files
echo "=========================================="
echo "Reference Files Setup"
echo "=========================================="
echo
echo "Do you want to download and setup reference files now?"
echo "This will download:"
echo "  - GTF file (~50 MB)"
echo "  - FASTA file (~3 GB)"
echo "  - Total: ~3.05 GB"
echo "  - Time: ~10-15 minutes"
echo
read -p "Setup reference files for GRCh38? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo "Setting up GRCh38 reference files..."
    modal run deployment/modal_app.py
    echo
    echo "✓ Reference files setup complete!"
else
    echo
    echo "Skipping reference file setup."
    echo "You can run it later with:"
    echo "  modal run deployment/modal_app.py"
fi

# Get the deployed URLs
echo
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo
echo "Your MMSplice API is deployed!"
echo
echo "Next steps:"
echo "1. Copy your API URLs from the deployment output above"
echo "2. Test the health endpoint:"
echo "   curl YOUR_HEALTH_URL"
echo
echo "3. Make a prediction:"
echo "   python deployment/test_client.py --url YOUR_PREDICT_URL --vcf tests/data/test.vcf.gz"
echo
echo "See deployment/README_MODAL.md for full documentation."
echo
echo "=========================================="
