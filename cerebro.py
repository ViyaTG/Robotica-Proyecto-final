"""
Motor de Inferencia y Control Centralizado.
Procesa fotogramas capturados por el ESP32, evalua predicciones
mediante TensorFlow Lite y comanda la navegacion del vehiculo.
"""

import cv2
import urllib.request
import numpy as np
import requests
import time
import tensorflow as tf

# Puntos de acceso al servidor del robot
URL_CAM = "http://192.168.4.1/capture"
URL_CMD = "http://192.168.4.1/control?var=car&val="

# Asignacion de tensores e inicializacion del modelo matematico
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def send_command(cmd_val):
    # Enrutador de instrucciones HTTP hacia el chasis
    try:
        requests.get(f"{URL_CMD}{cmd_val}", timeout=1)
    except requests.exceptions.RequestException:
        pass

def main():
    print("Inicializando Motor de Inferencia...")
    
    # Variables de control para la maquina de estados (Modo Busqueda)
    intentos_busqueda = 0
    limite_intentos = 10
    
    while True:
        try:
            # 1. Adquisicion del fotograma remoto
            img_resp = urllib.request.urlopen(URL_CAM)
            imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(imgnp, -1)

            # 2. Acondicionamiento de entrada a resolucion de entrenamiento
            img_resized = cv2.resize(frame, (96, 96))
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            
            # Normalizacion de datos a formato de punto flotante
            input_data = np.expand_dims(img_rgb, axis=0).astype(np.float32) / 255.0

            # 3. Evaluacion del clasificador neuronal
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            output_data = interpreter.get_tensor(output_details[0]['index'])[0]

            # Extraccion de la distribucion de probabilidades
            prob_rojo = output_data[0]
            prob_fondo = output_data[1]
            prob_verde = output_data[2]

            print(f"Prediccion -> Verde: {prob_verde:.2f} | Rojo: {prob_rojo:.2f} | Fondo: {prob_fondo:.2f}")

            # 4. Logica algoritmica de navegacion autonoma
            if prob_verde > 0.70:
                print("ESTADO: Objetivo Verde Localizado. Avanzando.")
                send_command(1) 
                intentos_busqueda = 0 # Reinicio del contador de busqueda al confirmar objetivo
                
            elif prob_rojo > 0.40:
                print("ESTADO: Señal de Paro Localizada. Deteniendo.")
                send_command(3) 
                intentos_busqueda = 0 # Reinicio del contador de busqueda al confirmar objetivo
                
            else:
                # Rutina de busqueda con radar rotativo ante falta de deteccion
                intentos_busqueda += 1
                
                if intentos_busqueda <= limite_intentos:
                    print(f"ESTADO: Señal perdida. Ejecutando escaneo rotativo... (Intento {intentos_busqueda}/{limite_intentos})")
                    send_command(2) # Ejecuta giro diferencial izquierdo
                else:
                    print("ESTADO: Freno tactico por exceso de intentos nulos.")
                    send_command(3) # Cesa todo movimiento
            
            # Renderizado de video local para monitorizacion de pruebas
            cv2.imshow("Telemetria Visual Robot", frame)
            
            # Terminacion forzada al presionar tecla Q
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # Retraso para estabilidad en el flujo de la red local
            time.sleep(0.5)
            
        except Exception as e:
            print("Sondeando conexion inalambrica con el robot...")
            time.sleep(2)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()