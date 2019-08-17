#  Created by Artem Manchenkov
#  artyom@manchenkoff.me
#
#  Modified by Anton Komrachkov
#  Anton-KAS@ya.ru
#
#  Copyright © 2019
#
#  Сервер для обработки сообщений от клиентов
#
from twisted.internet import reactor
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.protocol import ServerFactory, connectionDone

import random  # just for fun


class Client(LineOnlyReceiver):
    """Класс для обработки соединения с клиентом сервера"""

    delimiter = "\n".encode()  # \n для терминала, \r\n для GUI

    # указание фабрики для обработки подключений
    factory: 'Server'

    # информация о клиенте
    ip: str
    login: str = None

    def connectionMade(self):
        """
        Обработчик нового клиента

        - записать IP
        - внести в список клиентов
        - отправить сообщение приветствия
        """

        self.ip = self.transport.getPeer().host  # записываем IP адрес клиента
        self.factory.clients.append(self)  # добавляем в список клиентов фабрики

        self.sendLine("Welcome to the chat!".encode())  # отправляем сообщение клиенту

        print(f"Client {self.ip} connected")  # отображаем сообщение в консоли сервера

    def connectionLost(self, reason=connectionDone):
        """
        Обработчик закрытия соединения

        - удалить из списка клиентов
        - вывести сообщение в чат об отключении
        """

        self.factory.clients.remove(self)  # удаляем клиента из списка в фабрике

        print(f"Client {self.ip} disconnected")  # выводим уведомление в консоли сервера

    def lineReceived(self, line: bytes):
        """
        Обработчик нового сообщения от клиента

        - зарегистрировать, если это первый вход, уведомить чат
        - переслать сообщение в чат, если уже зарегистрирован
        """

        message = line.decode()  # раскодируем полученное сообщение в строку

        # если логин еще не зарегистрирован
        if self.login is None:
            if message.startswith("login:"):  # проверяем, чтобы в начале шел login:
                new_login = message.replace("login:", "")  # Выделяем логин из сообщения
                # создаем список активных логинов:
                active_logins = []  # пустой список активных логинов
                for client in self.factory.clients:
                    active_logins.append(client.login)
                # Проверяем логин на уникальность среди активных в чате
                if new_login in active_logins:
                    notification = f"Логин {new_login} занят, попробуйте другой"  # формируем сообщение клиенту
                    self.sendLine(notification.encode())  # отправляем сообщение клиенту
                    self.transport.loseConnection()  # отключаем клиента от сервера
                else:
                    self.login = new_login  # вырезаем часть после :
                    self.factory.send_history(self)
                    notification = f"New user: {self.login}"  # формируем уведомление о новом клиенте
                    self.factory.notify_all_users(notification)  # отсылаем всем в чат
            else:
                self.sendLine("Invalid login".encode())  # шлем уведомление, если в сообщении ошибка
        # если логин уже есть и это следующее сообщение
        else:
            format_message = f"{self.login}: {message}"  # форматируем сообщение от имени клиента
            self.factory.hist_message.append(message)  # сохраняем сообщение в историю (сохраняем всю историю сессии)
            self.factory.hist_login.append(self.login)
            # отсылаем всем в чат и в консоль сервера
            self.factory.notify_all_users(format_message)
            print(format_message)


class Server(ServerFactory):
    """Класс для управления сервером"""

    clients: list  # список клиентов
    protocol = Client  # протокол обработки клиента

    def __init__(self):
        """
        Старт сервера

        - инициализация списка клиентов
        - вывод уведомления в консоль
        """

        self.clients = []  # создаем пустой список клиентов
        self.hist_message = []  # создаем пустой список истории сообщений
        self.hist_login = []  # создаем пустой список истории клиентов отправивших сообщение

        print("Server started - OK")  # уведомление в консоль сервера

    def startFactory(self):
        """Запуск прослушивания клиентов (уведомление в консоль)"""

        print("Start listening ...")  # уведомление в консоль сервера

    def notify_all_users(self, message: str):
        """
        Отправка сообщения всем клиентам чата
        :param message: Текст сообщения
        """

        data = message.encode()  # закодируем текст в двоичное представление

        # отправим всем подключенным клиентам
        for user in self.clients:
            user.sendLine(data)

    def send_history(self, user):
        #  Просто развлечения ради
        add_fun = ["Началось все с user, который написал: ",
                   "А потом user пишет: ",
                   "А user такой: ",
                   "Вдруг user дополняет: ",
                   "А user ему: ",
                   "А user выдаёт: ",
                   "Неожиданно user: ",
                   "user внезапно: ",
                   "user отвечает: ",
                   "И последнее от user: "]
        if len(self.hist_login) > 0:  # проверка на наличие записей в истории сообщений
            history = "Ранее в чате:\n"  # заготовка отправки истории
            # Преобразуем список в строку
            n = 0  # Начальная точка отсчета
            m = 0
            if len(self.hist_login) > 10:  # проверка количества сообщений в истории
                n = -10  # берем только последние 10 сообщений
            # Выводим случайное сообщение (кроме первого и последнего)
            for login in self.hist_login[n:]:
                if m == 0:
                    fun_m = 0
                elif m == len(self.hist_login) - 1:
                    fun_m = 9
                else:
                    fun_m = random.randint(2, 8)
                history += add_fun[fun_m].replace("user", login) + self.hist_message[m] + "\n"
                m += 1
            history += "-- Вы находитесь здесь --"
        else:
            history = "В этом чате пока нет сообщений, будьте первым!\n"  # сообщение если в истории нет записей
        data = history.encode()  # закодируем текст в двоичное представление
        user.sendLine(data)  # отправка сообщения новому клиенту


if __name__ == '__main__':
    # параметры прослушивания
    reactor.listenTCP(
        7410,
        Server()
    )

    # запускаем реактор
    reactor.run()
