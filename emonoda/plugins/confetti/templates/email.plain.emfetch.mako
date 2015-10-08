=== You have ${len(updated)} torrents:
% for (file_name, attrs) in updated.items():
${file_name} (from ${attrs["torrent"].get_comment()}):
    % for (sign, cat) in ( \
        ("+", "added"), \
        ("-", "removed"), \
        ("~", "modified"), \
        ("?", "type_modified"), \
    ):
        % for item in sorted(getattr(attrs["result"]["diff"], cat)):
    ${sign} ${item}
        % endfor
    % endfor
% endfor

=== Extra summary:
% for (msg, col) in ( \
    ("Updated:      ", updated), \
    ("Passed:       ", passed), \
    ("Not in client:", not_in_client), \
    ("Unknown:      ", unknown), \
    ("Invalid:      ", invalid), \
    ("Errors:       ", error), \
    ("Exceptions:   ", exception), \
):
${msg} ${len(col)}
% endfor
