# SmtpRelaySpoof
<p> Send or Spoof Emails via an SMTP Relay </p>

Powerful Python3 Powered Smtp Relay Powered Emai Spoofer
<pre>
$ ./SendMail.py -h
usage: SendMail.py [-h] [-t TO_ADDRESS] [-a TO_ADDRESS_FILENAME]
                   [-f FROM_ADDRESS] [-n FROM_NAME] [-r REPLY_TO] [-j SUBJECT]
                   [-e EMAIL_FILENAME] [--important] [-i] [-F] [--image IMAGE]
                   [--attach ATTACHMENT_FILENAME] [--track] [-d DB_NAME]
                   [-s SMTP_SERVER] [-p SMTP_PORT] [--slow] [-u SMTP_USER]
                   [-P SMTP_PASS]

optional arguments:
  -h, --help            show this help message and exit

Email Options:
  -t TO_ADDRESS, --to TO_ADDRESS
                        Email address to send to
  -a TO_ADDRESS_FILENAME, --to_address_filename TO_ADDRESS_FILENAME
                        Filename containing a list of TO addresses
  -f FROM_ADDRESS, --from FROM_ADDRESS
                        Email address to send from
  -n FROM_NAME, --from_name FROM_NAME
                        From name
  -r REPLY_TO, --reply_to REPLY_TO
                        Reply-to header
  -j SUBJECT, --subject SUBJECT
                        Subject for the email
  -e EMAIL_FILENAME, --email_filename EMAIL_FILENAME
                        Filename containing an HTML email
  --important           Send as a priority email
  -i, --interactive     Input email in interactive mode
  -F, --force           Force send even if fails spoofcheck
  --image IMAGE         Attach an image
  --attach ATTACHMENT_FILENAME
                        Attach a file

Email Tracking Options:
  --track               Track email links with GUIDs
  -d DB_NAME, --db DB_NAME
                        SQLite database to store GUIDs

SMTP options:
  -s SMTP_SERVER, --server SMTP_SERVER
                        SMTP server IP or DNS name (default localhost)
  -p SMTP_PORT, --port SMTP_PORT
                        SMTP server port (default 25)
  --slow                Slow the sending
  -u SMTP_USER, --user SMTP_USER
                        Optional: Authenticate with this username
  -P SMTP_PASS, --password SMTP_PASS
                        Optional: Authenticate with this password
</pre>
