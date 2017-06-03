"""
    Emonoda -- A set of tools to organize and manage your torrents
    Copyright (C) 2015  Devaev Maxim <mdevaev@gmail.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import socket
import smtplib
import email.mime.multipart
import email.mime.text
import email.header
import email.utils
import contextlib
import time

from ...optconf import Option
from ...optconf.converters import as_string_or_none
from ...optconf.converters import as_string_list
from ...optconf.converters import as_path_or_none

from . import BaseConfetti
from . import templated


# =====
class Plugin(BaseConfetti):  # pylint: disable=too-many-instance-attributes
    PLUGIN_NAME = "email"

    def __init__(self,  # pylint: disable=super-init-not-called,too-many-arguments
                 to, cc, subject, sender, html, server, port, ssl, user, passwd, template, **kwargs):
        self._init_bases(**kwargs)

        self._to = to
        self._cc = cc
        self._subject = subject
        self._sender = sender
        self._html = html
        self._template_path = template

        self._server = server
        self._port = port
        self._ssl = ssl
        self._user = user
        self._passwd = passwd

    @classmethod
    def get_options(cls):
        return cls._get_merged_options({
            "to":       Option(default=["root@localhost"], type=as_string_list, help="Destination email address"),
            "cc":       Option(default=[], type=as_string_list, help="Email 'CC' field"),
            "subject":  Option(default="{source} report: you have {affected} new torrents ^_^", help="Email subject"),
            "sender":   Option(default="root@localhost", help="Email 'From' field"),
            "html":     Option(default=True, help="HTML or plaintext email body"),
            "template": Option(default=None, type=as_path_or_none, help="Mako template file name"),

            "server":   Option(default="localhost", help="Hostname of SMTP server"),
            "port":     Option(default=0, help="Port of SMTP server"),
            "ssl":      Option(default=False, help="Use SMTPS"),
            "user":     Option(default=None, type=as_string_or_none, help="Account on SMTP server"),
            "passwd":   Option(default=None, type=as_string_or_none, help="Passwd for account on SMTP server"),
        })

    # ===

    def send_results(self, source, results):
        msg = self._format_message(source, results)
        retries = self._retries
        while True:
            try:
                self._send_message(msg)
                break
            except (
                smtplib.SMTPServerDisconnected,
                smtplib.SMTPConnectError,
                smtplib.SMTPHeloError,
                socket.timeout,
            ):
                if retries == 0:
                    raise
                time.sleep(self._retries_sleep)
                retries -= 1

    # ===

    def _format_message(self, source, results):
        subject_placeholders = {field: len(items) for (field, items) in results.items()}
        subject_placeholders["source"] = source
        built_in = (self._template_path is None)
        return self._make_message(
            subject=self._subject.format(**subject_placeholders),
            body=templated(
                name=("email.{ctype}.{source}.mako" if built_in else self._template_path).format(
                    ctype=("html" if self._html else "plain"),
                    source=source,
                ),
                built_in=built_in,
                source=source,
                results=results,
            ),
        )

    def _make_message(self, subject, body):
        email_headers = {
            "From":    self._sender,
            "To":      ", ".join(self._to),
            "Date":    email.utils.formatdate(localtime=True),
            "Subject": email.header.Header(subject, "utf-8"),
        }
        if len(self._cc) > 0:
            email_headers["CC"] = ", ".join(self._cc)

        msg = email.mime.multipart.MIMEMultipart()
        for (key, value) in email_headers.items():
            msg[key] = value

        msg.attach(email.mime.text.MIMEText(
            _text=body.encode("utf-8"),
            _subtype=("html" if self._html else "plain"),
            _charset="utf-8",
        ))
        return msg

    def _send_message(self, msg):
        smtp_class = (smtplib.SMTP_SSL if self._ssl else smtplib.SMTP)
        with contextlib.closing(smtp_class(
            host=self._server,
            port=self._port,
            timeout=self._timeout,
        )) as client:
            if self._user is not None:
                client.login(self._user, self._passwd)  # pylint: disable=no-member
            client.send_message(msg)  # pylint: disable=no-member
