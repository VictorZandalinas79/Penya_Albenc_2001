import os
from dotenv import load_dotenv  # pip install python-dotenv
import psycopg2

load_dotenv()  # Cargar variables del archivo .env

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        print("✅ Conexión PostgreSQL exitosa!")
        conn.close()
    except Exception as e:
        print(f"❌ Error PostgreSQL: {e}")
else:
    print("⚠️ DATABASE_URL no encontrada")