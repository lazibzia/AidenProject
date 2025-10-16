import sqlite3

db_path = "permits.db"

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔄 Rebuilding client table without 'keywords' column...")

# 1. Create new table without the 'keywords' column
cursor.execute("""
CREATE TABLE client_new (
    name VARCHAR NOT NULL,
    company VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    phone VARCHAR NOT NULL,
    address VARCHAR NOT NULL,
    city VARCHAR NOT NULL,
    state VARCHAR NOT NULL,
    zip_code VARCHAR NOT NULL,
    country VARCHAR NOT NULL,
    rag_query VARCHAR NOT NULL,
    rag_filter_json VARCHAR NOT NULL,
    permit_type VARCHAR,
    permit_class_mapped VARCHAR,
    status VARCHAR NOT NULL,
    id INTEGER NOT NULL,
    slider_percentage INTEGER DEFAULT 100,
    priority INTEGER DEFAULT 999,
    PRIMARY KEY (id)
);
""")

# 2. Copy data (excluding 'keywords')
cursor.execute("""
INSERT INTO client_new (
    name, company, email, phone, address,
    city, state, zip_code, country,
    rag_query, rag_filter_json, permit_type,
    permit_class_mapped, status, id,
    slider_percentage, priority
)
SELECT 
    name, company, email, phone, address,
    city, state, zip_code, country,
    rag_query, rag_filter_json, permit_type,
    permit_class_mapped, status, id,
    slider_percentage, priority
FROM client;
""")

# 3. Drop old table
cursor.execute("DROP TABLE client;")

# 4. Rename new table
cursor.execute("ALTER TABLE client_new RENAME TO client;")

print("✅ 'keywords' column removed successfully.")

# 5. Add the two new columns
cursor.execute("ALTER TABLE client ADD COLUMN keywords_include TEXT;")
cursor.execute("ALTER TABLE client ADD COLUMN keywords_exclude TEXT;")

conn.commit()
conn.close()

print("✅ Added columns 'keywords_include' and 'keywords_exclude'.")
print("🎉 Table 'client' is now updated.")
