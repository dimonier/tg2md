#!/usr/bin/env python

# parse.py - converts telegram json to Obsidian md.
# Copyright (c) 2020, Lev Brekalov
# Changes from progxaker, 2021
# Further developed by dimonier, 2022

# TODO summary:
# - [x] replies (prev post transcluded)
# - [x] wiki-links and external links
# - [x] links to original telegram posts
# - [x] post author tag for groups
# - [x] `yyyy-mm` subfolders to output posts folder
# - [x] forwarded posts
# - [ ] single/muliple tags
# - [ ] custom post header

import os
import argparse
import json
from datetime import datetime

def simplify_name(name):
    printable_name = ''.join(c for c in name if c.isprintable())

    return printable_name

def unlinked_name(name):
    if name:
        unlinked_name = name.replace('[', '').replace(']', '')
    else:
        unlinked_name = ''

    return unlinked_name

def print_default_post_header(post_title, post_date, post_author, post_tag):


    '''
    returns default post header
    '''

    # TODO: handle post tag/tags
    # TODO: support for custom header
    post_header = '---\n'\
        'title: {title}\n'\
        'date: {date}\n'\
        'author: {author}\n'\
        'tags: {tag}\n'\
        '---\n'.format(title=post_title, date=post_date, author=post_author, tag=post_tag)

    return post_header


def print_custom_post_header(post_header_file, *args):

    '''
    now unusable (i dunno how it may work)
    '''

    with post_header_file as f:
        post_header_content = read(post_header_file)
    for arg in args:
        pass
    return post_header_content


def parse_post_photo(post, photo_dir):

    '''
    converts photo tag to markdown image link
    '''

    post_photo = '![image]({src})\n\n'.format(src=post['photo'].split('/')[-1])

    return post_photo


def parse_post_file(post, photo_dir):

    '''
    converts any file to markdown file link
    '''
    if post['file'].startswith('(File '):
        post_file = ''
    else:
        post_file = '[[{src}]]\n\n'.format(src=post['file'].split('/')[-1])

    return post_file


def text_format(string, fmt):

    '''
    wraps string in markdown-styled formatting
    '''

    if fmt in ('*', '**', '***', '`', '```'):
        output = '{fmt}{txt}{fmt}'
    elif fmt == '```':
        output = '{fmt}\n{txt}\n{fmt}'
    else:
        output = '<{fmt}>{txt}</{fmt}>'

    output = output.format(fmt=fmt, txt=string.strip())
    output += '\n' * string.split('\n').count('') * string.endswith('\n')
    return output


def text_link_format(text, link, alias):

    '''
    formats links
    '''

    # convert telegram links to anchors
    # this implies that telegram links are pointing to the same channel
    link_fmt = '[{text}]({href})'

    if link.startswith('https://t.me') and len(link.split('/')) > 2:
        if link.split('/')[-2] in alias:
            link = link.split('/')[-1]
            link_fmt = '[[{href}|{text}]]'

    link_fmt = link_fmt.format(text=text.strip(), href=link)
    link_fmt += '\n' * text.count('\n') * text.endswith('\n')

    return link_fmt


def parse_text_object(obj, alias):

    '''
    detects type of text object and wraps it in corresponding formatting
    '''

    obj_type = obj['type']
    obj_text = obj['text']

    if obj_type == 'hashtag':
        post_tag = obj_text
        return post_tag

    elif obj_type == 'text_link':
        return text_link_format(obj_text, obj['href'], alias)

    elif obj_type == 'link':
        post_link = obj_text
        if obj_text.startswith('https://t.me') and len(obj_text.split('/')) > 2:
            if obj_text.split('/')[-2] in alias:
                post_link = '[[' + obj_text.split('/')[-1] + ']]'
        # print(obj_text, '->', post_link)
        return post_link

    elif obj_type == 'email':
        link = obj_text.strip()
        link = 'https://' * (obj_type == 'link') * \
            (1 - link.startswith('https://')) + link
        post_link = '<{href}>'.format(href=link)
        return post_link

    elif obj_type == 'phone':
        return obj_text

    elif obj_type == 'italic':
        return text_format(obj_text, '*')

    elif obj_type == 'bold':
        return text_format(obj_text, '**')

    elif obj_type == 'code':
        return text_format(obj_text, '`')

    elif obj_type == 'pre':
        return text_format(obj_text, '```')

    elif obj_type == 'underline':
        return text_format(obj_text, 'u')

    elif obj_type == 'strikethrough':
        return text_format(obj_text, 's')


def parse_post_text(post, alias):
    # TODO: handle reply-to
    post_raw_text = post['text']
    post_parsed_text = ''

    if type(post_raw_text) == str:
        return str(post_raw_text)

    else:
        for obj in post_raw_text:
            if type(obj) == str:
                post_parsed_text += obj
            else:
                post_parsed_text += str(parse_text_object(obj, alias))

        return post_parsed_text

def parse_post_reply(post, alias):

    '''
    form a reply header
    '''

    post_reply = '**{author} [replied](https://t.me/{alias}/{id}) to [[{orig}|post]]**\n![[{orig}]]\n'.format(alias = alias[-1], id = post['id'], orig=post['reply_to_message_id'], author=unlinked_name(post['from']))

    return post_reply

def post_header(post, alias):

    '''
    form a post header
    '''

    post_header = '**{author} [wrote](https://t.me/{alias}/{id}):**\n'.format(alias = alias[-1], id = post['id'], author=unlinked_name(post['from']))

    return post_header


def parse_post_media(post, media_dir, alias):

    '''
    wraps file links to Obsidian link
    '''
    if post['file'].startswith('(File '):
        post_media = ''
    else:
        post_media = '\n![[{src}]]'.format(src=post['file'].split('/')[-1])

    return post_media


def parse_post(post, photo_dir, media_dir, alias):

    '''
    converts post object to formatted text
    '''

    post_output = ''

    # reply header or normal header
    if 'reply_to_message_id' in post:
        post_output += str(parse_post_reply(post, alias))
    else:
        post_output += str(post_header(post, alias))

    # optional image
    if 'photo' in post:
        post_output += str(parse_post_photo(post, photo_dir))

    # post text
    post_output += str(parse_post_text(post, alias))

    # optional media
    if 'file' in post:
        post_output += str(parse_post_media(post, media_dir, alias))

    return post_output


def main():

    parser = argparse.ArgumentParser(
            usage='%(prog)s [options] json_file',
            description='Convert exported Telegram channel data json to \
                    bunch of Markdown posts ready to use with Obsidian')
    parser.add_argument(
            'json', metavar='json_file',
            help='result.json file from Telegram export')
    parser.add_argument(
            '--alias', metavar='alias',
            nargs='?', default='',
            help='channel or group alias. Used for correct linking \
                    of posts (default: None')
    parser.add_argument(
            '--out-dir', metavar='out_dir',
            nargs='?', default='posts',
            help='output directory for Obsidian Markdown files\
                    (default: posts)')
    parser.add_argument(
            '--photo-dir', metavar='photo_dir',
            nargs='?', default='photos',
            help='location of image files. this changes only links\
                    to photos in markdown text, so specify your\
                    desired location (default: photos)')
    parser.add_argument(
            '--media-dir', metavar='media_dir',
            nargs='?', default='files',
            help='location of media files. this changes only links\
                    to files in markdown text, so specify your \
                    desired location (default: files)')
    args_wip = parser.add_argument_group('work in progress')
    args_wip.add_argument(
            '--post-header', metavar='post_header',
            nargs='?',
            help='yaml front matter for your posts \
                    (now doesn\'t work)')

    args = parser.parse_args()

    try:
        os.mkdir(args.out_dir)
    except FileExistsError:
        pass

    # load json file
    try:
        with open(args.json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit('result.json not found.\nPlease, specify right file')

    # list channel/group aliases used in links
    alias = [f'c/{data["id"]}']
    # print(type(args.alias))
    if args.alias: alias.append(args.alias)
    # print('Aliases', alias)

    lastmonth = ''

    # load only messages
    raw_posts = data['messages']
    print('Processing', len(raw_posts), 'posts in', alias[-1])

    for post in raw_posts:
        # TODO: handle forwarded posts
#        if post['type'] == 'message' and 'forwarded_from' not in post:
        if post['type'] == 'message':

            post_date = datetime.fromisoformat(post['date'])
            post_id = post['id']
            post_author = unlinked_name(post['from'])
            if 'channel' in data['type']:
                post_nametag = ''
            else:
                post_nametag = simplify_name(unlinked_name(post_author)).replace(' ', '_')
            post_filename = str(post_id) + '.md'
            post_subpath = str(post_date)[0:7]

            try:
                os.mkdir(os.path.join(args.out_dir, post_subpath))
            except FileExistsError:
                pass

            if post_subpath != lastmonth:
                lastmonth = post_subpath
                print(lastmonth)

            post_path = os.path.join(args.out_dir, post_subpath, post_filename)

            with open(post_path, 'w', encoding='utf-8') as f:
                print(print_default_post_header(
                    post_id, post_date, post_author, post_nametag), file=f)
                print(parse_post(post, args.photo_dir, args.media_dir, alias), file=f)


if __name__ == '__main__':
    main()
