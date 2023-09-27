"""
Модуль работы с OpenAI
"""
import os, time
import openai
import tiktoken
from dotenv import load_dotenv
from settings import BASE_DIR, SETTINGS_PATH, SYSTEM_PROMT_FILE, CHEAP_MODEL, EXPENSIVE_MODEL, TEMPERATURE, CSV_NAME, \
    SYSTEM_СLIENT_ERR, SYSTEM_MANGER_ERR
from service import read_csv_to_df, query_execution_time, current_time

# настраиваем OpenAI
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Готовим датафрейм для работы
read_csv_to_df()


def trim_to_max_tokens(messages, model):
    """
    Обрезаем количество токенов до максимально допустимого
    """
    # Максимальное количество токенов для моделей:
    answer_tokens = 1000
    if model in ['gpt-3.5-turbo-16k', 'gpt-3.5-turbo-16k-0613']:
        max_tokens = 16385-answer_tokens
    else:
        max_tokens = 4097-answer_tokens

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    # Подсчитаем токены в message
    num_tokens = 0
    for message in messages:
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))

    if num_tokens > max_tokens:
        print(f'{trim_to_max_tokens.__name__}: Превышено кол-во токенов в запросе ({num_tokens}). Обрезаем до {max_tokens}')
        extra_tokens = num_tokens - max_tokens
        print(f'Обрезаем {extra_tokens} токенов')

        print(f'{messages =}\n')
        user_promt = messages[-1]['content']
        print(f'{user_promt =}\n')
        tokens_user_promt = list(encoding.encode(user_promt))

        # Обрезаем user_prompt до нужного количества токенов
        if len(tokens_user_promt) > extra_tokens:
            tokens_user_promt = tokens_user_promt[:-extra_tokens]
            user_promt_trimmed = encoding.decode(tokens_user_promt)

            # Формируем новый список messages с обрезанным user_prompt
            messages_trimmed = messages[:-1] + [{'role': 'user', 'content': user_promt_trimmed}]
            # проверим новое количество токенов:
            new_num_tokens = 0
            for message in messages_trimmed:
                for key, value in message.items():
                    new_num_tokens += len(encoding.encode(value))
                print(f'{message =}')
            print(f'После обрезки: {new_num_tokens =}')
        return messages_trimmed

    else:
        return messages


def read_promt(system_promt):
    # Прочитаем промт из файла
    promt_file = os.path.join(SETTINGS_PATH, system_promt)
    try:
        with open(promt_file, 'r') as file:
            promt = file.read()
            #print(f"Прочитали промт {system_promt}:\n{promt}")
            return promt
    except Exception as e:
        print(f'Ошибка чтения ПРОМТА: {e}')
        return str(e)


@query_execution_time
def chat_with_gpt(system_content, user_content, model=EXPENSIVE_MODEL):
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
    #print(f'_chat_with_gpt_before_trim: {messages =}')
    messages = trim_to_max_tokens(messages, model) # Если сообщение слишком большое - обрежем его
    #print(f"_chat_with_gpt_after_trim: {messages =}")
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=TEMPERATURE
    )

    return response['choices'][0]['message']['content']


def analyze_any_role(df, promt_name, row_name):
    """
    проверка всех текстов и определение роли
    :return:
    """
    # прочитаем системный промт
    system_promt = read_promt(promt_name)
    #print(f"_analyze_any_role_: {system_promt}")
    # проверим и при необходимости создадим столбец
    if row_name not in df.columns:
        df[row_name] = None

    try:
        for index, row in df.iterrows():
            now = current_time()
            print(f'--------------------\nstarting {index} at {now}...')
            user_promt = row['Text']
            answer, exec_time = chat_with_gpt(system_promt, user_promt)
            df.at[index, row_name] = answer
            df.at[index, 'time'] = exec_time
            print(f'_analyze_any_role_ {index}: {row["Label"] =} \n{answer}')
            if exec_time < 5:
                time.sleep(5-exec_time)
        return df
    except Exception as e:
        print(f"Ошибка перебора: {e}")

def analyze_features(index, row):
    """
    поиск особенностей в каждой роле
    :return:
    """
    if row['Label'] == 'Клиент':
        system_promt = read_promt('promt_client.txt')
        print(f'Клиент:')
    elif row['Label'] == 'Менеджер':
        system_promt = read_promt('promt_manager.txt')
        print(f'Менеджер:')

    else:
        raise "Ошибка чтения роли"
        sys.exit()

    try:
        user_promt = row['Text']
        #print(f'{user_promt =}')
        answer, exec_time = chat_with_gpt(system_promt, user_promt)
        print(f'analyze_features {index}:\n{answer}')
        return answer, exec_time
    except Exception as e:
        print(f"Ошибка получения ответа ChatGPT: {e}")


def check_df_for_features(df):
    for index, row in df.iterrows():
        print(f'starting {index}...')

        # ______ анализ речи __________
        answer, exec_time = analyze_features(index, row)
        df.at[index, 'features'] = answer
        df.at[index, 'time'] = exec_time
        # ______ конец анализа речи __________
    return df


def check_df_for_role(df):

    for index, row in df.iterrows():
        print(f'starting {index}...')
        #______ анализ ролей __________
        answer, exec_time = analyze_any_role(index, row)
        df.at[index, 'chatGPT'] = answer
        # ______ конец анализа ролей __________
    return df


def summarize(df, role):
    """

    :param df:
    :param role:
    :return:
    """
    # Фильтруем DataFrame, чтобы оставить только строки с Label == 'Клиент'
    #df[role] = df[role].astype(str)
    df_client = df[df['Label'] == role]

    # Получаем список всех текстов в этих строках
    features = df_client['features'].tolist()

    # Объединяем каждые 10 текстов в один и сохраняем в новый список
    features_list = [' '.join(features[i:i + 10]) for i in range(0, len(features), 10)]

    return features_list

def analyze_err_role(df, promt_name):
    """
    проверка всех текстов и определение роли
    :return:
    """
    try:
        for index, row in df.iterrows():
            now = current_time()

            # найдем записи с ошибкой определения
            if row['Label']!=row['chatGPT']:
                print(f'\n\n{now} : Нашли ошибку в строке {index}: {row["Label"]} определился как {row["chatGPT"]} ')
                if row['Label'] == 'Клиент':
                    system_promt = read_promt(SYSTEM_СLIENT_ERR)

                elif row['Label'] == 'Менеджер':
                    system_promt = read_promt(SYSTEM_MANGER_ERR)

                else:
                    raise "Ошибка сравнения Ролей"

                print(f'--------------------\nstarting {index} at {now}...')
                user_promt = 'Промт для анализа:\n' + read_promt(promt_name) + 'Текст для анализа:\n' + row['Text']
                answer, exec_time = chat_with_gpt(system_promt, user_promt)
                df.at[index, 'err'] = answer
                df.at[index, 'time_err'] = exec_time
                print(f'_analyze_any_role_ {index}: {answer}')
                if exec_time<5:
                    time.sleep(5-exec_time)
        return df
    except Exception as e:
        print(f"Ошибка перебора {analyze_err_role.__name__}: {e}")



if __name__ == '__main__':

    df_monologs = read_csv_to_df()
    if 'chatGPT' not in df_monologs.columns:
        df_monologs['chatGPT'] = None
    if 'time' not in df_monologs.columns:
        df_monologs['time'] = None
    if 'features' not in df_monologs.columns:
        df_monologs['features'] = None

    #promt = 'promt_introduce.txt'
    promt = 'promt_introduce3.txt'
    result_row_name = 'Intro2'
    df_monologs = analyze_any_role(df_monologs, promt, result_row_name)


    #df_monologs = check_df_for_features(df_monologs)
    #df_monologs = check_df_for_features(df_monologs)

    # features_list_client = summarize(df_monologs, 'Клиент')
    # features_list_manager = summarize(df_monologs, 'Менеджер')
    # #print(f'{features_list_client[1] = }\n\n')
    # # print(f'{features_list_manager = }')
    #
    # #print(f'{len(features_list_client) =}')
    #
    # system_promt = read_promt('summ_promt.txt')
    # print(f'{system_promt =}')
    # user_promt = features_list_client[2]
    # #user_promt = features_list_manager[1]
    # print(f'{user_promt =}')
    # answer, exec_time = chat_with_gpt(system_promt, user_promt)
    # print(f'_обобщаем отчеты_:\n{answer}')

    # Для сохранения данных в файл должна быть раскоментирование следующая строка
    df_monologs.to_csv(os.path.join(BASE_DIR, CSV_NAME), index=False)


