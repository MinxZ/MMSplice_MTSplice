# MMSplice Modal Deployment Checklist

## Pre-Deployment

- [ ] Install Modal CLI: `pip install modal`
- [ ] Install requirements: `pip install -r deployment/requirements.txt`
- [ ] Create Modal account at https://modal.com
- [ ] Authenticate: `modal token new`
- [ ] Review [README_MODAL.md](README_MODAL.md) for full details

## Deployment Steps

### 1. Deploy the Application

- [ ] Review [modal_app.py](modal_app.py) configuration
- [ ] Adjust resources if needed (CPU, memory, timeout)
- [ ] Run deployment:
  ```bash
  modal deploy deployment/modal_app.py
  ```
- [ ] Copy and save the API URLs from output

### 2. Setup Reference Files

- [ ] Decide which genome(s) to use (GRCh38, GRCh37, or both)
- [ ] Run setup for GRCh38:
  ```bash
  modal run deployment/modal_app.py
  ```
- [ ] (Optional) Run setup for GRCh37:
  ```bash
  modal run deployment/modal_app.py --genome GRCh37
  ```
- [ ] Wait for downloads to complete (~10-15 minutes per genome)

### 3. Verify Deployment

- [ ] Test health endpoint:
  ```bash
  curl https://YOUR-HEALTH-URL
  ```
- [ ] Check reference files are ready (both GTF and FASTA should be `true`)
- [ ] List available genomes:
  ```bash
  curl https://YOUR-GENOMES-URL
  ```

### 4. Test Predictions

- [ ] Test with included data:
  ```bash
  python deployment/test_client.py \
    --url https://YOUR-PREDICT-URL \
    --vcf tests/data/test.vcf.gz
  ```
- [ ] Verify predictions are returned
- [ ] Check output CSV file is created

### 5. Configuration (Optional)

- [ ] Create `.env` file from `.env.example`
- [ ] Add your API URLs to `.env`
- [ ] Add authentication if needed (see README)
- [ ] Configure CORS if accessing from browser
- [ ] Set up rate limiting for production

## Post-Deployment

### Documentation

- [ ] Document your API URLs for team
- [ ] Share [QUICK_START.md](QUICK_START.md) with users
- [ ] Create examples for your specific use cases
- [ ] Set up monitoring/logging

### Integration

- [ ] Integrate with existing pipeline (if applicable)
- [ ] Create wrapper scripts for common workflows
- [ ] Test batch processing capabilities
- [ ] Set up automated testing

### Monitoring

- [ ] Monitor Modal dashboard for usage
- [ ] Track costs and optimize if needed
- [ ] Set up alerts for errors
- [ ] Review logs regularly:
  ```bash
  modal app logs mmsplice-api
  ```

## Files Created

All deployment files are in the `deployment/` directory:

| File | Description |
|------|-------------|
| [modal_app.py](modal_app.py) | Main Modal application with API endpoints |
| [README_MODAL.md](README_MODAL.md) | Complete deployment documentation |
| [QUICK_START.md](QUICK_START.md) | Quick reference guide |
| [deploy.sh](deploy.sh) | Automated deployment script |
| [test_client.py](test_client.py) | Command-line test client |
| [mmsplice_client.py](mmsplice_client.py) | Python client library |
| [requirements.txt](requirements.txt) | Python dependencies |
| [.env.example](.env.example) | Environment variables template |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | This checklist |

## Common Issues

### Issue: Modal authentication fails
- **Solution**: Run `modal token new` again
- **Verify**: `modal token --help` should work

### Issue: Reference files not found
- **Cause**: Setup script not run or failed
- **Solution**: Run `modal run deployment/modal_app.py`
- **Check**: Visit health endpoint to verify

### Issue: VCF upload fails
- **Cause**: Invalid VCF format or not indexed
- **Solution**:
  ```bash
  bgzip my_variants.vcf
  tabix -p vcf my_variants.vcf.gz
  ```

### Issue: Timeout errors
- **Cause**: Large VCF file or slow network
- **Solution**: Increase timeout in [modal_app.py](modal_app.py:30):
  ```python
  @app.function(timeout=1200)  # 20 minutes
  ```

### Issue: Out of memory
- **Cause**: Too many variants or large reference
- **Solution**: Increase memory in [modal_app.py](modal_app.py:32):
  ```python
  @app.function(memory=16384)  # 16GB
  ```

## Maintenance

### Regular Tasks

- [ ] Monitor usage and costs
- [ ] Review error logs weekly
- [ ] Update Modal SDK: `pip install --upgrade modal`
- [ ] Check for MMSplice updates
- [ ] Backup important prediction results

### Updates

To update the deployment after code changes:

```bash
modal deploy deployment/modal_app.py
```

Modal will rebuild and redeploy automatically.

### Scaling

If you need more performance:

1. **Increase resources** in [modal_app.py](modal_app.py):
   ```python
   @app.function(cpu=8.0, memory=32768)  # 8 CPUs, 32GB RAM
   ```

2. **Enable GPU** (if MMSplice adds GPU support):
   ```python
   @app.function(gpu="T4")  # Add GPU
   ```

3. **Batch processing**: Use `predict.map()` for multiple files

## Cost Optimization

- **Use smaller instance** if predictions are fast enough
- **Cache common predictions** to avoid reprocessing
- **Delete unused genomes** from Volume
- **Monitor free tier usage** ($30/month credit)

## Security Checklist

- [ ] Add API authentication for production
- [ ] Enable HTTPS only (Modal does this by default)
- [ ] Implement rate limiting
- [ ] Add input validation for VCF files
- [ ] Set file upload size limits
- [ ] Review access logs regularly
- [ ] Keep Modal SDK updated

## Support

- **Modal Support**: https://modal.com/docs
- **MMSplice GitHub**: https://github.com/gagneurlab/MMSplice
- **Issues**: Create GitHub issue in this repository

## Next Steps After Deployment

1. **Test thoroughly** with your own data
2. **Document your workflows** specific to your use case
3. **Share with team** and gather feedback
4. **Monitor performance** and optimize as needed
5. **Consider additional features**:
   - Batch upload endpoint
   - WebSocket for real-time updates
   - Result caching
   - Email notifications for large jobs

---

## Quick Command Reference

```bash
# Deploy
modal deploy deployment/modal_app.py

# Setup reference files
modal run deployment/modal_app.py

# Test
python deployment/test_client.py --url URL --vcf file.vcf.gz

# Check health
curl https://YOUR-HEALTH-URL

# View logs
modal app logs mmsplice-api

# Update
modal deploy deployment/modal_app.py

# Stop
modal app stop mmsplice-api
```

---

**Ready to deploy? Start here:**

```bash
bash deployment/deploy.sh
```
