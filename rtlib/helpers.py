import operator

from . import tfile
from . import fmt


# =====
def load_torrents_from_dir(dir_path, name_filter, log):
    fan = fmt.make_fan()

    def load_torrent(path):
        log.print("# Caching {cyan}%s/{yellow}%s {magenta}%s{reset}" % (
                  dir_path, name_filter, next(fan)), one_line=True)
        return tfile.load_torrent_from_path(path)

    torrents = list(sorted(
        tfile.load_from_dir(dir_path, name_filter, as_abs=True, loader=load_torrent).items(),
        key=operator.itemgetter(0),
    ))

    log.print("# Cached {magenta}%d{reset} torrents from {cyan}%s/{yellow}%s{reset}" % (
              len(torrents), dir_path, name_filter))
    return torrents


def make_captcha_reader(log):
    def read_captcha(url):
        log.print("# {yellow}Enter the captcha{reset} from [{blue}%s{reset}]: " % (url), no_nl=True)
        return input()
    return read_captcha
