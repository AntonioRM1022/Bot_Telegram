from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
from telegram import Update
from dotenv import load_dotenv
import os
import openai
import pandas as pd

# Carga de variables de entorno
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

mensajes = {}
dataframes = {}
promedios = {}

# Funciones auxiliares para la carga y procesamiento de datos
def cargar_archivos(archivos):
    global dataframes
    dataframes = {}
    for archivo in archivos:
        try:
            nombre = archivo.split('_')[1].split('.')[0]  # Extrae el nombre del estudiante
            df = pd.read_excel(archivo, header=None)
            df.columns = ['ID', 'Materia', 'Creditos', 'Semestre', 'Calificacion', 'Periodo']
            df['Calificacion'] = pd.to_numeric(df['Calificacion'], errors='coerce')
            dataframes[nombre] = df
        except Exception as e:
            print(f"Error al procesar {archivo}: {e}")

def calcular_promedios():
    global promedios
    promedios = {
        nombre: df['Calificacion'].mean()
        for nombre, df in dataframes.items()
        if not df['Calificacion'].isna().all()
    }

# Cargar los datos al inicio
archivos = ['kardex_Cesar_Meza.xlsx', 'kardex_torres_Raul.xlsx', 'kardex_leo_landa.xlsx', 'kardex_Angel_Radilla.xlsx']
cargar_archivos(archivos)
calcular_promedios()

# Guardar el mensaje del usuario
def handle_user_message(message):
    if mensajes.get(message.from_user.id) is None:
        mensajes[message.from_user.id] = {"messages": [{
            "role": "user",
            "content": message.text}]}
    else:
        mensajes[message.from_user.id]["messages"].append({
            "role": "user",
            "content": message.text})
        
# Generar la respuesta del bot
def generate_response(message):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=mensajes[message.from_user.id]["messages"],
    )
    response = completion.choices[0].message.content
    mensajes[message.from_user.id]["messages"].append({
        "role": "assistant",
        "content": response})
    return response

# Manejo de comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu asistente para calificaciones. Usa /promedios para ver los promedios de los estudiantes.")

async def promedios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not promedios:
        await update.message.reply_text("No hay datos disponibles para calcular los promedios.")
    else:
        respuesta = "\n".join([f"{nombre}: {promedio:.2f}" for nombre, promedio in promedios.items()])
        await update.message.reply_text(f"Promedios de los estudiantes:\n{respuesta}")

async def calificaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not dataframes:
        await update.message.reply_text("No hay datos disponibles.")
    else:
        for nombre, df in dataframes.items():
            await update.message.reply_text(f"Calificaciones de {nombre}:\n{df.to_string(index=False)}")

# Función para mensajes regulares
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    handle_user_message(update.message)
    response = generate_response(update.message)
    await update.message.reply_text(response)

def main():
    TELEGRAM_TOKEN = os.getenv("7512320848:AAH8AMxzChOM0k6I605ZSoC1m12hHgGatBk")
    bot = Application.builder().token(TELEGRAM_TOKEN).build()

    # Handlers para comandos
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("promedios", promedios))
    bot.add_handler(CommandHandler("calificaciones", calificaciones))

    # Handler para mensajes regulares
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Ejecutar el bot
    bot.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
