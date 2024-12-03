import sys
import unittest
import pandas as pd
sys.path.append('../Dev/')

import muser as mu
from mquery import mquery

class CheckUser(unittest.TestCase):

    # todo  Создать следующие тесты:
    #       0. Пользователя нет в БД
    #       1. Первичная проверка:
    #           1.1. Новый пользователь, в БД добавлен
    #           1.2. В БД уже есть такой пользователь - данные идентичны
    #           1.3. В БД уже есть такой пользователь - данные не идентичны - обновить
    #           1.4. Недостаточно данных для обновления
    #       2. Получение/установка прав пользователя
    #           2.1. Получение прав пользователя по умолчанию - 'user'
    #           2.2. Назначение администраторам роли пользователя: 'moderator'
    #           2.3. Назначение администраторам роли пользователя: 'user'
    #           2.4. Изменение прав пользователя с 'user' на 'moderator'
    #           2.5. Недостаточно прав для изменения роли
    # todo  3. Запись лога по действиям пользователя
    # todo      3.1. Пользователь зашел в БД


    # 0. Пользователя нет в БД
    def test_user_not_in_bd(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        res = mu.check_user_and_rights(test_user['tg_id'])
        # Результат
        self.assertEqual(res, None)

    # 1.1 Новый пользователь, в БД добавлен
    def test_add_user(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        res = mu.check_user_and_rights(test_user['tg_id'])
        # Зачистка
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res['role'], 'user')

    # 1.2. В БД уже есть такой пользователь - данные идентичны
    def test_exist_equal_user(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        res = mu.add_or_update_user(**test_user)
        # Зачистка
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res, 0)

    # 1.3. В БД уже есть такой пользователь - данные не идентичны - обновить
    def test_update_user_params(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        test_user['last_name'] = 'test_last_names'
        del test_user['home_email']
        res = mu.add_or_update_user(**test_user)
        # Зачистка
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res, 2)

    # 1.4. Недостаточно данных для обновления
    def test_not_enough_params(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        test_user['last_name'] = 'test_last_names'
        del test_user['tg_login']
        # Зачистка
        res = mu.add_or_update_user(**test_user)
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res, False)

    # 2.1. Получение прав пользователя по умолчанию - user
    def test_get_ordinary_user_rights(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        res = mu.check_user_and_rights(test_user['tg_id'])
        # Зачистка
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res['role'], 'user')

    # 2.2. Назначение администраторам роли пользователя: moderator
    def test_set_moderator_role(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        mu.set_user_rights(test_user['tg_id'], 'moderator', 140291166)
        res = mu.check_user_and_rights(test_user['tg_id'])
        # Зачистка
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res['role'], 'moderator')

    # 2.3. Назначение администраторам роли пользователя: 'user'
    def test_set_user_role_1(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        mu.set_user_rights(test_user['tg_id'], 'user', 140291166)
        res = mu.check_user_and_rights(test_user['tg_id'])
        # Зачистка
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res['role'], 'user')

    # 2.4. Изменение прав пользователя с 'user' на 'moderator'
    def test_set_user_role_2(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        mu.set_user_rights(test_user['tg_id'], 'moderator', 140291166)
        mu.set_user_rights(test_user['tg_id'], 'user', 140291166)

        res = mu.check_user_and_rights(test_user['tg_id'])
        # Зачистка
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res['role'], 'user')

# 2.5. Недостаточно прав для изменения роли
    def test_set_user_role_3(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        mu.set_user_rights(test_user['tg_id'], 'moderator', test_user['tg_id'])
        res = mu.check_user_and_rights(test_user['tg_id'])

        # Зачистка
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res['role'], 'user')

    def test_add2log_01(self):
        # Подготовка
        test_user = {'tg_id': 123456, 'tg_login': 'test_tg_login', 'first_name': 'test_first_name',
                     'last_name': 'test_last_name', 'phone': '+7 913 913 88 99',
                     'corp_email': 'test_user@sber.ru', 'home_email': 'test_user@gmail.com'}
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from events_h where tg_id = {test_user['tg_id']}")
        # Исполнение
        mu.add_or_update_user(**test_user)
        res = mu.add_event2log(test_user['tg_id'], '/start')

        # Зачистка
        mquery(f"delete from user_role_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from user_accounts_h where tg_id = {test_user['tg_id']}")
        mquery(f"delete from events_h where tg_id = {test_user['tg_id']}")
        # Результат
        self.assertEqual(res['event_name'], '/start')



if __name__ == '__main__':
    unittest.main()
