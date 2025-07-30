import sqlite3


def show_all_permits(db_path="permits.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM permits")

    rows = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]

    for row in rows:
        print(dict(zip(col_names, row)))

    print(f"\n✅ Total permits found: {len(rows)}")
    conn.close()


if __name__ == "__main__":
    show_all_permits()
