#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import socket

#массив словарей для хранения данных о словах и их частоте встречаемости
words_data = []

#функция очищает строку от ненужных символов (пока это только символы 
#переноса строки, но в будущем ее можно будет расширить по мере 
#необходимости)
def clear_line(line):
    #убрать все символы переноса строки
    if os.linesep in line:
        line = line.replace(os.linesep, "") 
    return line

def print_buf(buf):
    res = ""

    buf.sort(key=lambda p: p['wrd'])
    for r in buf:
        res += r['wrd'] + os.linesep

    return res

def get_top(part):
    #результат, куда будет записан "вывод"
    res = ""

    #максимальное количество результатов для каждой части слова
    max_num = 10 
    
    #массив для временного хранения результатов с одинаковой частотой 
    #встречаемости
    buf = [] 

    last_freq = words_data[0]['freq']

    for item in words_data:
        #выход из цикла после достижания вывода max_num результатов
        if max_num <= 0:
            break

        word = item['wrd']
        #можно исопльзовать `word.find(part) == 0`, но это может занимать 
        #больше времени в некоторых случаях
        if word[:len(part)] == part:
            max_num -= 1
            if last_freq != item['freq']:
                res += print_buf(buf)
                buf = [item]
                last_freq = item['freq']
            else:
                buf.append(item)
    
    if len(buf):
        res += print_buf(buf)

    #вывод пустой строки с переносом, если было найдено хотя бы 1 совпадение
    if max_num != 10:
        res += os.linesep

    return res

def handle_line(line):
    word, frequency = line.split(" ")

    try:
        frequency = int(frequency)
    except ValueError as e:
            #обработка ошибки - некорректное число частоты встречаемости
            return
    
    #занимает больше памяти, легче сортировать по ключу
    words_data.append({"wrd" : word, "freq" : frequency})

def main(path, port):
    try:
        port = int(port)
    except ValueError as e:
        #обработка ошибки - некорректное число для порта
        return

    #максимальная длина части слова
    max_len = 15
    
    with open(path, 'r') as f:
        data = f.readlines()
    
    try:
        num_of_words = int(data[0])
    except ValueError as e:
        #обработка ошибки - некорректное число частоты встречаемости
        return

    if num_of_words <= 0:
        return
    
    #цикл обработки num_of_words строк
    for line in data[1:]:
        line = clear_line(line)
        handle_line(line)

    #сортируем массив
    words_data.sort(key=lambda p: p['freq'], reverse=True)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('', port)
    sock.bind(server_address)
    sock.listen(1)
    
    while True:
        connection, _ = sock.accept()
        try:
            data = ""
            resp = ""
            while True:
                data = connection.recv(max_len + 1).strip().decode('utf-8')
                #print(":".join("{:02x}".format(ord(c)) for c in str(data)))

                if data:
                    resp = get_top(data)
                    #первые 5 байт - длина ответа
                    resp_len = "{:05d}".format(len(resp))
                    resp_len = str.encode(resp_len)
                    resp = str.encode(resp)

                    connection.sendall(resp_len + resp)
        except TypeError as e:
            pass    
        finally:
            connection.close()

if __name__ == "__main__":
    dict_path, port = sys.argv[1:]
    main(dict_path, port)
