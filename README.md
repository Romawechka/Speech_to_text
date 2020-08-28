# speech_to_text
+ Для работы скрипта требуются установленные бибилиотеки, пожалуйста установите их командой:
  + **pip install tinkoff-voicekit-client**
  + **pip install psycopg2**
  + **pip install mutagen**
+ Или же вы можете использовать команду:
  + **pip install -r requirements.txt**
+ 
+ 
+ Скрипт принимает на вход строку с параметрами (путь телефон фалг_записи_БД этап), строка имеет следующий вид (Example):
  + D:\Project\Python project\FILE_NAME.wav 89111794124 1 1
+ 
+ 
Вам необходимо поместить свои ключи для подключения к API
```python
API_KEY = "API_KEY"
SECRET_KEY = "SECRET_KEY"
```
Вам необходимо поместить свои настройки для подключения к БД PostgreSQL
```python
database = "postgres"
user = "postgres"
password = "5960363rR"
host = "localhost"
port = "5432"
```
