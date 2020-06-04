import socket
import struct
import os
from PIL import Image
import numpy as np
import cv2
import sys
from time import sleep
from math import ceil


ruta_imagenes = 'img/'

#MULTICAST------------------------------------------------
"""#Configuración inicial del socket para multicast.
grupo_multicast = ('224.1.1.1', 10000)
#Se crea el socket UDP (Recordemos que el multicast se implementa con UDP)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.2)
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)"""

import subprocess
subredes_activas = []


for ping in range(1,5):
    address = "10.10." + str(ping) + ".255"
    res = subprocess.call(['ping', '-c', '3', '-b', address])
    if res == 0:
        print("Ping to", address, "OK")
        subredes_activas.append(ping)
    elif res == 2:
        print("No response from", address)
    else:
        print("ping to", address, "failed!")


#BROADCAST------------------------------------------------
#Se crea el socket UDP.
servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
servidor.bind(('10.10.2.5', 12345))
#Se habilita el puerto para poder ser utilizado múltiples veces.
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
#Se permite realizar broadcast.
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#Se establece un tiempo máximo de respuesta.
servidor.settimeout(0.2)

direccion_broadcast = '10.10.'


lista_imagenes = os.listdir(ruta_imagenes)
lista_imagenes.sort()
print("Lista: ", lista_imagenes)

for num_img, nombre_img in enumerate(lista_imagenes):
    print(nombre_img)
    extension = nombre_img.split('.')[1]
    print("Extension:", extension)

    #Se abre la imagen.
    img = Image.open(ruta_imagenes+'img'+str(num_img+1)+'.'+extension)
    #Se obtiene la matriz de pixeles que representa la imagen.
    matriz_imagen = np.asarray(img)
    #Se convierte la matriz a una representación en bytes. (Serialización)
    img_ser = cv2.imencode('.'+extension, matriz_imagen)[1].tostring()

    tamanio_bytes_img = sys.getsizeof(img_ser) 
    num_caracteres = len(img_ser)
    print("Tamanio: ", tamanio_bytes_img, " bytes.")
    print("Num. caracteres: ", num_caracteres, " caracteres.")

    is_tamanio_valido = False
    while(not is_tamanio_valido):
        num_partes = int(input("Partes en las que se dividirá la imagen: "))
        tamanio_buffer = ceil(tamanio_bytes_img/num_partes)
        #2**16 es el tamaño máximo del buffer. 128 es el tamaño máximo para la cabecera inicial de información.
        if( tamanio_buffer < 17900 and tamanio_buffer > 128): 
            print("Número de partes válido. ")
            is_tamanio_valido = True
        else:
            print("Número de partes inválido. El tamanio resultante de las partes en las que se dividirá es demasiado grande o pequeño.")
    
    informacion_imagen = str(num_partes)+'_'+str(tamanio_buffer)+'_'+extension

    for subred in subredes_activas:

        try:
            #enviado = sock.sendto(informacion_imagen.encode(), grupo_multicast) Se utiliza en multicast.
            enviado = servidor.sendto(informacion_imagen.encode(), (direccion_broadcast+str(subred)+'.255', 12345)) #Se utiliza en broadcast.
            while(True):
                #print(sys.stderr, "Esperando respuestas...")
                try:
                    mensaje_recibido, emisor = servidor.recvfrom(1024)
                except socket.timeout:
                    print(sys.stderr, "Tiempo de recepción de respuestas finalizado.")
                    break
                else:
                    print(sys.stderr, "", mensaje_recibido, " de: ", emisor)
        except ValueError:
            print("Error: ", ValueError)

        sleep(2)

    aux_posicion_buffer_img = 0
    for i in range(num_partes):
        if(aux_posicion_buffer_img+tamanio_buffer > tamanio_bytes_img):
            segmento_a_enviar_img = img_ser[aux_posicion_buffer_img:]
        else:
            segmento_a_enviar_img = img_ser[aux_posicion_buffer_img:aux_posicion_buffer_img+tamanio_buffer]

        for subred in subredes_activas:

            print("Enviando a subred: ",direccion_broadcast+str(subred)+".255")
            try:
                #enviado = sock.sendto(segmento_a_enviar_img, grupo_multicast) Se usa en multicast.
                enviado = servidor.sendto(segmento_a_enviar_img, (direccion_broadcast+str(subred)+'.255', 12345)) #Se utiliza en broadcast.
                while(True):
                    #print(sys.stderr, "Esperando respuestas...")
                    try:
                        mensaje_recibido, emisor = servidor.recvfrom(1024)
                    except socket.timeout:
                        print(sys.stderr, "Tiempo de recepción de respuestas finalizado.")
                        break
                    else:
                        print(sys.stderr, "", mensaje_recibido, " de: ", emisor)
            except ValueError:
                print("Error: ", ValueError)

        aux_posicion_buffer_img += tamanio_buffer

    sleep(5)

print(sys.stderr, "Cerrando socket...")
servidor.close()
