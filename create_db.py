import pandas as pd
import sqlite3
import sys

# Replace 'your_file.csv' with the path to your CSV file
csv_file = 'id_to_prodnames.csv'
db_file = 'artemis.db'
table_name = 'id_to_prodnames'

# Read the CSV file into a DataFrame
df = pd.read_csv(csv_file)

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Create a table with the same columns as the DataFrame
df.to_sql(table_name, conn, if_exists='replace', index=False)

# Commit the changes and close the connection
conn.commit()
conn.close()

print(f"Data from {csv_file} has been imported into {db_file} in the table {table_name}.")