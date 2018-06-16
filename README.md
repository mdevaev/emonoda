# ![Chi](https://raw.githubusercontent.com/wiki/mdevaev/emonoda/chi.png) Emonoda -- 得物だ

[![PyPI Version](https://img.shields.io/pypi/v/emonoda.svg)](https://pypi.python.org/pypi/emonoda)
[![PyPI Status](https://img.shields.io/pypi/status/emonoda.svg)](https://pypi.python.org/pypi/emonoda)
[![PyPI License](https://img.shields.io/pypi/l/emonoda.svg)](https://pypi.python.org/pypi/emonoda)
[![Python Versions](https://img.shields.io/pypi/pyversions/emonoda.svg)](https://pypi.python.org/pypi/emonoda)
[![Build Status](https://img.shields.io/travis/mdevaev/emonoda.svg)](https://travis-ci.org/mdevaev/emonoda)


***

**Emonoda** (moon. _得物だ_, рус. _это добыча_) -- это набор программ для организации и управления коллекцией торрентов. Он поможет вам следить за актуальностью раздач и автоматически обновлять торрент-файлы, а так же вычищать старые данные, просматривать мета-информацию и делать множество других вещей. За подробностями обращайтесь к [документации](https://mdevaev.github.io/emonoda).


***
### Основные фичи

* **UNIX-way** -- система представлена в виде простых консольных программ с текстовыми конфигами. Не нужно разворачивать оракл, апач и кластер эллиптикса - просто поставьте **Emonoda** и укажите в ее конфиге несколько несложных параметров.
* **Python** -- можно легко добавить поддержку других трекеров, используя готовый набор классов и функций.
* **Интегрируемость** -- программы стараются по-максимуму использовать все возможности торрент-клиентов. Например, [emfile](https://mdevaev.github.io/emonoda/emfile) способна найти каталог, куда вы загружали указанный торрент, а [emupdate](https://mdevaev.github.io/emonoda/emupdate) при обновлении торрент-файла может сохранить его метку, назначенную в [ruTorrent](https://github.com/Novik/ruTorrent).
* **Прокси для каждого трекера** -- можно индивидуально настроить использование HTTP/Socks4/Socks5-прокси, если в вашей сети недоступен любимый ресурс.
* **Фингерпринты** -- перед тем, как логиниться на трекер, программа проверит содержимое сайта и сообщит вам, если вместо него вдруг показывается провайдерская заглушка.
* **Оповещения** -- можно добавить [emupdate](https://mdevaev.github.io/emonoda/emupdate) в крон и забыть о нем, а при появлении новых раздач программа сама вышлет вам оповещение на почту или телефон.


#### [Поддерживаемые трекеры](https://mdevaev.github.io/emonoda/trackers)

* http://rutracker.org
* http://nnm-club.me
* http://ipv6.nnm-club.name
* http://rutor.info
* http://tfile.cc
* http://pravtor.ru
* http://tr.anidub.com
* http://pornolab.net
* http://booktracker.org
* http://trec.to


#### [Поддерживаемые клиенты](https://mdevaev.github.io/emonoda/clients)

* [RTorrent](http://rakshasa.github.io/rtorrent/)
* [KTorrent](http://ktorrent.pwsp.net/)
* [Transmission](http://www.transmissionbt.com/)
* [qBittorrent](https://www.qbittorrent.org/)


#### [Способы оповещения](https://mdevaev.github.io/emonoda/confetti)

* **E-mail** -- в виде плейнтекста или HTML, на ваш выбор. Посылаются в виде дайджеста по всем обновленным раздачам.
* **Telegram** -- по отдельному сообщению на каждую обновленную раздачу для всех необходимых пользователей.
* [Pushover](https://pushover.net/) -- push-нотификации на айфон и андроид, по одной на раздачу, без подробностей.
* Генерация ленты обновлений в формате Atom.


***
### Основные компоненты из коробки

| Компонент | Описание |
|-----------|----------|
| [emupdate](https://mdevaev.github.io/emonoda/emupdate) | Следит за раздачами, используя плагины для популярных трекеров; обновляет торрент-файлы при добавлении новых серий или перезаливке; интегрируется с основными линуксовыми клиентами |
| [emfile](https://mdevaev.github.io/emonoda/emfile) | Позволяет читать метаданные торрент-файлов и выдает их в человекочитаемом, либо удобном для скриптов формате |
| [emdiff](https://mdevaev.github.io/emonoda/emdiff) | Показывает разницу содержимого двух торрент-файлов в виде диффа |
| [emload](https://mdevaev.github.io/emonoda/emload) | Загружает торрент, используя "ссылочную" модель хранения данных (см. документацию) |
| [emrm](https://mdevaev.github.io/emonoda/emrm) | Удаляет торрент из клиента |
| [emfind](https://mdevaev.github.io/emonoda/emfind) | Служит для выполнения различных поисковых запросов, например - найти в каталоге с данными файлы, не принадлежащими ни одному торренту, зарегистрированному в клиенте |


***
### Скриншоты

| emupdate в консоли | Оповещение на почту |
|--------------------|---------------------|
| [<img src=https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate.png height=150>](https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate.png) | [<img src=https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate_email.png height=150>](https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate_email.png) |


***
### Установка

Для работы программы требуется Python версии 3.6 или выше. Для сборки нужен [Cython](https://pypi.org/project/Cython).


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

**Emonoda** - очень развесистая система, имеющая тонну параметров для тонкой настройки под конкретные цели и юзкейсы. Чтобы начать эффективно пользоваться всеми ее возможностями, рекомендуется изучить [базовые принципы настройки](https://mdevaev.github.io/emonoda/config), а затем перейти к рассмотрению каждой команды, например [emupdate](https://mdevaev.github.io/emonoda/emupdate).

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

* [Базовая настройка](https://mdevaev.github.io/emonoda/config)
    * [Интеграция с торрент-клиентом](https://mdevaev.github.io/emonoda/clients)
    * [Настройка трекеров для обновления торрентов](https://mdevaev.github.io/emonoda/trackers)
    * [Настройка оповещений об обновлениях](https://mdevaev.github.io/emonoda/confetti)
* Команды
    * [emupdate](https://mdevaev.github.io/emonoda/emupdate) - обновление торрентов
    * [emfile](https://mdevaev.github.io/emonoda/emfile) - просмотр информации о торрент-файле
    * [emdiff](https://mdevaev.github.io/emonoda/emdiff) - сравнение торрент-файлов
    * [emload](https://mdevaev.github.io/emonoda/emload) - добавление торрента в клиент
    * [emrm](https://mdevaev.github.io/emonoda/emrm) - удаление торрента из клиента
    * [emfind](https://mdevaev.github.io/emonoda/emfind) - запросы к клиенту для обслуживания коллекции
    * [emconfetti-demo](https://mdevaev.github.io/emonoda/emconfetti-demo) - тестирование оповещений об обновлениях
    * [emconfetti-tghi](https://mdevaev.github.io/emonoda/emconfetti-tghi) - хелпер для Telegram-бота
* [Спецкостыли для разных клиентов](https://mdevaev.github.io/emonoda/hooks)
* Инфа для разработчиков
    * [rTorrent XMLRPC Reference](rTorrent-XMLRPC-Reference)
	* [rTorrent system_multicall](rTorrent-system_multicall)
