import network
import time
import utime
import socket
import urequests
import json
from machine import Pin

SSID = "RojasLaiMesh"
PASSWORD = "Jostoc12*"
BUZZER = Pin(15,Pin.OUT)
BUTTON = Pin(18,  Pin.IN, Pin.PULL_UP)
BUZZER.low()
UNIDAD_A = 0.2
UNIDAD_B = 0.3
SDI = Pin(14, Pin.OUT)
RCLK = Pin(13,Pin.OUT)
SDI2 = Pin(16, Pin.OUT)
RCLK2 = Pin(17,Pin.OUT)
#SRCLK = Pin(6, Pin.OUT)
SDI2.value(0)
RCLK2.low()
client = None
client_addr = None
gameStep = 0 # 0 es recibiendo 1 es jugador replica.

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

class LEDVocab:
    def __init__(self,letra,bit1,bit2):
        self.letra = letra
        self.bit1 = bit1
        self.bit2 = bit2
    
alfaLED = {"A": LEDVocab("A",0b00000000, 0b00110000),
           "B": LEDVocab("B",0b00000000, 0b01010000),
           "C": LEDVocab("C",0b00000000, 0b00101000),
           "D": LEDVocab("D",0b00000000, 0b01001000),
           "E": LEDVocab("E",0b00000000, 0b00100100),
           "F": LEDVocab("F",0b00000000, 0b01000100),
           "G": LEDVocab("G",0b00000000, 0b00100010),
           "H": LEDVocab("H",0b00000000, 0b01000010),
           "I": LEDVocab("I",0b00000000, 0b00100001),
           "J": LEDVocab("J",0b00000000, 0b01000001),
           "K": LEDVocab("K",0b10000000, 0b00100000),
           "L": LEDVocab("L",0b10000000, 0b01000000),
           "M": LEDVocab("M",0b01000000, 0b00100000),
           "N": LEDVocab("N",0b01000000, 0b01000000),
           "O": LEDVocab("O",0b00100000, 0b00100000),
           "P": LEDVocab("P",0b00100000, 0b01000000),
           "Q": LEDVocab("Q",0b00010000, 0b00100000),
           "R": LEDVocab("R",0b00010000, 0b01000000),
           "S": LEDVocab("S",0b00001000, 0b00100000),
           "T": LEDVocab("T",0b00001000, 0b01000000),
           "U": LEDVocab("U",0b00000100, 0b00100000),
           "V": LEDVocab("V",0b00000100, 0b01000000),
           "W": LEDVocab("W",0b00000010, 0b00100000),
           "X": LEDVocab("X",0b00000010, 0b01000000),
           "Y": LEDVocab("Y",0b00000001, 0b00100000),
           "Z": LEDVocab("Z",0b00000001, 0b01000000),
           "0": LEDVocab("0",0b00000000, 0b10010000),
           "1": LEDVocab("1",0b00000000, 0b10001000),
           "2": LEDVocab("2",0b00000000, 0b10000100),
           "3": LEDVocab("3",0b00000000, 0b10000010),
           "4": LEDVocab("4",0b00000000, 0b10000001),
           "5": LEDVocab("5",0b10000000, 0b10000000),
           "6": LEDVocab("6",0b01000000, 0b10000000),
           "7": LEDVocab("7",0b00100000, 0b10000000),
           "8": LEDVocab("8",0b00010000, 0b10000000),
           "9": LEDVocab("9",0b00001000, 0b10000000),
           "-": LEDVocab("+",0b00000100, 0b10000000),
           "+": LEDVocab("-",0b00000010, 0b10000000),
           "*": LEDVocab("*",0b00000001, 0b10000000)}

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

def shift_out(data):
    RCLK.value(0)
    SDI.value(0)
    for bit in range(8):
        bitValue=(data&0x80)>>7
        SDI.value(bitValue)
        RCLK.high()
        utime.sleep_us(1)
        #time.sleep(1)
        RCLK.low()
        utime.sleep_us(1)
        data = data<<1
    #RCLK.high()
    #utime.sleep_us(1)
    #RCLK.low()
    #utime.sleep_us(1)
        
def shift_out2(data):
    RCLK2.value(0)
    SDI2.value(0)
    for bit in range(8):
        bitValue=(data&0x80)>>7
        SDI2.value(bitValue)
        RCLK2.high()
        utime.sleep_us(1)
        #time.sleep(1)
        RCLK2.low()
        utime.sleep_us(1)
        data = data<<1

def connectToWifi(ssid,password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print ("Conectando...")
        wlan.connect(ssid,password)
        
        while not wlan.isconnected():
            print ("Esperando ¯\_(ツ)_/¯")
            time.sleep(1)
            
    print("Conectado a", ssid)
    print("Network configuration:", wlan.ifconfig())
    
def parse_message(message):
    parts = message.strip().split("|")
    
    result = {}
    
    for part in parts:
        if ":" in part:
            key, value = part.split(":", 1)
            result[key.strip()] = value.strip()
            
    frase = result.get("FRASA", "")
    morse = result.get("MORSE", "")
    
    return frase, morse


def startServer():
    addr = socket.getaddrinfo("0.0.0.0", 8080)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(1)
    print("Escuchando en",addr)
    return server

def esperarMensaje():
    global gameStep, server, client,client_addr
    
    while gameStep == 0:
        data = client.recv(1024)
        
        if data:
            message = data.decode("utf-8")
            print("Recibido:",message)
            
            frase, morse = parse_message(message)
            print("Frase:", frase)
            print("Morse:", morse)
            letra = ""
            
            
            for i in range(0, len(morse)):
                if morse[i] == "·":
                    bip(UNIDAD_A)
                    time.sleep(UNIDAD_A)
                    letra = letra+"·"
                elif morse[i] == "—":
                    bip(UNIDAD_A * 3.0)
                    time.sleep(UNIDAD_A)
                    letra = letra+"—"
                elif morse[i] == " ":
                    time.sleep(UNIDAD_A * 2.0) # por que 1 unidad esta en el · o —
                    if letra in morse_letras:
                        LEDPath=alfaLED[morse_letras[letra]]
                        shift_out (LEDPath.bit1)
                        shift_out2(LEDPath.bit2)
                        print(LEDPath.letra)
                        letra = ""
                elif morse[i] == "/":
                    time.sleep(UNIDAD_A * 6.0) # por que 1 unidad esta en el · o —
                    if letra in morse_letras:
                        LEDPath=alfaLED[morse_letras[letra]]
                        shift_out (LEDPath.bit1)
                        shift_out2(LEDPath.bit2)
                        print(LEDPath.letra)
                        letra = ""
                        
            if letra in morse_letras:
                LEDPath=alfaLED[morse_letras[letra]]
                shift_out (LEDPath.bit1)
                shift_out2(LEDPath.bit2)
                print(LEDPath.letra)
                letra = ""
          
            gameStep = 1
            time.sleep(UNIDAD_A*7)
            shift_out (0b00000000) #apaga los 8 leds del primer chip
            shift_out2(0b00000000)

    
def startConnection():
    global client,client_addr
    client,client_addr = server.accept()
    print("Cliente conectando:",client_addr)
    
def esperarMensajeKeyboard():
    global gameStep
    global server
    global client
    morse = ""
    lastState = 1
    pressStart = 0
    releaseStart = time.ticks_ms()
    playerHasStartedToPlay = False
    print("Esperando PC")
    while gameStep == 2:
        data = client.recv(1024)
        
        if data:
            message = data.decode("utf-8")
            print("Recibido:",message)
            
            letra = ""
            
            now = time.ticks_ms()
            currentState = not message == "p"
            if lastState == 1 and currentState == 0:
                pressStart = now
                BUZZER.value(1)#suena
                playerHasStartedToPlay = True
            elif lastState == 0 and currentState == 1:
                duracion = time.ticks_diff(now,pressStart)
                if duracion <= UNIDAD_B*1000:
                    letra = letra+"·"
                    morse = morse+"·"
                else:
                    letra = letra+"—"
                    morse = morse+"—"
                BUZZER.value(0)#silencio
                releaseStart = now
            if currentState == 1:
                idleTime = time.ticks_diff(now, releaseStart)
                if idleTime > UNIDAD_B*28*1000 and playerHasStartedToPlay:
                    # transmite frase
                    # se calcula la puntacion
                    # se cambia de jugador
                    if not morse == "":
                        frase = morse_a_texto(morse)
                        print (frase)
                        mensaje = f"FRASE:{frase}|MORSE:{morse}"
                        client.send(mensaje.encode("utf-8"))
                        morse = ""
                        gameStep = 1
                        shift_out (0b00000000) #apaga los 8 leds del primer chip
                        shift_out2(0b00000000)

                elif idleTime > UNIDAD_B*7*1000:
                    if not morse.endswith("/"):
                        morse=morse+"/"
                        #reconocer letra PLISSSSSSSSSSSS
                        if not letra == "" and letra in morse_letras:
                            print(morse_letras[letra])
                            LEDPath=alfaLED[morse_letras[letra]]
                            shift_out (LEDPath.bit1)
                            shift_out2(LEDPath.bit2)
                        letra = ""
                        print(morse)
                elif idleTime > UNIDAD_B*3*1000:
                    if not morse.endswith(" "):
                        morse=morse+" "
                        #reconocer letra PLISSSSSSSSSSSS
                        if not letra == "" and letra in morse_letras:
                            print(morse_letras[letra])
                            LEDPath=alfaLED[morse_letras[letra]]
                            shift_out (LEDPath.bit1)
                            shift_out2(LEDPath.bit2)
                        letra = ""
            lastState = currentState

def checkButton():
    global gameStep
    global server
    
    letra = ""
    morse = ""
    lastState = 1
    pressStart = 0
    releaseStart = time.ticks_ms()
    print("Le toca al jugador");
    playerHasStartedToPlay = False
    while gameStep == 1:
        now = time.ticks_ms()
        currentState = BUTTON.value()
        if lastState == 1 and currentState == 0:
            pressStart = now
            BUZZER.value(1)#suena
            playerHasStartedToPlay = True
        elif lastState == 0 and currentState == 1:
            duracion = time.ticks_diff(now,pressStart)
            if duracion <= UNIDAD_B*1000:
                letra = letra+"·"
                morse = morse+"·"
            else:
                letra = letra+"—"
                morse = morse+"—"
            BUZZER.value(0)#silencio
            releaseStart = now
        if currentState == 1:
            idleTime = time.ticks_diff(now, releaseStart)
            if idleTime > UNIDAD_B*28*1000 and playerHasStartedToPlay:
                # transmite frase
                # se calcula la puntacion
                # se cambia de jugador
                if not morse == "":
                    frase = morse_a_texto(morse)
                    print (frase)
                    mensaje = f"FRASE:{frase}|MORSE:{morse}"
                    client.send(mensaje.encode("utf-8"))
                    morse = ""
                    gameStep = 0
                    shift_out (0b00000000) #apaga los 8 leds del primer chip
                    shift_out2(0b00000000)

            elif idleTime > UNIDAD_A*7*1000:
                if not morse.endswith("/"):
                    morse=morse+"/"
                    #reconocer letra PLISSSSSSSSSSSS
                    if not letra == "" and letra in morse_letras:
                        print(morse_letras[letra])
                        LEDPath=alfaLED[morse_letras[letra]]
                        shift_out (LEDPath.bit1)
                        shift_out2(LEDPath.bit2)
                    letra = ""
                    print(morse)
            elif idleTime > UNIDAD_A*3*1000:
                if not morse.endswith(" "):
                    morse=morse+" "
                    #reconocer letra PLISSSSSSSSSSSS
                    if not letra == "" and letra in morse_letras:
                        print(morse_letras[letra])
                        LEDPath=alfaLED[morse_letras[letra]]
                        shift_out (LEDPath.bit1)
                        shift_out2(LEDPath.bit2)
                    letra = ""
        lastState = currentState
        time.sleep(0.01)

def bip(step):
    BUZZER.value(1)#suena
    time.sleep(step)#espera
    BUZZER.value(0)#apaga

shift_out (0b00000000) #apaga los 8 leds del primer chip
shift_out2(0b00000000)
connectToWifi(SSID,PASSWORD)
server = startServer()
startConnection()
while True:
    if gameStep == 0:
        esperarMensaje()
    elif gameStep==2:
        esperarMensajeKeyboard()
    else:
        checkButton()

client.close()
#res = urequests.get("https://httpbin.org/get")
#print("get:",res.status_code)
#print(res.text)
#res.close()