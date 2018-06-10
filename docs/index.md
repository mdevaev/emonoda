#![Chi](https://raw.githubusercontent.com/wiki/mdevaev/emonoda/chi.png) Emonoda -- 得物だ

[![PyPI Version](https://img.shields.io/pypi/v/emonoda.svg)](https://pypi.python.org/pypi/emonoda)
[![PyPI Status](https://img.shields.io/pypi/status/emonoda.svg)](https://pypi.python.org/pypi/emonoda)
[![PyPI License](https://img.shields.io/pypi/l/emonoda.svg)](https://pypi.python.org/pypi/emonoda)
[![Python Versions](https://img.shields.io/pypi/pyversions/emonoda.svg)](https://pypi.python.org/pypi/emonoda)
[![Build Status](https://img.shields.io/travis/mdevaev/emonoda.svg)](https://travis-ci.org/mdevaev/emonoda)


***

**Emonoda** (moon. _得物だ_, рус. _это добыча_) -- это набор программ для организации и управления коллекцией торрентов. Он поможет вам следить за актуальностью раздач и автоматически обновлять торрент-файлы, а так же вычищать старые данные, просматривать мета-информацию и делать множество других вещей.


***
### Основные фичи

* **UNIX-way** -- система представлена в виде простых консольных программ с текстовыми конфигами. Не нужно разворачивать оракл, апач и кластер эллиптикса - просто поставьте **Emonoda** и укажите в ее конфиге несколько несложных параметров.
* **Python** -- можно легко добавить поддержку других трекеров, используя готовый набор классов и функций.
* **Интегрируемость** -- программы стараются по-максимуму использовать все возможности торрент-клиентов. Например, [emfile](emfile) способна найти каталог, куда вы загружали указанный торрент, а [emupdate](emupdate) при обновлении торрент-файла может сохранить его метку, назначенную в [ruTorrent](https://github.com/Novik/ruTorrent).
* **Прокси для каждого трекера** -- можно индивидуально настроить использование HTTP/Socks4/Socks5-прокси, если в вашей сети недоступен любимый ресурс.
* **Фингерпринты** -- перед тем, как логиниться на трекер, программа проверит содержимое сайта и сообщит вам, если вместо него вдруг показывается провайдерская заглушка.
* **Оповещения** -- можно добавить [emupdate](emupdate) в крон и забыть о нем, а при появлении новых раздач программа сама вышлет вам оповещение на почту или телефон.


#### [Поддерживаемые трекеры](trackers)

* http://rutracker.org
* http://nnm-club.me
* http://ipv6.nnm-club.name
* http://rutor.info
* http://tfile-home.org
* http://pravtor.ru
* http://tr.anidub.com
* http://pornolab.net
* http://booktracker.org
* http://trec.to


#### [Поддерживаемые клиенты](clients)

* [RTorrent](http://rakshasa.github.io/rtorrent/)
* [KTorrent](http://ktorrent.pwsp.net/)
* [Transmission](http://www.transmissionbt.com/)


#### [Способы оповещения](confetti)

* **E-mail** -- в виде плейнтекста или HTML, на ваш выбор. Посылаются в виде дайджеста по всем обновленным раздачам.
* [Pushover](https://pushover.net/) -- push-нотификации на айфон и андроид, по одной на раздачу, без подробностей.
* Генерация ленты обновлений в формате Atom.


***
### Компоненты из коробки

| Компонент | Описание |
|-----------|----------|
| [emupdate](emupdate) | Следит за раздачами, используя плагины для популярных трекеров; обновляет торрент-файлы при добавлении новых серий или перезаливке; интегрируется с основными линуксовыми клиентами |
| [emfile](emfile) | Позволяет читать метаданные торрент-файлов и выдает их в человекочитаемом, либо удобном для скриптов формате |
| [emdiff](emdiff) | Показывает разницу содержимого двух торрент-файлов в виде диффа |
| [emfind](emfind) | Служит для выполнения различных поисковых запросов, например - найти в каталоге с данными файлы, не принадлежащими ни одному торренту, зарегистрированному в клиенте |
| [emload](emload) | Загружает торрент, используя "ссылочную" модель хранения данных (см. документацию) |
| [emrm](emrm) | Удаляет торрент из клиента |
| [Дополнительно](hooks) | Всякие спецкостыли для различных клиентов |


***
### Скриншоты

| emupdate в консоли | Оповещение на почту |
|--------------------|---------------------|
| [<img src=https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate.png height=150>](https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate.png) | [<img src=https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate_email.png height=150>](https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate_email.png) |


***
### Установка

Для работы программы требуется Python версии 3.6 или выше. Для сборки нужен Cython.


***
##### Локальная установка из PyPI ####

Вы можете поставить **emonoda** в свой домашний каталог из [PyPI](https://pypi.python.org/pypi/emonoda), при этом программы будут доступны в `~/.local/bin`, например - `~/.local/bin/emupdate`.

Для установки введите:

```
$ pip3 install --user --upgrade emonoda
```

***
##### Пакет для Arch Linux ####

Актуальный PKGBUILD находится в [AUR`е](https://aur.archlinux.org/packages/emonoda):

```
$ packer -S emonoda
```


***
### С чего начать?

**Emonoda** - очень развесистая система, имеющая тонну параметров для тонкой настройки под конкретные цели и юзкейсы. Чтобы начать эффективно пользоваться всеми ее возможностями, рекомендуется изучить [базовые принципы настройки](config), а затем перейти к рассмотрению каждой команды, например [emupdate](emupdate).

В самом простом случае вам потребуется лишь минимальная настройка. Скажем, если у вас большинство торрентов скачано с рутрекера, а в качестве клиента вы используете связку [rTorrent](https://github.com/rakshasa/rtorrent) с [ruTorrent](https://github.com/Novik/ruTorrent), вам будет достаточно создать файл `~/.config/emonoda.yaml` примерно такого содержания:

```yaml
core:
    client: rtorrent
    torrents_dir: /путь/к/торрент-файлам

trackers:
    rutracker.org:
        user: логин-на-рутрекере
        passwd: пароль
```

***

* [Базовая настройка](config)
    * [Интеграция с торрент-клиентом](clients)
    * [Настройка трекеров для обновления торрентов](trackers)
    * [Настройка оповещений об обновлениях](confetti)
* Команды
    * [emupdate](emupdate) - обновление торрентов
    * [emfile](emfile) - просмотр информации о торрент-файле
    * [emdiff](emdiff) - сравнение торрент-файлов
    * [emload](emload) - добавление торрента в клиент
    * [emrm](emrm) - удаление торрента из клиента
    * [emfind](emfind) - запросы к клиенту для обслуживания коллекции
* [Спецкостыли для разных клиентов](hooks)
* Инфа для разработчиков
    * [rTorrent XMLRPC Reference](rTorrent-XMLRPC-Reference)
	* [rTorrent system_multicall](rTorrent-system_multicall)
