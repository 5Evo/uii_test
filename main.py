"""
Тестовове задание для вакансии в УИИ
https://docs.google.com/document/d/1_-bRJNxtzCal6OJvcgdSW2DjrKYtdY_-n9DeAcSJZwU/edit

"""
import os

import pandas as pd
from flask import Flask, request, render_template, session
from service import read_dirs, read_file_context, create_new_df, process_text_file, add_row_to_DF
from settings import FLASK_SECRET_KEY

# Создаем приложение Flask, инициируем его с помощью секретного ключа сессии
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
folders, file_list = read_dirs()    # прочитаем и сохраним все файли и папки

@app.route('/')
def index():
    return render_template('index.html', num_folders=len(folders))


@app.route('/folders/', methods=['GET', 'POST'])
def show_folders():
    """
    Метод POST используется в шаболне "folder.html" в кнопке для переходна к следующему содержимому
    """
    if request.method == 'POST':    # Если нажали кнопку NEXT (или при выборе правильной роли)
        if 'folder' in session:
            session['folder'] += 1
        else:
            session['folder'] = 0
    else:
        session['folder'] = 0

    if session['folder'] >= len(folders):
        return "Вы просмотрели все папки!"

    folder_contents = os.listdir(folders[session['folder']][0]) # получим список файлов в директории
    folder_contents_sorted = sorted(folder_contents)
    progress_bar = [session['folder'], len(folders)]
    return render_template('folder.html', folder_contents=folder_contents_sorted, folder_path=folders[session['folder']], progress_bar=progress_bar)


@app.route('/files/', methods=['GET', 'POST'])
def show_files():
    """
    Метод POST используется в шаболне "folder.html" в кнопке для переходна к следующему содержимому
    """
    print('************************************************')

    # Если нажали кнопку NEXT (или при выборе правильной роли)
    if request.method == 'POST':    # Если нажали кнопку NEXT (или при выборе правильной роли)
        if 'transkrib_file' in session:

            # df_monologs = pd.read_json(session['df_monologs'])  # прочитали df из сессии

            # формат каждого элемента file_list: [путь_до_файла, [файл_клиента, файл_диалога, файл_менеджера, файл_json] ]:
            file_path = file_list[session['transkrib_file']][0]
            print(f'1.  {file_path = }')

            client_file = file_list[session['transkrib_file']][1][0]
            manager_file = file_list[session['transkrib_file']][1][2]
            print(f'2.  {client_file = }')
            print(f'3.  {manager_file = }')

            client_full_file = os.path.join(file_path, client_file)
            manager_full_file = os.path.join(file_path, manager_file)
            print(f'4.  {client_full_file = }')
            print(f'5.  {manager_full_file = }')

            client_file_context = read_file_context(client_full_file)
            manager_file_context = read_file_context(manager_full_file)
            print(f'6.  {client_file_context = }')
            print(f'7.  {manager_file_context = }')

            client_processed_file = process_text_file(client_full_file)
            manager_processed_file = process_text_file(manager_full_file)
            print(f'8.  {client_processed_file = }')
            print(f'9.  {manager_processed_file = }')

            client_record = [client_full_file, client_processed_file]
            manager_record = [manager_full_file, manager_processed_file]
            print(f'10. {client_record = }')
            print(f'11. {manager_record = }')
            # блок для проверки правильности Ролей и дополнения датафрейма:
            # print(df_monologs)
            if request.form['action'] == 'Правильные Роли ->':
                print('Роли правильные')
                client_record.append('Клиент')
                manager_record.append('Менеджер')

            if request.form['action'] == 'Изменить Роли->':
                print('Роли меняем')
                client_record.append('Менеджер')
                manager_record.append('Клиент')

            add_row_to_DF(client_record)
            add_row_to_DF(manager_record)
            print(f'_POST_method_: добавили данные в датафрейм:')

            #session['df_monologs'] = df_monologs.to_json()  # сохраним обновленный df в сессии
            # конец блока для проверки правильности Ролей и дополнения датафрейма:

            session['transkrib_file'] += 1

        else:
            # Если сессия не была создана ранее: создадим новую переменную сессии, создадим новый датасет
            session['transkrib_file'] = 0
            df_monologs = create_new_df()
            #session['df_monologs'] = df_monologs.to_json()      # сохраним df в сессии
            print(f'_POST_method_: создали датафрейм:')

    # Если первый раз загрузили страницу (GET-запрос)
    else:
        session['transkrib_file'] = 0
        df_monologs = create_new_df()
        #session['df_monologs'] = df_monologs.to_json()  # сохраним df в сессии
        print(f'_GET_method_: создали датафрейм:')


    # Проверка на завершение обработки всех файлов:
    if session['transkrib_file'] >= len(file_list):
        # TODO: сохранить df_monologs в csv после полной проверки файлов
        return "Вы просмотрели все файлы!"

    # формат каждого элемента file_list: [путь_до_файла, [файл_клиента, файл_диалога, файл_менеджера, файл_json] ]:
    file_name = file_list[session['transkrib_file']][1][1]
    file_path = file_list[session['transkrib_file']][0]
    full_file_name = os.path.join(file_path, file_name)
    file_context = read_file_context(full_file_name)
    file_progress_bar = [session['transkrib_file'], len(file_list)]
    #print(f'{full_file_name=}')

    return render_template('file_context.html',
                           file_context=file_context,
                           file_name=file_name,
                           file_progress_bar=file_progress_bar)




if __name__ == '__main__':
    #folders = read_dirs()
    # for folder in folders:
    #     print(folder)
    app.run(debug=True)

