# Robotica-Proyecto-final
Proyecto carro a control remoto y sistema de inferencia 

## Descripcion General

Este proyecto implementa un sistema de navegacion autonoma para un chasis robotico utilizando un microcontrolador ESP32-CAM y procesamiento de Inteligencia Artificial. El robot es capaz de tomar decisiones de movimiento en tiempo real basandose en la clasificacion de imagenes (deteccion de colores rojo y verde) procesadas mediante una red neuronal entrenada con Edge Impulse.

## Arquitectura del Sistema: ¿Por que se dividio el proyecto en dos partes?

Durante el desarrollo inicial, se intento ejecutar el modelo matematico de la red neuronal (MobileNetV2) directamente dentro del microcontrolador ESP32-CAM. Sin embargo, se tomo la decision critica de refactorizar la arquitectura hacia un modelo **Cliente-Servidor** (delegando el "cerebro" a una computadora externa y dejando los "musculos" en el ESP32) por las siguientes razones tecnicas:

1. **Prevencion de Saturacion de CPU (CPU Starvation):** El ESP32 es un procesador eficiente pero limitado. Al intentar mantener una conexion Wi-Fi activa, transmitir un flujo de video en tiempo real, manejar rutinas PWM para los motores y multiplicar matrices tensoriales de forma simultanea, el chip llegaba al 100% de su capacidad. Esto generaba bloqueos criticos.
2. **Estabilidad de Red y Protocolo de Seguridad:** Al estar el procesador saturado por la IA, el ESP32 no podia responder a tiempo a las solicitudes de "Handshake" (apreton de manos) de cifrado WPA2. Esto causaba que los dispositivos externos (laptops o telefonos) fueran expulsados de la red arrojando un falso error de "contrasena incorrecta".
3. **Escalabilidad y Flexibilidad:** Mudar el modelo `.tflite` a un script de Python en una computadora externa permite utilizar una capacidad de procesamiento infinitamente mayor. Esto reduce la latencia de la toma de decisiones a milisegundos y facilita la implementacion de logicas de navegacion mas complejas (como la maquina de estados de busqueda) sin modificar el firmware del robot.

En esta configuracion definitiva, el ESP32-CAM funciona estrictamente como un esclavo de hardware: captura imagenes y obedece comandos mecanicos. La computadora central funciona como el maestro: procesa la vision y dicta las acciones.

## Estructura de Hardware y Software

### Requisitos de Hardware

* Modulo ESP32-CAM (Camara OV2640).
* Modulo controlador de motores Puente H L298N.
* Chasis robotico con motores DC (Conduccion diferencial).
* Computadora (Laptop) para procesamiento central.

### Requisitos de Software

* **Microcontrolador:** Arduino IDE con el nucleo de ESP32 en su version **2.0.17**.
* **Computadora:** Python 3.x.
* **Dependencias de Python:** `pip install tensorflow opencv-python requests numpy`.
* Modelo neuronal exportado de Edge Impulse en formato TensorFlow Lite (`float32`).

## Modulos del Codigo

El proyecto consta de tres archivos principales minimizados y optimizados:

1. **`ESP32_CAM_Robot_Car.ino`:** Archivo principal de C++ para el microcontrolador. Inicializa la camara, desactiva protecciones de bajo voltaje (brown-out) para evitar reinicios, y levanta un Punto de Acceso (AP) Wi-Fi de red abierta.
2. **`app_httpd.cpp`:** Servidor web embebido y traductor de hardware. Contiene las rutinas de los canales PWM (`ledcWrite`) para controlar la velocidad y direccion de las llantas segun los comandos HTTP recibidos.
3. **`main.py`:** Script en Python que opera como el sistema de toma de decisiones.

## Logica de Navegacion (Maquina de Estados)

El script de Python implementa un algoritmo de navegacion con un mecanismo de seguridad para evitar estancamientos:

* **Objetivo Verde (Probabilidad > 60%):** El robot envia la peticion HTTP para avanzar (`/control?var=car&val=1`).
* **Señal de Paro Roja (Probabilidad > 60%):** El robot envia la peticion HTTP para frenar por completo (`/control?var=car&val=3`).
* **Modo Busqueda / Señal Perdida:** Si el sistema visualiza un entorno sin señales claras (Fondo), se acciona un contador. El robot realizara "escaneos rotativos" girando sobre su propio eje a la izquierda (`/control?var=car&val=2`) en intervalos cortos para buscar un objetivo.
* **Freno Tactico:** Si el robot supera el limite de busquedas (10 rotaciones) sin exito, asume que esta perdido y detiene todos los motores por seguridad hasta que se introduzca un nuevo estimulo visual.

## Instrucciones de Ejecucion

1. Cargar los archivos `.ino` y `.cpp` a la placa ESP32-CAM asegurando tener instalada la version correcta del nucleo y seleccionando particion de memoria adecuada para uso de camara.
2. Desconectar el cable serial, energizar el robot mediante las baterias conectadas al L298N y presionar el boton de Reset.
3. Desde la computadora, desconectarse de la red domestica y conectarse a la red inalambrica generada por el robot (por defecto: `Robot A55`).
4. Ubicar el archivo `model.tflite` en el mismo directorio que el script de Python.
5. Ejecutar el script `main.py` en la terminal. El robot comenzara a analizar el video y actuara de forma autonoma segun su entorno. Se puede detener la ejecucion presionando la tecla "Q" en la ventana de visualizacion de telemetria.
