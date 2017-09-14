#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
User input:
5
kare 10
kanojo 10
karetachi 1
korosu 7
sakura 3
3
k
ka
kar
"""

import os
import sys
import fileinput

#дескриптор-генератор для получения пользовательских данных
fi = None 
#массив словарей для хранения данных о словах и их частоте встречаемости
words_data = [] 
#массив для хранения частей слов (для обработки и вывода данных на их основе)
word_parts = [] 

#функция очищает строку от ненужных символов (пока это только символы 
#переноса строки, но в будущем ее можно будет расширить по мере 
#необходимости)
def clear_line(line):
    #убрать все символы переноса строки
    if os.linesep in line:
        line = line.replace(os.linesep, "") 

    return line

#функция позвращает введенное число пользователем
def get_number_input():
    global fi

    if fi == None:
        fi = fileinput.input()

    number = None
    #получаем число (делается в цикле, чтобы попытки были до тех пор, 
    #пока не введется корректное значение - число)
    for line in fi:
        line = clear_line(line)
        try:
            number = int(line)
        except ValueError as e:
            #обработка ошибки - некорректное число строк
            pass
        return number

def handle_line(line):
    word, frequency = line.split(" ")

    try:
        frequency = int(frequency)
    except ValueError as e:
            #обработка ошибки - некорректное число частоты встречаемости
            return
    
    #занимает больше памяти, легче сортировать по ключу
    words_data.append({"wrd" : word, "freq" : frequency}) 

def print_buf(buf):
    buf.sort(key=lambda p: p['wrd'])
    for r in buf:
        print(r['wrd'])

def print_top(part):
    #максимальное количество результатов для каждой части слова
    max_num = 10 
    
    #массив для временного хранения результатов с одинаковой частотой 
    #встречаемости
    buf = [] 

    last_freq = words_data[0]['freq']

    print(words_data)

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
                print_buf(buf)
                buf = [item]
                last_freq = item['freq']
            else:
                buf.append(item)
    
    if len(buf):
        print_buf(buf)

    #вывод пустой строки с переносом, если было найдено хотя бы 1 совпадение
    if max_num != 10:
        print() 

def main():
    num_of_words = 0
    num_of_parts = 0
    
    fi = fileinput.input()
    
    num_of_words = get_number_input()

    if num_of_words <= 0:
        sys.exit()
    
    #цикл ввода num_of_words строк
    for i in range(num_of_words):
        line = clear_line(next(fi))
        handle_line(line)

    #сортируем массив
    words_data.sort(key=lambda p: p['freq'], reverse=True)

    num_of_parts = get_number_input()

    if num_of_parts <= 0:
        sys.exit()

    #цикл ввода num_of_parts строк
    for i in range(num_of_parts):
        line = clear_line(next(fi))
        word_parts.append(line)

    #вывод пустой строки с переносом, чтобы отделить вывод от
    #ввода (убрать при ненадобности)
    print() 

    #обрабтка и вывод результатов
    for part in word_parts:
        print_top(part)

if __name__ == "__main__":
    main()
