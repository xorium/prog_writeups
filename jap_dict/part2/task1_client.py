#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import fileinput
import socket

#дескриптор-генератор для получения пользовательских данных
fi = None 

def send_data(sock, data):
    data = str.encode(data)

    sock.sendall(data)
    
    amount_received = 0
    #первые 5 байт - длина ответа
    expected = sock.recv(5).strip().decode('utf-8')

    #print("NUM: " + str(expected))
    if expected:
        expected = int(expected)
    else:
        return
    
    result = ""
    while amount_received < expected:
        tmp = sock.recv(16)
        amount_received += len(tmp)
        result += tmp.strip().decode('utf-8')
    
    #print("RESULT: " + result)
    return result

def main(path, port):
    try:
        port = int(port)
    except ValueError as e:
        #обработка ошибки - некорректное число для порта
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)
    sock.connect(server_address)
    try:
        for req in fileinput.input():
            req = req.split(" ")
            command = req[0]
            data = req[1]

            #в будущем можно будет добавлять различные другие команды
            if command == "get":
                res = send_data(sock, data)
                print(res)
            else:
                #обработка ошибки - неизвестная команда
                pass
    finally:
        sock.close()

if __name__ == "__main__":
    host, port = sys.argv[1:]

    #для корректного принятия входных данных через fileinput
    sys.argv = sys.argv[:1]

    main(host, port)
