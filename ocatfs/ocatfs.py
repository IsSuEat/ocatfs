import io
import os
import sys

import logging
from bs4 import BeautifulSoup
import requests
import fuse
from stat import S_IFDIR, S_IFLNK, S_IFREG
import time


# TODO: handle more than one page for threads and posts

class OcatParser(object):
    BASE_URL = "https://overclockers.at"

    def __init__(self):
        pass

    def get_subforums(self):
        forum_res = requests.get(self.BASE_URL + "/forums")
        soup = BeautifulSoup(forum_res.content, 'html.parser')
        subforums = soup.find_all('td', 'title')
        for s in subforums:
            links = s.find('a')
            yield (links.get('href'), links.get('title'))
            # print(s.find('a'))

    def get_threads(self, subforum):
        """
        fetches threads in a subforum
        :param subforum: string
        :return: generator with threads in the subforum
        """
        logging.info('Getting threads for subforum: {}'.format(subforum))
        subforum_res = requests.get(self.BASE_URL + '/' + subforum)
        soup = BeautifulSoup(subforum_res.content, 'html.parser')
        threads_td = soup.find_all('td', 'title')
        for t in threads_td:
            threads = t.find('a')
            yield (threads.get('href'), threads.get('title'))

    def get_posts(self, thread_url):

        """
        fetches post in a thread
        :param thread_url: relative path
        :return: tuple with message and username
        """

        thread_res = requests.get(self.BASE_URL + thread_url)
        soup = BeautifulSoup(thread_res.content, 'html.parser')
        post = soup.find_all('tr', 'post even')
        for p in post:
            message = p.find('div', 'message').text
            username = p.find('td', 'userdata').find('h4').find('a').string
            yield ((message, username))


class OcatFs(fuse.LoggingMixIn, fuse.Operations):
    def __init__(self, ocatparser):
        # keys: subforums, values thread titles
        self.thread_titles = {}
        self.ocatparser = ocatparser
        self.subforums_urls = [e[0] for e in ocatparser.get_subforums()]
        self.threads = {}

    def getattr(self, path, fh=None):
        logging.debug("CURRENT PATH FOR GETATTR: {}".format(path))

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
            dirents.extend(map((lambda x: x.strip('/)')), self.subforums_urls))
        else:
            subforum = path.split('/')[1]
            # only the thread titles are relevant for the dir entries
            self.thread_titles[subforum] = [e[0].split('/')[2] for e in self.ocatparser.get_threads(subforum)]
            dirents.extend(self.thread_titles[subforum])
        logging.debug('Current dirents {} for path {}'.format(dirents, path))
        return dirents

    def read(self, path, size, offset, fh):
        logging.debug('Reading :{}'.format(path))
        post_list = [e[0] for e in self.ocatparser.get_posts(path)]
        post_bytes = bytes(''.join(post_list), 'utf-8')
        return post_bytes[offset:offset + size]
        # no idea what i am doing lol
        # return posts[offset:offset + size]


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(1)

    logging.basicConfig(level=logging.DEBUG)
    fuse = fuse.FUSE(OcatFs(OcatParser()), sys.argv[1], foreground=True)
