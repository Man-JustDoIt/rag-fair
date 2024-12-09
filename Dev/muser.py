# todo В этом модуле соберем все операции с пользователями:
#       1. Добавить пользователя в БД, если его нет в БД
#       2. Наличие пользователя в БД и его права - по умолчанию user
#       3. Изменить данные пользователя
#       4. Изменить права пользователя
#       5. Занести событие в log

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


def add_event2log(tg_id, event_name) -> [dict, False]:
    #     return dict {report_dt,  tg_id,  event_name} or False
    #     Функция формирует лог по активностям пользователя
    #     В таблицу events_h заносится информация по следующим событиям:
    #           1. Вход нажатие кнопки '/start' пользователя с правами XXX

    res = mquery(f"select event_name_id from events_dict where event_name = '{event_name}'")
    if isinstance(res, pd.DataFrame) and not res.empty:
        event_name_id = res['event_name_id'].iloc(0)[0]
    else:
        print(f'{BC.FAIL}Error:{BC.ENDC} Событие {BC.WARNING}{event_name}{BC.ENDC} не зарегистрировано!')
        return False

    res = check_user_and_rights(tg_id)
    if isinstance(res, dict) and len(res) > 0:  # Существующий пользователь
        event_dict = res
    else:
        return False
    event_dict['tg_id'], event_dict['event_name_id'] = tg_id, event_name_id

    params = list(event_dict.keys())
    values = list(event_dict.values())

    res = mquery('last_event_time', [tg_id, event_name])
    if isinstance(res, pd.DataFrame) and not res.empty:
        last_event = res.to_dict(orient='records')[0]
    else:
        return False

    params_str = ', '.join(params)
    values_srt = str(values)[1:-1]
    params = [params_str, values_srt]
    res = mquery('add2log', params)
    if not (isinstance(res, numbers.Number) and res == 1):
        return False

    res = mquery('last_event_time', [tg_id, event_name])
    if isinstance(res, pd.DataFrame) and not res.empty:
        log_line = res.to_dict(orient='records')[0]
    else:
        return False

    log_line['last_event_dt'] = last_event['report_dt']
    return log_line


def add_or_update_user(**kwargs) -> [dict, False]:
    #     Функция добавляет или обновляет данные о пользователе в БД в таблице user_accounts_h
    #     0. Проверяем ключи **kwargs на количество и соответствие колонкам в таблице user_accounts_h
    #     1. Проверяем наличие пользователя в БД
    #     2. Если пользователь есть и параметры идентичны - возвращаем 0
    #     3. Если пользователь есть и параметры различны - деактивируем текущую запись и deactivate = 1
    #          3.1 Нужно изменить только те параметры, которые содержит *kwarg, остальные оставить старые
    #     4. Если пользователя в БД нет или deactivate = 1 - создаем запрос на добавление записи в БД

    table_name = 'user_accounts_h'
    min_params = ['tg_id', 'tg_login']
    sql_query = f'pragma table_info({table_name})'
    table_columns_df = mquery(sql_query)
    deactivate = 0

    if isinstance(table_columns_df, pd.DataFrame) and not table_columns_df.empty:
        table_columns = table_columns_df['name'].to_list()
        user_new_params_dict = kwargs
        user_new_params_keys = list(user_new_params_dict.keys())
        user_new_params_values = list(user_new_params_dict.values())
    else:
        print(f'{BC.FAIL}Error:{BC.ENDC} Не удается прочитать структуру таблицы {table_name} в БД!')
        return False

    if not set(user_new_params_keys).issubset(table_columns):
        delta = set(user_new_params_keys) - set(table_columns)
        print(f'{BC.FAIL}Error:{BC.ENDC} Столбцы {BC.WARNING}{delta}{BC.ENDC} отсутствуют в таблице {table_name}!')
        return False

    if not set(min_params).issubset(user_new_params_keys):
        delta = set(min_params) - set(user_new_params_keys)
        print(f'{BC.FAIL}Error:{BC.ENDC} Не хватает параметра {BC.WARNING}{delta}{BC.ENDC}!')
        return False

    user_current_params = check_user_and_rights(kwargs['tg_id'], all=True)

    if isinstance(user_current_params, dict) and len(user_current_params) > 0:  # Существующий пользователь
        # убираем поля, которых нет в таблице
        user_current_params_dict = {k: user_current_params[k] for k in table_columns if k in user_current_params}
        # выделяем ключи, которые есть как в существующих, так и в новых параметрах пользователя.
        user_current_params_keys_cut = user_current_params_dict.keys() & user_new_params_dict.keys()
        # в существующих параметрах оставляем только одинаковые поля
        user_current_params_dict_cut = {k: user_current_params_dict[k] for k in user_current_params_keys_cut}
        # если словари совпали, то ничего обновлять не нужно, возвращаем dict с данными пользователя
        if user_current_params_dict_cut == user_new_params_dict:
            return check_user_and_rights(kwargs['tg_id'], all=True)
        # если не совпали, то ищем расхождения в значениях (ключи мы привели к единому виду выше)
        delta_dict = dict(set(user_new_params_dict.items()) - set(user_current_params_dict_cut.items()))
        # заменяем данные в текущем словаре на новые, если есть различия
        user_current_params_dict.update(delta_dict)
        # для записи параметров в SQL выделим название столбцов и их значения
        user_params = ', '.join(list(user_current_params_dict.keys()))
        user_values = str(list(user_current_params_dict.values()))[1:-1]
        deactivate = 1

    elif user_current_params is None:  # Новый пользователь
        user_params = ', '.join(user_new_params_keys)
        user_values = str(user_new_params_values)[1:-1]
    else:
        return False

    if deactivate == 1:
        # деактивируем текущую запись
        mquery('deactivate_user_line', [kwargs['tg_id']])

    params = [user_params, user_values]
    res = mquery('add_user_line', params)
    if isinstance(res, numbers.Number) and res == 1:
        return check_user_and_rights(kwargs['tg_id'], True)
    else:
        return False


if __name__ == "__main__":
    test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                 'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                 'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
    # mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
    # mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
    # add_event2log(test_user['tg_id'], '/start')
    null = 'null'
    print('Out: ', add_or_update_user(**test_user))
    test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'new_first_name',
                 'last_name': 'test_last_name', 'phone': None}
    print('Out: ', add_or_update_user(**test_user))


    # res = set_user_rights(test_user['tg_id'], 'moderator', 140291166)
    # print(res)
