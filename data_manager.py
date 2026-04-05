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
        try:
            with self.engine.connect() as conn:
                # 1. ELIMINAMOS LA LÍNEA DEL DROP (Ya no hace falta borrarla más)
                # conn.execute(text("DROP TABLE IF EXISTS agenda CASCADE")) 

                tablas = {
                    "comidas": "id SERIAL PRIMARY KEY, fecha VARCHAR(50), dia VARCHAR(50), tipo_comida VARCHAR(100), cocineros TEXT",
                    "lista_compra": "id SERIAL PRIMARY KEY, fecha VARCHAR(50), objeto TEXT",
                    "mantenimiento": "id SERIAL PRIMARY KEY, año INTEGER, mantenimiento TEXT, cadafals TEXT",
                    "eventos": "id SERIAL PRIMARY KEY, fecha VARCHAR(50), evento VARCHAR(200), tipo TEXT",
                    "fiestas": "id SERIAL PRIMARY KEY, fecha VARCHAR(50), cocineros TEXT, menu TEXT, adultos INTEGER, nombres_adultos TEXT, niños INTEGER, nombres_niños TEXT, programa TEXT",
                    "cambios": "id SERIAL PRIMARY KEY, fecha VARCHAR(50), tipo_cambio VARCHAR(100), descripcion TEXT, usuario VARCHAR(100)",
                    "noticias": "id SERIAL PRIMARY KEY, fecha_scraping TIMESTAMP, titulo TEXT, link TEXT, imagen TEXT, resumen TEXT, origen TEXT",
                    "reuniones": "id SERIAL PRIMARY KEY, fecha VARCHAR(50), temas TEXT, asistentes TEXT, estado VARCHAR(20)",
                    "agenda": "id SERIAL PRIMARY KEY, fecha_scraping TIMESTAMP, fecha_evento TEXT, titulo TEXT, lugar TEXT, precio TEXT, link TEXT, imagen TEXT, tipo TEXT, origen TEXT"
                }

                for nombre, schema in tablas.items():
                    conn.execute(text(f"CREATE TABLE IF NOT EXISTS {nombre} ({schema})"))
                
                conn.commit()
            print("✅ [DATABASE] Tablas verificadas.")
        except Exception as e:
            print(f"❌ [DATABASE] Error: {e}")

    # ==========================================
    # GESTIÓN DE NOTICIAS (NUEVOS MÉTODOS)
    # ==========================================
    def get_agenda(self):
        """Obtener agenda ordenada por fecha"""
        try:
            # Quitamos el ORDER BY de la consulta SQL por si acaso y ordenamos en Python
            df = self.get_data('agenda')
            return df if not df.empty else pd.DataFrame()
        except:
            return pd.DataFrame()

    def borrar_agenda_antigua(self):
        """Borra eventos de la agenda con más de 15 días de antigüedad"""
        try:
            with self.engine.connect() as conn:
                # Cambiamos 30 días por 15 días
                conn.execute(text("DELETE FROM agenda WHERE fecha_scraping < NOW() - INTERVAL '15 days'"))
                conn.commit()
            print("🧹 Agenda antigua (15 días) eliminada.")
        except Exception as e:
            print(f"❌ Error borrando agenda antigua: {e}")

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
        if df_nuevas.empty: return [] # Devolvemos lista vacía
        try:
            existentes = self.get_data('noticias')
            links_existentes = existentes['link'].tolist() if not existentes.empty else []
            df_a_guardar = df_nuevas[~df_nuevas['link'].isin(links_existentes)]
            
            if not df_a_guardar.empty:
                df_a_guardar.to_sql('noticias', self.engine, if_exists='append', index=False)
                return df_a_guardar['titulo'].tolist() # DEVOLVEMOS LOS TÍTULOS
            return []
        except: return []

    def guardar_agenda_nueva(self, df_nuevas):
        if df_nuevas.empty: return [] # Devolvemos lista vacía
        try:
            existentes = self.get_data('agenda')
            if not existentes.empty:
                existentes['check'] = existentes['titulo'].astype(str) + existentes['fecha_evento'].astype(str)
                df_nuevas['check'] = df_nuevas['titulo'].astype(str) + df_nuevas['fecha_evento'].astype(str)
                df_a_guardar = df_nuevas[~df_nuevas['check'].isin(existentes['check'])].copy()
                df_a_guardar.drop(columns=['check'], inplace=True)
            else:
                df_a_guardar = df_nuevas

            if not df_a_guardar.empty:
                df_a_guardar.to_sql('agenda', self.engine, if_exists='append', index=False)
                # DEVOLVEMOS LISTA DE "FECHA - TITULO"
                return (df_a_guardar['fecha_evento'] + ": " + df_a_guardar['titulo']).tolist()
            return []
        except: return []
    
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
        """Agregar nueva fila a una tabla usando INSERT directo (seguro con múltiples workers)"""
        schemas = {
            'comidas': ['fecha', 'dia', 'tipo_comida', 'cocineros'],
            'lista_compra': ['fecha', 'objeto'],
            'mantenimiento': ['año', 'mantenimiento', 'cadafals'],
            'eventos': ['fecha', 'evento', 'tipo'],
            'fiestas': ['fecha', 'cocineros', 'menu', 'adultos', 'nombres_adultos', 'niños', 'nombres_niños', 'programa'],
            'cambios': ['fecha', 'tipo_cambio', 'descripcion', 'usuario'],
            'reuniones': ['fecha', 'temas', 'asistentes', 'estado']
        }

        columns = schemas.get(table, [])
        values = {}
        for i, col in enumerate(columns):
            if i < len(data):
                values[col] = data[i]
            else:
                values[col] = 0 if col in ['adultos', 'niños', 'año'] else ''

        cols_sql = ', '.join(values.keys())
        placeholders = ', '.join([f':{k}' for k in values.keys()])
        query = text(f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders})")

        try:
            with self.engine.connect() as conn:
                conn.execute(query, values)
                conn.commit()
            return True
        except Exception as e:
            print(f"Error insertando en {table}: {e}")
            return False
    
    def update_data(self, table, record_id, fields):
        """Actualizar un registro por ID usando UPDATE directo (seguro con múltiples workers)"""
        set_clause = ', '.join([f'{k} = :{k}' for k in fields.keys()])
        query = text(f"UPDATE {table} SET {set_clause} WHERE id = :_id")
        params = {**fields, '_id': record_id}
        try:
            with self.engine.connect() as conn:
                conn.execute(query, params)
                conn.commit()
            return True
        except Exception as e:
            print(f"Error actualizando {table} id={record_id}: {e}")
            return False

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

            with self.engine.connect() as conn:
                return pd.read_sql(text(query), conn)
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