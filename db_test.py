import streamlit as st
import snowflake.connector

# Retrieve connection parameters from Streamlit secrets
USER = st.secrets["snowflake"]["user"]
PASSWORD = st.secrets["snowflake"]["password"]
ACCOUNT = st.secrets["snowflake"]["account"]
REGION = st.secrets["snowflake"]["region"]  # new parameter
WAREHOUSE = st.secrets["snowflake"]["warehouse"]
DATABASE = st.secrets["snowflake"]["database"]
SCHEMA = st.secrets["snowflake"]["schema"]

# Establish the connection, passing the region explicitly
conn = snowflake.connector.connect(
    user=USER,
    password=PASSWORD,
    account=ACCOUNT,
    region=REGION,  # pass the region here
    warehouse=WAREHOUSE,
    database=DATABASE,
    schema=SCHEMA
)


# Create a cursor object
cur = conn.cursor()

# Create the 'users' table if it doesn't already exist
create_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER AUTOINCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP
);
"""
cur.execute(create_table_query)

# Query the table to verify creation
cur.execute("SELECT * FROM users")
results = cur.fetchall()

# Display the results in a table within the Streamlit app
st.write("Query Results:")
st.table(results)

# Close the cursor and connection when done
cur.close()
conn.close()
