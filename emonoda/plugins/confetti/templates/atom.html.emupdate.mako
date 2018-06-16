<?xml version="1.0" encoding="UTF-8"?>
<%!
    from html import escape as esc
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
        <summary type="xhtml"><div xmlns="http://www.w3.org/1999/xhtml">You have ${len(results["affected"])} new torrents</div></summary>
        <content type="xhtml">
            <div xmlns="http://www.w3.org/1999/xhtml">
            <h3>&#8226; &#8226; &#8226; You have ${len(results["affected"])} new torrents:</h3>
            <table cellspacing="0" cellpadding="0">
            % for (file_name, result) in results["affected"].items():
                <tr>
                    <td width="20" align="center" valign="top">&#8226;</td>
                    <td align="left" valign="top">
                        <b>${esc(file_name)}</b> (from <a href="${result.torrent.get_comment()}">${result.tracker.PLUGIN_NAMES[0]}</a>)
                        <table cellspacing="0" cellpadding="0">
                        % for (sign, color, field) in [ \
                            ("+", "green",  "added"), \
                            ("-", "red",    "removed"), \
                            ("~", "teal",   "modified"), \
                            ("?", "orange", "type_modified"), \
                        ]:
                            % for item in sorted_paths(getattr(result.diff, field)):
                                <tr>
                                    <td width="20" align="center" valign="top"><b><font color="${color}">${sign}</font></b></td>
                                    <td align="left" valign="top">${esc(item)}</td>
                                </tr>
                            % endfor
                        % endfor
                        </table>
                    </td>
                </tr>
            % endfor
            </table>
            <br></br>
            <h3>&#8226; &#8226; &#8226; Extra summary:</h3>
            <table>
            % for (msg, field) in [ \
                ("Updated",          "affected"), \
                ("Passed",           "passed"), \
                ("Not in client",    "not_in_client"), \
                ("Unknown",          "unknown"), \
                ("Invalid torrents", "invalid"), \
                ("Tracker errors",   "tracker_error"), \
                ("Unhandled errors", "unhandled_error"), \
            ]:
                <tr>
                    <td><b>${msg}:</b></td>
                    <td>${len(results[field])}</td>
                </tr>
            % endfor
            </table>
        </div>
        </content>
    </entry>
    % endfor
</feed>
