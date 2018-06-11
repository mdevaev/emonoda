<%!
    import html
%>
% if status == "passed":
<b>${status_msg}</b>: ${html.escape(file_name)}
% elif status == "affected":
<font color="#00aa5d"><b>${status_msg}</b></font>: ${html.escape(file_name)}
% else:
<font color="#aa0000"><b>${status_msg}</b></font>: ${html.escape(file_name)}
% endif
% if status != "invalid":
<b>***</b> <a href="${result.torrent.get_comment()}">${html.escape(result.torrent.get_name())}</a>
% endif
