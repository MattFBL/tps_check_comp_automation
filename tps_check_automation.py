import os
import requests
import csv
import time
from pathlib import Path

# Attempt to load environment variables from env/.env if present
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / "env" / ".env"
    # load if the file exists; load_dotenv is safe if file missing
    load_dotenv(dotenv_path=str(env_path))
except Exception:
    # If python-dotenv isn't installed, we'll still read from OS env vars
    pass

# --- CONFIG (from environment, fall back to placeholders) ---
HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "your_hubspot_access_token")
TPS_API_KEY = os.environ.get("TPS_API_KEY", "your_tps_api_key")
TPS_ENDPOINT = os.environ.get("TPS_ENDPOINT", "https://api.tpsservices.co.uk/check")
HUBSPOT_ENDPOINT = os.environ.get("HUBSPOT_ENDPOINT", "https://api.hubapi.com/crm/v3/objects/companies")
try:
    BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "10000"))
except ValueError:
    BATCH_SIZE = 10000

# --- STEP 1: Pull companies from HubSpot ---
def get_hubspot_companies():
    companies = []
    url = f"{HUBSPOT_ENDPOINT}?properties=phone&limit=100"
    headers = {"Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}"}

    while url:
        r = requests.get(url, headers=headers)
        data = r.json()
        for company in data.get("results", []):
            phone = company.get("properties", {}).get("phone")
            companies.append({"id": company["id"], "phone": phone})
        url = data.get("paging", {}).get("next", {}).get("link")
    return companies

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
    
    # Debug: print status and response
    print(f"  Status Code: {r.status_code}")
    if r.status_code != 200:
        print(f"  Response: {r.text[:300]}")
    
    if r.status_code != 200:
        raise Exception(f"TPS API returned {r.status_code}: {r.text}")
    
    return r.json()

# --- STEP 3: Update HubSpot properties ---
def update_hubspot(company_id, tps_checked, phone_status):
    url = f"{HUBSPOT_ENDPOINT}/{company_id}"
    headers = {"Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}", "Content-Type": "application/json"}
    data = {
        "properties": {
            "tps_checked": tps_checked,
            "tps_status": phone_status
        }
    }
    try:
        r = requests.patch(url, headers=headers, json=data, timeout=10)
        if r.status_code not in [200, 204]:
            print(f"    Warning: HubSpot update returned {r.status_code}")
    except Exception as e:
        print(f"    Error updating HubSpot: {str(e)[:80]}")

# --- MAIN WORKFLOW ---
def main():
    # Load already-checked contacts from CSV to skip them
    already_checked = set()
    if Path("tps_results.csv").exists():
        try:
            with open("tps_results.csv", "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 1:
                        already_checked.add(row[0].strip())
            print(f"✓ Skipping {len(already_checked)} already-checked company phone records")
            print()
        except Exception as e:
            print(f"Warning: Could not read existing results: {e}")
            print()
    
    companies = get_hubspot_companies()
    print(f"Total companies: {len(companies)}")

    # Filter out already-checked phone numbers
    companies_to_check = []
    for c in companies:
        if c["phone"] and c["phone"] not in already_checked:
            companies_to_check.append(("phone", c["id"], c["phone"]))
    
    print(f"Companies to check: {len(companies_to_check)}")

    # Prepare lists for TPS check in batches
    for i in range(0, len(companies_to_check), BATCH_SIZE):
        batch = companies_to_check[i:i+BATCH_SIZE]
        numbers = []
        mapping = []
        for number_type, company_id, phone in batch:
            numbers.append(phone)
            mapping.append((number_type, company_id))

        print(f"Checking batch {i//BATCH_SIZE + 1}... ({len(numbers)} numbers)")
        result = check_tps_batch(numbers)

        # Save results
        with open("tps_results.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for idx, res in enumerate(result.get("results", [])):
                number_type, company_id = mapping[idx]
                # Check if on TPS OR CTPS (correct field names from API)
                listed = res.get("on_tps", False) or res.get("on_ctps", False)
                status = "Listed" if listed else "Not Listed"

                # Just write to CSV
                try:
                    writer.writerow([company_id, number_type, numbers[idx], status])
                except Exception as e:
                    print(f"    Error writing to CSV: {str(e)[:50]}")

        time.sleep(2)  # Avoid rate limits
    print("✓ Complete!")

if __name__ == "__main__":
    main()