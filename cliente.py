import socket
import struct
import numpy as np
import cv2
from PIL import Image
from sys import getsizeof

#MULTICAST-----------------------------------------------
"""#Configuración inicial del socket.
grupo_multicast = '224.1.1.1'
info_servidor = ('', 10000)

#Se crea el socket UDP (Recordemos que el multicast es implementado con socket UDP)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(info_servidor)

group = socket.inet_aton(grupo_multicast)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
"""

#BROADCAST-----------------------------------
#Se crea el socket UDP.
cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
cliente.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
#Se permite conexiones broadcast.
cliente.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

cliente.bind(("", 10000))

for i in range(1, 7):
    num_img = i
    info_imagen_recibida = False

    while(not info_imagen_recibida):
        print("Esperando mensaje... ")
        try:
            mensaje_recibido, direccion_envio = cliente.recvfrom(128)
            print("Tamanio cabecera: ", getsizeof(mensaje_recibido), " bytes.")
        except:
            print("El servidor está a la mitad del envío de otra imagen, esperando a que termine...")
        else:
            info_imagen_recibida = True

    """print("Esperando mensaje... ")
    mensaje_recibido, direccion_envio = sock.recvfrom(1024)
    print("Tamanio cabecera: ", getsizeof(mensaje_recibido), " bytes.")"""

    print("Enviando ACK a ", direccion_envio)
    cliente.sendto(bytes('ACK', 'utf8'), direccion_envio)

    informacion_imagen = mensaje_recibido.decode().split('_')
    num_partes = informacion_imagen[0]
    tamanio_buffer = informacion_imagen[1]
    extension_img = informacion_imagen[2]

    print("Num partes:", num_partes)
    print("Tamanio buffer: ", tamanio_buffer)

    lista_segmentos = []

    for i in range(int(num_partes)):
        mensaje_recibido, direccion_envio = cliente.recvfrom(int(tamanio_buffer))
        lista_segmentos.append(mensaje_recibido)

        print("Enviando ACK a ", direccion_envio)
        cliente.sendto(bytes('ACK', 'utf8'), direccion_envio)

    #info_bytes_img = ''.split(lista_segmentos)

    print("Informacion: ", lista_segmentos[0])
    print("--------------------")
    print("Informacion: ", lista_segmentos[1])

    info_bytes_completa = b''
    for segmento in lista_segmentos:
        info_bytes_completa += segmento

    arreglo_img = np.frombuffer(info_bytes_completa, np.uint8)
    nueva_img = cv2.imdecode(arreglo_img, cv2.IMREAD_COLOR)

    print("Guardando imagen...")
    nueva_img_formateada = Image.fromarray(nueva_img)
    nueva_img_formateada = nueva_img_formateada.save("imgDescargada/clienteImg"+str(num_img)+"."+extension_img)
