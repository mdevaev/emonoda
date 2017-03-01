<?xml version="1.0" encoding="UTF-8"?>
<%!
  from datetime import datetime
  from emonoda.tools import sorted_paths
%>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:thr="http://purl.org/syndication/thread/1.0" xml:lang="en">
    <title type="text">Emonoda Update!</title>
    <subtitle type="text">Updates of torrents by emonoda!</subtitle>
    <updated>${datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}</updated>
    <id>${settings["url"]}feed/atom/</id>
    <link rel="self" type="application/atom+xml" href="${settings["url"]}feed/atom.xml" />
    <link rel="alternate" type="text/html" href="${settings["url"]}" />
    <generator uri="https://www.github.com/mdevaev/emonoda">emonoda</generator>
    % for results in results_set:
    <entry>
        <author>
            <name>emonoda</name>
            <uri>${settings["url"]}</uri>
        </author>
        <title type="html"><![CDATA[Emonoda update!]]></title>
        <id>emonoda_update_${results["ctime"]}</id>
        <published>${datetime.fromtimestamp(results["ctime"]).strftime("%Y-%m-%dT%H:%M:%SZ")}</published>
        <updated>${datetime.fromtimestamp(results["ctime"]).strftime("%Y-%m-%dT%H:%M:%SZ")}</updated>
        <summary type="text">You have ${len(results["affected"])} new torrents</summary>
        <content type="text">
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
        </content>
    </entry>
    % endfor
</feed>
