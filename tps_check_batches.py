#!/usr/bin/env python
"""
Run TPS checks in smaller batches - allows incremental testing
Skips contacts already checked in tps_results.csv
"""

import os
import csv
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / "env" / ".env"
    load_dotenv(dotenv_path=str(env_path))
except Exception:
    pass

import requests

# --- CONFIG ---
HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "your_hubspot_access_token")
TPS_API_KEY = os.environ.get("TPS_API_KEY", "your_tps_api_key")
TPS_ENDPOINT = os.environ.get("TPS_ENDPOINT", "https://service.tpsapi.com")
HUBSPOT_ENDPOINT = os.environ.get("HUBSPOT_ENDPOINT", "https://api.hubapi.com/crm/v3/objects/contacts")
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10000"))

print("="*70)
print("TPS CHECK AUTOMATION - BATCH MODE")
print("="*70)
print()

# Load already-checked contact IDs from CSV
checked_contact_ids = set()
csv_file = "tps_results.csv"
if Path(csv_file).exists():
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > 0:
                    checked_contact_ids.add(row[0].strip())
        print(f"✓ Loaded {len(checked_contact_ids)} already-checked contacts from {csv_file}")
    except Exception as e:
        print(f"⚠ Error loading CSV: {e}")
else:
    print(f"ℹ No existing results - will check all contacts")

print()

# --- STEP 1: Get contacts from HubSpot ---
def get_hubspot_contacts():
    contacts = []
    url = f"{HUBSPOT_ENDPOINT}?properties=phone,mobilephone&limit=100"
    headers = {"Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}"}

    print("Fetching contacts from HubSpot...")
    while url:
        r = requests.get(url, headers=headers)
        data = r.json()
        for contact in data.get("results", []):
            contact_id = contact["id"]
            # Skip if already checked
            if contact_id in checked_contact_ids:
                continue
                
            phone = contact.get("properties", {}).get("phone")
            mobile = contact.get("properties", {}).get("mobilephone")
            contacts.append({"id": contact_id, "phone": phone, "mobile": mobile})
        
        url = data.get("paging", {}).get("next", {}).get("link")
    
    return contacts

# --- STEP 2: TPS Check for a batch ---
def check_tps_batch(numbers):
    headers = {
        "Authorization": TPS_API_KEY,
        "Content-Type": "application/json",
        "check-tps": "true",
        "check-ctps": "true"
    }
    payload = {"phone_numbers": numbers}
    r = requests.post(TPS_ENDPOINT, headers=headers, json=payload)
    
    if r.status_code != 200:
        raise Exception(f"TPS API returned {r.status_code}: {r.text}")
    
    return r.json()

# --- MAIN ---
contacts = get_hubspot_contacts()
print(f"✓ Found {len(contacts)} new contacts to check")
print()

if not contacts:
    print("No new contacts to check!")
    exit(0)

# Ask user for batch size
print("How many contacts do you want to check in this run?")
print(f"(Default: {min(100, len(contacts))} | Max: {len(contacts)})")
try:
    user_input = input("Enter number: ").strip()
    if user_input:
        batch_limit = int(user_input)
    else:
        batch_limit = min(100, len(contacts))
except ValueError:
    batch_limit = min(100, len(contacts))

print()
print(f"Will check {batch_limit} contacts in this run")
print()

# Process contacts in batches
contacts_to_process = contacts[:batch_limit]
processed_count = 0

for i in range(0, len(contacts_to_process), BATCH_SIZE):
    batch = contacts_to_process[i:i+BATCH_SIZE]
    numbers = []
    mapping = []
    
    for c in batch:
        if c["phone"]:
            numbers.append(c["phone"])
            mapping.append(("phone", c["id"]))
        if c["mobile"]:
            numbers.append(c["mobile"])
            mapping.append(("mobile", c["id"]))

    batch_num = (i // BATCH_SIZE) + 1
    print(f"Checking batch {batch_num}/{(len(contacts_to_process) + BATCH_SIZE - 1) // BATCH_SIZE}...")
    print(f"  Phone numbers to check: {len(numbers)}")
    
    try:
        result = check_tps_batch(numbers)
        print(f"  ✓ Status Code: 200")
        
        # Save results
        with open("tps_results.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for idx, res in enumerate(result.get("results", [])):
                number_type, contact_id = mapping[idx]
                listed = res.get("on_tps", False) or res.get("on_ctps", False)
                status = "Listed" if listed else "Not Listed"
                
                writer.writerow([contact_id, number_type, numbers[idx], status])
                processed_count += 1
        
        print(f"  ✓ Saved {len(result.get('results', []))} results to CSV")
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")
        break
    
    time.sleep(2)  # Rate limiting

print()
print("="*70)
print(f"BATCH COMPLETE!")
print(f"  ✓ Processed: {processed_count} phone numbers")
print(f"  📄 Results saved to: tps_results.csv")
print("="*70)
print()
print(f"Remaining to check: {len(contacts) - batch_limit}")
print(f"Run this script again to check more contacts in batches")
