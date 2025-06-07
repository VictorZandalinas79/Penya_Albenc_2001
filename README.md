# 🏛️ PENYA L'ALBENC VILAFRANCA - Datos Reales

## 📋 **Datos Incluidos del PDF**

La aplicación ahora incluye **TODOS los datos reales** del PDF oficial de PENYA L'ALBENC:

### **📅 Años Cubiertos**: 2025 - 2045 (21 años)

### **👥 Personas Incluidas**:
- **David** | **Juan Fernando** | **Diego** | **Miguel A.**
- **Xisco** | **Serafin** | **Juan Ramon** | **Oscar**
- **Alfonso** | **Victor Z.** | **Victor M.** | **Raul A.**
- **Raul M.** | **Alonso** | **Lluis**

---

## 🎉 **Fiestas Oficiales con Fechas Calculadas**

### **🎭 Sant Antoni**
- **Cuándo**: Tercer sábado de enero
- **Tipo**: Solo cena
- **Menú**: Cena especial Sant Antoni, Coca amb tonyina, Vino tinto, Anís

### **⛪ Brena St Vicent**  
- **Cuándo**: Sábado más cercano al 28 de abril
- **Tipo**: Comida y cena
- **Menú**: Paella Valenciana, Ensalada mixta, Naranjas, Moscatel

### **🎪 Fira Magdalena**
- **Cuándo**: Tercer sábado de julio  
- **Tipo**: Comida y cena
- **Menú**: Arroz con pollo, Gazpacho, Melón con jamón, Horchata

### **🐂 Penya Taurina** *(antes Festa Septembre)*
- **Cuándo**: Último sábado de mayo
- **Tipo**: Solo comida  
- **Menú**: Fideuá de mariscos, Sepia a la plancha, Cerveza, Café

---

## 🔧 **Mantenimiento y Cadafals**

### **📋 Mantenimiento**
Encargados del mantenimiento general del local cada año.

### **🏗️ Cadafals**  
Encargados de montar y desmontar estructuras para fiestas.

**Ambos están separados en columnas distintas** según los datos del PDF.

---

## 🚀 **Cómo Usar los Datos Reales**

### **Opción 1: Importación Completa (Recomendada)**
```bash
# Importar TODOS los datos del PDF (2025-2045)
python scripts/import_penya_data.py
```

### **Opción 2: Datos Básicos**
```bash
# Solo algunos años de muestra
python scripts/reset_data.py
```

### **Opción 3: Ejecutar Directamente**
```bash
# Los datos básicos se crean automáticamente
python run.py
```

---

## 📊 **Estadísticas de Datos Reales**

### **📋 Mantenimiento**: 21 registros
- Un registro por año desde 2025 hasta 2045
- Dos columnas: Mantenimiento y Cadafals
- Personas asignadas según planificación oficial

### **🎉 Fiestas**: 84 eventos
- **21 Sant Antoni** (enero)
- **21 Brena St Vicent** (abril)  
- **21 Fira Magdalena** (julio)
- **21 Penya Taurina** (mayo)

### **👥 Personas**: 15 miembros
- Rotación organizada por años
- Distribución equitativa de responsabilidades
- Planificación a largo plazo (21 años)

---

## 📅 **Ejemplos de Fechas Calculadas para 2025**

| Fiesta | Fecha Calculada | Día Semana |
|--------|----------------|------------|
| **Sant Antoni** | 18/01/2025 | Sábado |
| **Brena St Vicent** | 26/04/2025 | Sábado |
| **Penya Taurina** | 31/05/2025 | Sábado |
| **Fira Magdalena** | 19/07/2025 | Sábado |

---

## 🎯 **Funcionalidades Específicas para PENYA L'ALBENC**

### **✅ Gestión de Comidas**
- Intercambio de encargados entre fechas
- Copia de asignaciones a nuevas fechas
- Edición directa en tablas

### **✅ Gestión de Fiestas**  
- Solo los 4 tipos oficiales de la penya
- Fechas calculadas automáticamente
- Menús tradicionales incluidos
- Encargados según planificación del PDF

### **✅ Mantenimiento Dual**
- Mantenimiento general del local
- Cadafals para estructuras de fiestas
- Planificación anual desde 2025 hasta 2045

### **✅ Lista de Compra**
- Plantillas rápidas (Básicos, Carnes, Verduras, Limpieza)  
- Organización por fechas
- Edición y eliminación fácil

---

## 🔄 **Comandos Útiles**

```bash
# Ver datos importados
python scripts/import_penya_data.py

# Resetear todo
python scripts/reset_data.py  

# Ejecutar aplicación
python run.py

# Hacer backup manual
cp data/*.parquet data/backups/
```

---

## 💡 **Notas Importantes**

1. **Fechas Dinámicas**: Las fechas se calculan automáticamente cada año
2. **Datos Históricos**: Incluye planificación hasta 2045
3. **Rotación Organizada**: Distribución equitativa de responsabilidades  
4. **Menús Tradicionales**: Platos típicos valencianos
5. **Backup Automático**: Los cambios se respaldan automáticamente

---

## 🎨 **Interfaz Personalizada**

- **Colores**: Verde y azul (colores de la penya)
- **Nombres Reales**: Todos los miembros incluidos
- **Fechas Valencianas**: Fiestas tradicionales de la región  
- **Usabilidad**: Optimizada para gestión diaria

---

**¡La aplicación ahora refleja fielmente la estructura y planificación real de PENYA L'ALBENC de Vilafranca!** 🏛️✨