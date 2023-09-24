"""
Сервисные функции
"""
from settings import BASE_DIR, COLUMNS, CSV_NAME
import os
import html
import re
import pandas as pd


def read_dirs():
    folders = []
    file_list = []
    for root, dirs, files in os.walk(BASE_DIR):

        # соберем все папки в folders
        for dir in dirs:
            folder_path = os.path.join(root, dir)
            # Сосчитаем количество файлов в папке:
            num_files = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
            # соберем только те папки, в которых хранится больше 1 файла (4 файла с транскрибацией)
            if num_files>1:
                folders.append([folder_path, num_files])

                # Соберем все группы файлов в file_list, упорядочим их по названию. Файл с диалогом будет с индексом 1
                folder_contents = os.listdir(folder_path)  # получим список файлов в директории
                folder_contents_sorted = sorted(folder_contents)
                file_list.append((folder_path, folder_contents_sorted))

        # for file in files:
        #     file_list.append(os.path.join(root, file))
    #print(f'__read_dirs__: Нашли {len(folders)} вложенных папок')
    return folders, file_list


def read_file_context(filename):
    """
    Безопасное чтение текстового файла с проверкой через модуль HTML
    :param filename:
    :return:
    """
    try:
        with open(filename, 'r', encoding='Windows-1251') as file:
            content = file.read()

            # с помощью модуля html проверяем на безопасность содержимое файла
            # и заменяем специальные символы на их ASCII-эквиваленты:
            safe_content = html.escape(content)
            return safe_content
    except FileNotFoundError:
        return "Файл не найден"
    except OSError as exc:
        if exc.errno == 36:
            print(f'вот тут и есть ошибка 36 {exc=}')
    except Exception as e:
        return str(e)


def process_text_file(filename):
    """
    Процессор обработки файла транскрибации:
    Удаляем временные метки, удаляем роли 'Менеджер:' и 'Клиент:'
    Заменяем перенос строки на пробел.
    Удаляем несколько подрядидущих пробелов.
    :param filename:
    :return:
    """
    #text = read_file_context(filename)  # Безопасно прочитали файл

    with open(filename, 'r', encoding='Windows-1251') as file:
        text = file.read()
    # Удаление подстрок
    text = re.sub(r'\d{2}:\d{2} ', '', text)  # Удаление временной метки в формате "00:18"
    text = text.replace('Менеджер: ', '')  # Удаление "Роли:"
    text = text.replace('Клиент:' , '')  # Удаление "Клиент:"

    # Замена переносов строк на пробелы
    text = text.replace('\n', ' ')

    # Замена нескольких подряд идущих пробелов на один пробел
    text = re.sub(r' +', ' ', text)

    # Удаление первого пробела, если он есть
    if text.startswith(' '):
        text = text[1:]

    return text



def create_new_df():
    """
    Создание пустого DataFrame с заданными колонками из Settings.py
    :return:
    """
    df = pd.DataFrame(columns=COLUMNS)
    # Сохранение DataFrame в файл
    df.to_csv(os.path.join(BASE_DIR, CSV_NAME), index=False)
    return df


def add_row_to_DF(data):
    """
    Добавление новой строки в DataFrame. Все операции идут через файл, тк df слишком большой для передачи через сессию
    """
    # Чтение DataFrame из файла
    df = pd.read_csv(os.path.join(BASE_DIR, CSV_NAME))

    df.loc[len(df)] = data

    # Сохранение DataFrame обратно в файл
    df.to_csv(os.path.join(BASE_DIR, CSV_NAME), index=False)

    #return df

if __name__ == '__main__':

    folders, file_list = read_dirs()

    # for folder in folders:
    #     print(f'{folder =}')
    print(f'__read_dirs__: Нашли {len(folders)} вложенных папок')

    for files in file_list:
        print(f'{files =}')

    file_number = 4
    file_path = os.path.join(file_list[file_number][0], file_list[file_number][1][0])
    print(f'Обработаем файл "{file_path}":')
    new_text = process_text_file_old(file_path)
    print(new_text)