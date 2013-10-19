# -*- coding: utf-8 -*-


import os
import argparse
import ConfigParser

import fetcherlib
import fetchers
import clients

from ulib.validatorlib import notEmptyStrip
from ulib.validatorlib import ValidatorError
from ulib.validators.common import validStringList
from ulib.validators.common import validRange
from ulib.validators.common import validNumber
from ulib.validators.common import validBool
from ulib.validators.common import validEmpty
from ulib.validators.common import validMaybeEmpty
from ulib.validators.fs import validAccessiblePath


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
def __validMaybeEmptyPath(path) :
	return validMaybeEmpty(path, validAccessiblePath)

def __validMaybeEmptyMode(mode) :
	valid_mode = ( lambda arg : validNumber(( arg if isinstance(arg, int) else int(str(arg), 8) ), 0) )
	return validMaybeEmpty(mode, valid_mode)

def __validSetCustoms(pairs) :
	if isinstance(pairs, dict) :
		return pairs
	customs_dict = {}
	for pair in pairs :
		(key, value) = map(str.strip, (pair.split("=", 1)+[""])[:2])
		customs_dict[notEmptyStrip(key, "custom key")] = value
	return customs_dict

def __makeValidMaybeEmptyRange(valid_list) :
	valid_range = ( lambda arg : validRange(arg, valid_list) )
	return ( lambda arg : validMaybeEmpty(arg, valid_range) )

def __makeValidList(valid_list) :
	return ( lambda arg : [ validRange(item, valid_list) for item in validStringList(arg) ] )

def __makeValidNumber(*args_tuple) :
	return ( lambda arg : validNumber(arg, *args_tuple) )


###
def __makeOptions() :
	options_list = [ value for (key, value) in globals().iteritems() if key.startswith("OPTION_") ]
	all_options_dict = {}
	all_dests_dict = {}
	for option_tuple in options_list :
		(option, dest, default, validator) = option_tuple
		option_dict = {
			"option"    : option_tuple,
			"dest"      : dest,
			"default"   : default,
			"validator" : validator,
		}
		all_options_dict[option] = option_dict
		if not dest is None :
			all_dests_dict[dest] = option_dict
	return all_options_dict, all_dests_dict


###
OPTION_MKDIR_MODE        = ("mkdir-mode",        "mkdir_mode",             None,                                __validMaybeEmptyMode)
OPTION_DATA_DIR          = ("data-dir",          "data_dir_path",          None,                                __validMaybeEmptyPath)
OPTION_SOURCE_DIR        = ("source-dir",        "src_dir_path",           ".",                                 validAccessiblePath)
OPTION_BACKUP_DIR        = ("backup-dir",        "backup_dir_path",        None,                                __validMaybeEmptyPath)
OPTION_NAMES_FILTER      = ("names-filter",      "names_filter",           None,                                validEmpty)
OPTION_ONLY_FETCHERS     = ("only-fetchers",     "only_fetchers_list",     fetchers.FETCHERS_MAP.keys(),        __makeValidList(fetchers.FETCHERS_MAP.keys()))
OPTION_TIMEOUT           = ("timeout",           "socket_timeout",         DEFAULT_TIMEOUT,                     __makeValidNumber(0))
OPTION_LOGIN             = ("login",             None,                     fetcherlib.DEFAULT_LOGIN,            str)
OPTION_PASSWD            = ("passwd",            None,                     fetcherlib.DEFAULT_PASSWD,           str)
OPTION_URL_RETRIES       = ("url-retries",       "url_retries",            fetcherlib.DEFAULT_URL_RETRIES,      __makeValidNumber(0))
OPTION_URL_SLEEP_TIME    = ("url-sleep-time",    "url_sleep_time",         fetcherlib.DEFAULT_URL_SLEEP_TIME,   __makeValidNumber(0))
OPTION_PROXY_URL         = ("proxy-url",         "proxy_url",              fetcherlib.DEFAULT_PROXY_URL,        validEmpty)
OPTION_INTERACTIVE       = ("interactive",       "interactive_flag",       fetcherlib.DEFAULT_INTERACTIVE_FLAG, validBool)
OPTION_SKIP_UNKNOWN      = ("skip-unknown",      "skip_unknown_flag",      False,                               validBool)
OPTION_PASS_FAILED_LOGIN = ("pass-failed-login", "pass_failed_login_flag", False,                               validBool)
OPTION_SHOW_PASSED       = ("show-passed",       "show_passed_flag",       False,                               validBool)
OPTION_SHOW_DIFF         = ("show-diff",         "show_diff_flag",         False,                               validBool)
OPTION_CHECK_VERSIONS    = ("check-versions",    "check_versions_flag",    False,                               validBool)
OPTION_REAL_UPDATE       = ("real-update",       "real_update_flag",       False,                               validBool)
OPTION_CLIENT            = ("client",            "client_name",            None,                                __makeValidMaybeEmptyRange(clients.CLIENTS_MAP.keys()))
OPTION_CLIENT_URL        = ("client-url",        "client_url",             None,                                validEmpty)
OPTION_SAVE_CUSTOMS      = ("save-customs",      "save_customs_list",      (),                                  validStringList)
OPTION_SET_CUSTOMS       = ("set-customs",       "set_customs_dict",       {},                                  __validSetCustoms)
OPTION_NO_COLORS         = ("no-colors",         "no_colors_flag",         False,                               validBool)
OPTION_FORCE_COLORS      = ("force-colors",      "force_colors_flag",      False,                               validBool)

ARG_MKDIR_MODE           = (("-m", OPTION_MKDIR_MODE[0],),              OPTION_MKDIR_MODE,        { "action" : "store", "metavar" : "<mode>" })
ARG_DATA_DIR             = (("-a", OPTION_DATA_DIR[0],),                OPTION_DATA_DIR,          { "action" : "store", "metavar" : "<dir>" })
ARG_SOURCE_DIR           = (("-s", OPTION_SOURCE_DIR[0],),              OPTION_SOURCE_DIR,        { "action" : "store", "metavar" : "<dir>" })
ARG_BACKUP_DIR           = (("-b", OPTION_BACKUP_DIR[0],),              OPTION_BACKUP_DIR,        { "action" : "store", "metavar" : "<dir>" })
ARG_NAMES_FILTER         = (("-f", OPTION_NAMES_FILTER[0],),            OPTION_NAMES_FILTER,      { "action" : "store", "metavar" : "<substring>" })
ARG_ONLY_FETCHERS        = (("-o", OPTION_ONLY_FETCHERS[0],),           OPTION_ONLY_FETCHERS,     { "nargs"  : "+",     "metavar" : "<plugin>" })
ARG_TIMEOUT              = (("-t", OPTION_TIMEOUT[0],),                 OPTION_TIMEOUT,           { "action" : "store", "metavar" : "<seconds>" })
ARG_URL_RETRIES          = ((      OPTION_URL_RETRIES[0],),             OPTION_URL_RETRIES,       { "action" : "store", "metavar" : "<number>" })
ARG_URL_SLEEP_TIME       = ((      OPTION_URL_SLEEP_TIME[0],),          OPTION_URL_SLEEP_TIME,    { "action" : "store", "metavar" : "<seconds>" })
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

(ALL_OPTIONS_MAP, ALL_DESTS_MAP) = __makeOptions()


##### Public methods #####
def syncParsers(app_section, cli_options, config_dict, ignore_list = ()) :
	for (dest, option_dict) in ALL_DESTS_MAP.iteritems() :
		option = option_dict["option"]
		if option in ignore_list or not hasattr(cli_options, dest) :
			continue
		value = getCommonOption((SECTION_MAIN, app_section), option_dict["option"], config_dict, getattr(cli_options, dest))
		setattr(cli_options, dest, value)

def partialParser(argv_list, **kwargs_dict) :
	cli_parser = argparse.ArgumentParser(add_help=False)
	cli_parser.add_argument("-c", "--config", dest="config_file_path", default=os.path.expanduser(DEFAULT_CONFIG_PATH), metavar="<file>")
	(cli_options, remaining_list) = cli_parser.parse_known_args()
	config_dict = ( {} if cli_options.config_file_path is None else __readConfig(cli_options.config_file_path) )
	kwargs_dict.update({
			"formatter_class" : argparse.RawDescriptionHelpFormatter,
			"parents"         : [cli_parser],
		})
	new_parser = argparse.ArgumentParser(**kwargs_dict)
	return (new_parser, config_dict, remaining_list)

def addArguments(cli_parser, *args_tuple) :
	for arg_tuple in args_tuple :
		addArgument(cli_parser, arg_tuple)

def addArgument(cli_parser, arg_tuple) :
	options_list = [
		( option if option.startswith("-") else "--"+option )
		for option in arg_tuple[0]
	]
	kwargs_dict = arg_tuple[2]
	kwargs_dict.update({ "dest" : arg_tuple[1][1], "default" : None })
	cli_parser.add_argument(*options_list, **kwargs_dict)


###
def getOption(section, option_tuple, config_dict) :
	(option, _, default, validator) = option_tuple
	return __raiseIncorrectValue(option, validator, config_dict[section].get(option, default))

def getCommonOption(sections_list, option_tuple, config_dict, cli_value = None) :
	(option, _, default, validator) = option_tuple
	if cli_value is None :
		requests_list = [ (section, option) for section in sections_list ]
		value = __lastValue(config_dict, default, requests_list)
	else :
		value = cli_value
	return __raiseIncorrectValue(option, validator, value)


##### Private methods #####
def __readConfig(file_path) :
	parser = ConfigParser.ConfigParser()
	parser.read(file_path)
	config_dict = {}
	for section in parser.sections() :
		config_dict.setdefault(section, {})
		for option in parser.options(section) :
			validator = ALL_OPTIONS_MAP.get(option, {}).get("validator")
			if validator is None :
				raise ValidatorError("Unknown option: %s::%s" % (section, option))
			else :
				value = parser.get(section, option)
				value = __raiseIncorrectValue("%s::%s" % (section, option), validator, value)
				config_dict[section][option] = value
	return config_dict

def __lastValue(config_dict, first, requests_list) :
	assert len(requests_list) > 0
	last_value = first
	for (section, option) in requests_list :
		if config_dict.get(section, {}).has_key(option) :
			last_value = config_dict[section][option]
	return last_value

def __raiseIncorrectValue(option, validator, value) :
	try :
		return validator(value)
	except ValidatorError, err :
		raise ValidatorError("Incorrect value for option \"%s\": %s" % (option, err))

