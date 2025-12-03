#!/usr/bin/env python
"""
Update HubSpot contacts with TPS results already in tps_results.csv
This uses existing CSV data, not new API calls to TPS.
"""

import os
import csv
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / "env" / ".env"
    load_dotenv(dotenv_path=str(env_path))
except Exception:
    pass

import requests

HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "your_hubspot_access_token")
HUBSPOT_ENDPOINT = os.environ.get("HUBSPOT_ENDPOINT", "https://api.hubapi.com/crm/v3/objects/contacts")

print("="*70)
print("UPDATE HUBSPOT FROM EXISTING TPS RESULTS")
print("="*70)
print()

# Check if CSV exists
csv_file = "tps_results.csv"
if not Path(csv_file).exists():
    print(f"✗ {csv_file} not found!")
    exit(1)

# Read CSV and collect results by contact ID
results_by_contact = {}
try:
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        
        for row in reader:
            if len(row) < 4:
                continue
            
            contact_id = row[0].strip()
            number_type = row[1].strip().lower()
            phone_number = row[2].strip()
            status = row[3].strip()
            
            if not contact_id or not number_type or not status:
                continue
            
            if contact_id not in results_by_contact:
                results_by_contact[contact_id] = {"phone": "", "mobile": ""}
            
            results_by_contact[contact_id][number_type] = status
    
    print(f"✓ Loaded {len(results_by_contact)} unique contacts from {csv_file}")
    print()
except Exception as e:
    print(f"✗ Error reading CSV: {e}")
    exit(1)

# Update HubSpot
headers = {"Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}", "Content-Type": "application/json"}
updated_count = 0
failed_count = 0

print("Updating HubSpot contacts...")
print()

for contact_id, statuses in results_by_contact.items():
    url = f"{HUBSPOT_ENDPOINT}/{contact_id}"
    
    # Build properties object based on what we have
    # tps_checked uses true/false, other properties use "Listed"/"Not Listed"
    properties = {"tps_checked": "true"}  # Always mark as checked
    
    if statuses.get("phone"):
        # Phone status goes to tps_status_contact
        status_val = statuses["phone"]
        # Map status values directly - "Listed on TPS/CTPS" or "Not Listed"
        properties["tps_status_contact"] = status_val if status_val in ["Listed", "Not Listed"] else status_val
    
    if statuses.get("mobile"):
        # Mobile status goes to mobile_phone___tps
        status_val = statuses["mobile"]
        # Map status values directly - "Listed on TPS/CTPS" or "Not Listed"
        properties["mobile_phone___tps"] = status_val if status_val in ["Listed", "Not Listed"] else status_val
    
    data = {"properties": properties}
    
    # Debug output for first few contacts
    if updated_count < 3:
        print(f"  Contact {contact_id}: {data}")
    
    # Retry logic for network errors
    retry = 0
    max_retries = 2
    success = False
    
    while retry <= max_retries and not success:
        try:
            r = requests.patch(url, headers=headers, json=data, timeout=30)
            if r.status_code in [200, 204]:
                updated_count += 1
                if updated_count % 100 == 0:
                    print(f"  ✓ Updated {updated_count} contacts...")
                success = True
            else:
                if retry < max_retries:
                    retry += 1
                    import time
                    time.sleep(2)
                else:
                    print(f"  ✗ Contact {contact_id}: {r.status_code}")
                    failed_count += 1
                    success = True
        except Exception as e:
            if retry < max_retries:
                retry += 1
                import time
                time.sleep(5)
            else:
                print(f"  ✗ Contact {contact_id}: {str(e)[:50]}")
                failed_count += 1
                success = True

print()
print("="*70)
print(f"COMPLETE!")
print(f"  ✓ Successfully updated: {updated_count}")
print(f"  ✗ Failed: {failed_count}")
print("="*70)
