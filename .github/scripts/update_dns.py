import os
import sys
import json
import requests

# Cloudflare API credentials from environment variables
API_TOKEN = os.getenv('CF_API_TOKEN')
ZONE_ID = os.getenv('CF_ZONE_ID')
API_BASE_URL = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"

# Headers for Cloudflare API requests
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def get_existing_records():
    """Fetch all existing DNS records for the zone."""
    response = requests.get(API_BASE_URL, headers=HEADERS)
    response.raise_for_status()
    return response.json()['result']

def create_or_update_record(subdomain, record_type, content, proxied):
    """Create or update a DNS record in Cloudflare."""
    existing_records = get_existing_records()
    record_name = f"{subdomain}.justs.rocks"
    record_id = None

    for record in existing_records:
        if record['name'] == record_name and record['type'] == record_type:
            record_id = record['id']
            break

    payload = {
        "type": record_type,
        "name": record_name,
        "content": content,
        "proxied": proxied,
        "ttl": 1  # Auto TTL
    }

    if record_id:
        url = f"{API_BASE_URL}/{record_id}"
        response = requests.put(url, headers=HEADERS, json=payload)
        print(f"Updated DNS record for {record_name}")
    else:
        response = requests.post(API_BASE_URL, headers=HEADERS, json=payload)
        print(f"Created DNS record for {record_name}")

    response.raise_for_status()

def main():
    if len(sys.argv) < 2:
        print("No changed files provided. Exiting.")
        return

    raw_input = sys.argv[1]
    print(f"Raw input: {raw_input}")
    try:
        changed_files = json.loads(raw_input)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {raw_input}")
        print(f"JSON decode error: {str(e)}")
        sys.exit(1)

    if not changed_files:
        print("No JSON files changed. Exiting.")
        return

    has_error = False
    for json_file in changed_files:
        if not json_file.startswith('domains/') or not json_file.endswith('.json'):
            print(f"Skipping invalid file: {json_file} (must be in domains/ and end with .json)")
            continue

        try:
            with open(json_file, 'r') as f:
                file_content = f.read()
                data = json.loads(file_content)

            subdomain = json_file.split('/')[-1].replace('.json', '')
            records = data.get('records', {})
            proxied = data.get('proxied', False)

            for record_type, content in records.items():
                print(f"Processing {record_type} record for {subdomain}.justs.rocks")
                create_or_update_record(subdomain, record_type, content, proxied)
        except json.JSONDecodeError as e:
            print(f"Error processing {json_file}: Invalid JSON: {str(e)}")
            print(f"File content: {file_content}")
            has_error = True
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
            has_error = True

    if has_error:
        sys.exit(1)

if __name__ == "__main__":
    main()
