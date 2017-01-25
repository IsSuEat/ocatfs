from bs4 import BeautifulSoup
import requests


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
        :param subforum: tuple consisting of relative url and name
        :return: generator with threads in the subforum
        """

        subforum_res = requests.get(self.BASE_URL + subforum[0])
        soup = BeautifulSoup(subforum_res.content, 'html.parser')
        threads_td = soup.find_all('td', 'title')
        for t in threads_td:
            threads = t.find('a')
            yield (threads.get('href'), threads.get('title'))

    def get_posts(self, thread):

        """
        fetches post in a thread
        :param thread: a tuple containing relative ulr and name
        :return: tuple with message and username
        """

        thread_res = requests.get(self.BASE_URL + thread[0])
        soup = BeautifulSoup(thread_res.content, 'html.parser')
        post = soup.find_all('tr', 'post even')
        for p in post:
            message = p.find('div', 'message').text
            username = p.find('td', 'userdata').find('h4').find('a').string
            yield ((message, username))


ocatp = OcatParser()
for p in ocatp.get_posts(('/sport/s-waage_247141', 'S: Waage')):
    print(p)
