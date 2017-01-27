#! /usr/bin/env python3

import logging
import os
import sys
import time
from stat import S_IFDIR, S_IFREG
import fuse
import requests
from bs4 import BeautifulSoup
import argparse
import textwrap


# TODO: handle more than one page for threads and posts
# TODO: nicer folder names, maybe use parsed title
# TODO: st_mtime according to last post date
# TODO: maybe posting?

class Thread:
    def __init__(self, title, url):
        self.url = url
        self.title = title


class Post:
    def __init__(self, author, message):
        self.author = author
        self.message = message

    # TODO: better formatting
    def __repr__(self):
        # prefix all lines with a tab
        msg = textwrap.indent(self.message, '\t')
        return '\n{0}:\n\n{1:>20} \n'.format(self.author, msg)


class OcatScraper:
    BASE_URL = "https://overclockers.at"

    def __init__(self):
        pass

    def get_subforums(self):
        forum_res = requests.get(self.BASE_URL + "/forums")
        soup = BeautifulSoup(forum_res.content, 'html.parser')

        subforums_trs = soup.find_all('tr', 'forum level3')
        for tr in subforums_trs:

            links = tr.find('td', 'title').find('a')
            yield (links.get('href'), links.get('title'))

    def get_threads(self, subforum):
        logging.info('Getting threads for subforum: {}'.format(subforum))
        subforum_res = requests.get(self.BASE_URL + '/' + subforum)
        soup = BeautifulSoup(subforum_res.content, 'html.parser')
        threads_td = soup.find_all('td', 'title')
        for t in threads_td:
            threads = t.find('a')
            yield Thread(threads.get('title'), threads.get('href'))

    def get_posts(self, thread_url):
        logging.info('Getting posts for thread: {}'.format(thread_url))
        thread_res = requests.get(self.BASE_URL + thread_url)
        soup = BeautifulSoup(thread_res.content, 'html.parser')
        post = soup.find_all('tr', {'class': ['post odd', 'post even']})

        for p in post:
            message = '\n'.join(p.find('div', 'message').stripped_strings)
            username = p.find('td', 'userdata').find('h4').find('a').string
            yield Post(username, message)


class OcatFs(fuse.LoggingMixIn, fuse.Operations):
    def __init__(self, ocatparser):
        # keys: subforums, values thread titles
        self.thread_titles = {}
        self.ocatparser = ocatparser
        # relative urls
        self.subforums_urls = [e[0] for e in ocatparser.get_subforums()]

    def getattr(self, path, fh=None):

        if path == '/':
            return dict(st_mode=(S_IFDIR | 0o755), st_nlink=2,
                        st_ctime=time.time(), st_mtime=time.time(),
                        st_atime=time.time())
        elif path in self.subforums_urls:
            return dict(st_mode=(S_IFDIR | 0o755), st_nlink=2,
                        st_ctime=time.time(), st_mtime=time.time(),
                        st_atime=time.time())
        else:
            return dict(st_mode=(S_IFREG | 0o444), st_nlink=1,
                        st_size=4096, st_ctime=time.time(), st_mtime=time.time(),
                        st_atime=time.time())

    def readdir(self, path, fh):
        dirents = ['.', '..']

        if path == '/':
            # extend root entries to contain subforums. easiest to strip the slash off the path
            dirents.extend(map((lambda x: x.strip('/')), self.subforums_urls))
        else:
            subforum = path.split('/')[1]
            # only the thread titles are relevant for the dir entries
            self.thread_titles[subforum] = [e.url.split('/')[-1] for e in self.ocatparser.get_threads(subforum)]
            dirents.extend(self.thread_titles[subforum])
        logging.debug('Current dirents {} for path {}'.format(dirents, path))
        return dirents

    def read(self, path, size, offset, fh):
        if '.git' in path:
            pass
        logging.debug('Reading :{}'.format(path))
        post_text = ''
        for p in self.ocatparser.get_posts(path):
            post_text += repr(p)

        post_bytes = bytes(post_text, 'utf-8')
        return post_bytes[offset:offset + size]


def _arg_parser():
    parser = argparse.ArgumentParser(description="oc.at as a filesystem in userspace")
    parser.add_argument('mountpoint', help="Where to mount the fs to, required")
    parser.add_argument('--background', default=False, action='store_true', help="Run fuse in the background")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    return parser.parse_args()


def run():
    args = _arg_parser()

    if not os.path.isdir(args.mountpoint):
        print('Mountpoint not available or not a directory')
        sys.exit(1)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    fuse.FUSE(OcatFs(OcatScraper()), args.mountpoint, foreground=not args.background)


if __name__ == '__main__':
    run()
