from . import tfile
from . import fmt


# =====
def load_torrents_from_dir(dir_path, name_filter, log):
    fan = fmt.make_fan()

    def load_torrent(path):
        log.print("# Caching {cyan}%s/{yellow}%s {magenta}%s{reset}" % (
                  dir_path, name_filter, next(fan)), one_line=True)
        return tfile.load_torrent_from_path(path)

    torrents = tfile.load_from_dir(dir_path, name_filter, as_abs=True, loader=load_torrent)

    log.print("# Cached {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}" % (
              len(torrents), dir_path, name_filter))
    return torrents
