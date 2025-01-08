import requests
from azure.identity import InteractiveBrowserCredential
from dotenv import load_dotenv
import os
import openpyxl

# Load environment variables
load_dotenv()
tenant_id = os.getenv('TENANT_ID')
subscription_id = os.getenv('SUBSCRIPTION_ID')

# Initialize InteractiveBrowserCredential
credential = InteractiveBrowserCredential(tenant_id=tenant_id)

# Function to get access token for the ARM API
def get_access_token():
    try:
        token = credential.get_token("https://management.azure.com/.default")
        return token.token
    except Exception as e:
        print(f"[ERROR]: Failed to acquire token. {e}")
        return None

# Function to make calls to Azure Management API
def make_management_api_call(url, access_token, pagination=True):
    headers = {'Authorization': f'Bearer {access_token}'}
    resources = []

    while url:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            resources.extend(data.get('value', []))
            if pagination and 'nextLink' in data:
                url = data['nextLink']
            else:
                break
        except Exception as e:
            print(f"[ERROR]: Failed to fetch data. {e}")
            break

    return resources

# Fetch resources from ARM API
def fetch_resources_from_arm_api():
    access_token = get_access_token()
    if not access_token:
        print("[ERROR]: Unable to authenticate.")
        return []

    url = f"https://management.azure.com/subscriptions/{subscription_id}/resources?api-version=2021-04-01"
    return make_management_api_call(url, access_token)

# Append data to Excel sheet
def append_data_to_sheet(sheet, data):
    for row in data:
        sheet.append(row)

# Main logic
if __name__ == "__main__":
    # Workbook setup
    workbook = openpyxl.Workbook()
    resources_sheet = workbook.active
    resources_sheet.title = "Resources"

    # Fetch and append resources
    print("Fetching Azure resources from ARM API...")
    resources = fetch_resources_from_arm_api()
    resources_data = [
        [resource['name'], resource['type'], resource['location']]
        for resource in resources
    ]
    append_data_to_sheet(resources_sheet, resources_data)

    # Save workbook
    workbook.save("azure_resources_via_arm_api.xlsx")
    print("Resources saved to azure_resources_via_arm_api.xlsx")


