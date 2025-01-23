'''
Artemis is a versatile command-line tool designed to interact with Microsoft Azure and Microsoft Entra ID (formerly Azure Active Directory).
The tool helps you retrieve and export information about users, groups, licenses, resources, and subscriptions from your Azure tenant.
'''

from azure.identity import InteractiveBrowserCredential
import requests
import sqlite3
from datetime import datetime
import click
import csv
import random

# Load global variables
db_file = 'artemis.db'
table_name = 'id_to_prodnames'
emoji_table = [
  "\U0001F920",
  "\U0001F973",
  "\U0001F60E",
  "\U0001F913",
  "\U0001F4A5",
  "\U0001F4AB",
  "\U0001F44C",
  "\U0001F47B",
  "\U0001F47D",
  "\U0001F47E",
  "\U0001F916",
  "\U0001F596",
  "\U0001F9DB",
  "\U0001F9DF"
  ]

# Function to acquire tokens - TESTING CREDENTIAL AS INPUT
def rand_emoji():
  emoji = random.choice(emoji_table)
  return emoji

def get_access_token(credential, scope):
  try:
    token = credential.get_token(scope)
    return token.token
  except Exception as e:
    print(f"[ERROR]: Failed to acquire token. {e}")
    return None

# ENTRAID

# Function to make Graph API calls
def make_graph_call(url, scope, credential, pagination=True):
  access_token = get_access_token(credential, scope)
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

def fetch_users(credential):
  url = 'https://graph.microsoft.com/v1.0/users'
  scope = "https://graph.microsoft.com/.default"
  users = make_graph_call(url, scope, credential)
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
def fetch_groups(credential):
  cred_val = credential
  url = 'https://graph.microsoft.com/v1.0/groups'
  scope = "https://graph.microsoft.com/.default"
  groups = make_graph_call(url, scope, credential=cred_val)

  for group in groups:
    group_id = group['id']
    members_url = f'https://graph.microsoft.com/v1.0/groups/{group_id}/members'
    members = make_graph_call(url=members_url, scope=scope, credential=cred_val)
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

def fetch_licenses(credential):
  url = 'https://graph.microsoft.com/v1.0/subscribedSkus'
  scope = "https://graph.microsoft.com/.default"
  licenses = make_graph_call(url, scope, credential)

  for license in licenses:
     license['skuId'] = fetch_product_display_name(license['skuId'])
  
  return [
      [
        license['accountName'],
        license['skuId'],
        license['appliesTo'],
        license['prepaidUnits']['enabled'],
        license['consumedUnits']
      ]
      for license in licenses
  ]

# AZURE RESOURCES

# Function to make calls to Azure Management API
def make_management_call(url, scope, credential, pagination=True):
  access_token = get_access_token(credential, scope)
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
def fetch_subscriptions_v2(credential):
  url = "https://management.azure.com/subscriptions?api-version=2021-04-01"
  scope = "https://management.azure.com/.default"
  subscriptions_arm_api = make_management_call(url, scope, credential)
  return [
    {
      'subscriptionId': subscription_int['subscriptionId'],
      'displayName': subscription_int['displayName'],
      'state': subscription_int['state']
    }
    for subscription_int in subscriptions_arm_api
  ]

# Fetch resources from ARM API
def fetch_resources_v2(subscription, credential):
  scope = "https://management.azure.com/.default"
  url = f"https://management.azure.com/subscriptions/{subscription}/resources?api-version=2021-04-01"
  resources = make_management_call(url, scope, credential)
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

# Create and append data to CSV File
def create_csv(file_path, data, headers=None):
  with open(file_path, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

    # Check if headers exists
    if headers:
      writer.writerow(headers)
    
    writer.writerows(data)

# Fetch from DB
def fetch_product_display_name(guid):
    db_file = "./artemis.db"
    table_name = 'id_to_prodnames'

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Query to fetch the Product_Display_Name based on GUID
    query = f"SELECT Product_Display_Name FROM {table_name} WHERE GUID = ?"
    cursor.execute(query, (guid,))
    
    # Fetch the result
    result = cursor.fetchone()
    
    # Close the connection
    conn.close()
    
    if result:
        return result[0]
    else:
        return None

def _get_time():
  current_time = datetime.now()
  format_date = current_time.strftime("%d%m%Y-%H%M")
  return format_date


def create_title_workbook(tenant_name, scope="GENERIC"):
  current_time = _get_time()
  return f"{tenant_name}-{scope}-{current_time}"

def fetch_tenant_properties_v2(tenantid, credential):
    url = f"https://graph.microsoft.com/v1.0/tenantRelationships/findTenantInformationByTenantId(tenantId='{tenantid}')"
    scope = "https://graph.microsoft.com/.default"
    access_token = get_access_token(credential, scope)

    headers = {'Authorization': f'Bearer {access_token}'}

    response = requests.get(url=url, headers=headers)
    response.raise_for_status()
    graph_result = response.json()

    return graph_result

# CLI COMMANDS

@click.group()
def cli():
  pass

TYPES = {
  "full": "f",
  "entraIdOnly": "eio",
  "resourcesOnly": "ro"
}

@click.command(help='Initialize my_command')
@click.option("-m", "--mode", type=click.Choice(TYPES.keys()), default="full")
@click.option("-p", "--savePath", prompt="File Path", default=".", help="Save file path in the filesystem")
@click.option("--tenantId", prompt="Tenant ID", help="Tenant ID that requires the assessment")

def run(mode, tenantid, savepath):
  # Initialize InteractiveBrowserCredential
  print("Connecting to tenant...")
  global credential
  credential = InteractiveBrowserCredential(tenant_id=tenantid)
  tenant_data = fetch_tenant_properties_v2(tenantid, credential)

  if mode == "full":
    # Tenant Identification
    print(f"{rand_emoji()} Tenant Id: {tenant_data['tenantId']}\n{rand_emoji()} Tenant Name: {tenant_data['displayName']}\n{rand_emoji()} Default Domain Name: {tenant_data['defaultDomainName']}")
    # Process users
    users_data = fetch_users(credential)
    total_users = len(users_data)
    print(f"{rand_emoji()} Found {total_users} Users - Creating CSV File...")
    users_headers = ['id', 'displayName', 'jobTitle', 'userPrincipalName', 'mail']
    users_csv_name = create_title_workbook(tenant_data['displayName'], scope="USERS")
    create_csv(users_csv_name, users_data, users_headers)

    # Process groups
    groups_data = fetch_groups(credential)
    total_groups = len(groups_data)
    print(f"{rand_emoji()} Found {total_groups} Groups - Creating CSV File...")
    groups_headers = ['id', 'displayName', 'description', 'onPremisesDomainName', 'onPremisesSyncEnabled', 'membersList']
    groups_csv_name = create_title_workbook(tenant_data['displayName'], scope="GROUPS")
    create_csv(groups_csv_name, groups_data, groups_headers)

    # Process Licenses
    licenses_data = fetch_licenses(credential)
    total_licenses = len(licenses_data)
    print(f"{rand_emoji()} Found {total_licenses} Licenses - Creating CSV File...")
    licenses_headers = ['accountName', 'skuId', 'appliesTo', 'prepaidUnits', 'consumedUnits']
    licenses_csv_name = create_title_workbook(tenant_data['displayName'], scope="LICENSES")
    create_csv(licenses_csv_name, licenses_data, licenses_headers)

    # Fetch Resources
    subscriptions_data = fetch_subscriptions_v2(credential)

    resources_data = []

    for i in range(len(subscriptions_data)):
      resources = fetch_resources_v2(subscriptions_data[i]['subscriptionId'], credential)
      for resource in resources:
        resource.append(subscriptions_data[i]['displayName'])
        resources_data.append(resource)
    
    total_resources = len(resources_data)
    print(f"{rand_emoji()} Found {total_resources} Resources - Creating CSV File...")
    resources_headers = ['id', 'name', 'type', 'location', 'subscription']
    resources_csv_name = create_title_workbook(tenant_data['displayName'], scope="RESOURCES")
    create_csv(resources_csv_name, resources_data, resources_headers)

    print("...Done!")

  elif mode == "entraIdOnly":
    # Tenant Identification
    print(f"{rand_emoji()} Tenant Id: {tenant_data['tenantId']}\n{rand_emoji()} Tenant Name: {tenant_data['displayName']}\n{rand_emoji()} Default Domain Name: {tenant_data['defaultDomainName']}")
    # Process users
    users_data = fetch_users(credential)
    total_users = len(users_data)
    print(f"{rand_emoji()} Found {total_users} Users - Creating CSV File...")
    users_headers = ['id', 'displayName', 'jobTitle', 'userPrincipalName', 'mail']
    users_csv_name = create_title_workbook(tenant_data['displayName'], scope="USERS")
    create_csv(users_csv_name, users_data, users_headers)

    # Process groups
    groups_data = fetch_groups(credential)
    total_groups = len(groups_data)
    print(f"{rand_emoji()} Found {total_groups} Groups - Creating CSV File...")
    groups_headers = ['id', 'displayName', 'description', 'onPremisesDomainName', 'onPremisesSyncEnabled', 'membersList']
    groups_csv_name = create_title_workbook(tenant_data['displayName'], scope="GROUPS")
    create_csv(groups_csv_name, groups_data, groups_headers)

    # Process Licenses
    licenses_data = fetch_licenses(credential)
    total_licenses = len(licenses_data)
    print(f"{rand_emoji()} Found {total_licenses} Licenses - Creating CSV File...")
    licenses_headers = ['accountName', 'skuId', 'appliesTo', 'prepaidUnits', 'consumedUnits']
    licenses_csv_name = create_title_workbook(tenant_data['displayName'], scope="LICENSES")
    create_csv(licenses_csv_name, licenses_data, licenses_headers)

    print("...Done!")

  elif mode == "resourcesOnly":
    # Tenant Identification
    print(f"{rand_emoji()} Tenant Id: {tenant_data['tenantId']}\n{rand_emoji()} Tenant Name: {tenant_data['displayName']}\n{rand_emoji()} Default Domain Name: {tenant_data['defaultDomainName']}")

    # Fetch Resources
    subscriptions_data = fetch_subscriptions_v2(credential)

    resources_data = []

    for i in range(len(subscriptions_data)):
      resources = fetch_resources_v2(subscriptions_data[i]['subscriptionId'], credential)
      for resource in resources:
        resource.append(subscriptions_data[i]['displayName'])
        resources_data.append(resource)
    
    total_resources = len(resources_data)
    print(f"{rand_emoji()} Found {total_resources} Resources - Creating CSV File...")
    resources_headers = ['id', 'name', 'type', 'location', 'subscription']
    resources_csv_name = create_title_workbook(tenant_data['displayName'], scope="RESOURCES")
    create_csv(resources_csv_name, resources_data, resources_headers)

    print("...Done!")

# ADD COMMANDS

cli.add_command(run)

# Main logic
if __name__ == '__main__':
  cli()