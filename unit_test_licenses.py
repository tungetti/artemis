import json
import sqlite3

def fetch_licenses():
  with open("./licenses.json", "r") as lic_file:
    licenses = json.load(lic_file)

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

if __name__ == "__main__":
  test = fetch_licenses()
  print(test)
  print(fetch_product_display_name('c5928f49-12ba-48f7-ada3-0d743a3601d5'))