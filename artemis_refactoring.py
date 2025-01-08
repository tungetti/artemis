# Define imports
import msal
import requests
import json
import os
from dotenv import load_dotenv
import openpyxl
import pandas as pd
import random as rd

# Load ENV variables
try:
  load_dotenv()
except:
  pass
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
tenant_id = os.getenv('TENANT_ID')

# Load config file
config = {
  'client_id': f'{client_id}',
  'client_secret': f'{client_secret}',
  'authority': f'https://login.microsoftonline.com/{tenant_id}',
  'scope': ['https://graph.microsoft.com/.default'] 
}

# Define a function that takes parameter 'url' and executes a graph call.
# Optional parameter 'pagination' can be set to False to return only first page of graph results
def make_graph_call(url, pagination=True):
  try:
    token_result = client.acquire_token_for_client(scopes=config['scope'])
  except Exception as e:
    print(f"[ERROR]: {e}")

   # If token available, execute Graph query
  if 'access_token' in token_result:
    headers = {'Authorization': 'Bearer ' + token_result['access_token']}
    graph_results = []

    while url:
      try:
        graph_result = requests.get(url=url, headers=headers).json()
        graph_results.extend(graph_result['value'])
        if (pagination == True):
          url = graph_result['@odata.nextLink']
        else:
          url = None
      except:
         break
  else:
    print(token_result.get('error'))
    print(token_result.get('error_description'))
    print(token_result.get('correlation'))

  return graph_results

try:
  client = msal.ConfidentialClientApplication(config['client_id'], authority=config['authority'], client_credential=config['client_secret'])
except Exception as e:
  print(f"[ERROR]: {e}")

## Main

# Load the workbook and sheets
workbook = openpyxl.load_workbook('./source/template_entraid.xlsx')
users_sheet = workbook['Users']
groups_sheet = workbook['Groups']
licenses_sheet = workbook['Licenses']  # STILL TO DEFINE

# Function to fetch data and append to a sheet
def append_data_to_sheet(sheet, data):
    for row in data:
        sheet.append(row)

# Fetch and process users
def fetch_users():
    url = 'https://graph.microsoft.com/v1.0/users'
    users = make_graph_call(url)
    return [
        [user['id'], user['displayName'], user.get('jobTitle', 'N/A'), user['userPrincipalName']]
        for user in users
    ]

# Fetch and process groups
def fetch_groups():
    url = 'https://graph.microsoft.com/v1.0/groups'
    groups = make_graph_call(url)

    for group in groups:
        group_id = group['id']
        members_url = f'https://graph.microsoft.com/v1.0/groups/{group_id}/members'
        members = make_graph_call(url=members_url)
        group['membersList'] = ", ".join(member['displayName'] for member in members)

    return [
        [
            group['id'], 
            group['displayName'], 
            group.get('onPremisesDomainName', 'N/A'), 
            group.get('onPremisesSyncEnabled', 'N/A'), 
            group['membersList']
        ]
        for group in groups
    ]

# Fetch licenses - TO DEFINE
def fetch_licenses():
    pass

# Fetch Azure resources
def fetch_resources():
    pass

# Create workbook name - TO DEFINE
def wb_name():
    pass

# Main logic
if __name__ == "__main__":
    # Process users
    users_data = fetch_users()
    append_data_to_sheet(users_sheet, users_data)

    # Process groups
    groups_data = fetch_groups()
    append_data_to_sheet(groups_sheet, groups_data)

    # Save workbook
    workbook.save("my_excel_file_v1_refactored.xlsx")
