
import requests
from azure.identity import InteractiveBrowserCredential
from dotenv import load_dotenv
import os
import openpyxl

# Load environment variables
load_dotenv()
tenant_id = os.getenv('TENANT_ID')

# Initialize InteractiveBrowserCredential
credential = InteractiveBrowserCredential(tenant_id=tenant_id)

# Function to get access token for the ARM API
def get_access_token(scope):
  try:
    token = credential.get_token(scope)
    return token.token
  except Exception as e:
    print(f"[ERROR]: Failed to acquire token. {e}")
    return None

# Function to make calls to Azure Management API
def make_management_api_call(url, scope, pagination=True):
  access_token = get_access_token(scope)
  if not access_token:
    print("[ERROR]: No access token available.")
    return []

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

# Fetch subscriptions from ARM API
def fetch_subscriptions_v2():
  url = "https://management.azure.com/subscriptions?api-version=2021-04-01"
  scope = "https://management.azure.com/.default"
  subscriptions_arm_api = make_management_api_call(url, scope)
  return [
    {
      'subscriptionId': subscription_int['subscriptionId'],
      'displayName': subscription_int['displayName'],
      'state': subscription_int['state']
    }
    for subscription_int in subscriptions_arm_api
  ]

def fetch_resources_v2(subscription):
  scope = "https://management.azure.com/.default"
  url = f"https://management.azure.com/subscriptions/{subscription}/resources?api-version=2021-04-01"
  resources = make_management_api_call(url, scope)
  return [
    [
      resource['id'],
      resource['name'],
      resource['type'],
      resource['location']
    ]
    for resource in resources
  ]

# Main logic
if __name__ == "__main__":

  # Fetch and append subscriptions
  print("Fetching Azure subscriptions from ARM API...")
  subscriptions_data = fetch_subscriptions_v2()

  complete_list_resources = []

  for i in range(len(subscriptions_data)):
    resources = fetch_resources_v2(subscriptions_data[i]['subscriptionId'])
    for resource in resources:
      resource.append(subscriptions_data[i]['displayName'])
      complete_list_resources.append(resource)
    
  print(complete_list_resources)