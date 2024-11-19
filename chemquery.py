# Este proyecto tiene como objetivo desarrollar una aplicación que permita consultar información 
# sobre productos químicos a través de una API de inteligencia artificial (OpenAI) y almacenar 
# las consultas realizadas en una base de datos y un archivo CSV. Además, la aplicación incluye un 
# lector de códigos de barra o QR que facilita la identificación de los productos mediante escaneo. 
# El flujo de la aplicación está diseñado para ofrecer dos opciones: escanear un código o ingresar 
# el nombre del producto manualmente, lo que proporciona flexibilidad en la entrada de datos.

# Importamos las bibliotecas necesarias para la funcionalidad de la aplicación
import openai
import csv
from datetime import datetime
import sqlite3
import cv2
from pyzbar.pyzbar import decode
from config import Api_key  

# Configuramos la clave de la API de OpenAI
openai.api_key = Api_key

# Inicializamos la base de datos SQLite para registrar las consultas
# Esta función crea una tabla en la base de datos llamada 'consultas' si no existe,
# donde se almacenarán el nombre del producto, el resultado de la consulta y la fecha.
def inicializar_db():
    conn = sqlite3.connect('consultas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP,
            producto TEXT,
            resultado TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Función para guardar cada consulta realizada en la base de datos
# Recibe el nombre del producto y el resultado de la consulta, y almacena ambos junto con la fecha.
def registrar_consulta(nombre_producto, resultado):
    try:
        conn = sqlite3.connect('consultas.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO consultas (fecha, producto, resultado)
            VALUES (?, ?, ?)
        ''', (datetime.now(), nombre_producto, resultado))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al registrar en la base de datos: {e}")
    finally:
        conn.close()

# Función para realizar una consulta a OpenAI sobre el producto
# Envía una pregunta a OpenAI sobre la seguridad del producto y retorna la respuesta del modelo.
def consulta_bot(pregunta):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Cambia a "gpt-4" si tienes acceso
            messages=[{"role": "user", "content": pregunta}],
            temperature=0.5
        )
        return response.choices[0].message['content']
    except openai.error.RateLimitError:
        print("Se ha excedido el límite de la cuota de OpenAI.")
        return "Error: Límite de consultas excedido."
    except Exception as e:
        print(f"Error en la consulta a OpenAI: {e}")
        return "Error en la consulta."

# Función principal para consultar si el producto es peligroso
# Genera una pregunta sobre la peligrosidad del producto y llama a la función de consulta.
# Luego guarda el resultado en la base de datos.
def consultar_producto(nombre_producto):
    pregunta = f"¿Es peligroso el producto {nombre_producto} y cómo manejarlo de manera segura?"
    resultado = consulta_bot(pregunta)
    registrar_consulta(nombre_producto, resultado)
    return resultado

# Función para registrar la consulta en un archivo CSV
# Guarda cada consulta realizada en un archivo CSV con la fecha, el nombre del producto y el resultado.
def registrar_consulta_csv(nombre_producto, resultado):
    try:
        with open('registro_consultas.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([datetime.now(), nombre_producto, resultado])
    except IOError as e:
        print(f"Error al guardar en CSV: {e}")

# Lector de códigos de barra o QR
# Utiliza la cámara para detectar y leer códigos de barra o QR. Retorna el texto del código leído.
def leer_codigo():
    cap = cv2.VideoCapture(0)
    print("Escanea un código QR o de barras")

    while True:
        _, frame = cap.read()
        for barcode in decode(frame):
            data = barcode.data.decode("utf-8")
            print(f"Código detectado: {data}")
            cap.release()
            cv2.destroyAllWindows()
            return data  # Retorna el texto del código
        cv2.imshow("Lector de Código", frame)
        if cv2.waitKey(1) == 27:  # Presiona ESC para salir
            break
    cap.release()
    cv2.destroyAllWindows()
    return None

# Integración del lector con la consulta del bot
# Escanea un código y realiza la consulta sobre el producto identificado, registrando el resultado en CSV.
def iniciar_consulta_por_codigo():
    codigo = leer_codigo()
    if codigo:
        resultado = consultar_producto(codigo)
        registrar_consulta_csv(codigo, resultado)  # También registramos en CSV
        print(f"Resultado de la consulta para {codigo}: {resultado}")
    else:
        print("No se detectó ningún código.")

# Ejecución principal del programa
# Este bloque permite al usuario elegir entre escanear un código o ingresar manualmente el nombre del producto.
if __name__ == "__main__":
    inicializar_db()  # Inicializa la base de datos para registrar consultas

    opcion = input("¿Quieres escanear un código (1) o ingresar un nombre de producto (2)? ")
    if opcion == "1":
        iniciar_consulta_por_codigo()
    elif opcion == "2":
        nombre_producto = input("Ingresa el nombre del producto químico: ")
        resultado = consultar_producto(nombre_producto)
        registrar_consulta_csv(nombre_producto, resultado)  # Registro en CSV
        print(f"Resultado de la consulta para {nombre_producto}: {resultado}")
    else:
        print("Opción no válida")
