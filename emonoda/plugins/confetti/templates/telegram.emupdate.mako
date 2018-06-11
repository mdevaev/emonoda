<%!
    from html import escape as esc
    from emonoda.tools import sorted_paths
%>
<b>${status_msg}</b>: ${esc(file_name)}
% if status != "invalid":
<b>***</b> <a href="${result.torrent.get_comment()}">${esc(result.torrent.get_name())}</a>
    % if status == "affected":

        % for (sign, field) in [ \
            ("+", "added"), \
            ("-", "removed"), \
            ("~", "modified"), \
            ("?", "type_modified"), \
        ]:
            % for item in sorted_paths(getattr(result.diff, field)):
<b>${sign}</b> <i>${esc(item)}</i>
            % endfor
        % endfor
    % elif status == "tracker_error":
${esc(result.err_name)}(${esc(result.err_msg)})
    % endif
% endif
