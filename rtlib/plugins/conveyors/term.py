import operator

from ...optconf import Option

from ... import fmt

from . import BaseConveyor
from . import WithLogs


# =====
class Plugin(BaseConveyor, WithLogs):  # pylint: disable=too-many-instance-attributes
    def __init__(self, show_unknown, show_passed, show_diff, **kwargs):  # pylint: disable=super-init-not-called
        for parent in self.__class__.__bases__:
            parent.__init__(self, **kwargs)

        self._show_unknown = show_unknown
        self._show_passed = show_passed
        self._show_diff = show_diff

        self._current_count = 0
        self._current_file_name = None
        self._current_torrent = None

    @classmethod
    def get_name(cls):
        return "term"

    @classmethod
    def get_options(cls):
        return {
            "show_unknown": Option(default=False, help="Show the torrents with unknown tracker in the log"),
            "show_passed":  Option(default=False, help="Show the torrents without changes"),
            "show_diff":    Option(default=True, help="Show diff between old and updated torrent files"),
        }

    # ===

    def get_torrents(self):
        for (count, (file_name, torrent)) in enumerate(sorted(self._torrents.items(), key=operator.itemgetter(0))):
            self._current_count = count
            self._current_file_name = file_name
            self._current_torrent = torrent
            yield torrent

    def read_captcha(self, url):
        self._log_stderr.print("# {yellow}Enter the captcha{reset} from [{blue}%s{reset}]: " % (url), no_nl=True)
        return input()

    def print_summary(self):
        self._log_stderr.print("# " + ("-" * 10))
        self._log_stderr.print("# Invalid:       {}".format(self.invalid_count))
        self._log_stderr.print("# Not in client: {}".format(self.not_in_client_count))
        self._log_stderr.print("# Unknown:       {}".format(self.unknown_count))
        self._log_stderr.print("# Passed:        {}".format(self.passed_count))
        self._log_stderr.print("# Updated:       {}".format(self.updated_count))
        self._log_stderr.print("# Errors:        {}".format(self.error_count))
        self._log_stderr.print("# Exceptions:    {}".format(self.exception_count))

    # ===

    def mark_invalid(self):
        self._log_stdout.print(self._format_fail("red", "!", "INVALID_TORRENT"))
        self.invalid_count += 1

    def mark_not_in_client(self):
        self._log_stdout.print(self._format_fail("red", "!", "NOT_IN_CLIENT"))
        self.not_in_client_count += 1

    def mark_unknown(self):
        self._log_stdout.print(self._format_fail("yellow", " ", "UNKNOWN"), one_line=(not self._show_unknown))
        self.unknown_count += 1

    def mark_in_progress(self, fetcher):
        self._log_stdout.print(self._format_status("magenta", " ", fetcher), one_line=True)

    def mark_passed(self, fetcher):
        self._log_stdout.print(self._format_status("blue", " ", fetcher), one_line=(not self._show_passed))
        self.passed_count += 1

    def mark_updated(self, fetcher, diff):
        self._log_stdout.print(self._format_status("green", "+", fetcher))
        if self._show_diff:
            self._log_stdout.print(fmt.format_torrents_diff(diff, "\t"))
        self.updated_count += 1

    def mark_fetcher_error(self, fetcher, err):
        self._log_stdout.print(self._format_status("red", "-", fetcher) +
                               " :: {red}%s({reset}%s{red}){reset}" % (type(err).__name__, err))
        self.error_count += 1

    def mark_exception(self, fetcher):
        self._log_stdout.print(self._format_status("red", "-", fetcher))
        self._log_stdout.print(fmt.format_traceback("\t"))
        self.exception_count += 1

    # ===

    def _format_fail(self, color, sign, error):
        return "[{%s}%s{reset}] %s {%s}%s {cyan}%s{reset}" % (
            color, sign, self._format_progress(), color, error, self._current_file_name,
        )

    def _format_status(self, color, sign, fetcher):
        return "[{%s}%s{reset}] %s {%s}%s {cyan}%s{reset} -- %s" % (
            color, sign, self._format_progress(), color, fetcher.get_name(),
            self._current_file_name, (self._current_torrent.get_comment() or ""),
        )

    def _format_progress(self):
        return fmt.format_progress(self._current_count + 1, len(self._torrents))
