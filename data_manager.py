import pandas as pd
from sqlalchemy import create_engine, text
import os

class DataManager:
    """Gestor de datos usando PostgreSQL (Supabase)"""
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/penya')
        
        # Conectar
        self.engine = create_engine(self.db_url)
        self.init_tables()
    
    def init_tables(self):
        """Crear tablas si no existen"""
        with self.engine.connect() as conn:
            # Comidas
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS comidas (
                    id SERIAL PRIMARY KEY,
                    fecha VARCHAR(50),
                    dia VARCHAR(50),
                    tipo_comida VARCHAR(100),
                    cocineros TEXT
                )
            """))
            
            # Lista compra
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lista_compra (
                    id SERIAL PRIMARY KEY,
                    fecha VARCHAR(50),
                    objeto TEXT
                )
            """))
            
            # Mantenimiento
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS mantenimiento (
                    id SERIAL PRIMARY KEY,
                    año INTEGER,
                    mantenimiento TEXT,
                    cadafals TEXT
                )
            """))
            
            # Eventos
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS eventos (
                    id SERIAL PRIMARY KEY,
                    fecha VARCHAR(50),
                    evento VARCHAR(200),
                    tipo TEXT
                )
            """))
            
            # Fiestas
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS fiestas (
                    id SERIAL PRIMARY KEY,
                    fecha VARCHAR(50),
                    cocineros TEXT,
                    menu TEXT,
                    adultos INTEGER,
                    nombres_adultos TEXT,
                    niños INTEGER,
                    nombres_niños TEXT,
                    programa TEXT
                )
            """))
            
            # Cambios
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cambios (
                    id SERIAL PRIMARY KEY,
                    fecha VARCHAR(50),
                    tipo_cambio VARCHAR(100),
                    descripcion TEXT,
                    usuario VARCHAR(100)
                )
            """))
            conn.commit()
        
        print("Tablas verificadas/creadas")
    
    def get_data(self, table):
        """Leer datos de una tabla"""
        try:
            return pd.read_sql_table(table, self.engine)
        except Exception as e:
            print(f"Error leyendo {table}: {e}")
            return pd.DataFrame()
    
    def save_data(self, table, df):
        """Guardar datos en una tabla"""
        try:
            if 'id' not in df.columns and len(df) > 0:
                df = df.reset_index(drop=True)
                df['id'] = range(1, len(df) + 1)
            
            df.to_sql(table, self.engine, if_exists='replace', index=False)
            return True
        except Exception as e:
            print(f"Error guardando {table}: {e}")
            return False
    
    def add_data(self, table, data):
        """Agregar nueva fila a una tabla"""
        df = self.get_data(table)
        
        new_id = 1 if len(df) == 0 else int(df['id'].max()) + 1
        
        schemas = {
            'comidas': ['id', 'fecha', 'dia', 'tipo_comida', 'cocineros'],
            'lista_compra': ['id', 'fecha', 'objeto'],
            'mantenimiento': ['id', 'año', 'mantenimiento', 'cadafals'],
            'eventos': ['id', 'fecha', 'evento', 'tipo'],
            'fiestas': ['id', 'fecha', 'cocineros', 'menu', 'adultos', 'nombres_adultos', 'niños', 'nombres_niños', 'programa'],
            'cambios': ['id', 'fecha', 'tipo_cambio', 'descripcion', 'usuario']
        }
        
        columns = schemas.get(table, [])
        new_row = {'id': new_id}
        
        for i, col in enumerate(columns[1:]):
            if i < len(data):
                new_row[col] = data[i]
            else:
                new_row[col] = 0 if col in ['adultos', 'niños', 'año'] else ''
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        return self.save_data(table, df)

dm = DataManager()