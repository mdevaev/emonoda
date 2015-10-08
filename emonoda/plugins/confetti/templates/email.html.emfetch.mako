<h3>&bull; &bull; &bull; You have ${len(updated)} torrents:</h3>
<table cellspacing="0" cellpadding="0">
% for (file_name, attrs) in updated.items():
    <tr>
        <td width="20" align="center" valign="top">&bull;</td>
        <td align="left" valign="top">
            <b>${file_name}</b> (from <a href="${attrs["torrent"].get_comment()}">${attrs["fetcher"].get_name()}</a>)
            <table cellspacing="0" cellpadding="0">
            % for (sign, color, cat) in ( \
                ("+", "green", "added"), \
                ("-", "red", "removed"), \
                ("~", "teal", "modified"), \
                ("?", "orange", "type_modified"), \
            ):
                % for item in sorted(getattr(attrs["result"]["diff"], cat)):
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
% for (msg, col) in ( \
    ("Updated",       updated), \
    ("Passed",        passed), \
    ("Not in client", not_in_client), \
    ("Unknown",       unknown), \
    ("Invalid",       invalid), \
    ("Errors",        error), \
    ("Exceptions",    exception), \
):
    <tr>
        <td><b>${msg}:</b></td>
        <td>${len(col)}</td>
    </tr>
% endfor
</table>
