#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# https://github.com/darkerego/SmtpRelaySpoof
# Modified by Darkerego, 2019
# xelectron@protonmail.com
# Tips: BTC:17hcGfgvvTz2wB1wx17GHyWpt8BsLuu5PX
#

# imports
import argparse
import logging
import mimetypes
import random
import re
import smtplib
import sqlite3
import time
import uuid
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sys import exit
from os import mkdir
from time import strftime
import socks
# local imports (from ./lib)
from lib.prettyoutput import *
from lib import spoofcheck
# some globals
global db
msgdir = './messages'

# Create message store directory
try:
    mkdir(msgdir)
except FileExistsError:
    pass


def time_stamp():
    """\
    Generate a timestamp
    :return: time string: example: 2019-06-19-14-14-49
    """
    ts = strftime("%Y-%m-%d-%H-%M-%S")
    ts = str(ts)
    return ts


"""def check_domain(domain):
    
    spoofable = check(domain)
    if spoofable:
        return True
    else:
        return False"""


def get_ack(force):
    """\
    Force function - Send even if Spoof Check fails
    :param force: specified on CLI
    :return: true or false
    """
    output_info("To continue: [yes/no]")
    if force is False:
        yn = input('[>] ')
        if yn != "yes":
            return False
        else:
            return True
    elif force is True:
        output_indifferent("Forced yes")
        return True
    else:
        raise TypeError("Passed in non-boolean")


def get_interactive_email():
    """\
    My function for interactively taking input and parsing it into a valid
    HTML/EML document
    :return:
    """
    outfile = msgdir + '/' + 'tmp.html'
    subject = args.subject

    output_ok("""Enter each line as a paragraph. Lines will be wrapped in <p>line</p> tags. To remove the previous line,
    enter "_DEL_", and it will be discarded. Enter "_EOF_" or press ctrl+c when done composing message.""")

    message = []
    signature = []

    def data_input():
        datalist = []
        while True:
            try:
                data = input('>> ')
                if data == '_DEL_':
                    datalist = datalist[:-1]
                elif data == '_EOF_':
                    print('<<')
                    return datalist
                else:
                    datalist.append(data)
            except KeyboardInterrupt:
                print('<<')
                break
            except EOFError:
                output_bad('Caught hangup. Exiting.')
                exit(1)
        return datalist

    message = data_input()
    with open(outfile, 'w+') as f:
        f.write(str("<!DOCTYPE html>\n<html>\n<head>\n<title>\n") + str(subject) + str('\n</title>\n</head>\n<body>\n'))
        for line in message:
            f.write('<p>' + str(line) + '</p>')

        do_sig = input('Include a signature? Formatted italized, Navy Blue (y/n) :')
        if do_sig == 'y' and do_sig is not None:
            signature = data_input()
            for line in signature:
                f.write('<i style="color:Navy;">' + str(line) + '</i><br>\n')
        f.write('<br><!-- Powered by Darkeregos awesome smtp tool. '
                'https://github.com/darkerego/SmtpRelaySpoof --></body>\n</html>\n')
    with open(outfile, 'r') as ff:
        msg = ff.read()
        return msg


def get_file_email():
    """\
    Open a file and parse to send
    :return: email text
    """
    email_text = ""
    try:
        with open(args.email_filename, "r") as infile:
            output_info("Reading " + args.email_filename + " as email file")
            email_text = infile.read()
    except IOError:
        output_error("Could not open file " + args.email_filename)
        exit(-1)

    return email_text


def is_domain_spoofable(from_address, to_address):
    global force
    """\
    Enhanced DMARC, SPF, and Cross Orgin Checks
    :param from_address: sending from
    :param to_address: sending to
    :return: - exit if check fails
    """
    email_re = re.compile(".*@(.*\...*)")

    from_domain = email_re.match(from_address).group(1)
    to_domain = email_re.match(to_address).group(1)
    output_info("Checking if from domain " + Style.BRIGHT + from_domain + Style.NORMAL + " is spoofable...")
    if spoofcheck.check(from_domain):  # check actual dmarc and spf records
        output_good('Sending domain: SPF and DMARC records weak, looking good!')
        send_ok = True
        """\
        Do we need to check both?
        output_info("Checking if to domain " + Style.BRIGHT + to_domain + Style.NORMAL + " is spoofable...")
        if spoofcheck.check(to_domain):
            output_good('Rcpt domain: SPF and DMARC records weak, looking great! ')
            send_ok = True
        else:
            output_bad('Domain has spoof protection, this might not be a good idea...')
            send_ok = False"""
    else:
        output_bad('Domain has spoof protection, this might not be a good idea...')
        send_ok = False
        if not send_ok or force:
            proceed = input('Proceed anyway ? (y/n) :' )
            if proceed != 'y':
                output_bad('Exiting...')
                exit(0)
        else:
            output_bad('Domain failed spoofcheck, but --force was specfied... ')

    if from_domain == "gmail.com":
        if to_domain == "gmail.com":
            output_bad("You are trying to spoof from a gmail address to a gmail address.")
            output_bad("The Gmail web application will display a warning message on your email.")
            if not get_ack(args.force):
                output_bad("Exiting")
                exit(1)
        else:
            output_indifferent("You are trying to spoof from a gmail address.")
            output_indifferent(
                "If the domain you are sending to is controlled by Google Apps "
                "the web application will display a warning message on your email.")
            if not get_ack(args.force):
                output_bad("Exiting")
                exit(1)

    output_good("Seems spoofable ... Sending to " + args.to_address)


def bootstrap_db():
    global db
    db.execute("CREATE TABLE IF NOT EXISTS targets(email_address, uuid)")
    db.commit()


def save_tracking_uuid(email_address, target_uuid):
    global db
    db.execute("INSERT INTO targets(email_address, uuid) VALUES (?, ?)", (email_address, target_uuid))
    db.commit()


def create_tracking_uuid(email_address):
    tracking_uuid = str(uuid.uuid4())
    save_tracking_uuid(email_address, tracking_uuid)
    return tracking_uuid


def inject_tracking_uuid(email_text, tracking_uuid):
    TRACK_PATTERN = "\[TRACK\]"

    output_ok("Injecting tracking UUID %s" % tracking_uuid)

    altered_email_text = re.sub(TRACK_PATTERN, tracking_uuid, email_text)
    return altered_email_text


def inject_name(email_text, name):
    NAME_PATTERN = "\[NAME\]"
    output_ok("Injecting name %s" % name)

    altered_email_text = re.sub(NAME_PATTERN, name, email_text)
    return altered_email_text


def delay_send():
    sleep_time = random.randint(1, 55) + (60 * 5)
    time.sleep(sleep_time)


def main():
    global args
    parser = argparse.ArgumentParser()

    email_options = parser.add_argument_group("Email Options")

    email_options.add_argument("-t", "--to", dest="to_address", help="Email address to send to")
    email_options.add_argument("-a", "--to_address_filename", dest="to_address_filename",
                               help="Filename containing a list of TO addresses")
    email_options.add_argument("-f", "--from", dest="from_address", help="Email address to send from")
    email_options.add_argument("-n", "--from_name", dest="from_name", help="From name")
    email_options.add_argument("-r", "--reply_to", dest="reply_to", help="Reply-to header")

    email_options.add_argument("-j", "--subject", dest="subject", default='Automated Message Service',
                               help="Subject for the email")
    email_options.add_argument("-e", "--email_filename", dest="email_filename",
                               help="Filename containing an HTML email")
    email_options.add_argument("--important", dest="important", action="store_true", default=False,
                               help="Send as a priority email")
    email_options.add_argument("-i", "--interactive", action="store_true", dest="interactive_email",
                               help="Input email in interactive mode")
    email_options.add_argument("-F", "--force", action="store_true", dest="force",
                               help="Force send even if fails spoofcheck")
    email_options.add_argument("--image", action="store", dest="image", help="Attach an image")
    email_options.add_argument("--attach", action="store", dest="attachment_filename", help="Attach a file")
    email_options.add_argument("-y", "--yes", action="store_true", dest='yes_send', help='Do not ask for confirmation'
                                                                                         'when sending message.'
                                                                                         'Useful for automated tasks '
                                                                                         'such as cronjobs.')

    tracking_options = parser.add_argument_group("Email Tracking Options")
    tracking_options.add_argument("--track", dest="track", action="store_true", default=False,
                                  help="Track email links with GUIDs")
    tracking_options.add_argument("-d", "--db", dest="db_name", help="SQLite database to store GUIDs")

    smtp_options = parser.add_argument_group("SMTP options")
    smtp_options.add_argument("-s", "--server", dest="smtp_server",
                              help="SMTP server IP or DNS name (default localhost)", default="localhost")
    smtp_options.add_argument("-p", "--port", dest="smtp_port", type=int, help="SMTP server port (default 25)",
                              default=25)
    smtp_options.add_argument("--slow", action="store_true", dest="slow_send", default=False, help="Slow the sending")
    smtp_options.add_argument("-u", "--user", dest="smtp_user", default=0, type=str,
                              help="Optional: Authenticate with this username")
    smtp_options.add_argument("-P", "--password", dest="smtp_pass", default=0, type=str,
                              help="Optional: Authenticate with this password")
    smtp_options.add_argument("-T", "--tls", dest='tls', action='store_true', help='Authenticate with TLS')
    smtp_options.add_argument("--proxy", dest='socks_proxy', type=str, default=None, help='Socks5 proxy '
                                                                                          '<ex: localhost:9050>')

    global db
    args = parser.parse_args()
    if args.force:
        globals()['force'] = True
    if args.yes_send:
        globals()['yes_send'] = True

    if args.smtp_user and args.smtp_pass:
        use_auth = True
    else:
        use_auth = False

    global db
    if args.track:
        if args.db_name is not None:
            db = sqlite3.connect(args.db_name)
            bootstrap_db()
        else:
            logging.error("DB name is empty")
            exit(1)

    email_text = ""
    if args.interactive_email:
        email_text = get_interactive_email()
    else:
        try:
            email_text = get_file_email()
        except TypeError:
            logging.error("Could not load email from file %s" % args.email_filename)
            exit(1)

    to_addresses = []
    if args.to_address is not None:
        to_addresses.append(args.to_address)
    elif args.to_address_filename is not None:
        try:
            with open(args.to_address_filename, "r") as to_address_file:
                to_addresses = to_address_file.readlines()
        except IOError as e:
            logging.error("Could not locate file %s", args.to_address_filename)
            raise e
    else:
        logging.error("Could not load input file names")
        exit(1)
    if args.socks_proxy:
        socks_proxy = args.socks_proxy.split(':')
        output_info("Using socks5 proxy %s" % args.socks_proxy)
        socks_host = socks_proxy[0]
        socks_port = socks_proxy[1]
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, socks_host, socks_port)
        socks.wrapmodule(smtplib)

    if not args.yes_send and not args.force:
        output_indifferent('[?] Send message? (y/n) : ')
        proceed = input('[>] ')
        if proceed == 'y' or proceed == 'Y' or proceed == 'yes':
            pass
        else:
            output_error('Abort. Quitting!')
            exit(1)
    try:
        output_info("Connecting to SMTP server at " + args.smtp_server + ":" + str(args.smtp_port))
        server = smtplib.SMTP(args.smtp_server, args.smtp_port)
        if args.tls:
            output_info("Using TLS ...")
            server.starttls()
        if use_auth:
            output_indifferent('Attempting Authentication...')
            try:
                server.login(args.smtp_user, args.smtp_pass)
            except Exception as err:
                output_bad('Error authenticating: ' + str(err))
                exit(1)
        msg = MIMEMultipart("alternative")
        msg.set_charset("utf-8")

        if args.from_name is not None:
            output_info("Setting From header to: " + args.from_name + "<" + args.from_address + ">")
            msg["From"] = args.from_name + "<" + args.from_address + ">"
        else:
            output_info("Setting From header to: " + args.from_address)
            msg["From"] = args.from_address

        if args.reply_to is not None:
            output_info("Setting Reply-to header to " + args.reply_to)
            msg["Reply-to"] = args.reply_to

        if args.subject is not None:
            output_info("Setting Subject header to: " + args.subject)
            msg["Subject"] = args.subject

        if args.important:
            msg['X-Priority'] = '2'

        if args.image:
            with open(args.image, "rb") as imagefile:
                img = MIMEImage(imagefile.read())
                msg.attach(img)

        for to_address in to_addresses:
            is_domain_spoofable(args.from_address, to_address)
            msg["To"] = to_address

            if args.track:
                tracking_uuid = create_tracking_uuid(to_address)
                altered_email_text = inject_tracking_uuid(email_text, tracking_uuid)
                msg.attach(MIMEText(altered_email_text, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(email_text, 'html', 'utf-8'))

            if args.attachment_filename is not None:

                ctype, encoding = mimetypes.guess_type(args.attachment_filename)
                if ctype is None or encoding is not None:
                    # No guess could be made, or the file is encoded (compressed), so
                    # use a generic bag-of-bits type.
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                with open(args.attachment_filename, "rb") as attachment_file:
                    inner = MIMEBase(maintype, subtype)
                    inner.set_payload(attachment_file.read())
                    encoders.encode_base64(inner)
                inner.add_header('Content-Disposition', 'attachment', filename=args.attachment_filename)
                msg.attach(inner)

            server.sendmail(args.from_address, to_address, msg.as_string())
            ts = time_stamp()
            with open(msgdir + '/msg_' + ts + '.eml', 'w+') as f:
                eml_msg = msg.as_string()
                f.write(eml_msg)
            output_info("Email Sent to " + to_address)
            if args.slow_send:
                delay_send()
                output_info("Connecting to SMTP server at " + args.smtp_server + ":" + str(args.smtp_port))
                server = smtplib.SMTP(args.smtp_server, args.smtp_port)

    except smtplib.SMTPException as err:
        output_error("Error: Could not send email")
        output_bad('Server says: ' + str(err))
        output_indifferent('Exit')
        # raise err
        exit(1)


if __name__ == "__main__":
    main()
