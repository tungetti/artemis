import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
db_file = 'artemis.db'

# Create a table with the same columns as the DataFrame
table_name = 'id_to_prodnames'

def fetch_product_display_name(guid):
    # Connect to the SQLite database
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

def fetch_licenses():
  url = 'https://graph.microsoft.com/v1.0/subscribedSkus'
  scope = "https://graph.microsoft.com/.default"
  licenses = make_graph_call(url, scope)
  return licenses
  # [
  #     [
  #       user['id'],
  #       user['displayName'],
  #       user.get('jobTitle', 'N/A'),
  #       user['userPrincipalName'],
  #       user.get('mail', 'N/A')
  #     ]
  #     for user in users
  # ]

# Example usage
guid_input = '95de1760-7682-406d-98c9-52ef14e51e2b'
product_display_name = fetch_product_display_name(guid_input)
print(f"The Product_Display_Name for GUID '{guid_input}' is '{product_display_name}'.")