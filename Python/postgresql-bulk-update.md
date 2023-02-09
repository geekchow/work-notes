# postgresql bulk update with python

## How to use `psycopg2.extras.execute_values`  to do bulk insert against postgreSQL table 

```python
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(<your_database_connection_string>)
cur = conn.cursor()

# Example data to insert
data = [(1, "John"), (2, "Jane"), (3, "Jim")]

# SQL INSERT statement with placeholders
insert_sql = "INSERT INTO your_table (column1, column2) VALUES %s"

# Use the execute_values method to perform the bulk insert
psycopg2.extras.execute_values(cur, insert_sql, data)

# Commit the transaction
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()

```

## How to do it when the primary key of the table is a sequence 


If the table has a sequence as the primary key, you can still use psycopg2.extras.execute_values to perform a bulk insert. You just need to modify the INSERT statement to use the nextval function from the pg_sequences to get the next value from the sequence for each row being inserted.


```python
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(<your_database_connection_string>)
cur = conn.cursor()

# Example data to insert
data = [(1, "John"), (2, "Jane"), (3, "Jim")]

# SQL INSERT statement with placeholders
insert_sql = "INSERT INTO your_table (id, column1, column2) VALUES (%s, %s, %s)"

# Use the execute_values method to perform the bulk insert
psycopg2.extras.execute_values(cur, insert_sql, data, template="(nextval('your_sequence'), %s, %s)", page_size=1000)

# Commit the transaction
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()

```

In this example, the execute_values method will automatically create a batch of multiple INSERT statements, each with a call to the nextval function to get the next value from the sequence for the id column. The batch size can be specified by passing the page_size argument to the method.

