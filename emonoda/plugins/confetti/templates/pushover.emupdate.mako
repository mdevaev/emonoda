<%!
    from html import escape as esc
%>
% if status == "affected":
<font color="#00aa5d"><b>${status_msg}</b></font>: ${esc(file_name)}
% else:
<font color="#aa0000"><b>${status_msg}</b></font>: ${esc(file_name)}
% endif
% if status != "invalid":
<b>***</b> <a href="${result.torrent.get_comment()}">${esc(result.torrent.get_name())}</a>
    % if status == "tracker_error":
${esc(result.err_name)}(${esc(result.err_msg)})
    % endif
% endif
