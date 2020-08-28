"""
Author: https://github.com/Romawechka
Python version 3.8
"""

import datetime
import psycopg2
from tinkoff_voicekit_client import ClientSTT
from mutagen.wave import WAVE

# Ваши ключи для доступа к API Тинькофф
# Your keys for accessing the Tinkoff API
API_KEY = "API_KEY"
SECRET_KEY = "SECRET_KEY"

client = ClientSTT(API_KEY, SECRET_KEY)

# Настройки кодировки для аудио файлов (https://github.com/TinkoffCreditSystems/voicekit_client_python)
# Encoding settings for audio files (https://github.com/TinkoffCreditSystems/voicekit_client_python)
audio_config = {
    "encoding": "LINEAR16",
    "sample_rate_hertz": 8000,
    "num_channels": 1
}

# Настройки для подключения к БД
# Settings for connecting to the database
database = "postgres"
user = "postgres"
password = "password"
host = "localhost"
port = "5432"


# Функция для подключение к БД
# Function for connecting to the database
def connection_on_BD():
    try:
        con = psycopg2.connect(
            database=database,
            user=user,
            password=password,
            host=host,
            port=port
        )

        # Если нету необходимой схемы или таблиц, создаем их. Сразу помещаем данные в таблицы Project и Server
        # If you don't have the schema or tables, create them and put the data in the Project and Server tables
        cur = con.cursor()
        cur.execute("""
            CREATE SCHEMA if not exists speech_to_text;
            CREATE TABLE if not exists speech_to_text.Project
                (
                    Id SERIAL PRIMARY KEY,
                    name varchar,
                    description varchar
                );
            CREATE TABLE if not exists speech_to_text.Server
                (
                    Id SERIAL PRIMARY KEY,
                    name varchar,
                    ip_address varchar,
                    description varchar
                );
            insert into speech_to_text.project (name, description ) values('incoming', 'тестовый');
            insert into speech_to_text.project (name) values('alfa-warm');
            insert into speech_to_text.server (name, ip_address, description ) values('alfa-warm', '8.8.8.8', 'google');

        """)
        con.commit()

        cur.execute("""            
            CREATE table if not exists speech_to_text.operations(  
                data date,
                time varchar(80),
                id SERIAL PRIMARY key,
                AO varchar(80),
                phone varchar(80),
                audio_length numeric,
                result varchar(80),
                ProjectID INTEGER,
                ServerID INTEGER,
                foreign key (ProjectID) references speech_to_text.Project (id),
                foreign key (ServerID) references speech_to_text.Server (id)
            );"""
                    )
        con.commit()
        return {'conection': con, 'cursor': cur}
    except Exception as e:
        return False


# функция для логгирования
# function for logging
def log(message, exc):

    # 'exc' дает понять пложительный ли резульат или ошибка
    # 'exc' lets you know whether the result is positive or not
    if exc:
        logname = "log.txt"
    else:
        logname = "log_negative.txt"

    log_file = open(logname, "a")
    log_file.write(message + '\n')
    log_file.close()


# Конвертируем речь в текст
# Converting speech to text
def speech_to_text(filename, cursor):

    # Из полученной строки вынимаем нужные нам параметры
    # We extract the parameters we need from the received string
    path = filename.split('.wav')[0] + '.wav'  # нужно чтобы учесть папки у которых в названии есть пробел
    filename = filename.replace(path + ' ', '')
    parameters = [path]
    parameters.extend(filename.split(' '))

    # проверяем что нету не заданных параметров
    # check that there are no parameters that are not set
    if len(parameters) != 4:
        log(
            f'date:{datetime.datetime.today().strftime("%Y-%m-%d")} time:{datetime.datetime.today().strftime("%H:%M")}'
            f' id:{1} AO:{""} phone:{""} audio_length:{""} result:{""} '
            f'except:{"Неверное колличество параметров! Вы должны указать 4 параметра через пробел"}',
            False)
        raise Exception('Неверное колличество параметров! Вы должны указать 4 параметра через пробел\n'
                        'Example: Путь телефон флаг_записи_БД этап')

    # получаем переменные
    # getting variables
    path, phone, flag_bd, step = parameters[0], parameters[1], parameters[2], parameters[3]

    try:
        response = client.recognize(path, audio_config)
        print(response)

        # первый случай
        # first case
        if step == '1':

            # задаем множество со словами, которые нужно отследить
            # specify multiple words that you want to monitor
            checklist = {'автоответчик', 'сигнала'}
            common_words = set(response[0]["alternatives"][0]["transcript"].split()) & checklist
            if len(common_words) > 0:
                AO = 'AO'
            else:
                AO = 'человек'

        # второй случай
        # second case
        elif step == '2':

            # задаем множество со словами, которые нужно отследить
            # specify multiple words that you want to monitor
            checklist = {'да', 'удобно', 'говорите', 'слушаю'}
            common_words = set(response[0]["alternatives"][0]["transcript"].split()) & checklist

            if len(common_words) > 0:
                AO = 'положительно'
            else:
                AO = 'отрицательно'

        else:
            log(
                f'date:{datetime.datetime.today().strftime("%Y-%m-%d")} time:{datetime.datetime.today().strftime("%H:%M")}'
                f' id:{1} AO:{""} phone:{phone} audio_length:{""} result:{""} '
                f'except:{"Этап распознования может быть либо 1 либо 2"}', False)
            raise Exception('Этап распознования может быть либо 1 либо 2')

        # получаем длину аудио
        # get the length of audio
        audio_length = str(WAVE('1.wav').info.length)

        # запись в бд
        # the record in the database
        if flag_bd == '1':

            # в качестве ProjectID будем брать этап распознавания, а в качестве ServerID будем брать flag_bd
            # we will use the recognition stage as the ProjectID, and we will use flag_bd as the ServerID
            cursor['cursor'].execute(
                f'INSERT INTO speech_to_text.operations (data,time,ao,phone,audio_length, result, ProjectID, ServerID)'
                f' VALUES (\'{datetime.datetime.today().strftime("%Y-%m-%d")}\','
                f' \'{datetime.datetime.today().strftime("%H:%M")}\', \'{AO}\', \'{phone}\', \'{audio_length}\','
                f' \'{response[0]["alternatives"][0]["transcript"]}\', {step}, {flag_bd}) RETURNING id')

            # получаем уникальный id записи в БД
            # get the unique id of the database entry
            id = cursor['cursor'].fetchone()[0]
            cursor['conection'].commit()
        else:
            with open('log.txt') as f:
                id = str(sum(1 for _ in f)) + 'n'

        # логируем успешный вариант
        # log the successful option
        log(
            f'date:{str(datetime.datetime.today().strftime("%Y-%m-%d"))} time:\'{str(datetime.datetime.today().strftime("%H:%M"))}\''
            f' id:{id} AO:{AO} phone:{phone} audio_length:{audio_length} result:{response[0]["alternatives"][0]["transcript"]}',
            True)

        # Возвращаем в зависимости от шага и распознания
        # We return it depending on the step and recognition
        if (AO == 'AO') or (AO == 'отрицательно'):
            return 0
        else:
            return 1

    except Exception as e:
        log(
            f'date:{datetime.datetime.today().strftime("%Y-%m-%d")} time:{datetime.datetime.today().strftime("%H:%M")}'
            f' id:{1} AO:{""} phone:{phone} audio_length:{""} result:{""} except:{str(e)}',
            False)


# инициализируем соединение с БД
# initializing the database connection
cursor = connection_on_BD()

# если соединение установлено и таблицы готовы, выполняем код
# if the connection is established and the tables are ready, run the code
if cursor:
    param = input('Принимаю параметры в формате : путь к .wav файлу(Example: D:\Project\Python project\FILE_NAME.wav)),'
                  ' номер телефона(Example: 89111794124), флаг необходимости записи в базу данных(0/1, где 1 запись нужна,'
                  '. 0 нет),'
                  ' этап распознавания(1/2). Все записи через пробел.\n')

    speech_to_text(param, cursor)
else:
    print("Отсутствует соединение с БД, пожалуйста проверьте настройки подключения к БД и попробуйте еще раз")
