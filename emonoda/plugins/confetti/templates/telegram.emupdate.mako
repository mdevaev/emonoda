<%!
    import html
    from emonoda.tools import sorted_paths
%>
Updated <b>${html.escape(file_name)}</b> (from <a href="${result.torrent.get_comment()}">${html.escape(result.torrent.get_comment())}</a>):

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
