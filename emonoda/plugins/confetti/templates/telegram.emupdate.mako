<%!
    import html
    from emonoda.tools import sorted_paths
%>
<b>${status_msg}</b>: ${html.escape(file_name)}
% if status != "invalid":
<b>***</b> <a href="${result.torrent.get_comment()}">${html.escape(result.torrent.get_name())}</a>
    % if status == "affected":

        % for (sign, field) in [ \
            ("+", "added"), \
            ("-", "removed"), \
            ("~", "modified"), \
            ("?", "type_modified"), \
        ]:
            % for item in sorted_paths(getattr(result.diff, field)):
<b>${sign}</b> <i>${html.escape(item)}</i>
            % endfor
        % endfor
    % elif status == "tracker_error":
${html.escape(result.err_name)}(${html.escape(result.err_msg)})
    % endif
% endif
