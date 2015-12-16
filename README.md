![Chi](https://raw.githubusercontent.com/wiki/mdevaev/emonoda/chi.png) Emonoda -- 得物だ
=======

[![PyPI Version](https://img.shields.io/pypi/v/emonoda.svg)](https://pypi.python.org/pypi/emonoda/)
[![Python Versions](https://img.shields.io/pypi/pyversions/emonoda.svg)](https://pypi.python.org/pypi/emonoda/)
[![PyPI License](https://img.shields.io/pypi/l/emonoda.svg)](https://pypi.python.org/pypi/emonoda/)
[![Build Status](https://img.shields.io/travis/mdevaev/emonoda.svg)](https://travis-ci.org/mdevaev/emonoda)

**Emonoda** (moon. _得物だ_, рус. _это добыча_) -- это набор программ для организации и управления коллекцией торрентов. Он поможет вам следить за актуальностью раздач и автоматически обновлять торрент-файлы, а так же вычищать старые данные, просматривать мета-информацию и делать множество других вещей.  
За детальной информацией обращайтесь на вики: https://github.com/mdevaev/emonoda/wiki  

***

### Из коробки ###
* [emupdate](https://github.com/mdevaev/emonoda/wiki/emupdate) -- Следит за раздачами, используя плагины для популярных трекеров; обновляет торрент-файлы при добавлении новых серий или перезаливке; интегрируется с основными линуксовыми клиентами.
* [emfile](https://github.com/mdevaev/emonoda/wiki/emfile) -- Позволяет читать метаданные торрент-файлов и выдает их в человекочитаемом, либо удобном для скриптов формате.
* [emdiff](https://github.com/mdevaev/emonoda/wiki/emdiff) -- Показывает разницу содержимого двух торрент-файлов в виде диффа.
* [emfind](https://github.com/mdevaev/emonoda/wiki/emfind) -- Служит для выполнения различных поисковых запросов, например - найти в каталоге с данными файлы, не принадлежащими ни одному торренту, зарегистрированному в клиенте.
* [emload](https://github.com/mdevaev/emonoda/wiki/emload) -- Загружает торрент, используя "ссылочную" модель хранения данных (см. документацию).
* [emrm](https://github.com/mdevaev/emonoda/wiki/emrm) -- Удаляет торрент из клиента.

***

### Основные фичи ###
* **UNIX-way** -- система представлена в виде простых консольных программ с текстовыми конфигами. Не нужно разворачивать оракл, апач и кластер эллиптикса - просто поставьте **emonoda** и укажите в ее конфиге несколько несложных параметров.
* **Python** -- можно легко добавить поддержку других трекеров, используя готовый набор классов и функций.
* **Интегрируемость** -- программы стараются по-максимуму использовать все возможности торрент-клиентов. Например, **emfile** способна найти каталог, куда вы загружали указанный торрент, а **emupdate**, при обновлении торрент-файла, может сохранить его метку, назначенную в [ruTorrent](https://github.com/Novik/ruTorrent).
* **Прокси для каждого трекера** -- можно индивидуально настроить использование HTTP/Socks4/Socks5-прокси, если в вашей сети недоступен любимый ресурс.
* **Фингерпринты** -- перед тем, как логиниться на трекер, программа проверит содержимое сайта и сообщит вам, если вместо него вдруг показывается провайдерская заглушка.
* **Оповещения** -- можно добавить **emupdate** в крон и забыть о нем, а при появлении новых раздач программа сама вышлет вам оповещение на почту или телефон.

***

### [Поддерживаемые трекеры](https://github.com/mdevaev/emonoda/wiki/fetchers) ###
* http://rutracker.org
* http://nnm-club.me
* http://ipv6.nnm-club.me
* http://rutor.org
* http://tfile.me
* http://pravtor.ru
* http://tr.anidub.com
* http://pornolab.net
* http://booktracker.org

***

### [Поддерживаемые клиенты](https://github.com/mdevaev/emonoda/wiki/clients) ###
* [RTorrent](http://rakshasa.github.io/rtorrent/)
* [KTorrent](http://ktorrent.pwsp.net/)
* [Transmission](http://www.transmissionbt.com/)

***

### [Способы оповещения](https://github.com/mdevaev/emonoda/wiki/confetti) ###
* **E-mail** -- в виде плейнтекста или HTML, на ваш выбор. Посылаются в виде дайджеста по всем обновленным раздачам.
* [Notify My Android](http://notifymyandroid.com/) -- короткие push-нотификации на андроид, по одной на обновленную раздачу.

***

### Установка ###
Для работы программы вам потребуется Python версии 3.4 или выше.

##### Локальная установка из PyPI ####
Вы можете поставить **emonoda** в свой домашний каталог из [PyPI](https://pypi.python.org/pypi/emonoda), при этом программы будут доступны в `~/.local/bin`, например - `~/.local/bin/emupdate`. Для установки введите:
```
pip install --user --upgrade emonoda
```
##### Пакет для Arch Linux ####
Актуальный PKGBUILD находится в [AUR`е](https://aur4.archlinux.org/packages/emonoda/):
```
packer -S emonoda
```

***

### Скриншотики ###

| emupdate в консоли | Сообщение на почту | Нотификации на андроид |
|-------------------|--------------------|------------------------|
| <img src=https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate.png height=150> | <img src=https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate_email.png height=150> | <img src=https://raw.githubusercontent.com/wiki/mdevaev/emonoda/emupdate_android.png height=150> |
