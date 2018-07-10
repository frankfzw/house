import requests

region_list = ['东方城市花园']

base_url = 'https://sh.lianjia.com/xiaoqu/rs'
for r in region_list:
    postfix = '{}'.format(r.encode('utf-8'))[2:-1]
    postfix = postfix.replace('\\x', '%')
    postfix = postfix.upper()
    url = base_url + postfix
    r = requests.post(url=url)
    print(r.content)
