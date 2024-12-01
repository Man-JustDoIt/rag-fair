import sys
import unittest
import pandas as pd
sys.path.append('../Dev/')

from mquery import mquery

class CheckUser(unittest.TestCase):

    # todo  Создать следующие тесты:
    # todo  1. Первичная проверка:
    # todo      1.1. Новый пользователь, в БД добавлен
    # todo      1.2. Существующий в БД пользователь
    # todo  2. Проверка прав пользователя:
    # todo      2.1. Обычный пользователь
    # todo      2.2. Админ
    # todo      2.3. Редактор контента
    # todo      2.4. Banned user
    # todo  3. Дате/время последнего входа
    # todo      3.1. В БД нет данных о входе
    # todo      2.2. В БД еть данные о входе

    # 1.1. Новый пользователь, в БД добавлен
    def test_add_new_user(self):
        test_user = [123456, 'test_tg_login', 'test_first_name', 'test_last_name']
        result = ''

        res = mquery('check_user_in_BD', [test_user[0]])
        if isinstance(res, pd.DataFrame) and res.empty:
            mquery('add_new_user', test_user)
            res = mquery('check_user_in_BD', [test_user[0]])
            len_res = len(res)
            tg_login = res['tg_login'].iloc(0)[0]
            result = [len_res, tg_login]
            sql_query = 'delete from user_accounts_h where tg_id = 123456'
            mquery(sql_query, [test_user[0]])

        self.assertEqual(result, [1, 'test_tg_login'])

    # 1.2. Существующий в БД пользователь
    def test_user_already_exist(self):
        res = mquery('check_user_in_BD', [140291166])
        result = res['tg_login'].iloc(0)[0]
        self.assertEqual(result, 'Dmitry_Ufimtsev')

    # 2. Проверка прав пользователя:
    def test_user_rights(self):

        # создаем тестового пользователя
        # не добавляем ему роль - роль должна быть 'user'
        # проверяем является ли инициирующий пользователь администратором
        # добавляем ему роль 'content_redactor' - проверяем, что роль присвоилась
        # добавляем ему роль 'admin' - проверяем, что роль 'content_redactor' стала не активной, активна роль 'admin'
        # добавляем ему роль 'banned_user' - проверяем, что все остальные роли не активны
        # записываем 4 состояния пользователя
        # удаляем пользователя и его роли
        # сверяем результат тестирования с эталонным [123456, 'user', 'content_redactor', 'admin', 'banned_user']

        result = []
        test_user = [123456, 'test_tg_login', 'test_first_name', 'test_last_name']
        res = mquery('check_user_in_BD', [test_user[0]])
        if isinstance(res, pd.DataFrame) and res.empty:
            mquery('add_new_user', test_user)
        # роль - user
        res = mquery('check_user_and_rights', [test_user[0]])
        result.append(res['role'].iloc(0)[0])

        self.assertEqual(result, ['user'])



