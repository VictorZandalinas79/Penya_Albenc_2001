import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()

class DataManager:
    """Gestor de datos usando PostgreSQL (Supabase) - VERSIÓN OPTIMIZADA"""
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/penya')
        
        # Agregar SSL si es necesario (para Render u otros servicios remotos)
        if 'localhost' not in self.db_url and '127.0.0.1' not in self.db_url:
            # Es una base de datos remota, configurar SSL de forma flexible
            connect_args = {
                "sslmode": "prefer",
                "connect_timeout": 10
            }
            self.engine = create_engine(
                self.db_url, 
                connect_args=connect_args,
                pool_pre_ping=True,  # Verifica conexiones antes de usarlas
                pool_size=5,  # Tamaño del pool de conexiones
                max_overflow=10  # Conexiones adicionales permitidas
            )
        else:
            # Es local, sin SSL
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

            # Noticias
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS noticias (
                    id SERIAL PRIMARY KEY,
                    fecha_scraping TIMESTAMP,
                    titulo TEXT,
                    link TEXT,
                    imagen TEXT,
                    resumen TEXT,
                    origen TEXT
                )
            """))

            # Reuniones
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS reuniones (
                    id SERIAL PRIMARY KEY,
                    fecha VARCHAR(50),
                    temas TEXT,
                    asistentes TEXT,
                    estado VARCHAR(20)
                )
            """))
            conn.commit()
        
        print("Tablas verificadas/creadas")

    # ==========================================
    # GESTIÓN DE NOTICIAS (NUEVOS MÉTODOS)
    # ==========================================

    def get_noticias(self):
        """Obtener noticias ordenadas por fecha de scraping reciente"""
        return self.get_data_filtered(
            'noticias',
            order_by="fecha_scraping DESC"
        )

    def necesita_actualizar_noticias(self, dias=3):
        """Comprueba si la última noticia es más antigua de 'dias'"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT MAX(fecha_scraping) FROM noticias"))
                ultima_fecha = result.scalar()
                
            if not ultima_fecha:
                return True # No hay datos, actualizar
            
            # Si es string, convertir a datetime
            if isinstance(ultima_fecha, str):
                ultima_fecha = datetime.strptime(ultima_fecha, '%Y-%m-%d %H:%M:%S')
                
            diferencia = datetime.now() - ultima_fecha
            return diferencia.days >= dias
        except Exception as e:
            print(f"Error comprobando fecha noticias: {e}")
            return True

    def borrar_noticias_antiguas(self):
        """Borra noticias con más de 30 días de antigüedad"""
        try:
            # PostgreSQL syntax para borrar cosas de hace más de 1 mes
            with self.engine.connect() as conn:
                conn.execute(text("DELETE FROM noticias WHERE fecha_scraping < NOW() - INTERVAL '30 days'"))
                conn.commit()
            print("🧹 Noticias antiguas (más de 30 días) eliminadas.")
        except Exception as e:
            print(f"❌ Error borrando noticias antiguas: {e}")

    def guardar_noticias_nuevas(self, df_nuevas):
        """Guarda nuevas noticias evitando duplicados por Link"""
        try:
            if df_nuevas.empty:
                return False

            # 1. Obtener links existentes para no duplicar
            noticias_existentes = self.get_data('noticias')
            links_existentes = []
            if not noticias_existentes.empty and 'link' in noticias_existentes.columns:
                links_existentes = noticias_existentes['link'].tolist()
            
            # 2. Filtrar el DF nuevo: solo las que NO estén ya en la base de datos
            df_a_guardar = df_nuevas[~df_nuevas['link'].isin(links_existentes)]
            
            if not df_a_guardar.empty:
                # 3. Usamos 'append' para añadir sin borrar lo anterior
                df_a_guardar.to_sql('noticias', self.engine, if_exists='append', index=False)
                print(f"💾 Guardadas {len(df_a_guardar)} noticias nuevas.")
                return True
            else:
                print("👌 No hay noticias nuevas que guardar (ya existían).")
                return False
                
        except Exception as e:
            print(f"Error guardando noticias: {e}")
            return False
    
    # ==========================================
    # MÉTODOS ORIGINALES (mantener compatibilidad)
    # ==========================================
    
    def get_data(self, table):
        """Leer datos de una tabla (método original)"""
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
            'cambios': ['id', 'fecha', 'tipo_cambio', 'descripcion', 'usuario'],
            'reuniones': ['id', 'fecha', 'temas', 'asistentes', 'estado']  
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
    
    # ==========================================
    # NUEVOS MÉTODOS OPTIMIZADOS
    # ==========================================
    
    def get_data_filtered(self, table, where_clause=None, order_by=None, limit=None):
        """
        Obtener datos con filtros SQL para consultas más rápidas
        
        Args:
            table: nombre de la tabla
            where_clause: condición SQL (ej: "fecha >= '2025-01-01'")
            order_by: ordenamiento (ej: "fecha DESC")
            limit: número máximo de registros
        
        Returns:
            DataFrame con los resultados
        """
        try:
            query = f"SELECT * FROM {table}"
            
            if where_clause:
                query += f" WHERE {where_clause}"
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            if limit:
                query += f" LIMIT {limit}"
            
            return pd.read_sql(query, self.engine)
        except Exception as e:
            print(f"Error en consulta filtrada de {table}: {e}")
            return pd.DataFrame()
    
    def get_comidas_recientes(self, limit=50):
        """Obtener solo comidas del año actual y próximo año"""
        año_actual = datetime.now().year
        año_siguiente = año_actual + 1
        return self.get_data_filtered(
            'comidas',
            where_clause=f"fecha >= '{año_actual}-01-01' AND fecha < '{año_siguiente + 1}-01-01'",
            order_by="fecha ASC",
            limit=limit
        )
    
    def get_eventos_proximos(self, limit=20):
        """Obtener solo eventos futuros"""
        hoy = datetime.now().strftime('%Y-%m-%d')
        return self.get_data_filtered(
            'eventos',
            where_clause=f"fecha >= '{hoy}'",
            order_by="fecha ASC",
            limit=limit
        )
    
    def get_cambios_recientes(self, limit=15):
        """Obtener solo los últimos cambios"""
        return self.get_data_filtered(
            'cambios',
            order_by="fecha DESC",
            limit=limit
        )
    
    def get_fiestas_agosto(self):
        """Obtener solo fiestas de agosto 2025"""
        return self.get_data_filtered(
            'fiestas',
            where_clause="fecha >= '2025-08-08' AND fecha <= '2025-08-17'",
            order_by="fecha ASC"
        )
    
    def get_reuniones_recientes(self, limit=20):
        """Obtener reuniones recientes"""
        return self.get_data_filtered(
            'reuniones',
            order_by="fecha DESC",
            limit=limit
        )
    
    def get_lista_compra_activa(self):
        """Obtener lista de compra (normalmente es pequeña)"""
        return self.get_data('lista_compra')
    
    def get_mantenimiento_actual(self):
        """Obtener solo mantenimiento del año actual"""
        año_actual = datetime.now().year
        return self.get_data_filtered(
            'mantenimiento',
            where_clause=f"año = {año_actual}"
        )
    
    def count_records(self, table):
        """Contar registros en una tabla (más rápido que cargar todos)"""
        try:
            query = f"SELECT COUNT(*) as total FROM {table}"
            result = pd.read_sql(query, self.engine)
            return result['total'].iloc[0] if not result.empty else 0
        except Exception as e:
            print(f"Error contando registros de {table}: {e}")
            return 0

dm = DataManager()