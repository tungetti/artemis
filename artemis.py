from azure.identity import InteractiveBrowserCredential
from azure.mgmt.resource import ResourceManagementClient
import requests
import openpyxl
import os
from dotenv import load_dotenv
import sys

# Load environment variables
try:
  load_dotenv()
except:
  pass

tenant_id = os.getenv('TENANT_ID')
subscription_id = os.getenv('SUBSCRIPTION_ID')

# Initialize InteractiveBrowserCredential
credential = InteractiveBrowserCredential(tenant_id=tenant_id)

# Function to acquire tokens
def get_access_token(scope):
  try:
    token = credential.get_token(scope)
    return token.token
  except Exception as e:
    print(f"[ERROR]: Failed to acquire token. {e}")
    return None

# ENTRAID

# Function to make Graph API calls
def make_graph_call(url, scope, pagination=True):
  access_token = get_access_token(scope)
  if not access_token:
    print("[ERROR]: No access token available.")
    return []

  headers = {'Authorization': f'Bearer {access_token}'}
  graph_results = []

  while url:
    try:
      response = requests.get(url=url, headers=headers)
      response.raise_for_status()
      graph_result = response.json()
      graph_results.extend(graph_result.get('value', []))
      if pagination and '@odata.nextLink' in graph_result:
        url = graph_result['@odata.nextLink']
      else:
        break
    except Exception as e:
      print(f"[ERROR]: Failed to fetch data. {e}")
      break

  return graph_results

def fetch_users():
  url = 'https://graph.microsoft.com/v1.0/users'
  scope = "https://graph.microsoft.com/.default"
  users = make_graph_call(url, scope)
  return [
      [
        user['id'],
        user['displayName'],
        user.get('jobTitle', 'N/A'),
        user['userPrincipalName'],
        user.get('mail', 'N/A')
      ]
      for user in users
  ]

# Fetch and process groups
def fetch_groups():
  url = 'https://graph.microsoft.com/v1.0/groups'
  scope = "https://graph.microsoft.com/.default"
  groups = make_graph_call(url, scope)

  print(groups)

  for group in groups:
    group_id = group['id']
    members_url = f'https://graph.microsoft.com/v1.0/groups/{group_id}/members'
    members = make_graph_call(url=members_url, scope=scope)
    group['membersList'] = ", ".join(member['displayName'] for member in members)

  return [
    [
      group['id'], 
      group['displayName'], 
      group.get('description', 'N/A'),
      group.get('onPremisesDomainName', 'N/A'), 
      group.get('onPremisesSyncEnabled', 'N/A'), 
      group['membersList']
    ]
    for group in groups
  ]

# AZURE RESOURCES

# Function to make calls to Azure Management API
def make_management_call(url, scope, pagination=True):
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

# Fetch and process users
def fetch_subscriptions_v2():
  url = "https://management.azure.com/subscriptions?api-version=2021-04-01"
  scope = "https://management.azure.com/.default"
  subscriptions_arm_api = make_management_call(url, scope)
  return [
    {
      'subscriptionId': subscription_int['subscriptionId'],
      'displayName': subscription_int['displayName'],
      'state': subscription_int['state']
    }
    for subscription_int in subscriptions_arm_api
  ]

# Fetch resources from ARM API
def fetch_resources_v2(subscription):
  scope = "https://management.azure.com/.default"
  url = f"https://management.azure.com/subscriptions/{subscription}/resources?api-version=2021-04-01"
  resources = make_management_call(url, scope)
  return [
    [
      resource['id'],
      resource['name'],
      resource['type'],
      resource['location']
    ]
    for resource in resources
  ]

# Append data to Excel sheets
def append_data_to_sheet(sheet, data):
  for row in data:
    sheet.append(row)

# Main logic
if __name__ == "__main__":

  # Workbook setup
  workbook = openpyxl.load_workbook('./source/template_entraid.xlsx')
  users_sheet = workbook['Users']
  groups_sheet = workbook['Groups']
  licenses_sheet = workbook['Licenses']
  resources_sheet = workbook['Resources']

  # Process users
  users_data = fetch_users()
  append_data_to_sheet(users_sheet, users_data)

  # Process groups
  groups_data = fetch_groups()
  append_data_to_sheet(groups_sheet, groups_data)

  # Save workbook
  workbook.save("my_excel_file_user_auth.xlsx")

