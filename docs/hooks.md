В состав **Emonoda** входят несколько полезных скриптов, которые могут использоваться отдельно от нее и не требуют ни ее настроек, ни библиотек. Вызываются они через `python -m`, например так:

```
$ python -m emonoda.apps.hooks.rtorrent.manage_trackers --help
```


***
### emonoda.apps.hooks.rtorrent.manage_trackers

Это костылик для группового управления трекерами в rTorrent. Он позволяет включать и отключать трекеры одновременно для всех раздач. Он подключается к клиенту, выгружает список раздач, а затем производит над их трекерами необходимые операции. Был написан, чтобы отключить использование ретрекеров, которых часто нет в локальных сетях, а rTorrent ругается на то, что не может зарезольвить их хостнеймы или получить из них данные.


#### Опции

* **`--enable <s1 ...>`**
    * Если что-то из указанных подстрок входит в имя трекера на раздаче - включить этот трекер.

* **`--disable <s1 ...>`**
    * Работает по той же логике, что и `--enable`, но отключает совпавшие трекеры.

* **`-t, --timeout <number>`**
    * Таймаут на все сетевые операции, по умолчанию - `5` секунд.

* **`--client-url <url>`**
    * URL для подключения к XMLRPC клиента, по умолчанию - `http://localhost/RPC2`.


#### Примеры использования

Включить трекеры на домене `rutracker.org` и отключить остальное:

```
$ python -m emonoda.apps.hooks.rtorrent.manage_trackers --enable rutracker.org --disable rutracker.net retracker.local
```


***
### emonoda.apps.hooks.rtorrent.collectd_stat

Это специальный скрипт для [Collectd](https://collectd.org), собирающий статистику с rTorrent. Он использует [текстовый протокол](https://collectd.org/wiki/index.php/Plain_text_protocol) для сброса этой информации в плагин [Exec](https://collectd.org/wiki/index.php/Plugin:Exec). По умолчанию считываются только метрики загрузки и отдачи, лимиты на скорость, а так же объем скачанных и отданных данных. Названия метрик говорят сами за себя.


#### Опции

* **`-t, --timeout <number>`**
    * Таймаут на все сетевые операции, по умолчанию - `5` секунд.
* **`--client-url <url>`**
    * URL для подключения к XMLRPC клиента, по умолчанию - `http://localhost/RPC2`.
* **`--with-dht`**
    * Добавляет метрики для DHT.
* **`--with-summary`**
    * Добавляет метрики с общим количеством торрентов, с активной отдачей, загрузкой и с ошибками.
* **`-n, --host <hostname>`**
    * Хостнейм в идентификаторах всех метрик. По умолчанию - `localhost` или содержимое переменной окружения `COLLECTD_HOSTNAME`.
* **`-i, --interval <number>`**
    * Скрипт запускает внутри себя цикл получения новых метрик с указанной паузой между итерациями. По умолчанию - `60` секунд или содержимое переменной окружения `COLLECTD_INTERVAL`.


#### Примеры использования

Для включения плагина пропишите в `/etc/collectd.conf` что-то типа этого:

```
LoadPLugin exec
<Plugin exec>
    Exec "data" "python" "-m" "emonoda.apps.hooks.rtorrent.collectd_stat" "--client-url=http://localhost/RPC2" "--with-summary"
</Plugin>
```

Скрипт также можно запустить из консоли и посмотреть, какие метрики и как он выводит:

```
$ python -m emonoda.apps.hooks.rtorrent.collectd_stat --with-dht --with-summary
PUTVAL localhost/rtorrent/gauge-dn_rate interval=60 N:22847
PUTVAL localhost/rtorrent/gauge-dn_rate_limit interval=60 N:0
PUTVAL localhost/rtorrent/bytes-dn_total interval=60 N:71241345665
PUTVAL localhost/rtorrent/gauge-up_rate interval=60 N:11170199
PUTVAL localhost/rtorrent/gauge-up_rate_limit interval=60 N:0
PUTVAL localhost/rtorrent/bytes-up_total interval=60 N:4343293548954
PUTVAL localhost/rtorrent/gauge-dht_active interval=60 N:1
PUTVAL localhost/rtorrent/count-dht_nodes interval=60 N:191
PUTVAL localhost/rtorrent/count-dht_cycle interval=60 N:434
PUTVAL localhost/rtorrent/count-dht_torrents interval=60 N:0
PUTVAL localhost/rtorrent/count-dht_buckets interval=60 N:25
PUTVAL localhost/rtorrent/count-dht_replies_received interval=60 N:8708162
PUTVAL localhost/rtorrent/count-dht_peers interval=60 N:0
PUTVAL localhost/rtorrent/count-dht_peers_max interval=60 N:0
PUTVAL localhost/rtorrent/count-dht_errors_caught interval=60 N:2054
PUTVAL localhost/rtorrent/count-dht_errors_received interval=60 N:775079
PUTVAL localhost/rtorrent/count-dht_queries_sent interval=60 N:17309084
PUTVAL localhost/rtorrent/count-dht_queries_received interval=60 N:27524
PUTVAL localhost/rtorrent/bytes-dht_bytes_written interval=60 N:1809635518
PUTVAL localhost/rtorrent/bytes-dht_bytes_read interval=60 N:2285090405
PUTVAL localhost/rtorrent/count-summary_total interval=60 N:546
PUTVAL localhost/rtorrent/count-summary_dn interval=60 N:0
PUTVAL localhost/rtorrent/count-summary_up interval=60 N:100
PUTVAL localhost/rtorrent/count-summary_errors interval=60 N:219
```
