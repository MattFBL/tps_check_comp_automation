# TPS Check Automation - HubSpot Webhook Integration ✅

Automatically check phone numbers against the TPS (Telephone Preference Service) database whenever a contact is created or updated in HubSpot.

## How It Works

1. **Contact Update in HubSpot** → 2. **Webhook Sent** → 3. **TPS Check** → 4. **Status Updated in HubSpot**

When you create or update a contact in HubSpot with a phone number:
- A webhook is triggered
- The phone number is checked against the TPS API
- The contact is automatically updated with the TPS status: **"Listed"** or **"Not Listed"**

## Setup

### Prerequisites
- Python 3.11+
- HubSpot account with webhook integration
- TPS API credentials

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure credentials:**
Copy `env/.env.example` to `env/.env` and fill in:
```
HUBSPOT_ACCESS_TOKEN=pat-eu1-xxxxx
TPS_API_KEY=xxxxx
TPS_ENDPOINT=https://api.tpsservices.co.uk/check
HUBSPOT_ENDPOINT=https://api.hubapi.com/crm/v3/objects/contacts
```

3. **Start the webhook server:**
```bash
python app.py
```

4. **Expose to internet (for development/testing):**
```bash
ngrok http 5000
```

5. **Configure HubSpot webhook:**
- Go to HubSpot Settings → Integrations → Webhooks
- Create webhook with Target URL: `https://your-ngrok-url/api/webhooks/hubspot`
- Subscribe to events:
  - `contact.creation`
  - `contact.propertyChange` (for phone and mobilephone)

## Files

### Core
- **`app.py`** - Flask webhook server (main file)
- **`requirements.txt`** - Python dependencies
- **`env/.env`** - Your credentials (git-ignored)
- **`env/.env.example`** - Credential template

### Optional - Batch Processing
- **`tps_check_automation.py`** - Check all contacts in batches
- **`tps_check_batches.py`** - Check contacts with user-controlled batch size
- **`update_hubspot_from_csv.py`** - Bulk update from CSV results

## Testing

Test the webhook locally before deploying:
```powershell
$json = @{
    objectId = "123"
    subscriptionType = "contact.creation"
    propertyChanges = @(@{
        propertyName = "phone"
        propertyValue = "07700900000"
    })
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:5000/api/webhooks/hubspot" `
  -Method POST -Body $json -ContentType "application/json"
```

## API Endpoints

### `POST /api/webhooks/hubspot`
Receives webhook events from HubSpot. Automatically checks phone numbers and updates contacts.

**Response:** `{"received": true}` (200 OK)

### `GET /health`
Health check endpoint for monitoring.

**Response:** `{"status": "ok"}` (200 OK)

## Monitoring

Watch Flask logs to see webhook processing:
```
✅ WEBHOOK ENDPOINT HIT!
📞 Processing contact 564944476395
  Checking phone: 07714620899
  ✓ Updated 564944476395 (phone): Not Listed
✓ Webhook processed successfully
```

## Production Deployment

For production, consider:
- **Render.com** (EU-hosted, GDPR compliant, recommended)
- **AWS Lambda** (with API Gateway)
- **Heroku** (note: US-based, may not meet GDPR requirements)

## HubSpot Field Mapping

The webhook automatically updates:
- **`tps_checked`** → "true" (when checked)
- **`Phone Number - TPS`** → "Listed" or "Not Listed"
- **`Mobile Phone - TPS`** → "Listed" or "Not Listed"

## Troubleshooting

**Webhook not triggering?**
- Check HubSpot Settings → Integrations → Webhooks → Logs
- Verify Target URL is correct and reachable
- Ensure Flask server is running and ngrok is active

**HubSpot field not updating?**
- Check Flask logs for errors
- Verify HubSpot Access Token is valid
- Confirm contact ID exists in HubSpot

**Connection errors?**
- Test health endpoint: `http://localhost:5000/health`
- Check TPS_API_KEY and network connectivity
- Review Flask error logs

## Support

1. Check Flask console for error messages
2. Check HubSpot webhook logs (Settings → Webhooks → Logs)
3. Test health endpoint for connectivity

---

**Status:** ✅ Fully operational with ngrok (development) or production deployment ready
