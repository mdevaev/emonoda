import os

from ulib import optconf

from ulib.validatorlib import notEmptyStrip
from ulib.validators.common import validStringList
from ulib.validators.common import validRange
from ulib.validators.common import validNumber
from ulib.validators.common import validBool
from ulib.validators.common import validEmpty
from ulib.validators.common import validMaybeEmpty
from ulib.validators.fs import validAccessiblePath

from . import fetcherlib
from . import fetchers
from . import clients


##### Public constants #####
DEFAULT_CONFIG_PATH = "~/.config/rtlib.conf"
DEFAULT_TIMEOUT = 5


###
SECTION_MAIN = "main"
SECTION_RTFETCH = "rtfetch"
SECTION_RTFILE = "rtfile"
SECTION_RTDIFF = "rtdiff"
SECTION_RTLOAD = "rtload"


###
def _validMaybeEmptyPath(path) :
    return validMaybeEmpty(path, validAccessiblePath)

def _validFetchers(fetchers_list) :
    return [
        validRange(item, list(fetchers.FETCHERS_MAP.keys()))
        for item in filter(None, map(str.strip, validStringList(fetchers_list)))
    ]

def _validMaybeEmptyMode(mode) :
    valid_mode = ( lambda arg : validNumber(( arg if isinstance(arg, int) else int(str(arg), 8) ), 0) )
    return validMaybeEmpty(mode, valid_mode)

def _validSaveCustoms(keys_list) :
    return list(filter(None, map(str.strip, validStringList(keys_list))))

def _validSetCustoms(pairs_list) :
    if isinstance(pairs_list, dict) :
        return pairs_list
    customs_dict = {}
    for pair in filter(None, map(str.strip, pairs_list)) :
        (key, value) = map(str.strip, (pair.split("=", 1)+[""])[:2])
        customs_dict[notEmptyStrip(key, "custom key")] = value
    return customs_dict

def _makeValidMaybeEmptyRange(valid_list) :
    valid_range = ( lambda arg : validRange(arg, valid_list) )
    return ( lambda arg : validMaybeEmpty(arg, valid_range) )

def _makeValidNumber(*args_tuple) :
    return ( lambda arg : validNumber(arg, *args_tuple) )


###
OPTION_MKDIR_MODE        = ("mkdir-mode",        "mkdir_mode",             None,                                _validMaybeEmptyMode)
OPTION_PRE_MODE          = ("pre-mode",          "pre_mode",               None,                                _validMaybeEmptyMode)
OPTION_DATA_DIR          = ("data-dir",          "data_dir_path",          None,                                _validMaybeEmptyPath)
OPTION_SOURCE_DIR        = ("source-dir",        "src_dir_path",           ".",                                 validAccessiblePath)
OPTION_BACKUP_DIR        = ("backup-dir",        "backup_dir_path",        None,                                _validMaybeEmptyPath)
OPTION_BACKUP_SUFFIX     = ("backup-suffix",     "backup_suffix",          ".%Y.%m.%d-%H:%M:%S.bak",            str)
OPTION_NAMES_FILTER      = ("names-filter",      "names_filter",           None,                                validEmpty)
OPTION_ONLY_FETCHERS     = ("only-fetchers",     "only_fetchers_list",     list(fetchers.FETCHERS_MAP.keys()),  _validFetchers)
OPTION_EXCLUDE_FETCHERS  = ("exclude-fetchers",  "exclude_fetchers_list",  (),                                  _validFetchers)
OPTION_TIMEOUT           = ("timeout",           "timeout",                DEFAULT_TIMEOUT,                     _makeValidNumber(0))
OPTION_LOGIN             = ("login",             None,                     fetcherlib.DEFAULT_LOGIN,            str)
OPTION_PASSWD            = ("passwd",            None,                     fetcherlib.DEFAULT_PASSWD,           str)
OPTION_URL_RETRIES       = ("url-retries",       "url_retries",            fetcherlib.DEFAULT_URL_RETRIES,      _makeValidNumber(0))
OPTION_URL_SLEEP_TIME    = ("url-sleep-time",    "url_sleep_time",         fetcherlib.DEFAULT_URL_SLEEP_TIME,   _makeValidNumber(0))
OPTION_USER_AGENT        = ("user-agent",        "user_agent",             fetcherlib.DEFAULT_USER_AGENT,       validEmpty)
OPTION_CLIENT_AGENT      = ("client-agent",      "client_agent",           fetcherlib.DEFAULT_CLIENT_AGENT,     validEmpty)
OPTION_PROXY_URL         = ("proxy-url",         "proxy_url",              fetcherlib.DEFAULT_PROXY_URL,        validEmpty)
OPTION_INTERACTIVE       = ("interactive",       "interactive_flag",       fetcherlib.DEFAULT_INTERACTIVE_FLAG, validBool)
OPTION_SKIP_UNKNOWN      = ("skip-unknown",      "skip_unknown_flag",      False,                               validBool)
OPTION_PASS_FAILED_LOGIN = ("pass-failed-login", "pass_failed_login_flag", False,                               validBool)
OPTION_SHOW_PASSED       = ("show-passed",       "show_passed_flag",       False,                               validBool)
OPTION_SHOW_DIFF         = ("show-diff",         "show_diff_flag",         False,                               validBool)
OPTION_CHECK_VERSIONS    = ("check-versions",    "check_versions_flag",    False,                               validBool)
OPTION_REAL_UPDATE       = ("real-update",       "real_update_flag",       False,                               validBool)
OPTION_CLIENT            = ("client",            "client_name",            None,                                _makeValidMaybeEmptyRange(list(clients.CLIENTS_MAP.keys())))
OPTION_CLIENT_URL        = ("client-url",        "client_url",             None,                                validEmpty)
OPTION_SAVE_CUSTOMS      = ("save-customs",      "save_customs_list",      (),                                  _validSaveCustoms)
OPTION_SET_CUSTOMS       = ("set-customs",       "set_customs_dict",       {},                                  _validSetCustoms)
OPTION_NO_COLORS         = ("no-colors",         "no_colors_flag",         False,                               validBool)
OPTION_FORCE_COLORS      = ("force-colors",      "force_colors_flag",      False,                               validBool)

ARG_MKDIR_MODE           = (("-m", OPTION_MKDIR_MODE[0],),              OPTION_MKDIR_MODE,        { "action" : "store", "metavar" : "<mode>" })
ARG_PRE_MODE             = ((      OPTION_PRE_MODE[0],),                OPTION_PRE_MODE,          { "action" : "store", "metavar" : "<mode>" })
ARG_DATA_DIR             = (("-a", OPTION_DATA_DIR[0],),                OPTION_DATA_DIR,          { "action" : "store", "metavar" : "<dir>" })
ARG_SOURCE_DIR           = (("-s", OPTION_SOURCE_DIR[0],),              OPTION_SOURCE_DIR,        { "action" : "store", "metavar" : "<dir>" })
ARG_BACKUP_DIR           = (("-b", OPTION_BACKUP_DIR[0],),              OPTION_BACKUP_DIR,        { "action" : "store", "metavar" : "<dir>" })
ARG_BACKUP_SUFFIX        = ((      OPTION_BACKUP_SUFFIX[0],),           OPTION_BACKUP_SUFFIX,     { "action" : "store", "metavar" : "<strftime>" })
ARG_NAMES_FILTER         = (("-f", OPTION_NAMES_FILTER[0],),            OPTION_NAMES_FILTER,      { "action" : "store", "metavar" : "<substring>" })
ARG_ONLY_FETCHERS        = (("-o", OPTION_ONLY_FETCHERS[0],),           OPTION_ONLY_FETCHERS,     { "nargs"  : "+",     "metavar" : "<plugin>" })
ARG_EXCLUDE_FETCHERS     = (("-x", OPTION_EXCLUDE_FETCHERS[0],),        OPTION_EXCLUDE_FETCHERS,  { "nargs"  : "+",     "metavar" : "<plugin>" })
ARG_TIMEOUT              = (("-t", OPTION_TIMEOUT[0],),                 OPTION_TIMEOUT,           { "action" : "store", "metavar" : "<seconds>" })
ARG_URL_RETRIES          = ((      OPTION_URL_RETRIES[0],),             OPTION_URL_RETRIES,       { "action" : "store", "metavar" : "<number>" })
ARG_URL_SLEEP_TIME       = ((      OPTION_URL_SLEEP_TIME[0],),          OPTION_URL_SLEEP_TIME,    { "action" : "store", "metavar" : "<seconds>" })
ARG_USER_AGENT           = ((      OPTION_USER_AGENT[0],),              OPTION_USER_AGENT,        { "action" : "store", "metavar" : "<string>" })
ARG_CLIENT_AGENT         = ((      OPTION_CLIENT_AGENT[0],),            OPTION_CLIENT_AGENT,      { "action" : "store", "metavar" : "<string>" })
ARG_PROXY_URL            = ((      OPTION_PROXY_URL[0],),               OPTION_PROXY_URL,         { "action" : "store", "metavar" : "<url>" })
ARG_INTERACTIVE          = (("-i", OPTION_INTERACTIVE[0],),             OPTION_INTERACTIVE,       { "action" : "store_true" })
ARG_NO_INTERACTIVE       = ((      "no-"+OPTION_INTERACTIVE[0],),       OPTION_INTERACTIVE,       { "action" : "store_false" })
ARG_SKIP_UNKNOWN         = (("-u", OPTION_SKIP_UNKNOWN[0],),            OPTION_SKIP_UNKNOWN,      { "action" : "store_true" })
ARG_NO_SKIP_UNKNOWN      = ((      "no-"+OPTION_SKIP_UNKNOWN[0],),      OPTION_SKIP_UNKNOWN,      { "action" : "store_false" })
ARG_PASS_FAILED_LOGIN    = (("-l", OPTION_PASS_FAILED_LOGIN[0],),       OPTION_PASS_FAILED_LOGIN, { "action" : "store_true" })
ARG_NO_PASS_FAILED_LOGIN = ((      "no-"+OPTION_PASS_FAILED_LOGIN[0],), OPTION_PASS_FAILED_LOGIN, { "action" : "store_false" })
ARG_SHOW_PASSED          = (("-p", OPTION_SHOW_PASSED[0],),             OPTION_SHOW_PASSED,       { "action" : "store_true" })
ARG_NO_SHOW_PASSED       = ((      "no-"+OPTION_SHOW_PASSED[0],),       OPTION_SHOW_PASSED,       { "action" : "store_false" })
ARG_SHOW_DIFF            = (("-d", OPTION_SHOW_DIFF[0],),               OPTION_SHOW_DIFF,         { "action" : "store_true" })
ARG_NO_SHOW_DIFF         = ((      "no-"+OPTION_SHOW_DIFF[0],),         OPTION_SHOW_DIFF,         { "action" : "store_false" })
ARG_CHECK_VERSIONS       = (("-k", OPTION_CHECK_VERSIONS[0],),          OPTION_CHECK_VERSIONS,    { "action" : "store_true" })
ARG_NO_CHECK_VERSIONS    = ((      "no-"+OPTION_CHECK_VERSIONS[0],),    OPTION_CHECK_VERSIONS,    { "action" : "store_false" })
ARG_REAL_UPDATE          = (("-e", OPTION_REAL_UPDATE[0],),             OPTION_REAL_UPDATE,       { "action" : "store_true" })
ARG_NO_REAL_UPDATE       = ((      "no-"+OPTION_REAL_UPDATE[0],),       OPTION_REAL_UPDATE,       { "action" : "store_false" })
ARG_CLIENT               = ((      OPTION_CLIENT[0],),                  OPTION_CLIENT,            { "action" : "store", "metavar" : "<plugin>" })
ARG_CLIENT_URL           = ((      OPTION_CLIENT_URL[0],),              OPTION_CLIENT_URL,        { "action" : "store", "metavar" : "<url>" })
ARG_SAVE_CUSTOMS         = ((      OPTION_SAVE_CUSTOMS[0],),            OPTION_SAVE_CUSTOMS,      { "nargs"  : "+",     "metavar" : "<key>" })
ARG_SET_CUSTOMS          = ((      OPTION_SET_CUSTOMS[0],),             OPTION_SET_CUSTOMS,       { "nargs"  : "+",     "metavar" : "<key(=value)>" })
ARG_NO_COLORS            = ((      OPTION_NO_COLORS[0],),               OPTION_NO_COLORS,         { "action" : "store_true" })
ARG_USE_COLORS           = ((      "use-colors",),                      OPTION_NO_COLORS,         { "action" : "store_false" })
ARG_FORCE_COLORS         = ((      OPTION_FORCE_COLORS[0],),            OPTION_FORCE_COLORS,      { "action" : "store_true" })
ARG_NO_FORCE_COLORS      = ((      "no-"+OPTION_FORCE_COLORS[0],),      OPTION_FORCE_COLORS,      { "action" : "store_false" })


##### Public methods #####
def makeParser(**kwargs_dict) :
    return optconf.OptionsConfig(
        [ value for (key, value) in globals().items() if key.startswith("OPTION_") ],
        os.path.expanduser(DEFAULT_CONFIG_PATH),
        **kwargs_dict
    )

