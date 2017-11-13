# arkivist - Offline Archival of POP &amp; IMAP Mail

The goal of this project is to provide a tool for offline
archival of your email from your POP & IMAP email.  If
you operate primarily from webmail, but need a way to
backup your email folders so that you can remain within
your mail provider's quotas, this is for you.

## Planned Features

* Connect to a POP or IMAP email account
* Accept search criteria to identify emails for archival
* Handle multipart messages & attachments reasonably
* Store emails in a SQLite database
* Search archived emails
* Export archived emails
* Encryption-at-rest
* Local webapp interface?

## Design Considerations

* `imaplib` -> `email.message` -> (JSON|MessagePack|Pickle)
* SQLCipher?
