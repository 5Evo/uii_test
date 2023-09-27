# директория с файлами транскрибации
BASE_DIR = '/home/alex/AI_home/uii_test'

# директория с промтами
SETTINGS_PATH = './promts/'

# SYSTEM_PROMT_FILE = 'promt3.txt'
SYSTEM_PROMT_FILE = 'promt_pronoun_act.txt'
# SYSTEM_PROMT_FILE = 'promt_pronoun_def.txt'


SYSTEM_СLIENT_ERR = 'promt_err_client.txt'
SYSTEM_MANGER_ERR = 'promt_err_manager.txt'

CHEAP_MODEL = 'gpt-3.5-turbo'
EXPENSIVE_MODEL = 'gpt-3.5-turbo-16k'
TEMPERATURE = 0.1

#имя файла отчета в директории BASE_DIR
CSV_NAME = 'monologs.csv'

# произволный секретный ключ для Сессии Flask
FLASK_SECRET_KEY = 'il.,sdfpi187'

# Список колонок для датафрейма
COLUMNS = ['File_path', 'Text', 'Label']