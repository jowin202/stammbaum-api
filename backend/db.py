import asyncpg
import os

pool = None


connection_pool = None

async def initialize_connection_pool():
    """
    Initialize the connection pool. This should be called at application startup.
    """
    global connection_pool
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')  # Default to localhost if not set
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)         # Default to 5432 if not set
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    connection_pool = await asyncpg.create_pool(DATABASE_URL)

async def get_pg_connection():
    """
    Get a connection from the connection pool.
    """
    global connection_pool
    if connection_pool is None:
        raise RuntimeError("Connection pool is not initialized. Call initialize_connection_pool() first.")
    
    return await connection_pool.acquire()

async def release_pg_connection(connection):
    """
    Release a connection back to the pool.
    """
    global connection_pool
    if connection_pool is None:
        raise RuntimeError("Connection pool is not initialized. Call initialize_connection_pool() first.")
    await connection_pool.release(connection)





async def pg_db_init():
    conn = await get_pg_connection() 
    try:

        await conn.execute('''DROP TABLE IF EXISTS personen ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS personen (
                id SERIAL PRIMARY KEY,
                vorname VARCHAR(100) NOT NULL,
                nachname VARCHAR(100) NOT NULL,
                geburtsdatum DATE,
                geschlecht BOOLEAN,  -- WICHTIG: Muss BOOLEAN sein
                vater_id INT REFERENCES personen(id) ON DELETE SET NULL,
                mutter_id INT REFERENCES personen(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        ''')

    except Exception as e:
        print(f"An error occurred: {e}",flush=True)
    finally:
        if conn:
            await release_pg_connection(conn)

            