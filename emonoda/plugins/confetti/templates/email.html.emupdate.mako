<%!
    from emonoda.tools import sorted_paths
%>
<h3>&bull; &bull; &bull; You have ${len(results["affected"])} new torrents:</h3>
<table cellspacing="0" cellpadding="0">
% for (file_name, result) in results["affected"].items():
    <tr>
        <td width="20" align="center" valign="top">&bull;</td>
        <td align="left" valign="top">
            <b>${file_name}</b> (from <a href="${result["torrent"].get_comment()}">${result["tracker"].PLUGIN_NAME}</a>)
            <table cellspacing="0" cellpadding="0">
            % for (sign, color, field) in ( \
                ("+", "green",  "added"), \
                ("-", "red",    "removed"), \
                ("~", "teal",   "modified"), \
                ("?", "orange", "type_modified"), \
            ):
                % for item in sorted_paths(result["diff"][field]):
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
<br>
<h3>&bull; &bull; &bull; Extra summary:</h3>
<table>
% for (msg, field) in ( \
    ("Updated",          "affected"), \
    ("Passed",           "passed"), \
    ("Not in client",    "not_in_client"), \
    ("Unknown",          "unknown"), \
    ("Invalid torrents", "invalid"), \
    ("Tracker errors",   "tracker_error"), \
    ("Unhandled errors", "unhandled_error"), \
):
    <tr>
        <td><b>${msg}:</b></td>
        <td>${len(results[field])}</td>
    </tr>
% endfor
</table>
