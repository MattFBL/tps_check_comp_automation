# Render Deployment Guide - Company TPS Automation

This guide will walk you through deploying the company-based TPS automation to Render.

## Prerequisites

- GitHub account (already have: MattFBL)
- Render account (https://render.com)
- HubSpot Access Token (with company read/write permissions)
- TPS API Key

## Step 1: Push to GitHub

First, ensure all changes are committed to your GitHub repository:

```powershell
cd "c:\Users\MattJones\OneDrive - Salus Capital Partners Limited\Desktop\TPS_Check_Comp_Automation"
git add .
git commit -m "Update TPS automation for company properties instead of contacts"
git push origin main
```

## Step 2: Create New Render Service

1. Go to https://render.com/dashboard
2. Click **"New +"** button
3. Select **"Web Service"**
4. Connect your GitHub repository: `MattFBL/tps_check_conumbers`
5. Choose branch: `main`
6. Configure the service:

### Service Settings

- **Name:** `tps-automation-companies` (or similar)
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --workers 2 --timeout 30`
- **Plan:** `Free` (or paid if needed)
- **Region:** `Frankfurt` (EU - GDPR compliant)

## Step 3: Set Environment Variables

In the Render dashboard, go to **Environment** and add:

```
HUBSPOT_ACCESS_TOKEN=your_token_here
TPS_API_KEY=your_api_key_here
TPS_ENDPOINT=https://api.tpsservices.co.uk/check
HUBSPOT_ENDPOINT=https://api.hubapi.com/crm/v3/objects/companies
BATCH_SIZE=10000
PORT=5000
```

## Step 4: Deploy

1. Click **"Create Web Service"**
2. Render will automatically build and deploy
3. Once deployed, you'll get a URL like: `https://tps-automation-companies.onrender.com`

## Step 5: Configure HubSpot Webhook

1. Go to **HubSpot Settings** → **Integrations** → **Webhooks**
2. Click **"Create webhook"**
3. Set **Target URL:** `https://tps-automation-companies.onrender.com/api/webhooks/hubspot`
4. Subscribe to events:
   - ✅ `company.creation`
   - ✅ `company.propertyChange` (select "phone" property)
5. Click **"Create"**

## Step 6: Test the Webhook

1. In HubSpot, create or update a company with a phone number
2. Check Render logs: **Dashboard** → Your service → **Logs**
3. You should see output like:
```
✅ WEBHOOK ENDPOINT HIT!
🏢 Processing company 12345
  Checking phone: 07700900000
  ✓ Updated company 12345: Not Listed
✓ Webhook processed successfully
```

## Health Check

Monitor your service:
```bash
curl https://tps-automation-companies.onrender.com/health
```

Should return: `{"status": "ok", "processed_events": X}`

## Troubleshooting

### Webhook not triggering?
- Verify Target URL in HubSpot settings matches your Render URL
- Check HubSpot webhook logs
- Check Render service logs for errors

### "502 Bad Gateway" error?
- Check Render logs for Python errors
- Verify all environment variables are set
- Restart the service

### Service spinning (restarting constantly)?
- Check for errors in the logs
- Verify `requirements.txt` has all dependencies
- Check Python syntax in `app.py`

## Monitoring & Logging

### View Live Logs
```
Render Dashboard → Your Service → Logs
```

### Key Events to Look For
```
✅ WEBHOOK ENDPOINT HIT!        ← Webhook received
🏢 Processing company X          ← Processing started
  Checking phone: XXXXXXXXX     ← TPS check in progress
  ✓ Updated company X: Listed   ← Success
✓ Webhook processed successfully ← Complete
```

### Common Issues in Logs
```
✗ Webhook error: ...            ← Processing failed
Error updating HubSpot: ...     ← Token/permission issue
TPS API error (XXX): ...        ← TPS API problem
```

## Stopping/Restarting

- **Pause service:** Render Dashboard → Service → Settings → Pause
- **Restart service:** Render Dashboard → Service → Manual Deploy
- **Delete service:** Render Dashboard → Service → Settings → Delete

## Managing Multiple Services

If you have both contact AND company automations:

| Service | URL | Webhook | Properties |
|---------|-----|---------|-----------|
| Contacts | `tps-automation-contacts.onrender.com` | `/api/webhooks/hubspot` | phone, mobilephone |
| Companies | `tps-automation-companies.onrender.com` | `/api/webhooks/hubspot` | phone |

Each needs:
- Separate Render service
- Separate GitHub branch (optional but recommended)
- Separate HubSpot webhook configuration

## Cost Considerations

- **Free tier:** 0.5 CPU, 512MB RAM - suitable for this workload
- **Paid tiers:** For higher traffic (> 1000 events/day)
- **Execution time:** ~2-5 seconds per TPS check

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create Render service
3. ✅ Set environment variables
4. ✅ Configure HubSpot webhook
5. ✅ Test with a company update
6. ✅ Monitor logs for issues

---

**Questions?** Check Render documentation: https://render.com/docs
