<%!
    from emonoda.tools import sorted_paths
    from emonoda.plugins.confetti import STATUSES
%>
% if len(results["affected"]) != 0:
=== You have ${len(results["affected"])} changed torrents:
    % for (file_name, result) in results["affected"].items():
${file_name} (from ${result.torrent.get_comment()}):
        % for (sign, field) in [ \
            ("+", "added"), \
            ("-", "removed"), \
            ("~", "modified"), \
            ("?", "type_modified"), \
        ]:
            % for item in sorted_paths(getattr(result.diff, field)):
    ${sign} ${item}
            % endfor
        % endfor
    % endfor
% endif
% for status in statuses:
    % if status != "affected" and len(results[status]) != 0:

=== ${STATUSES[status]} (${len(results[status])}):
        % for (file_name, result) in results[status].items():
            % if status == "invalid":
${file_name}
            % else:
${file_name} (from ${result.torrent.get_comment()})
            % endif
			% if status in ["tracker_error", "unhandled_error"]:
    ${result.err_name}(${result.err_msg})
			% endif
        % endfor
    % endif
% endfor

=== Extra summary:
% for (msg, field) in [ \
    ("Updated:          ", "affected"), \
    ("Passed:           ", "passed"), \
    ("Not in client:    ", "not_in_client"), \
    ("Unknown:          ", "unknown"), \
    ("Invalid torrents: ", "invalid"), \
    ("Tracker errors:   ", "tracker_error"), \
    ("Unhandled errors: ", "unhandled_error"), \
]:
${msg} ${len(results[field])}
% endfor
