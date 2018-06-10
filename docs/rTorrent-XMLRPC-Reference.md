### Introduction

Draft reference for XML-RPC commands for rTorrent.

!!! info
    I've picked up this document from [gi-torrent wiki](https://code.google.com/p/gi-torrent).
    Copyright &copy; Hans.Hasert@gmail.com


***
### Details


#### system.listMethods

Return an array of all available XML-RPC methods on the server.


#### system.methodSignature

Given the name of a method, return an array of legal signatures. Each signature is an array of strings.  The first item of each signature is the return type, and any others items are parameter types.


#### system.methodHelp

Given the name of a method, return a help string.


#### system.multicall

Process an array of calls, and return an array of results.  Calls should be structs of the form `{'methodName': string, 'params': array}`. Each result will either be a single-item array containg the result value, or a struct of the form `{'faultCode': int, 'faultString': string}`.  This is useful when you need to make lots of small calls without lots of round trips. See [rTorrent-system_multicall](rTorrent-system_multicall) for syntax.


#### system.shutdown

Shut down the server. Return code is always zero.


***
### Managing Torrents

The commands that act on a torrent are prefixed with `d.`. They can be used separately (with the `hash` as the parameter that distinguishes the specific torrent) or together by using `d.multicall`.


#### d.multicall

Process an array of calls, and return an array of results. This is specific for a torrent listing, where the following arguments can be used to acquire information. The first argument is the type of view (f.i. `main`, `started`, `stopped`, `hashing`, `seeding`) that you want to get returned. The arguments can be used on their own as well, with the 'hash' as the parameter to distinguish the torrents. Whenever in a multicall, the char `=` is added at the end.

```
d.add_peer
d.check_hash               Initiate a hash check
d.close                    Stop the torrent
d.create_link
d.delete_link
d.delete_tied
d.erase                    Erase the torrent from the list
d.get_base_filename
d.get_base_path
d.get_bitfield
d.get_bytes_done
d.get_chunk_size           Get the size of a block of data (chunk)
d.get_chunks_hashed
d.get_complete
d.get_completed_bytes
d.get_completed_chunks
d.get_connection_current
d.get_connection_leech
d.get_connection_seed
d.get_creation_date        Get the date the torrent was created
d.get_custom1
d.get_custom2
d.get_custom3
d.get_custom4
d.get_custom5
d.get_custom_throw
d.get_directory
d.get_directory_base
d.get_down_rate             Get the speed in bytes/sec in which the torrent is downloading
d.get_down_total
d.get_free_diskspace
d.get_hash                  Always query the hash, since it is the index for other calls.
d.get_hashing
d.get_hashing_failed
d.get_ignore_commands
d.get_left_bytes
d.get_loaded_file
d.get_local_id
d.get_local_id_html
d.get_max_file_size
d.get_max_size_pex
d.get_message
d.get_mode
d.get_name                  The name of the torrent.
d.get_peer_exchange
d.get_peers_accounted       The number of leechers
d.get_peers_complete        The number of complete peers = seeders
d.get_peers_connected
d.get_peers_max
d.get_peers_min
d.get_peers_not_connected   Get the peers rtorrent sees but is not connected to
d.get_priority              Get the priority (0=off, 1=low, 2=normal, 3=high)
d.get_priority_str          Get the priority as a string (Off, Low, Normal, High)
d.get_ratio                 Get the ratio (upload divided by download)
d.get_size_bytes            Get the torrent size in bytes
d.get_size_chunks           Get the size of the torrent in chunks
d.get_size_files
d.get_size_pex
d.get_skip_rate
d.get_skip_total
d.get_state
d.get_state_changed
d.get_state_counter
d.get_throttle_name
d.get_tied_to_file
d.get_tracker_focus
d.get_tracker_numwant
d.get_tracker_size
d.get_up_rate              Get the speed in bytes/sec in which the torrent is uploading
d.get_up_total
d.get_uploads_max
d.initialize_logs
d.is_active                Get the active state (0=inactive, 1=active)
d.is_hash_checked
d.is_hash_checking         Get the hash state (0=not hash checking, 1=hash checking)
d.is_multi_file
d.is_open                  Get the state of the torrent (0=closed, 1=open)
d.is_pex_active
d.is_private               Get the privacy of the torrent (0=public, 1=private)
d.open
d.pause
d.resume
d.save_session
d.set_connection_current
d.set_custom1
d.set_custom2
d.set_custom3
d.set_custom4
d.set_custom5
d.set_directory
d.set_directory_base
d.set_hashing_failed
d.set_ignore_commands
d.set_max_file_size
d.set_message
d.set_peer_exchange
d.set_peers_max
d.set_peers_min
d.set_priority              Set the priority (0 = off (do not allocate up/down slots), 1=low, 2=normal, 3=high)
d.set_throttle_name
d.set_tied_to_file
d.set_tracker_numwant
d.set_uploads_max
d.start                     Start the torrent
d.stop                      Stop the torrent
d.try_close
d.try_start
d.try_stop
d.update_priorities         Update the torrent after changes to file priorities
d.views
d.views.has
d.views.push_back
d.views.push_back_unique
d.views.remove
```


***
### Managing Files

The commands that act on a torrent are prefixed with `f.`. They can be used separately (with the 'hash and file number' as the parameter that distinguishes the specific torrent) or together by using `f.multicall`.


#### f.multicall

Process an array of calls, and return an array of results. This is specific for a file listing, where the following arguments can be used to acquire information. The first argument is the hash that you got from the previous torrent listing. Whenever in a multicall, the char '=' is added at the end of the individual commands.

The arguments can be used on their own as well, with the 'hash' as the parameter to distinguish the torrents and the file number to distinguish individual files. There are multiple ways to address a file, but for me the hash:f# method was the only working solution (see [rTorrent XML-RPC guide](http://libtorrent.rakshasa.no/wiki/RTorrentXMLRPCGuide))

```
'f.get_completed_chunks'       Get the chunks that already downloaded
'f.get_frozen_path'
'f.get_last_touched'           Last time the file was touched in microseconds since 1970
'f.get_match_depth_next'
'f.get_match_depth_prev'
'f.get_offset'
'f.get_path'                   Get the path of the file
'f.get_path_components'
'f.get_path_depth'
'f.get_priority'               Get the priority (0=do not download, 1=normal, 2=high)
'f.get_range_first'            Get the chunk range start
'f.get_range_second'           Get the chunk range end
'f.get_size_bytes'             Get the size of the file in bytes
'f.get_size_chunks'            Get the size of the file in chunks
'f.is_create_queued'
'f.is_created'
'f.is_open'                    Get the state of the file (0=closed, 1=open)
'f.is_resize_queued'
'f.set_create_queued'
'f.set_priority'               Set the priority for the file (0=do not download, 1=normal, 2=high)
'f.set_resize_queued'
'f.unset_create_queued'
'f.unset_resize_queued'
```


***
### Managing Peers

The commands that act on a peer are prefixed with 'p.'. They can be used separately (with the 'hash' as the parameter that distinguishes the specific torrent) or together by using p.multicall.


#### p.multicall

Process an array of calls, and return an array of results. This is specific for a peer listing, where the following arguments can be used to acquire information. The first argument is the hash that you got from the previous torrent listing. Whenever in a multicall, the char '=' is added at the end of the individual commands.

The arguments can be used on their own as well, with the 'hash' as the parameter to distinguish the torrents.

```
'p.get_address'             Get the peer ip address
'p.get_client_version'      Get the client version
'p.get_completed_percent'   Get the download state of the peer
'p.get_down_rate'           Get the speed rTorrent is downloading for this peer
'p.get_down_total'          Get the total bytes dowloaded from the peer
'p.get_id'
'p.get_id_html'
'p.get_options_str'
'p.get_peer_rate'           Get the total speed of the peer as reported by the peer
'p.get_peer_total'          Get the total bytes of the peer as reported by the peer
'p.get_port'                Get the port on which the peer is reached
'p.get_up_rate'             Get the speed rTorrent is uploading to this peer
'p.get_up_total'            Get the total bytes rTorrent uploaded to this peer
'p.is_encrypted'            Get the encryption state (0=not, 1=encrypted)
'p.is_incoming'             Get the directional state (0=outgoing, 1=incomming)
'p.is_obfuscated'           Is the peer obfuscated (0=no, 1=yes)
'p.is_snubbed'              Is the peer snubbed (0=no, 1=yes)
```


***
### Managing Trackers

The commands that act on a tracker are prefixed with 't.'. They can be used separately (with the 'hash' as the parameter that distinguishes the specific torrent) or together by using t.multicall.


#### t.multicall

Process an array of calls, and return an array of results. This is specific for a tracker listing, where the following arguments can be used to acquire information. The first argument is the hash that you got from the previous torrent listing. Whenever in a multicall, the char '=' is added at the end of the individual commands.

The arguments can be used on their own as well, with the 'hash' as the parameter to distinguish the torrents.

```
't.get_group'
't.get_id'
't.get_min_interval'
't.get_normal_interval'
't.get_scrape_complete'       Get the complete peers registered on the tracker
't.get_scrape_downloaded'
't.get_scrape_incomplete'     Get the incomplete peers registered on the tracker
't.get_scrape_time_last'
't.get_type'                  Get the tracker type (1=http, 2=udp, 3=dht)
't.get_url'                   Get the url for the tracker
't.is_enabled'                Get the status of the tracker (0=disabled, 1=enabled)
't.is_open'                   Get the status of the tracker (0=closed, 1=open)
't.set_enabled'               Enable the tracker
```

!!! info "Note"
    rTorrent does not support explicit scrape, so the scrape values might be '0'.


***
### dht\_statistics

Delivers statistics on the dht component. Data is returned in the following structure :

```xml
<methodResponse>
 <params>
  <param>
   <value>
    <struct>
      <member>
       <name/>
       <value><i8/></value>
      </member>
      <member>
       <name/>
       <value><string/>
      </member>
     </struct>
    </value>
  </param>
 </params>
</methodResponse>
```
Parameters returned are :
```
active                      0 = inactive, 1 = active
buckets
bytes_read
bytes_written
cycle
dht                         string; reflects setting in .rtorrentrc
nodes
peers                       peers tracked by dht
peers_max                   the number of peers in the largest torrent for which DHT acts
                            as tracker
queries_received
queries_sent
replies_received
torrents
```


***
### To functions

```
to_* functions operate on another command, the following operate on a unix timestamp :

'to_date'                   convert the unix timestamp to a date string
'to_elapsed_time'
'to_gm_date'                convert the unix timestamp to a GM date string
'to_gm_time'                convert the unix timestamp to a GM time string
'to_time'                   convert the unix timestamp to a time string
'to_throttle'

Syntax is 'to_*=$.....'. Example : 'to_date=$d.get_creation_date'.

'to_kb'                     convert to Kb
'to_mb'                     convert to Mb
'to_xb'
```


***
### Loading Torrents

The URL for a restricted site is `http://userid:password@Torrent.location.org.`

```
'load'                   Load/download a torrent URL/file
'load_raw'               Load a torrent file content
'load_raw_start'         Load a torrent file content and start it
'load_raw_verbose'       Load a torrent file content and supply verbose info
'load_start'             Load/download a torrent URL/file and start it
'load_start_verbose'     Load/download a torrent URL/file, start it and supply verbose info
'load_verbose'           Load/download a torrent URL/file and supply verbose info
```


***
### Other Commands

```
'call_download'
'cat'                    Used to convert to a string, cat=$......
'close_low_diskspace'
'close_on_ratio'
'close_untied'
'create_link'
'delete_link'
'dht'
'dht_add_node'
'download_list'
'enable_trackers'
'encoding_list'
'encryption'
'execute'
'execute_capture'
'execute_capture_nothrow'
'execute_log'
'execute_nothrow'
'execute_raw'
'execute_raw_nothrow'
'event.download.closed'
'event.download.erased'
'event.download.finished'
'event.download.hash_done'
'event.download.hash_queued'
'event.download.hash_removed'
'event.download.inserted'
'event.download.inserted_new'
'event.download.inserted_session'
'event.download.opened'
'event.download.paused'
'event.download.resumed'
'false'
'fi.get_filename_last'
'fi.is_file'
'get_bind'
'get_check_hash'
'get_connection_leech'
'get_connection_seed'
'get_dht_port'              Get the port configured for Dht
'get_directory'
'get_down_rate'             Get the overall download speed in bytes/sec
'get_down_total'
'get_download_rate'         Get the max download speed in bytes/sec
'get_handshake_log'
'get_hash_interval'
'get_hash_max_tries'
'get_hash_read_ahead'
'get_http_cacert'
'get_http_capath'
'get_http_proxy'
'get_ip'
'get_key_layout'
'get_max_downloads_div'
'get_max_downloads_global'
'get_max_file_size'
'get_max_memory_usage'
'get_max_open_files'
'get_max_open_http'
'get_max_open_sockets'
'get_max_peers'
'get_max_peers_seed'
'get_max_uploads'
'get_max_uploads_div'
'get_max_uploads_global'
'get_memory_usage'
'get_min_peers'
'get_min_peers_seed'
'get_name'
'get_peer_exchange'
'get_port_open'
'get_port_random'
'get_port_range'              Get the configured port range
'get_preload_min_size'
'get_preload_required_rate'
'get_preload_type'
'get_proxy_address'
'get_receive_buffer_size'
'get_safe_free_diskspace'
'get_safe_sync'
'get_scgi_dont_route'
'get_send_buffer_size'
'get_session'
'get_session_lock'
'get_session_on_completion'
'get_split_file_size'
'get_split_suffix'
'get_stats_not_preloaded'
'get_stats_preloaded'
'get_throttle_down_max'
'get_throttle_down_rate'
'get_throttle_up_max'
'get_throttle_up_rate'
'get_timeout_safe_sync'
'get_timeout_sync'
'get_tracker_dump'
'get_tracker_numwant'
'get_up_rate'                   Get the overall upload speed in bytes/sec
'get_up_total'
'get_upload_rate'               Get the max upload speed in bytes/sec
'get_use_udp_trackers'
'get_xmlrpc_size_limit'
'greater'
'group.insert'
'group.insert_persistent_view'
'group.seeding.ratio.command'
'group.seeding.ratio.disable'
'group.seeding.ratio.enable'
'group.seeding.ratio.max'
'group.seeding.ratio.max.set'
'group.seeding.ratio.min'
'group.seeding.ratio.min.set'
'group.seeding.ratio.upload'
'group.seeding.ratio.upload.set'
'group.seeding.view'
'group.seeding.view.set'
'if'
'import'
'less'
'load'
'load_raw'
'load_raw_start'
'load_raw_verbose'
'load_start'
'load_start_verbose'
'load_verbose'
'not'
'on_close'
'on_erase'
'on_finished'
'on_hash_queued'
'on_hash_removed'
'on_insert'
'on_open'
'on_ratio'
'on_start'
'on_stop'
'or'
'print'
'ratio.disable'
'ratio.enable'
'ratio.max'
'ratio.max.set'
'ratio.min'
'ratio.min.set'
'ratio.upload'
'ratio.upload.set'
'remove_untied'
'scgi_local'
'scgi_port'
'schedule'
'schedule_remove'
'scheduler.max_active'
'scheduler.max_active.set'
'scheduler.simple.added'
'scheduler.simple.removed'
'scheduler.simple.update'
'session_save'
'set_bind'
'set_check_hash'
'set_connection_leech'
'set_connection_seed'
'set_dht_port'
'set_dht_throttle'
'set_directory'
'set_download_rate'
'set_handshake_log'
'set_hash_interval'
'set_hash_max_tries'
'set_hash_read_ahead'
'set_http_cacert'
'set_http_capath'
'set_http_proxy'
'set_ip'
'set_key_layout'
'set_max_downloads_div'
'set_max_downloads_global'
'set_max_file_size'
'set_max_memory_usage'
'set_max_open_files'
'set_max_open_http'
'set_max_open_sockets'
'set_max_peers'
'set_max_peers_seed'
'set_max_uploads'
'set_max_uploads_div'
'set_max_uploads_global'
'set_min_peers'
'set_min_peers_seed'
'set_name'
'set_peer_exchange'
'set_port_open'
'set_port_random'
'set_port_range'
'set_preload_min_size'
'set_preload_required_rate'
'set_preload_type'
'set_proxy_address'
'set_receive_buffer_size'
'set_safe_sync'
'set_scgi_dont_route'
'set_send_buffer_size'
'set_session'
'set_session_lock'
'set_session_on_completion'
'set_split_file_size'
'set_split_suffix'
'set_timeout_safe_sync'
'set_timeout_sync'
'set_tracker_dump'
'set_tracker_numwant'
'set_upload_rate'
'set_use_udp_trackers'
'set_xmlrpc_size_limit'
'start_tied'
'stop_on_ratio'
'stop_untied'
'system.client_version'
'system.file_allocate'
'system.file_allocate.set'
'system.file_status_cache.prune'
'system.file_status_cache.size'
'system.get_cwd'
'system.hostname'
'system.library_version'
'system.method.erase'
'system.method.get'
'system.method.has_key'
'system.method.insert'
'system.method.list_keys'
'system.method.set'
'system.method.set_key'
'system.pid'
'system.set_cwd'
'system.set_umask'
'system.time'
'system.time_seconds'
'system.time_usec'
'test.method.simple'
'throttle_down'
'throttle_ip'
'throttle_up'
'tos'
'try_import'
'ui.current_view.set'
'ui.unfocus_download'
'view.event_added'
'view.event_removed'
'view.filter_download'
'view.persistent'
'view.set_not_visible'
'view.set_visible'
'view.size'
'view.size_not_visible'
'view_add'
'view_filter'
'view_filter_on'
'view_list'
'view_set'
'view_sort'
'view_sort_current'
'view_sort_new'
'xmlrpc_dialect'
```
