# gunicorn.conf.py

# Número de "trabajadores" (workers) para manejar las peticiones.
# Un buen punto de partida es (2 * número_de_cores_cpu) + 1
workers = 3

# Interfaz a la que se vinculará el servidor (0.0.0.0 para todas las interfaces)
bind = "0.0.0.0:8050"

# Timeout en segundos. Si una petición tarda más que esto, se reinicia el worker.
# Lo subimos a 120 segundos para dar tiempo a tareas lentas como generar PDFs.
timeout = 120

# Nivel de los logs (debug, info, warning, error, critical)
loglevel = "info"

# Recargar automáticamente los workers si el código cambia (solo para desarrollo, no usar en producción final)
# reload = True