import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
import time
import socket
from PIL import Image, ImageTk
import winsound
import pygame

ancho = 900
alto = 700
UNIDAD_A = 0.2
UNIDAD_B = 0.3


# Configurar audio para bip
pygame.mixer.pre_init(44100, -16, 1, 256) # buffer pequeno para mas velocidad
pygame.init()

tone = pygame.mixer.Sound("cods/host/bip.wav") # cargamos el wav con el tono
# para hacerlo sonar usamos tono.play(-1) y para denterlo usamos tono.stop()

# Crear ventana principal
window = tk.Tk()
window.title("Juego de Morse Stranger TEC")
window.geometry(f"{ancho}x{alto}")
window.resizable(True, True)

# Cargar imagen de fondo
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
bg_image = Image.open(os.path.join(BASE_DIR, "cods/host/Fondo/fondo.png"))
bg_image = bg_image.resize((ancho, alto))
bg_photo = ImageTk.PhotoImage(bg_image)

canvas = tk.Canvas(window, width=ancho, height=alto, highlightthickness=0)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, anchor="nw", image=bg_photo)
canvas.image = bg_photo

#modificar el estilo
style = ttk.Style()

style.configure("TFrame", background="")
style.configure("TLabel", background="#0d0d0d", foreground="#FFFFFF")# para el fondo de los textos y el color de sus letras
style.configure("TButton", background="#ff003300", foreground="#FFFFFF", font=("Arial", 12, "bold")) # para el fondo de los botones y el color de sus letras
window.configure(background="#0d0d0d") # para el fondo de la ventana
print(os.path.exists)

frases = [
    "Aguacate majado", "Que gustazo", "Proceso", "Singular", "Amarillo", "Si", "No", 
    "Vamos", "Busque bien", "Pereza"
]

# Diccionario Morse incluyendo simbolos y números
letras_morse = {
    "A": "·—", "B": "—···", "C": "—·—·", "D": "—··", "E": "·",
    "F": "··—·", "G": "——·", "H": "····", "I": "··", "J": "·———",
    "K": "—·—", "L": "·—··", "M": "——", "N": "—·", "O": "———",
    "P": "·——·", "Q": "——·—", "R": "·—·", "S": "···", "T": "—",
    "U": "··—", "V": "···—", "W": "·——", "X": "—··—", "Y": "—·——", "Z": "——··",
    "0": "—————", "1": "·————", "2": "··———", "3": "···——", "4": "····—",
    "5": "·····", "6": "—····", "7": "——···", "8": "———··", "9": "————·",
    "+": "·—·—·", "-": "—····—"
}

morse_letras = {v: k for k, v in letras_morse.items()}
# función para convertir texto a morse  nota char = carácter individual
def texto_a_morse(texto):
    resultado = []
    for char in texto.upper():  # Convertir a Mayúsculas para buscar en el diccionario
        if char in letras_morse:
            resultado.append(letras_morse[char])
        elif char == " ":
            resultado.append("/")  # Separador de palabras concatenarlas sin que se peguen
        else:
            resultado.append(char)
    return " ".join(resultado)
# convertidor de morse a texto nota código = morse individual, 
# resultado concatenado sin espacios, palabra = codigos morse ingresados
def morse_a_texto(morse):
    palabras = morse.split("/")
    resultado = []
    for palabra in palabras:
        letras = palabra.split(" ")
        texto_palabra = ""
        for codigo in letras:
            if codigo in morse_letras:
                texto_palabra += morse_letras[codigo]
            else:
                texto_palabra += codigo
        resultado.append(texto_palabra)
    return " ".join(resultado)
# Variables globales para el juego
frase_actual = ""
puntaje_jugador_a = 0
puntaje_jugador_b = 0
turno_actual = "A"  # turno del jugador A o B
modo_juego = ""     # modo de juego "simple" o "escucha_transmision"
nivel_velocidad = 1 # nivel de velocidad del juego 1=lento, 2=medio, 3=rápido
sock=None

def abrirSocket():
    global sock
    # IP de la Raspberry Pi Pico W (cámbiarla por la real)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("192.168.50.107", 8080))  # PUERTO
        return True
    except:
        messagebox.showerror("Error", "No se pudo conectar con Raspberry") # en caso de que no se logre la conexión
        return False

# función para enviar mensaje a la raspberry mediante wifi  ojo que esta parte es experimental
# pues aun no se tiene el código importado esta parte es como una plantilla
def enviar_a_raspberry(mensaje):
    global sock
    try:
        sock.send(mensaje.encode())
        return True
    except Exception as e:
        messagebox.showerror("Error", "No se pudo conectar con Raspberry") # en caso de que no se logre la conexión
        print (str(e))
        return False
    

# receptor de mensaje de la raspberry nuevamente este apartado es experimental pues hay que definirla
def recibir_de_raspberry():
    global puntaje_jugador_a
    global puntaje_jugador_b
    # Implementar cuando tengas el código de la Raspberry
    try:
        data = sock.recv(1024)
        if data:
            message = data.decode("utf-8")
            frase,morse=parse_message(message)
            print("Maqueta envio:",frase, "con morse:", morse)
            # Calcular puntaje 
            puntaje = sum(1 for a, b in zip(frase_actual, frase) if a == b)   
            #if turno_actual == "B":
            #    puntaje_jugador_a += puntaje
            #    label_puntaje_a.config(text=f"Jugador A: {puntaje_jugador_a}")
            #else:
            puntaje_jugador_b += puntaje
            label_puntaje_b.config(text=f"Jugador B: {puntaje_jugador_b}")  
    except:
        messagebox.showerror("Error", "No se pudo conectar con Raspberry") # en caso de que no se logre la conexión
        return "No"     
    return message  # Mensaje de prueba


# selección de frase aleatoria para el juego
def nueva_frase():
    global frase_actual, keyboardMorse, letraMorse
    frase_actual = random.choice(frases)
    morse_frase = texto_a_morse(frase_actual)
    
    # Etiquetas para mostrar la frase en morse en la interfaz 
    label_frase.config(text=f"Frase secreta: ******")  # se presenta problemas con las etiquetas hay que tratar de corregir
    label_morse.config(text=f"Morse: ******")
    keyboardMorse = ""
    letraMorse = ""

    # Enviar a Raspberry
    enviar_a_raspberry(f"FRASA:{frase_actual}|MORSE:{morse_frase}")
    
    # Resetear entrada
    entrada_jugador.delete(0, tk.END)
    



# Calificador de la respuesta del jugador actual y le asigna su puntaje dependiendo de la cantidad de caracteres correctos
def evaluar_respuesta():
    global puntaje_jugador_a, puntaje_jugador_b, turno_actual, keyboardMorse
    
    #respuesta = entrada_jugador.get().strip().upper()
    texto_respuesta = morse_a_texto(keyboardMorse)
    
    # Calcular puntaje 
    puntaje = sum(1 for a, b in zip(frase_actual, texto_respuesta) if a == b)
    
    #if turno_actual == "A":
    puntaje_jugador_a += puntaje
    label_puntaje_a.config(text=f"Jugador A: {puntaje_jugador_a}")
    #else:
    #    puntaje_jugador_b += puntaje
    #    label_puntaje_b.config(text=f"Jugador B: {puntaje_jugador_b}")

    morse_frase = texto_a_morse(frase_actual)
    
    # Etiquetas para mostrar la frase en morse en la interfaz 
    label_frase.config(text=f"Frase secreta: {frase_actual}")  # se presenta problemas con las etiquetas hay que tratar de corregir
    label_morse.config(text=f"Morse: {morse_frase}")
    
    messagebox.showinfo("Resultado", 
                       f"Tu respuesta: {texto_respuesta}\n"
                       f"Correcto: {frase_actual}\n"
                       f"Puntos: {puntaje}")
    
    cambiar_turno()
    respuesta = recibir_de_raspberry()
    #print("llego: " + respuesta)

# función de cambio de turno del jugador A al B
def cambiar_turno():
    global turno_actual
    turno_actual = "B" if turno_actual == "A" else "A"
    label_turno.config(text=f"Turno: Jugador {turno_actual}")
    entrada_jugador.delete(0, tk.END)
    entrada_jugador.focus()

#Descompone respuesta de raspberry   
def parse_message(message):
    parts = message.strip().split("|")
    
    result = {}
    
    for part in parts:
        if ":" in part:
            key, value = part.split(":", 1)
            result[key.strip()] = value.strip()
            
    frase = result.get("FRASE", "")
    morse = result.get("MORSE", "")
    
    return frase, morse

# inicio de la nueva ronda del juego
def iniciar_ronda():
    global puntaje_jugador_a, puntaje_jugador_b
    turno_actual = "A"
    label_puntaje_a.config(text="Jugador A: 0")
    label_puntaje_b.config(text="Jugador B: 0")
    label_turno.config(text="Turno: Jugador A")
    nueva_frase()

    #respuesta = recibir_de_raspberry()
    #print("llego: " + respuesta)

# función del modo simple del juego donde la raspberry manda el mensaje y el PC la recibe
def configurar_modo_simple():
    global modo_juego
    modo_juego = "simple"
    label_modo.config(text="MODO: Transmisión Simple")
    # En modo simple: Raspberry envía, PC recibe
    try:
        frase = random.choice(frases)  # Seleccionar frase aleatoria
        morse_frase = texto_a_morse(frase)
        enviar_a_raspberry(f"SIMPLE:{frase}|MORSE:{morse_frase}")
        label_frase.config(text=f"Enviado a Raspberry: {frase}")
        print(f"Enviado a Raspberry: {frase}")
    except Exception as e:
        label_frase.config(text=f"Error enviando: {str(e)}")
        print(f"Error: {e}")

puntaje_jugador_a = 0
puntaje_jugador_b = 0
# modo de juego doble donde el  jugador escucha y replica el mensaje
def configurar_modo_doble():
    global modo_juego
    modo_juego = "escucha_transmision"
    label_modo.config(text="MODO: Escucha y Transmisión")
    iniciar_ronda()

pressStart=None
releaseStart=None
keyboardMorse=""
letraMorse = ""
letraCompleta=False
palabraCompleta=False
def onKeyPress(event):
    global pressStart, keyboardEnableEntry, letraCompleta, palabraCompleta, tone
    if keyboardEnableEntry:
        return
    if event.keysym == "space" and pressStart is None:
        pressStart=time.time()
        letraCompleta = False
        palabraCompleta = False
        #enviar_a_raspberry("p")
        # quitamos winsound.PlaySound("bip.wav",winsound.SND_ASYNC | winsound.SND_LOOP) por que es muy lento
        tone.play(-1)
        return "break"

def onKeyRelease(event):
    global pressStart, keyboardMorse, keyboardEnableEntry, releaseStart, letraMorse, tone
    if keyboardEnableEntry:
        return
    if event.keysym == "space" and pressStart is not None:
        duration = time.time()-pressStart
        releaseStart = time.time()
        #enviar_a_raspberry("n")
        # quitamos winsound.PlaySound(None,winsound.SND_PURGE) por que es muy lento
        tone.stop()
        if duration < 0.3:
            keyboardMorse = keyboardMorse + "·"
            letraMorse = letraMorse + "·"
        else:
            keyboardMorse = keyboardMorse + "—"
            letraMorse = letraMorse + "—"
        pressStart = None
        return "break"

def checkIdleTime():
    global keyboardMorse, letraCompleta, palabraCompleta, letraMorse
    if pressStart == None and not releaseStart == None:
        idle = time.time()-releaseStart
        if idle > UNIDAD_A*7 and not palabraCompleta:
            keyboardMorse = keyboardMorse + "/"
            if letraMorse in morse_letras:
                print(morse_letras[letraMorse]), "/"
            letraMorse = "" 
            letraCompleta = True
            palabraCompleta = True
            #enviar_a_raspberry(" ")
        elif idle > UNIDAD_A*3 and not letraCompleta:
            keyboardMorse = keyboardMorse + " "
            letraCompleta = True
            if letraMorse in morse_letras:
                print(morse_letras[letraMorse], " ")
            letraMorse = "" 
            #enviar_a_raspberry(" ")
    window.after(100, checkIdleTime)

# --------------------configuración de la interfaz gráfica--------------------
# sección de configuración modo de juego
main_frame = tk.Frame(canvas, bd=0, highlightthickness=0, bg="#0d0d0d")
canvas.create_window(ancho//2, alto-170, anchor="center", window=main_frame, width=ancho-40, height=0)

keyboardEnableEntry = True

def entryClicked(event):
    global keyboardEnableEntry
    keyboardEnableEntry = True
    entrada_jugador.focus_set()

def windowClicked(event):
    global keyboardEnableEntry
    if event.widget != entrada_jugador:
        keyboardEnableEntry = False
        window.focus_set()


canvas.bind("<Button-1>", windowClicked)

window.bind_all("<KeyPress>", onKeyPress)
window.bind_all("<KeyRelease>", onKeyRelease)

# Botones de modo
btn_modo_simple = tk.Button(canvas, text="Modo Transmisión Simple",
                            command=configurar_modo_simple,
                            bg="#ff0000", fg="#FFFFFF", font=("Arial", 12, "bold"),
                            relief="flat", cursor="hand2")
canvas.create_window(250, 380, anchor="center", window=btn_modo_simple)

btn_modo_doble = tk.Button(canvas, text="Modo Escucha y Transmisión",
                           command=configurar_modo_doble,
                           bg="#ff0000", fg="#FFFFFF", font=("Arial", 12, "bold"),
                           relief="flat", cursor="hand2")
canvas.create_window(500, 380, anchor="center", window=btn_modo_doble)

label_modo = tk.Label(canvas, text="MODO: No seleccionado",
                      font=("Arial", 12, "bold"), bg="#0d0d0d", fg="#FFFFFF")
canvas.create_window(780, 380, anchor="center", window=label_modo)

# información del juego
frame_info = tk.Frame(main_frame, bg="#0d0d0d", highlightbackground="#ff0000", highlightthickness=1)
tk.Label(frame_info, text=" Información del Juego", bg="#0d0d0d", fg="#ff0000", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W)
frame_info.grid(row=2, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

label_frase = ttk.Label(frame_info, text="Frase secreta: ---", 
                       font=("Arial", 14, "bold"))
label_frase.grid(row=1, column=0, sticky=tk.W, padx=5)

label_morse = ttk.Label(frame_info, text="Morse: ---", 
                       font=("Arial", 12))
label_morse.grid(row=2, column=0, sticky=tk.W, padx=5)

label_turno = ttk.Label(frame_info, text="Turno: Jugador A", 
                       font=("Arial", 12, "bold"))
label_turno.grid(row=3, column=0, sticky=tk.W, padx=5)

# asignación de puntajes
frame_puntajes = tk.Frame(main_frame, bg="#0d0d0d", highlightbackground="#ff0000", highlightthickness=1)
tk.Label(frame_puntajes, text=" PUNTAJES", bg="#0d0d0d", fg="#ff0000", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W)
frame_puntajes.grid(row=3, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

label_puntaje_a = ttk.Label(frame_puntajes, text="Jugador A: 0", 
                           font=("Arial", 14, "bold"))
label_puntaje_a.grid(row=1, column=0, padx=20, pady=5)

label_puntaje_b = ttk.Label(frame_puntajes, text="Jugador B: 0", 
                           font=("Arial", 14, "bold"))
label_puntaje_b.grid(row=1, column=1, padx=20)


# entrada y botones asignados
frame_entrada = tk.Frame(main_frame, bg="#0d0d0d", highlightbackground="#ff0000", highlightthickness=1)
tk.Label(frame_entrada, text=" Ingresa tu respuesta en Morse", bg="#0d0d0d", fg="#ff0000", font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=3, sticky=tk.W)
frame_entrada.grid(row=4, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

entrada_jugador = ttk.Entry(frame_entrada, font=("Arial", 14), width=40)
entrada_jugador.grid(row=1, column=0, padx=5, pady=5)
entrada_jugador.focus()  # Foco automático

# Botones de acción
btn_enviar = tk.Button(frame_entrada, text="Enviar Respuesta",
                      command=evaluar_respuesta,
                      bg="#ff0000", fg="#FFFFFF", font=("Arial", 12, "bold"),
                      relief="flat", cursor="hand2")
btn_enviar.grid(row=1, column=1, padx=5)

btn_nueva_ronda = tk.Button(frame_entrada, text="Nueva Ronda",
                           command=iniciar_ronda,
                           bg="#ff0000", fg="#FFFFFF", font=("Arial", 12, "bold"),
                           relief="flat", cursor="hand2")
btn_nueva_ronda.grid(row=1, column=2, padx=5)

# ------------- Configuración de la ventana--------------
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1)
main_frame.rowconfigure(0, weight=1)

# Bind Enter para enviar respuesta
def on_enter(event):
    evaluar_respuesta()
window.bind('<Return>', lambda e: on_enter(e))

print("Juego Morse iniciado!")
print("Cambia la IP en enviar_a_raspberry() por la de tu Raspberry Pi Pico W")

# entrada y botones asignados
frame_entrada = tk.Frame(main_frame, bg="#0d0d0d", highlightbackground="#ff0000", highlightthickness=1)
tk.Label(frame_entrada, text=" Ingresa tu respuesta en Morse", bg="#0d0d0d", fg="#ff0000", font=("Arial", 9, "bold")).grid(row=0, column=0, columnspan=3, sticky=tk.W)
frame_entrada.grid(row=4, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))

entrada_jugador = ttk.Entry(frame_entrada, font=("Arial", 14), width=40)
entrada_jugador.grid(row=1, column=0, padx=5, pady=5)
#entrada_jugador.focus()  # Foco automático
entrada_jugador.bind("<Button-1>", entryClicked)
# Botones de acción
btn_enviar = ttk.Button(frame_entrada, text="Enviar Respuesta", 
                       command=evaluar_respuesta)
btn_enviar.grid(row=1, column=1, padx=5)

btn_nueva_ronda = ttk.Button(frame_entrada, text="Nueva Ronda", 
                            command=iniciar_ronda)
btn_nueva_ronda.grid(row=1, column=2, padx=5)

abrirSocket()
window.after(100, checkIdleTime)
window.mainloop()
sock.close()

