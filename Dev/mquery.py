import os
from dotenv import load_dotenv
import sqlite3
import pandas as pd
import yaml


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


def mquery(sql_query: str, params=None):
    """
       В качестве входного sql_query могут быть переданы 3 типа параметров:
            a) Метка для файла ../SQL/requests.yml
            b) Путь к текстовому файлу
            c) Непосредственно текст SQL запроса

       1. Проверяем, является ли sql_query путем к файлу. Если да, то открываем и текст сохраняем в переменную sql_query.
       2. Проверяем является ли текст переменной sql_query SQL запросом.
       3. Если с текстом запроса передаются параметры, то проверяем количество параметров = кол-ву переменных
       4. Проверим отсутствие SQL инъекций в тексте параметров
       5. Если п.2 = п.3 = п.4 = True - выполняем текст запроса sql_query
       """
    load_dotenv()
    db_path = os.getenv('db_path')
    yml_path = os.getenv('yml_path')

    sql_keywords = ["from", "select", "where", "join", "group by", "having", "order by",
                    "drop", "insert", "update", "delete", "create", "alter"]

    with open(yml_path, 'r') as file:
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

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    out = False
    # print(BC.WARNING, sql_query, BC.ENDC)
    try:
        if any(keyword in sql_query.lower() for keyword in sql_keywords[7:]):
            cursor.executescript(sql_query)
            connection.commit()
            out = cursor.rowcount
        else:
            out = pd.read_sql_query(sql_query, connection)
        connection.close()
    except Exception as e:
        print(f'Не удалось выполнить запрос {BC.OKBLUE}{sql_query}{BC.ENDC} - {BC.WARNING}{e}{BC.ENDC}')
    return out


if __name__ == "__main__":
    # if not mquery('create_tables'):
    #     print(f'{BC.FAIL}Error: не удалось проверить целостность таблиц БД!{BC.ENDC}')

    # params = [140291166, 'команда /start']
    # res = mquery('add2log', params)

    # event = 'команда /start'
    # res = mquery('check_event', [event])
    # print(res)
    # res = mquery('check_event', params)

    params = [140291166, 'команда /start']
    query = """
    select 
            eh.report_dt
        ,	eh.tg_id
        ,	ua.tg_login
        ,	ua.first_name
        ,	ua.last_name
        ,	ud.role
        ,	ed.event
        
    from events_h as eh
        join events_dict as ed on 1=1
            and eh.event_id = ed.event_id
            and eh.tg_id = %var%
            and ed.event = '%var%'
            and eh.report_dt = (select max(report_dt) from events_h)
        join user_accounts_h as ua on 1=1
            and eh.tg_id = ua.tg_id
        left join user_role_h as ur on 1=1
            and ur.tg_id = eh.tg_id
            and ur.is_actual = 1
        left join user_role_dict as ud on 1=1
            and ud.role_id = ur.role_id
    
    """
    # res = mquery('return_user_role', params)

    query = "select * from user_accounts_h"
    res = mquery(query, params)
    print(res['phone'].iloc(0)[0])

    # print(res['role'].item())

    # res = mquery('create_tables')
    # print(res)
    # print('!!!!!!!')
    # res = mquery('../SQL/create tables.sql')
    # print(res)
    # params = [140291166, 'Dmitry_Ufimtsev', 'Дмитрий', 'Уфимцев']
    # res = mquery('../SQL/add users.sql', params)
    # print(res)
    # params = [140291166]
    # params = [140291166, 'Dmitry_Ufimtsev', 'Дмитрий', 'Уфимцев']
    # res = mquery('add_users', params)
    # print(res)
    # params = [140291166]
    # res = mquery('check_users', params)
    # print(res)
