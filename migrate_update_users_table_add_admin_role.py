import sqlite3
import logging

def migrate():
    db_path = "medical_office.db"
    logger = logging.getLogger(__name__)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Begin transaction
        cursor.execute("BEGIN TRANSACTION;")

        # Rename old users table
        cursor.execute("ALTER TABLE users RENAME TO users_old;")

        # Create new users table with updated role CHECK constraint including 'Admin'
        cursor.execute("""
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Admin', 'Doctor', 'Receptionist', 'Assistant'))
            );
        """)

        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO users (user_id, username, password_hash, role)
            SELECT user_id, username, password_hash,
                CASE
                    WHEN role = 'Receptionist' THEN 'Admin'  -- Migrate Receptionist to Admin if needed
                    ELSE role
                END
            FROM users_old;
        """)

        # Drop old users table
        cursor.execute("DROP TABLE users_old;")

        # Commit transaction
        conn.commit()
        logger.info("Migration to add 'Admin' role to users table completed successfully.")
        print("Migration to add 'Admin' role to users table completed successfully.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
