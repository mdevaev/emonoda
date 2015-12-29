<%!
    from emonoda.tools import sorted_paths
%>
=== You have ${len(results["affected"])} new torrents:
% for (file_name, result) in results["affected"].items():
${file_name} (from ${result["torrent"].get_comment()}):
    % for (sign, field) in ( \
        ("+", "added"), \
        ("-", "removed"), \
        ("~", "modified"), \
        ("?", "type_modified"), \
    ):
        % for item in sorted_paths(result["diff"][field]):
    ${sign} ${item}
        % endfor
    % endfor
% endfor

=== Extra summary:
% for (msg, field) in ( \
    ("Updated:          ", "affected"), \
    ("Passed:           ", "passed"), \
    ("Not in client:    ", "not_in_client"), \
    ("Unknown:          ", "unknown"), \
    ("Invalid torrents: ", "invalid"), \
    ("Tracker errors:   ", "tracker_error"), \
    ("Unhandled errors: ", "unhandled_error"), \
):
${msg} ${len(results[field])}
% endfor
