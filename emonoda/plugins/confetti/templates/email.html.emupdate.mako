<%!
    from html import escape as esc
    from emonoda.tools import sorted_paths
    from emonoda.plugins.confetti import STATUSES
%>
% if len(results["affected"]) != 0:
    <h3>&bull; &bull; &bull; You have ${len(results["affected"])} changed torrents:</h3>
    <table cellspacing="0" cellpadding="0">
    % for (file_name, result) in results["affected"].items():
        <tr>
            <td width="20" align="center" valign="top">&bull;</td>
            <td align="left" valign="top">
                <b>${esc(file_name)}</b> (from <a href="${result.torrent.get_comment()}">${result.tracker.PLUGIN_NAMES[0]}</a>)
                <table cellspacing="0" cellpadding="0">
                % for (sign, color, field) in [ \
                    ("+", "green",  "added"), \
                    ("-", "red",    "removed"), \
                    ("~", "teal",   "modified"), \
                    ("?", "orange", "type_modified"), \
                ]:
                    % for item in sorted_paths(getattr(result.diff, field)):
                        <tr>
                            <td width="20" align="center" valign="top"><b><font color="${color}">${sign}</font></b></td>
                            <td align="left" valign="top">${item}</td>
                        </tr>
                    % endfor
                % endfor
                </table>
            </td>
        </tr>
    % endfor
    </table>
% endif
% for status in statuses:
    % if status != "affected" and len(results[status]) != 0:
        <br>
        <h3>&bull; &bull; &bull; ${STATUSES[status]} (${len(results[status])})</h3>
        <table cellspacing="0" cellpadding="0">
        % for (file_name, result) in results[status].items():
            <tr>
                <td width="20" align="center" valign="top">&bull;</td>
                <td align="left" valign="top">
                    % if status == "invalid":
                        <b>${esc(file_name)}</b>
                    % else:
                        <b>${esc(file_name)}</b> (from <a href="${result.torrent.get_comment()}">${esc(result.torrent.get_comment())}</a>)
                    % endif
                    % if status in ["tracker_error", "unhandled_error"]:
                        <table cellspacing="0" cellpadding="0">
                            <tr>
                                <td align="left" valign="top">${esc(result.err_name)}(${esc(result.err_msg)})</td>
                            </tr>
                        </table>
                    % endif
                </td>
            </tr>
        % endfor
        </table>
    % endif
% endfor
<br>
<h3>&bull; &bull; &bull; Extra summary:</h3>
<table>
% for (msg, field) in [ \
    ("Updated",          "affected"), \
    ("Passed",           "passed"), \
    ("Not in client",    "not_in_client"), \
    ("Unknown",          "unknown"), \
    ("Invalid torrents", "invalid"), \
    ("Tracker errors",   "tracker_error"), \
    ("Unhandled errors", "unhandled_error"), \
]:
    <tr>
        <td><b>${msg}:</b></td>
        <td>${len(results[field])}</td>
    </tr>
% endfor
</table>
