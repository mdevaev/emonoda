### Описание

**emfind** - команда для выполнения различных поисковых запросов по данным клиента и торрент-файлам. Она позволяет содержать вашу коллекцию раздачи в чистоте (помогая удалять старые данные, искать дубликаты торрентов) и активно использует кеширование для повышение скорости работы. Имеет несколько подкоманд, передаваемых в виде аргумента:

* **`not-in-client`**
    * Выводит список торрент-файлов из каталога, указанного [параметром](config) `core/torrents_dir`, не зарегистрированных в клиенте (такие торренты [emupdate](emupdate) помечает меткой `NOT_IN_CLIENT`).

* **`missing-torrents`**
    * Выводит список хешей и имен торрентов, которые зарегистрированы в клиенте, но не имеют торрент-файлов в каталоге `core/torrents_dir`.

* **`duplicate-torrents`**
    * Выводит список торрент-файлов с разными именами, но одинаковым содержимым, найденных в каталоге `core/torrents_dir`.

* **`orphans`**
    * Выводит список файлов и подкаталогов из каталога `core/data_root_dir` (и `core/another_data_root_dirs`), которые не предоставляются ни одним торрент-файлом из `core/torrents_dir`, зарегистрированном в клиенте. Такое часто случается, когда релизер переименовывает какой-нибудь файл в обновленной версии торрента, а клиент скачивает его, больше не считая файл со старым именем частью раздачи. Из-за этого может накопиться много мусора из мелких файлов, лежащих мертвым грузом (автор набрал таким образом примерно 500 гигабайт всякого хлама), но используя `emfind orphans` вы сможете избавиться от них. Первый вызов команды построит внутренний кеш (см. ниже), который в дальнейшем будет использоваться для быстрого поиска.

* **`rebuild-cache`**
    * Форсирует перестройку кеша, по умолчанию сохраняемого в файле `~/.cache/emfind.json`. Обычно кеши перестраиваются автоматически при необходимости, однако если вы перемещаете данные торрента из одного каталога в другой, кеши нужно будет обновить вручную.


***
### Опции

{!_stdopts.md!}

* **`-v, --verbose`**
    * Включает отладочные сообщения, направляемые в stderr.


***
### Конфигурационные параметры

Общие параметры и способ настройки описаны на странице [config](config), здесь же приведены специфические параметры программы.

* **`emfind/cache_file=~/.cache/emfind.json`**
    * Кеш для `emfind orphans`, содержащий список файлов в раздачах и их метаданные.

* **`emfind/name_filter='*.torrent'`**
    * Шаблон, которому должны соответствовать файлы из каталога `core/torrents_dir`.


***
### Примеры использования

Найти все данные, незарегистрированные в клиенте:

```
$ emfind orphans
# I: Client rtorrent is ready
# I: Reading the cache from /home/mdevaev/.cache/emfind.json ...
# I: Fetching all hashes from client ...
# I: Validating the cache ...
# I: Removed 1 obsolete hashes from cache
# I: Loaded 555 torrents from /home/mdevaev/torrents/*.torrent
# I: Added 3 new hashes from client
# I: Writing the cache to /home/mdevaev/.cache/emfind.json ...
# I: Scanning directory /srv/storage/torrents ...
# I: Transposing the cache: by-hashes -> files ...
# I: Orhpaned files:
F /srv/storage/torrents/o/one_punch_man.torrent.data/[AniDub]_One-Punch_Man_[720p]_[JAM]/[AniDub]_One-Punch_Man_OVA_[720p_x264_AAC]_[JAM].mp4
F /srv/storage/torrents/r/real_drive__hdtvrip_720p.torrent.data/Real Drive/Real Drive - 10 (D-NTV 1280x720 x264 AAC) [AU-Raws].utf8.ass
F /srv/storage/torrents/r/real_drive__hdtvrip_720p.torrent.data/Real Drive/Real Drive - 12 (D-NTV 1280x720 x264 AAC) [AU-Raws].utf8.ass
F /srv/storage/torrents/r/real_drive__hdtvrip_720p.torrent.data/Real Drive/Real Drive - 20 (D-NTV 1280x720 x264 AAC) [AU-Raws].utf8.ass
F /srv/storage/torrents/r/real_drive__hdtvrip_720p.torrent.data/Real Drive/Real Drive - 20 (D-NTV 1280x720 x264 AAC) [Negi-Raws].utf8.ass
F /srv/storage/torrents/r/real_drive__hdtvrip_720p.torrent.data/Real Drive/Real Drive - 25 (D-NTV 1280x720 x264 AAC) [Negi-Raws].utf8.ass
F /srv/storage/torrents/s/serenity_comics.torrent.data/Serenity/readme
# I: Found 7 orphaned files = 311.7 MB
```
