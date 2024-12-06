import os
import re
import sys
from dotenv import load_dotenv
import sqlite3
import pandas as pd
import yaml

sql_keywords = ["from", "select", "where", "join", "group by", "having", "order by", "pragma",
                "drop", "insert", "update", "delete", "create", "alter"]

load_dotenv()

class BC:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def replace_semicolon(text, direction):
    """
    Если direction = 1
        1.  Создать список из всех части текста text, обрамленные " или '
        2.  Проверить, есть ли внутри какого-либо элемента символ ;
        3.  Если есть, то заменить его на %!%
        4.  Меняем это элемент в тексте, проверяем до конца списка
        5.  После всех замен возвращаем текст с заменой ; на %!%
    Если direction = 0
        1.  На вход должен подаваться список, состющих из команд SQL
        2.  В каждом элементе списка ищем %!% и меняем на ;
        3.  Возвращеме востановленный список.
    """
    list_to_replace = []
    if direction:
        matches = re.findall(r"'(.+?)'", text)      # обрамление одинарными кавычками
        matches += re.findall(r'"(.+?)"', text)     # обрамление двойными кавычками
        for match in matches:
            if ';' in match:
                before = match
                after = match.replace(';', '%!%')
                list_to_replace.append([before, after])
        if list_to_replace:
            for block in list_to_replace:
                text = text.replace(block[0], block[1])
        return text
    else:
        for i, block in enumerate(text):
            if '%!%' in block:
                text[i] = text[i].replace('%!%', ';')
        return text


def replace_none(text):
    words = text.split(',')
    for i, word in enumerate(words):
        if word.strip() == 'None':
            words[i] = words[i].replace('None', 'Null')
    text = ','.join(words)
    return text


def get_sql_text(sql_query: str, params=None):
    """
           В качестве входного sql_query могут быть переданы 3 типа параметров:
                a) Метка для файла ../SQL/requests.yml
                b) Путь к текстовому файлу
                c) Непосредственно текст SQL запроса

           1. Проверяем, является ли sql_query путем к файлу. Если да, то открываем и текст сохраняем в переменную sql_query.
           2. Проверяем является ли текст переменной sql_query SQL запросом.
           3. Если с текстом запроса передаются параметры, то проверяем количество параметров = кол-ву переменных
           4. Проверим отсутствие SQL инъекций в тексте параметров
           5. Если п.2 = п.3 = п.4 = True, то ищем в тексте ';', если есть, то разделяем запрос на подзапросы
       """
    yml_path = os.getenv('yml_path')

    with open(yml_path, 'r', encoding='utf-8') as file:
        requests = yaml.safe_load(file)
    #     Проверяем, является ли sql_query ключом Yaml
    try:
        sql_query = requests[sql_query]
    except KeyError:
        #     Проверяем, является ли sql_query файлом sql
        if os.path.isfile(sql_query):
            try:
                with open(sql_query, 'r') as file:
                    sql_query = file.read()
            except (OSError, IOError):
                print(f'{BC.FAIL}Error: не удалось открыть файл {BC.WARNING}{sql_query}.{BC.ENDC}')
                return False

    #   Проверим что полученный текст запроса это SQL запрос
    if not any(keyword in sql_query.lower() for keyword in sql_keywords):
        print(f'{BC.FAIL}Error: текст {BC.WARNING}{sql_query}{BC.FAIL} не является SQL запросом.{BC.ENDC}')
        return False

    #   Проверим наличие SQL инъекций в тексте передаваемых параметров
    if params is None:
        params = []
    else:
        for param in params:
            if any(keyword in str(param).lower() for keyword in sql_keywords):
                print(f'{BC.FAIL}Error: текст переменной  {BC.WARNING}{param}{BC.FAIL} содержит SQL инъекцию!{BC.ENDC}')
                return False

    var_count = sql_query.count('%var%')
    if var_count == len(params) > 0:
        for i, value in enumerate(params):
            sql_query = sql_query.replace(f'%var%', str(value), 1)
    elif var_count > 0:
        print(f'{BC.FAIL}Error: в запрос передается параметров {BC.WARNING}{len(params)}{BC.FAIL}'
              f', ожидается {BC.WARNING}{var_count}{BC.ENDC}: \n{params}\n {sql_query}')
        return False

    # Временно заменяем те ';' которые не являются разделителми блоков SQL
    sql_flat = replace_semicolon(sql_query, 1)
    # Py понимает None, но SQL понимает Null, нужно заменить
    sql_flat = replace_none(sql_flat)
    # Разбиваем SQL на исполняемые блоки
    sql_list = sql_flat.split(';')
    sql_list = sql_list[:-1] if sql_list[-1].strip() == '' else sql_list

    # Возвращаем на место ';' которые заменены для верного разбиения на исполняемые блоки SQL
    sql_list = replace_semicolon(sql_list, 0)
    return sql_list


def mquery(sql_query: str, params=None):
    """
    1. Принимаем параметры и передаем их на обработку - возвращаем список sql команд
    2. Соединяемся с БД
    2. Последовательно выполняем полученные sql команды
    """

    db_path = os.getenv('db_path')

    sql_list = get_sql_text(sql_query, params)
    if not sql_list:
        return False

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    out = False
    # print(BC.WARNING, sql_query, BC.ENDC)
    for sql in sql_list:
        try:
            if any(keyword in sql.lower() for keyword in sql_keywords[8:]):
                cursor.execute(sql)
                connection.commit()
                out = cursor.rowcount
            else:
                out = pd.read_sql_query(sql, connection)
        except Exception as e:
            print(f'Не удалось выполнить запрос {BC.OKBLUE}{sql_query}{BC.ENDC} - {BC.WARNING}{e}{BC.ENDC}')
            return False

    connection.close()
    return out


if __name__ == "__main__":
    # tg_id, new_role, author_tg_id = 123456, 'banned_user', 140291166
    # params = [tg_id, author_tg_id, new_role, tg_id]
    # res = mquery('set_user_and_rights', params)
    # print(res)
    #
    # params = ['команда /start']
    # res = mquery('check_event', params)
    # print(res)




    # if not mquery('create_tables'):
    #     print(f'{BC.FAIL}Error: не удалось проверить целостность таблиц БД!{BC.ENDC}')

    # params = [140291166, 'команда /start']
    # res = mquery('add2log', params)

    # event = 'команда /start'
    # res = mquery('check_event', [event])
    # print(res)
    # res = mquery('check_event', params)

    # params = [140291166, 'команда /start']
    # query = """
    # select
    #         eh.report_dt
    #     ,	eh.tg_id
    #     ,	ua.tg_login
    #     ,	ua.first_name
    #     ,	ua.last_name
    #     ,	ud.role
    #     ,	ed.event
    #
    # from events_h as eh
    #     join events_dict as ed on 1=1
    #         and eh.event_id = ed.event_id
    #         and eh.tg_id = %var%
    #         and ed.event = '%var%'
    #         and eh.report_dt = (select max(report_dt) from events_h)
    #     join user_accounts_h as ua on 1=1
    #         and eh.tg_id = ua.tg_id
    #     left join user_role_h as ur on 1=1
    #         and ur.tg_id = eh.tg_id
    #         and ur.is_actual = 1
    #     left join user_role_dict as ud on 1=1
    #         and ud.role_id = ur.role_id
    #
    # """
    # # res = mquery('return_user_role', params)
    #
    query = 'delete from user_role_h where tg_id = 123456'
    res = mquery(query)
    print(res)
    # print(res['phone'].iloc(0)[0])
    #
    # # print(res['role'].item())
    #
    # # res = mquery('create_tables')
    # # print(res)
    # # print('!!!!!!!')
    # # res = mquery('../SQL/create tables.sql')
    # # print(res)
    # # params = [140291166, 'Dmitry_Ufimtsev', 'Дмитрий', 'Уфимцев']
    # # res = mquery('../SQL/add users.sql', params)
    # # print(res)
    # # params = [140291166]
    # # params = [140291166, 'Dmitry_Ufimtsev', 'Дмитрий', 'Уфимцев']
    # # res = mquery('add_users', params)
    # # print(res)
    # # params = [140291166]
    # # res = mquery('check_users', params)
    # # print(res)
