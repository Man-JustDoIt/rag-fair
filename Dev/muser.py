# todo В этом модуле соберем все операции с пользователями:
#       1. Наличие пользователя в БД и его права, если он есть в БД - по умолчанию user  --  done
#       2. Добавить пользователя в БД, если его нет в БД
#       3. Изменить данные пользователя
#       4. Изменить права пользователя
# todo  5. Занести событие в log

import pandas as pd
import numbers
import sys

from mquery import mquery
from mquery import BC


def check_user_and_rights(tg_id, all=False):
    res = mquery('check_user_and_rights', [tg_id])
    if isinstance(res, pd.DataFrame) and res.empty:
        print(f'{BC.WARNING}Warning: {BC.ENDC}Пользователь {BC.OKBLUE}{tg_id}{BC.ENDC} отсутствует в БД!')
        return None
    elif isinstance(res, pd.DataFrame) and len(res.index) == 1:
        res = res.to_dict(orient='records')[0]
        if all:  # return dict not null user params
            res_dict = {k: v for k, v in res.items() if v is not None}
        else:  # return dict 'tg_login' and 'role' user params
            res_dict = {k: res[k] for k in ['tg_login', 'role']}
        return res_dict
    else:
        return False


def set_user_rights(tg_id, new_role, author_tg_id):
    res = check_user_and_rights(tg_id)
    if not res:
        return False
    current_login, current_role = res['tg_login'], res['role']
    if current_role == new_role:
        return 0

    res = check_user_and_rights(author_tg_id)
    author_login, author_role = res['tg_login'], res['role']
    if not author_role:
        return False
    if author_role != 'admin':
        print(f'{BC.FAIL}Error:{BC.ENDC} У пользователя {BC.WARNING}{author_role}{BC.ENDC} недостаточно прав!')
        return False
    if new_role == 'user':
        res = mquery(f'update user_role_h set is_actual = 0 where tg_id = {tg_id}')
    else:
        params = [tg_id, author_tg_id, new_role, tg_id]
        res = mquery('set_user_and_rights', params)
    if isinstance(res, numbers.Number) and res == 1:
        return res
    else:
        return False


def add_or_update_user(**kwargs):
    #     Функция добавляет или обновляет данные о пользователе в БД в таблице user_accounts_h
    #     0. Проверяем ключи **kwargs на количество и соответствие колонкам в таблице user_accounts_h
    #     1. Проверяем наличие пользователя в БД
    #     2. Если пользователь есть и параметры идентичны - возвращаем 0
    #     3. Если пользователь есть и параметры различны - деактивируем текущую запись и deactivate = 1
    #     4. Если пользователя в БД нет или deactivate = 1 - создаем запрос на добавление записи в БД

    table_name = 'user_accounts_h'
    min_params = ['tg_id', 'tg_login']
    sql_query = f'pragma table_info({table_name})'
    res = mquery(sql_query)
    deactivate = 0

    if isinstance(res, pd.DataFrame) and not res.empty:
        table_columns = res['name'].to_list()
        params = list(kwargs.keys())
        values = list(kwargs.values())
    else:
        print(f'{BC.FAIL}Error:{BC.ENDC} Не удается прочитать структуру таблицы {table_name} в БД!')
        return False

    if not set(params).issubset(table_columns):
        delta = set(params) - set(table_columns)
        print(f'{BC.FAIL}Error:{BC.ENDC} Столбцы {BC.WARNING}{delta}{BC.ENDC} отсутствуют в таблице {table_name}!')
        return False

    if not set(min_params).issubset(params):
        delta = set(min_params) - set(params)
        print(f'{BC.FAIL}Error:{BC.ENDC} Не хватает параметра {BC.WARNING}{delta}{BC.ENDC}!')
        return False

    res = check_user_and_rights(kwargs['tg_id'], all=True)
    if isinstance(res, dict) and len(res) > 0:  # Существующий пользователь
        res_dict = {k: res[k] for k in table_columns if k in res}
        if res_dict == kwargs:
            return 0
        else:
            res = mquery('deactivate_user_account', [kwargs['tg_id']])
            deactivate = 1

    if res is None or deactivate == 1:  # Завести новую запись по пользователю
        params_str = ', '.join(params)
        values_srt = str(values)[1:-1]
        params = [params_str, values_srt]
        res = mquery('add_new_user', params)
        if isinstance(res, numbers.Number) and res == 1:
            return res + deactivate
        else:
            return False
    else:
        return False


def add_event2log():
    #     todo  Функция добавляет в таблицу events_h информацию по следующим событиям:
    #     todo  0. Регистрация нового пользователя в БД
    #     todo  1. Вход пользователя с правами - нажатие кнопки 'команда /start'
    table_name = 'user_events_h'
#     нужно создать таблицу user_events_h со следующими полями:
#   id - автоинкримент, уникальный идентификатор
#   report_dt - дата и время события
#   last_time_dt - дата и время события предыдущего события по этому пользователю
#   tg_id - id пользователя
#   tg_login - login пользователя
#   role - role пользователя
#   id_event - id события из словаря event_dict
#   is_success - 0 или 1, успешно или неуспешно произошло событие
#   comment - комментарий по событию




if __name__ == "__main__":
    test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                 'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                 'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
    mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
    mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")

    add_or_update_user(**test_user)
    res = set_user_rights(test_user['tg_id'], 'moderator', 140291166)
    print(res)
