### Yatube, социальная сеть

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

``` bash
git clone git@github.com:AlexeyWer/yatube.git
```

``` bash
cd yatube
```

Cоздать и активировать виртуальное окружение:

``` bash
python3 -m venv env
```

``` bash
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

``` bash
python -m pip install --upgrade pip
```

``` bash
pip install -r requirements.txt
```

Выполнить миграции:

``` bash
python3 manage.py migrate
```

Запустить проект:

``` bash
python3 manage.py runserver
```
