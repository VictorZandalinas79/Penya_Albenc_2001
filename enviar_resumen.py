import os
import asyncio
import pandas as pd
from datetime import datetime
from telegram import Bot
from data_manager import dm


async def _enviar_mensaje_async(bot_token, chat_id, mensaje):
    """Función async interna para enviar el mensaje."""
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')


def enviar_notificacion_telegram(mensaje):
    """Envía un mensaje a Telegram de forma síncrona."""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ ERROR: Variables de entorno de Telegram no configuradas.")
        print("   Asegúrate de tener TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID definidas.")
        return False
    
    try:
        # Crear nuevo event loop para evitar conflictos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_enviar_mensaje_async(bot_token, chat_id, mensaje))
        loop.close()
        print("✅ Mensaje enviado a Telegram.")
        return True
    except Exception as e:
        print(f"❌ ERROR al enviar a Telegram: {e}")
        return False


def generar_y_enviar_resumen():
    """
    Obtiene los datos de las comidas del año, los formatea y los envía.
    Pensado para ejecutarse como Cron Job trimestral.
    """
    print("🗓️ Iniciando la generación del resumen trimestral de comidas...")
    
    try:
        # 1. Obtener todas las comidas de la base de datos
        comidas_df = dm.get_data('comidas')
        if comidas_df.empty:
            enviar_notificacion_telegram("🗓️ *Resum Trimestral:*\n\nEncara no hi ha menjars registrats.")
            return

        # 2. Filtrar por el año actual
        año_actual = datetime.now().year
        comidas_df['año'] = pd.to_datetime(comidas_df['fecha']).dt.year
        comidas_año_actual = comidas_df[comidas_df['año'] == año_actual].sort_values('fecha')
        
        if comidas_año_actual.empty:
            enviar_notificacion_telegram(
                f"🗓️ *Resum Trimestral:*\n\nEncara no hi ha menjars registrats per al {año_actual}."
            )
            return

        # 3. Formatear el mensaje de resumen
        resumen_str = f"🗓️ *Resum Trimestral de Menjars ({año_actual}):*\n"
        
        for _, row in comidas_año_actual.iterrows():
            fecha_formateada = pd.to_datetime(row['fecha']).strftime('%d/%m/%Y')
            dia_formateado = (row['dia'] or 'Comida').replace('_', ' ').title()
            cocineros = row['cocineros'] or 'No assignats'
            resumen_str += f"\n• *{fecha_formateada}* ({dia_formateado}): {cocineros}"

        # 4. Añadir estadísticas
        total_comidas = len(comidas_año_actual)
        resumen_str += f"\n\n📊 *Total menjars programats:* {total_comidas}"

        # 5. Enviar el mensaje formateado
        enviar_notificacion_telegram(resumen_str)
        print("✅ Resumen trimestral generado y enviado con éxito.")

    except Exception as e:
        print(f"❌ ERROR FATAL al generar el resumen: {e}")
        mensaje_error = f"🤖 Error en el sistema de resums automàtics:\n`{e}`"
        enviar_notificacion_telegram(mensaje_error)


def generar_resumen_semanal():
    """
    Genera un resumen de los próximos eventos de la semana.
    Útil para recordatorios semanales (ej: cada lunes).
    """
    print("📅 Generando resumen semanal...")
    
    try:
        from datetime import timedelta
        
        hoy = datetime.now()
        fin_semana = hoy + timedelta(days=7)
        
        # Obtener comidas de la próxima semana
        comidas_df = dm.get_data('comidas')
        eventos_df = dm.get_data('eventos')
        
        mensaje = f"📅 *Resum Setmanal ({hoy.strftime('%d/%m')} - {fin_semana.strftime('%d/%m')}):*\n"
        hay_eventos = False
        
        # Comidas de la semana
        if not comidas_df.empty:
            comidas_df['fecha_dt'] = pd.to_datetime(comidas_df['fecha'])
            comidas_semana = comidas_df[
                (comidas_df['fecha_dt'] >= hoy) & 
                (comidas_df['fecha_dt'] <= fin_semana)
            ].sort_values('fecha_dt')
            
            if not comidas_semana.empty:
                hay_eventos = True
                mensaje += "\n🍽️ *Menjars:*"
                for _, row in comidas_semana.iterrows():
                    fecha = row['fecha_dt'].strftime('%A %d').capitalize()
                    dia = (row['dia'] or '').replace('_', ' ').title()
                    mensaje += f"\n• {fecha}: {dia} - {row['cocineros']}"
        
        # Eventos de la semana
        if not eventos_df.empty:
            eventos_df['fecha_dt'] = pd.to_datetime(eventos_df['fecha'])
            eventos_semana = eventos_df[
                (eventos_df['fecha_dt'] >= hoy) & 
                (eventos_df['fecha_dt'] <= fin_semana)
            ].sort_values('fecha_dt')
            
            if not eventos_semana.empty:
                hay_eventos = True
                mensaje += "\n\n🎉 *Events:*"
                for _, row in eventos_semana.iterrows():
                    fecha = row['fecha_dt'].strftime('%A %d').capitalize()
                    mensaje += f"\n• {fecha}: {row['evento']}"
        
        if not hay_eventos:
            mensaje += "\n\nNo hi ha events programats aquesta setmana. 😴"
        
        enviar_notificacion_telegram(mensaje)
        print("✅ Resumen semanal enviado.")
        
    except Exception as e:
        print(f"❌ ERROR en resumen semanal: {e}")


if __name__ == '__main__':
    import sys
    
    # Permite elegir qué resumen enviar desde línea de comandos
    if len(sys.argv) > 1:
        if sys.argv[1] == 'semanal':
            generar_resumen_semanal()
        elif sys.argv[1] == 'trimestral':
            generar_y_enviar_resumen()
        else:
            print("Uso: python enviar_resumen.py [semanal|trimestral]")
    else:
        # Por defecto, envía el resumen trimestral
        generar_y_enviar_resumen()