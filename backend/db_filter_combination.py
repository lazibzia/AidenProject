import sqlite3
import pandas as pd
# Show full values instead of "..."
pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_rows", None)   # if you want to see all rows (be careful if it's huge)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)


# Path to your SQLite DB
DB_PATH = "permits.db"

# Connect to the database
conn = sqlite3.connect(DB_PATH)

# Columns to analyze
columns = ["permit_num", "permit_type", "permit_class_mapped", "work_class"]

# Loop through columns and get unique counts
for col in columns:
    print(f"\n===== Unique values for {col} =====")
    query = f"""
        SELECT {col}, COUNT(*) as total_count
        FROM permits
        GROUP BY {col}
        ORDER BY total_count DESC;
    """
    df = pd.read_sql_query(query, conn)
    print(df)

# Now find unique combinations of the selected columns
print("\n===== Unique combinations of permit_type, permit_class_mapped, work_class =====")
combo_query = """
    SELECT permit_type, permit_class_mapped, work_class, COUNT(*) as total_count
    FROM permits
    GROUP BY permit_type, permit_class_mapped, work_class
    ORDER BY total_count DESC;
"""
combo_df = pd.read_sql_query(combo_query, conn)
print(combo_df)

# Count total distinct combinations
distinct_count_query = """
    SELECT COUNT(*) as total_combinations
    FROM (
        SELECT DISTINCT permit_type, permit_class_mapped, work_class
        FROM permits
    ) AS unique_combos;
"""
distinct_count = pd.read_sql_query(distinct_count_query, conn)
print("\nTotal unique combinations:", distinct_count.iloc[0,0])

# Close connection
conn.close()
