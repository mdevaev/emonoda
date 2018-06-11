<%!
    from html import escape as esc
%>
% if status == "passed":
<b>${status_msg}</b>: ${esc(file_name)}
% elif status == "affected":
<font color="#00aa5d"><b>${status_msg}</b></font>: ${esc(file_name)}
% else:
<font color="#aa0000"><b>${status_msg}</b></font>: ${esc(file_name)}
% endif
% if status != "invalid":
<b>***</b> <a href="${result.torrent.get_comment()}">${esc(result.torrent.get_name())}</a>
% endif
