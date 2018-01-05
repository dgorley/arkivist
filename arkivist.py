#!/usr/bin/env python3

import hashlib
import imaplib
import os.path
import uuid

import jinja2
import maya
import yaml


def read_config(filename='settings.yml'):
    """Read the configuration from the YAML config file."""
    with open(filename, 'r') as fh:
        return yaml.load(fh.read())


def parse_headers(header_dict):
    """Extract meaningful values from the IMAP header dictionary."""
    values = dict()
    values['from_addr'] = header_dict.get(b'From', '').decode('utf8')
    values['to_addr'] = header_dict.get(b'To', '').decode('utf8')
    values['subject'] = header_dict.get(b'Subject', '').decode('utf8')
    values['spam'] = header_dict.get(b'X-Spam-Flag', '').decode('utf8')
    message_timestamp_str = header_dict[b'Date'].decode('utf8')
    values['ts'] = maya.MayaDT.from_rfc2822(message_timestamp_str)
    return values


def imap_connection(settings):
    M = imaplib.IMAP4(settings['mail_server'], port=143)
    M.login(settings['username'], settings['password'])
    return M


def message_count(settings, imap):
    _, data = imap.select()
    return int(data[0])


def retrieve_headers(settings, imap, msg_num):
    _, data = imap.fetch(str(msg_num).encode('utf8'), '(BODY.PEEK[HEADER])')
    header = data[0][1]
    header_lines = header.split(b'\r\n')
    header_dict = dict()
    for l in header_lines:
        try:
            k, v = l.split(b': ', maxsplit=1)
            header_dict[k] = v
        except ValueError:
            pass
    return header, parse_headers(header_dict)


def retrieve_body(settings, imap, msg_num):
    _, data = imap.fetch(str(msg_num).encode('utf8'), '(RFC822.TEXT.PEEK)')
    return data[0][1]


def write_email_to_file(settings, imap, msg_num):
    raw_header, header_dict = retrieve_headers(settings, imap, msg_num)
    # Use header_dict to write HTML index
    body_text = retrieve_body(settings, imap, msg_num)
    filename_digest = hashlib.sha1()
    filename_digest.update(raw_header)
    filename_digest.update(body_text)
    output_basename = filename_digest.hexdigest()
    output_path = os.path.join(settings['output_directory'], output_basename + '.eml')
    with open(output_path, 'wb') as fh:
        fh.write(raw_header)
        fh.write(body_text)
    return output_path, header_dict


def write_html_index(settings, processed_messages):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('./'))
    tmpl = env.get_template(settings['index_template'])
    content = tmpl.render(messages=processed_messages)
    index_filename = f'_index_{maya.now().epoch}.html'
    index_file = os.path.join(settings['output_directory'], index_filename)
    with open(index_file, 'w') as fh:
        fh.write(content)


def delete_message(settings, imap, msg_num):
    print("Deleting {}".format(msg_num))
    imap.store(str(msg_num).encode('utf8'), '+FLAGS', r'(\Deleted)')
    typ, expunge_response = imap.expunge()
    print('Response: {} {}'.format(typ, expunge_response))


def main(settings):
    imap = imap_connection(settings)
    num_msgs = message_count(settings, imap)
    print('There are {} messages in INBOX'.format(num_msgs))
    processed_messages = list()
    for num in range(settings['max_email_count'], 0, -1):
        filename, header_dict = write_email_to_file(settings, imap, num)
        processed_messages.append((filename, header_dict))
        if settings['delete_after_archive']:
            delete_message(settings, imap, num)
    imap.logout()
    write_html_index(settings, processed_messages)

if __name__ == '__main__':
    settings = read_config()
    main(settings)
