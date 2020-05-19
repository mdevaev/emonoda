<%!
    from html import escape as esc
    from emonoda.tools import sorted_paths
%>
<b>${status_msg}</b>: ${esc(file_name)}<br/>
% if status != "invalid":
<b>***</b> <a href="${result.torrent.get_comment()}">${esc(result.torrent.get_name())}</a><br/>
    % if status == "affected":

        % for (sign, color, field) in [ \
            ("+", "green",  "added"), \
            ("-", "red",    "removed"), \
            ("~", "teal",   "modified"), \
            ("?", "orange", "type_modified"), \
        ]:
            % for item in sorted_paths(getattr(result.diff, field)):
<font color="${color}"><b>${sign}</b></font> <i>${esc(item)}</i><br/>
            % endfor
        % endfor
    % elif status in ["tracker_error", "unhandled_error"]:
<font color="red">${esc(result.err_name)}(${esc(result.err_msg)})</font>
    % endif
% endif
