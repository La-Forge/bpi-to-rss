from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import os
from lxml import html
from xml.etree import ElementTree
import requests
from feedgen.feed import FeedGenerator
import pprint
import sys
import datetime


BPI_URL = 'https://www.bpifrance.fr/A-la-une/Appels-a-projets-concours'


def get_raw_text(element):
    raw_text = ElementTree.tostring(
        element, encoding='utf8', method='text').decode()
    normalized_text = " ".join(raw_text.split())
    return normalized_text


def get_text(element):
    return ElementTree.tostring(element, encoding='utf8').decode()


def extract_data():
    # extract content
    page = requests.get(BPI_URL)

    # generate dom tree
    tree = html.fromstring(page.content)

    # extract items
    items = tree.xpath('//div[@class="item-offre"]')

    # reverse order to have last item first
    items.reverse()

    # extract content
    articles = []
    for item in items:
        article = {}
        # print(get_text(item))
        # extract delai
        article['delai'] = item.xpath(
            './/div[starts-with(@class,\'delai \')]/strong/text()')[0]

        # extract title
        article['title'] = item.xpath(
            './/div[starts-with(@class,\'delai \')]/strong/text()')[0]

        # extract date
        article['date'] = get_raw_text(item.xpath('.//div[@class="date"]')[0])

        # create published date
       # begin_date = article['date'].split(" - ")[0].strip()
        #print(begin_date+".")
        #date_time_obj = datetime.datetime.strptime(begin_date, '%d %m %Y')
        #article['published']= date_time_obj

        # extract type
        article['type'] = get_raw_text(
            item.xpath('.//div[@class="type-offre"]')[0])

        
        # extract title
        article['title'] = "["+article['type']+"] "+get_raw_text(
            item.xpath('.//div[@class="titre-offre"]')[0])

        # extract description
        article['content'] = get_raw_text(
            item.xpath('.//div[@class="text-offre"]')[0])

        # link
        article['link'] = 'https://www.bpifrance.fr/' + \
            item.xpath('.//div[@class="group-link"]/a/@href')[-1]

        # generate description
        article['description'] =  f"[{article['delai']}][{article['date']}]\n{article['content']}"

        articles.append(article)
    return articles

def print_data():
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(extract_data())

def generate_feed():
    fg = FeedGenerator()
    fg.title('BPI - Appels à projets & concours')
    fg.id(BPI_URL+"/rss")
    fg.author( {'name':'Bpifrance'} )
    fg.link( href=BPI_URL, rel='alternate' )
    fg.subtitle('Powered by www.la-forge.ai')
    fg.language('fr')

    #add articles
    articles = extract_data()
    for article in articles:
        fe = fg.add_entry()
        fe.id(article['link'])
        fe.title(article['title'])
        fe.published(article['date'])
        fe.link(href=article['link'])
        fe.description(article['description'])   

    atomfeed = fg.atom_str(pretty=True) # Get the ATOM feed as string
    return atomfeed


class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/rss+xml; charset=utf-8")
        self.end_headers()
        self.wfile.write(generate_feed())
 
def start_server(hostPort):
    hostName = ''
    print(hostPort)

    myServer = HTTPServer((hostName, hostPort), MyRequestHandler)
    print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

    try:
        myServer.serve_forever()
    except KeyboardInterrupt:
        pass

    myServer.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))

if __name__ == "__main__":
    #start_server(int(sys.argv[1]))
    print_data()
