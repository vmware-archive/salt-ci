# -*- coding: utf-8 -*-
'''
    saltci.notif.modules.sendmail
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Simple salt module to send emails.

    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2013 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.
'''

# Import python libs
import os
import json
import socket
import logging
import smtplib
import getpass

from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

# Import salt-ci libs
from saltci.config import _DEFAULT_SENDMAIL_CONFIG


log = logging.getLogger(__name__)


__opts__ = _DEFAULT_SENDMAIL_CONFIG.copy()


# Tell salt explicitly what functions this module provides
__load__ = ['send', 'test']


def __virtual__():
    opts = _get_config()
    if not opts['smtp_host'] or not opts['smtp_user'] or not opts['smtp_pass']:
        log.warning('Sendmail not configured. Not loading module.')
        return False
    return True


def _get_config():
    '''
    Load the default configuration.

    We start with the default configuration and iterate over it's keys.
    If the key is present in __opts__ and the value of __opts__[key] is not equal to the default
    one, then that value is used and we continue onto the next key.
    If the key is not found in __opts__, but instead is found in __pillar__ and the value of
    __pillar__[key] is not equal to the default value, then that value is used.
    If the key is not in either __opts__ nor __pillar__, the value remains at it's default.
    '''

    result = _DEFAULT_SENDMAIL_CONFIG.copy()
    opts = __opts__.get('sendmail', {})
    pillar = __pillar__.get('sendmail', {})
    for key, value in _DEFAULT_SENDMAIL_CONFIG.iteritems():
        if key in opts and opts[key] != value:
            # Any options in __opts__ takes precedence to __pillar__
            value = opts[key]
        elif key in pillar and pillar[key] != value:
            value = pillar[key]
        result[key] = value
    return result


def _setup_mailserver():
    '''
    Setup the mail server and store it in the current context.
    '''
    if 'mailserver' not in __context__:
        log.info('Setting up mailserver')
        __context__['mailserver'] = _Connection()


class _Connection(object):

    def connect(self):
        if getattr(self, 'server', None) is not None:
            # Already connected
            return

        opts = _get_config()

        try:
            if opts.get('use_ssl', False) is True:
                log.debug(
                    'Setting up an SSL SMTP connection to {smtp_host}:{smtp_port}'.format(
                        **opts
                    )
                )
                mailserver = smtplib.SMTP_SSL(
                    opts['smtp_host'],
                    opts['smtp_port'],
                    timeout=5
                )
            else:
                log.debug(
                    'Setting up an SMTP connection to {smtp_host}:{smtp_port}'.format(
                        **opts
                    )
                )
                mailserver = smtplib.SMTP(
                    opts['smtp_host'],
                    opts['smtp_port'],
                    timeout=5
                )
        except socket.error, err:
            log.error(
                'Failed to setup SMTP connection: {0}'.format(err),
                exc_info=err
            )
            raise

        mailserver.ehlo_or_helo_if_needed()

        if opts.get('use_tls', False):
            if 'starttls' not in mailserver.esmtp_features:
                return 'TLS enabled but server does not support TLS'
            mailserver.starttls()
            mailserver.ehlo_or_helo_if_needed()

        if opts['smtp_user'] and opts['smtp_pass']:
            mailserver.login(
                opts['smtp_user'],
                opts['smtp_pass']
            )

        mailserver.set_debuglevel(opts.get('smtp_debug_level', 0))
        self.server = mailserver

    def disconnect(self):
        if getattr(self, 'server', None) is not None:
            server = self.server
            self.server = None
            try:
                server.quit()
            except socket.sslerror, err:
                # avoid false failure detection when the server closes the SMTP connection with
                # TLS enabled
                if not opts['use_tls']:
                    log.exception(err)
                    raise err

    def send(self, sender, send_to, message):
        if getattr(self, 'server', None) is None:
            try:
                self.connect()
            except Exception, err:
                raise Exception('Failed to setup SMTP connection: {0}'.format(err))
        self.server.sendmail(sender, send_to, message.as_string())

    def __del__(self):
        self.disconnect()
        if __context__ and 'mailserver' in __context__:
            __context__.pop('mailserver')


def _detect_mimetype(filename):
    try:
        import magic
        mag = magic.open(magic.MAGIC_MIME)
        mag.load()
        mimetype = mag.file(filename)
        mimetype.rsplit(';')[0]
        return mimetype.split('/')
    except ImportError:
        import mimetypes
        mimetype = mimetypes.guess_type(filename)
        if mimetype == (None, None):
            return ('text', 'plain')


def send(subject=None, recipients=(), sender=None, body=None, html=None, cc=(), bcc=(),
         attachments=(), reply_to=None, charset=None, extra_headers=None):
    '''

    Send an email

    :param subject: A string containing the email subject.
    :param recipients: A list of email addresses or a comma delimited string of email addresses.
    :param sender: The email address of the sender. Defaults to what was set on the configuration
                   file. If it's a list or tuple it's expected to be something like:
                       (name, address)
    :param body: A plain text string with the email contents.
    :param html: An HTML formated string with the email contents.
    :param cc: A list of email addresses or a comma delimited string of email addresses which will
               be sent as a Carbon-Copy of the original.
    :param bcc: A list of email addresses or a comma delimited string of email addresses which will
                be sent as a Blind-Carbon-Copy of the original.
    :param attachments: A list of filenames or a comma delimited string of filenames which will be
                        sent as attachments.
    :param reply_to: The email address of who should be replied. Defaults to what was set on the
                     configuration file. If it's a list or tuple it's expected to be something
                     like:
                       (name, address)
    :param charset: The charset to use in the message. If not set, defaults to utf-8.
    :param extra_headers: A dictionary containing the key and value pairs for each header. If it's
                          a string, it's handled as it was a JSON string.
    :returns: A string if the message was properly queued on the server, a dictionary with an
              'error' keys explaining what the problem was.

    CLI Example::
        salt '*' subject=Foo recipients=foo@biz.tld,bar@biz.tld body='Test message!!!'
        salt '*' subject=Foo recipients=foo@biz.tld body='Test message!!!' extra_headers='{"foo": 1}'
        salt '*' subject=Foo recipients=foo@biz.tld body='Test message!!!' attachments=/full/path/to/file1,/full/path/to/file2

    **ATTENTION**: The example above WILL send the exact same email from every matching minion
                   which has sendmail configured!
    '''

    if not recipients and not cc and not bcc:
        log.error('No recipients provided. Message will not be sent!')
        return {'error': 'No recipients provided. Message will not be sent!'}

    # ----- Let's convert the values passed from cli if that's the case ------------------------->
    if recipients and isinstance(recipients, basestring):
        recipients = tuple([addr.strip() for addr in recipients.split(',')])

    if cc and isinstance(cc, basestring):
        cc = tuple([addr.strip() for addr in cc.split(',')])

    if bcc and isinstance(bcc, basestring):
        bcc = tuple([addr.strip() for addr in bcc.split(',')])

    if attachments and isinstance(attachments, basestring):
        attachments = tuple([attachment.strip() for attachment in attachments.split(',')])
    # <---- Let's convert the values passed from cli if that's the case --------------------------

    if extra_headers and isinstance(extra_headers, basestring):
        try:
            extra_headers = json.loads(extra_headers)
        except ValueError:
            return {'error': 'Failed to parse the extra headers JSON string'}
        if not isinstance(extra_headers, dict):
            return {
                'error': 'The provided JSON string containing the extra headers did not result '
                         'in a python dictionary'
            }

    opts = _get_config()

    if charset is None:
        charset = 'utf-8'

    if sender is None:
        # Grab any sender set on the configuration
        sender = opts.get('sender', opts['smtp_user'])

        if sender is None:
            # Sender is still None, let's compute it
            sender = '{0}@{1}'.format(getpass.getuser(), socket.getfqdn())

    if isinstance(sender, (list, tuple)):
        # sender can be tuple of (name, address)
        sender = '{0} <{1}>'.format(*sender)

    if reply_to is None and opts.get('reply_to', None) is not None:
        reply_to = opts['reply_to']
    if isinstance(sender, (list, tuple)):
        # reply_to can be tuple of (name, address)
        reply_to = '{0} <{1}>'.format(*reply_to)

    # Let's start constructing the email message
    if len(attachments) == 0 and not html:
        # No html content and zero attachments means plain text
        msg = MIMEText(body, _subtype='text', _charset=charset)
    elif len(attachments) > 0 and not html:
        # No html and at least one attachment means multipart
        msg = MIMEMultipart()
        msg.attach(MIMEText(body, _subtype='text', _charset=charset))
    else:
        # Anything else
        msg = MIMEMultipart()
        alternative = MIMEMultipart('alternative')
        alternative.attach(MIMEText(body, _subtype='plain', _charset=charset))
        alternative.attach(MIMEText(html, _subtype='html', _charset=charset))
        msg.attach(alternative)

    msg['Message-ID'] = make_msgid()
    msg['Subject'] = subject.rstrip()
    msg['From'] = sender.rstrip()
    msg['Date'] = formatdate(localtime=True)

    if recipients:
        msg['To'] = ', '.join([addr.rstrip() for addr in recipients])
    if cc:
        msg['Cc'] = ', '.join([addr.rstrip() for addr in cc])
    if bcc:
        msg['Bcc'] = ', '.join([addr.rstrip() for addr in bcc])
    if reply_to:
        msg['Reply-To'] = reply_to.rstrip()

    send_to = set(recipients or ()) | set(bcc or ()) | set(cc or ())

    if extra_headers:
        for key, value in extra_headers.iteritems():
            msg[key] = str(value).rstrip()

    for entry in attachments:
        if isinstance(entry, dict):
            if isinstance(entry['mimetype'], basestring):
                entry['mimetype'] = entry['mimetype'].split('/')

            attachment = MIMEBase(*entry['mimetype'])
            attachment.set_payload(entry['data'])
            encode_base64(attachment)

            attachment.add_header(
                'Content-Disposition', '{0};filename={1}'.format(
                    entry.get('disposition', 'attachment'),
                    entry['filename']
                )
            )
            for key, value in entry.get('headers', {}):
                attachment.add_header(key, value.rstrip())

        elif os.path.isfile(entry):
            attachment = MIMEBase(*_detect_mimetype(entry))
            attachment.set_payload(open(entry, 'rb').read())
            encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition', '{0};filename={1}'.format(
                    'attachment',
                    os.path.basename(entry)
                )
            )
        else:
            # We currently only support dict based or explicit filename attachments.
            # Maybe latter we can add salt:// support for attachments.
            # Would be cool if we could do something like:
            #   salt://<minion-id>/filename
            #   salt:///path/to/filename@<minion-id>
            #   salt://<minion-id>@/path/to/filename
            raise NotImplementedError

        msg.attach(attachment)

    _setup_mailserver()
    try:
        __context__['mailserver'].send(sender, send_to, msg)
        return 'Message delivered to SMTP server'
    except smtplib.SMTPException, err:
        return {'error': 'Failed to send email message: {0}'.format(err)}


def test(recipent=None):
    '''
    Test the current email setup.

    It will send a simple email to the provided address assuring your setup is correct.

    CLI Example::
        salt '*' sendmail.test foo@bar.tld
    '''
    return send(
        subject="Test Email", recipients=(recipent,),
        body='This is a test email from your salt installation.'
    )
