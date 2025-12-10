import os
import json
import threading
from pathlib import Path
import requests
from flask import Flask, request, jsonify

print("="*70)
print("FLASK APP STARTING")
print("="*70)

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / "env" / ".env"
    load_dotenv(dotenv_path=str(env_path))
except Exception:
    pass

# Configuration
HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN")
HUBSPOT_ENDPOINT = os.environ.get("HUBSPOT_ENDPOINT", "https://api.hubapi.com/crm/v3/objects/companies")
TPS_API_KEY = os.environ.get("TPS_API_KEY")
TPS_ENDPOINT = os.environ.get("TPS_ENDPOINT", "https://api.tpsservices.co.uk/check")
PORT = os.environ.get("PORT", "5000")

print(f"PORT: {PORT}")
print(f"HUBSPOT_ENDPOINT: {HUBSPOT_ENDPOINT}")
print(f"TPS_ENDPOINT: {TPS_ENDPOINT}")
print("="*70)

# Track processed events
processed_events = {}

app = Flask(__name__)

def check_tps_for_number(phone_number):
    """Check a single phone number with TPS API"""
    try:
        headers = {
            "Authorization": TPS_API_KEY,
            "Content-Type": "application/json",
            "check-tps": "true",
            "check-ctps": "true"
        }
        payload = {"phone_numbers": [phone_number]}
        
        r = requests.post(TPS_ENDPOINT, headers=headers, json=payload, timeout=10)
        
        if r.status_code != 200:
            print(f"  TPS API error ({r.status_code}): {r.text[:200]}")
            return None
        
        results = r.json().get("results", [])
        if results:
            return results[0]
        return None
    except Exception as e:
        print(f"  TPS check error: {str(e)[:100]}")
        return None

def update_hubspot_company(company_id, tps_result):
    """Update a HubSpot company with TPS status"""
    try:
        if not tps_result:
            print(f"  Skipping update for {company_id} - no TPS result")
            return False
        
        # Determine status
        listed = tps_result.get("on_tps", False) or tps_result.get("on_ctps", False)
        status = "Listed" if listed else "Not Listed"
        
        url = f"{HUBSPOT_ENDPOINT}/{company_id}"
        headers = {
            "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "properties": {
                "tps_checked": "true",
                "tps_status": status
            }
        }
        
        r = requests.patch(url, headers=headers, json=data, timeout=10)
        
        if r.status_code in [200, 204]:
            print(f"  ✓ Updated company {company_id}: {status}")
            return True
        else:
            print(f"  ✗ HubSpot update failed ({r.status_code}): {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  Error updating HubSpot: {str(e)[:100]}")
        return False

def process_company_event(company_id, properties):
    """Process a company event and check TPS"""
    try:
        print(f"\n🏢 Processing company {company_id}")
        
        # Extract phone number
        phone_to_check = None
        
        if isinstance(properties, dict):
            phone = properties.get("phone", {})
            if isinstance(phone, dict):
                phone = phone.get("value")
            if phone and isinstance(phone, str) and phone.strip():
                phone_to_check = phone.strip()
        
        if not phone_to_check:
            print("  No phone number to check")
            return
        
        # Check the phone number and update HubSpot
        print(f"  Checking phone: {phone_to_check}")
        tps_result = check_tps_for_number(phone_to_check)
        if tps_result:
            update_hubspot_company(company_id, tps_result)
        
        print(f"✓ Company {company_id} processed successfully")
    except Exception as e:
        print(f"✗ Error processing company: {str(e)[:150]}")

@app.route('/api/webhooks/hubspot', methods=['POST'])
def hubspot_webhook():
    """HubSpot Webhook Endpoint - Company Properties"""
    print("\n" + "="*70)
    print("✅ WEBHOOK ENDPOINT HIT!")
    print("="*70)
    
    try:
        # Get raw and parsed data
        raw_data = request.get_data(as_text=True)
        print(f"Raw payload: {raw_data[:500]}")
        
        # Parse events
        events = request.get_json()
        if not events:
            print("No events in payload")
            return jsonify({"received": True}), 200
        
        # Handle both list and dict
        if isinstance(events, dict):
            events = [events]
        
        print(f"🔔 Received {len(events)} event(s)")
        
        # Process each event
        for event in events:
            company_id = event.get("objectId")
            event_type = event.get("subscriptionType")
            properties = event.get("propertyChanges", [])
            
            print(f"Company ID: {company_id}, Type: {event_type}")
            
            # Build properties dict from change events
            company_properties = {}
            for prop_change in properties:
                if isinstance(prop_change, dict):
                    prop_name = prop_change.get("propertyName")
                    prop_value = prop_change.get("propertyValue")
                    company_properties[prop_name] = {"value": prop_value}
            
            # Fetch full company to get phone
            if company_id:
                try:
                    print(f"Fetching full company {company_id}...")
                    headers = {"Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}"}
                    url = f"{HUBSPOT_ENDPOINT}/{company_id}?properties=phone"
                    r = requests.get(url, headers=headers, timeout=10)
                    if r.status_code == 200:
                        full_company = r.json()
                        company_properties = full_company.get("properties", {})
                        print(f"  ✓ Got company properties")
                except Exception as e:
                    print(f"  Could not fetch full company: {str(e)[:50]}")
            
            # Extract phone number
            phone_to_check = None
            
            if isinstance(company_properties, dict):
                phone = company_properties.get("phone", {})
                if isinstance(phone, dict):
                    phone = phone.get("value")
                if phone and isinstance(phone, str) and phone.strip():
                    phone_to_check = phone.strip()
            
            # Check TPS for the phone number
            if company_id and phone_to_check:
                print(f"  Checking phone: {phone_to_check}")
                tps_result = check_tps_for_number(phone_to_check)
                if tps_result:
                    update_hubspot_company(company_id, tps_result)
        
        print("✓ Webhook processed successfully")
        return jsonify({"received": True}), 200
    
    except Exception as e:
        print(f"✗ Webhook error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "processed_events": len(processed_events)}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
