import os
import pandas as pd
from datetime import datetime
from telegram import Bot
from data_manager import dm # Importamos nuestro gestor de datos existente


def enviar_notificacion_telegram(mensaje):
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not bot_token or not chat_id:
        print("❌ ERROR: Variables de entorno de Telegram no configuradas.")
        return False
    try:
        bot = Bot(token=bot_token)
        asyncio.run(bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown'))
        print("✅ Mensaje enviado a Telegram.")
        return True
    except Exception as e:
        print(f"❌ ERROR al enviar a Telegram: {e}"

        return False

def generar_y_enviar_resumen():
    """
    Obtiene los datos de las comidas del año, los formatea y los envía.
    """
    print("🗓️ Iniciando la generación del resumen trimestral de comidas...")
    
    try:
        # 1. Obtener todas las comidas de la base de datos
        comidas_df = dm.get_data('comidas')
        if comidas_df.empty:
            enviar_notificacion_telegram("🗓️ *Resum Trimestral:*\n\nEncara no hi ha menjars registrats aquest any.")
            return

        # 2. Filtrar por el año actual
        año_actual = datetime.now().year
        comidas_df['año'] = pd.to_datetime(comidas_df['fecha']).dt.year
        comidas_año_actual = comidas_df[comidas_df['año'] == año_actual].sort_values('fecha')
        
        if comidas_año_actual.empty:
            enviar_notificacion_telegram(f"🗓️ *Resum Trimestral:*\n\nEncara no hi ha menjars registrats per al {año_actual}.")
            return

        # 3. Formatear el mensaje de resumen
        resumen_str = f"🗓️ *Resum Trimestral de Menjars ({año_actual}):*"
        for _, row in comidas_año_actual.iterrows():
            fecha_formateada = pd.to_datetime(row['fecha']).strftime('%d/%m/%Y')
            dia_formateado = row['dia'].replace('_', ' ').title()
            resumen_str += f"\n- *{fecha_formateada}* ({dia_formateado}): {row['cocineros']}"

        # 4. Enviar el mensaje formateado
        enviar_notificacion_telegram(resumen_str)
        print("✅ Resumen trimestral generado y enviado con éxito.")

    except Exception as e:
        print(f"❌ ERROR FATAL al generar el resumen: {e}")
        mensaje_error = f"🤖 Error en el sistema de resums automàtics: {e}"
        enviar_notificacion_telegram(mensaje_error)

if __name__ == '__main__':
    # Esta línea asegura que el código se ejecute cuando Render llame al script.
    generar_y_enviar_resumen()