# test_guardado.py
from data_manager import dm
import pandas as pd

print("🧪 PROBANDO GUARDADO EN PARQUET")
print("="*50)

# Ver datos actuales
lista_antes = dm.get_data('lista_compra')
print(f"\n📊 Lista ANTES: {len(lista_antes)} items")
print(lista_antes)

# Agregar un item de prueba
print("\n➕ Agregando item de prueba...")
resultado = dm.add_data('lista_compra', ('2025-01-15', 'Test Item'))
print(f"Resultado add_data: {resultado}")

# Verificar después
lista_despues = dm.get_data('lista_compra')
print(f"\n📊 Lista DESPUÉS: {len(lista_despues)} items")
print(lista_despues)

# Ver el archivo físico
import os
filepath = 'data/lista_compra.parquet'
if os.path.exists(filepath):
    size = os.path.getsize(filepath)
    print(f"\n📁 Archivo: {filepath}")
    print(f"   Tamaño: {size} bytes")
    
    # Leer directamente del parquet
    df_directo = pd.read_parquet(filepath)
    print(f"   Registros en archivo: {len(df_directo)}")
else:
    print(f"\n❌ Archivo no existe: {filepath}")