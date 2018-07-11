import requests
from lxml import html
import pandas as pd

region_list = ['东方城市花园', '中冶尚城']

base_url = 'https://sh.lianjia.com/xiaoqu/rs'

columns = ['name', 'year', 'school', 'price', 'size', 'url']

query_result = []

for r in region_list:
    postfix = '{}'.format(r.encode('utf-8'))[2:-1]
    postfix = postfix.replace('\\x', '%')
    postfix = postfix.upper()
    url = base_url + postfix
    search_result = requests.post(url=url)
    tree = html.fromstring(search_result.content)
    results = tree.xpath('//ul[@class="listContent"]/li[@class="clear xiaoquListItem"]')[0]
    title = results.find_class('info')[0]
    for link in title.xpath("//div[@class='title']//a[@target='_blank']"):
        name = link.text_content()
        href = link.attrib['href']
