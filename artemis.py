from azure.identity import InteractiveBrowserCredential
from azure.mgmt.resource import ResourceManagementClient
import requests
import openpyxl
from dotenv import load_dotenv
import sqlite3
from datetime import datetime
import click

# Load environment variables

db_file = 'artemis.db'
table_name = 'id_to_prodnames'

# Initialize InteractiveBrowserCredential
# credential = InteractiveBrowserCredential(tenant_id=tenant_id)

# Function to acquire tokens - TESTING CREDENTIAL AS INPUT
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


def create_title_workbook(tenant_name):
  current_time = _get_time()
  return f"{tenant_name}-{current_time}"

def fetch_tenant_properties_v2(tenant_id, credential):
    url = f"https://graph.microsoft.com/v1.0/tenantRelationships/findTenantInformationByTenantId(tenantId='{tenant_id}')"
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
@click.option("-t", "--mode", type=click.Choice(TYPES.keys()))
@click.option("-p", "--savePath", prompt="File Path", help="Save file path in the filesystem")
@click.option("--tenantId", prompt="Tenant ID", help="Tenant ID that requires the assessment")

def run(mode, tenantid, savepath):
  # Initialize InteractiveBrowserCredential
  tenant_id=tenantid
  credential = InteractiveBrowserCredential(tenant_id)
  tenant_data = fetch_tenant_properties_v2(tenant_id)

  # Workbook setup
  workbook = openpyxl.load_workbook('./source/the_googd_one_v1.xlsx')
  # overview_sheet = workbook['Overview']
  overview_sheet = workbook['Overview']
  users_sheet = workbook['Users']
  groups_sheet = workbook['Groups']
  licenses_sheet = workbook['Licenses']
  resources_sheet = workbook['Resources']

  if mode == "f":
    # Process users
    users_data = fetch_users(credential)
    append_data_to_sheet(users_sheet, users_data)
    total_users = len(users_data)

    # Process groups
    groups_data = fetch_groups(credential)
    append_data_to_sheet(groups_sheet, groups_data)
    total_groups = len(groups_data)

    # Process Licenses
    licenses_data = fetch_licenses(credential)
    append_data_to_sheet(licenses_sheet, licenses_data)
    total_groups = len(groups_data)

    # Fetch Resources
    subscriptions_data = fetch_subscriptions_v2(credential)

    resources_data = []

    for i in range(len(subscriptions_data)):
      resources = fetch_resources_v2(subscriptions_data[i]['subscriptionId'], credential)
      for resource in resources:
        resource.append(subscriptions_data[i]['displayName'])
        resources_data.append(resource)
      
    append_data_to_sheet(resources_sheet, resources_data)

    # Fetch Tenant Informations
    tenant_data = fetch_tenant_properties_v2(tenant_id, credential)
    sheet = workbook['Overview']
    sheet['C4'] = tenant_data['tenantId']
    sheet['C5'] = tenant_data['displayName']
    sheet['C6'] = tenant_data['federationBrandName']
    sheet['C7'] = tenant_data['defaultDomainName']

    sheet['C9'] = total_users
    sheet['C10'] = total_groups

  elif mode == "eio":
    # Fetch Resources
    subscriptions_data = fetch_subscriptions_v2(credential)

    resources_data = []

    for i in range(len(subscriptions_data)):
      resources = fetch_resources_v2(subscriptions_data[i]['subscriptionId'], credential)
      for resource in resources:
        resource.append(subscriptions_data[i]['displayName'])
        resources_data.append(resource)
      
    append_data_to_sheet(resources_sheet, resources_data)

    # Fetch Tenant Informations
    tenant_data = fetch_tenant_properties_v2(tenant_id, credential)
    sheet = workbook['Overview']
    sheet['C4'] = tenant_data['tenantId']
    sheet['C5'] = tenant_data['displayName']
    sheet['C6'] = tenant_data['federationBrandName']
    sheet['C7'] = tenant_data['defaultDomainName']

    wb_title = create_title_workbook(tenant_data['displayName'])

  elif mode == "ro":
    # Fetch Resources
    subscriptions_data = fetch_subscriptions_v2(credential)

    resources_data = []

    for i in range(len(subscriptions_data)):
      resources = fetch_resources_v2(subscriptions_data[i]['subscriptionId'], credential)
      for resource in resources:
        resource.append(subscriptions_data[i]['displayName'])
        resources_data.append(resource)
      
    append_data_to_sheet(resources_sheet, resources_data)

    # Fetch Tenant Informations
    tenant_data = fetch_tenant_properties_v2(tenant_id, credential)
    sheet = workbook['Overview']
    sheet['C4'] = tenant_data['tenantId']
    sheet['C5'] = tenant_data['displayName']
    sheet['C6'] = tenant_data['federationBrandName']
    sheet['C7'] = tenant_data['defaultDomainName']

  # Build output file name
  wb_title = create_title_workbook(tenant_data['displayName'])

  # Save workbook

  if savepath is True:
    try:
      workbook.save(f"{savepath}/{wb_title}.xlsx")
    except Exception as e:
      print(f"[ERROR]: {e}")
  else:
    workbook.save(f"{wb_title}.xlsx")

# ADD COMMANDS

cli.add_command(run)

# Main logic
if __name__ == '__main__':
  cli()