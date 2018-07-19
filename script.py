import requests
import random
import time
from lxml import html
import pandas as pd
import os
from openpyxl import load_workbook

year = 2000

file_path = os.path.join('H:', 'house')

region_list = ['pudong']

base_url = 'https://sh.lianjia.com/xiaoqu/rs'

index_map = {'均价': 3, '建筑年代': 4, '建筑类型': 5, '地址': 6, '物业费用': 7, '物业公司': 8, '开发商': 9}

columns = ['name', 'url', 'school', 'price', 'year', 'type', 'address', 'management_fee', 'management', 'builder', 'index']

query_result = []

def parse_details(url):
    ret = {}
    detail_page = requests.post(url=url)
    tree = html.fromstring(detail_page.content)
    tmp = tree.xpath('//div[@class="xiaoquOverview"]/div[@class="xiaoquDescribe fr"]')
    if len(tmp) == 0:
        return ret
    details = tmp[0]
    addr = tree.find_class('detailDesc')[0].text_content()
    ret['地址'] = addr
    price = -1
    tmp = details.find_class('xiaoquUnitPrice')
    if len(tmp) != 0:
        price = tmp[0].text_content()
    ret['均价'] = int(price)
    info = details.find_class('xiaoquInfoItem')
    for i in info:
        key = i.find_class('xiaoquInfoLabel')[0].text_content()
        content = i.find_class('xiaoquInfoContent')[0].text_content()
        if key == '建筑年代':
            try:
                content = int(content[:4])
            except ValueError:
                content = -1
        elif key == '物业费用':
            try:
                content = float(content[:content.find('/')-1])
            except ValueError:
                content = -1.0
        ret[key] = content
    return ret

def load_prev(region):
    output_path = region + '_out.xlsx'
    p = os.path.join(file_path, output_path)
    try:
        df = pd.read_excel(p)
        downloaded = df['name'].values
        max_index = df['index'].values[-1]
        return (downloaded, max_index)
    except FileNotFoundError:
        return ([], 0)


def dedup(region):
    output_path = region + '_out.xlsx'
    p = os.path.join(file_path, output_path)
    try:
        df = pd.read_excel(p)
        writer = pd.ExcelWriter(p, engine='openpyxl')
        df = df.drop_duplicates(subset=['name', 'address'])
        df.to_excel(writer, index=False)
        writer.save()
    except FileNotFoundError:
        return


def main():
    for s in region_list:
        csv = []
        downloaded, max_index = load_prev(s)
        output_path = s + '_out.xlsx'
        writer = pd.ExcelWriter(os.path.join(file_path, output_path), engine='openpyxl')
        file_name = s + '.xls'
        path = os.path.join(file_path, file_name)
        df = pd.read_excel(path)
        df = df[df['小区名称'].notnull() & (df['学校名称'] != '统筹安排')][['学校名称', '小区名称', '序号']]
        kv_pair = df.as_matrix()
        # print(kv_pair)
        # kv_pair = [['abc', '南崇明路1号']]
        count = len(downloaded)
        if count > 0:
            book = load_workbook(os.path.join(file_path, output_path))
            writer.book = book
            writer.sheets = dict(
                (ws.title, ws) for ws in writer.book.worksheets)
        last_count = count
        nu = 0
        while nu < len(kv_pair):
            kv = kv_pair[nu]
            try:
                school = kv[0]
                region = kv[1]
                if not isinstance(region, str):
                    nu += 1
                    continue
                if '福山证大' in school:
                    region = '证大家园'
                if kv[-1] <= max_index and '福山证大' not in school:
                    nu += 1
                    continue
                postfix = '{}'.format(region.encode('utf-8'))[2:-1]
                postfix = postfix.replace('\\x', '%')
                postfix = postfix.upper()
                url = base_url + postfix
                search_result = requests.post(url=url)
                tree = html.fromstring(search_result.content)
                tmp = tree.xpath('//ul[@class="listContent"]/li[@class="clear xiaoquListItem"]')
                if len(tmp) == 0:
                    nu += 1
                    continue
                # results = tree.xpath('//ul[@class="listContent"]/li[@class="clear xiaoquListItem"]')[0]
                results = tmp[0]
                title = results.find_class('info')[0]
                for link in title.xpath("//div[@class='title']//a[@target='_blank']"):
                    name = link.text_content()
                    href = link.attrib['href']
                    print(name)
                    detail = parse_details(href)
                    entry = [0] * 11
                    entry[0] = name
                    entry[1] = href
                    entry[2] = school
                    # set index
                    entry[10] = kv[2]
                    for k in detail.keys():
                        if k in index_map:
                            entry[index_map[k]] = detail[k]
                    if entry[4] > year:
                        print(entry)
                        csv.append(entry)
                        count += 1
                    if (count - last_count) >= 5:
                        print("Saving")
                        res = pd.DataFrame(csv, columns=columns)
                        if last_count == 0:
                            res.to_excel(writer, index=False, startrow=last_count)
                        else:
                            res.to_excel(writer, sheet_name='Sheet1', index=False, startrow=last_count+1, header=None)
                        writer.save()
                        csv = []
                        last_count = count
                        st = random.randint(1, 10)
                        time.sleep(st)
                nu += 1
            except Exception as e:
                print(e)
                time.sleep(1000)
        if len(csv) > 0:
            res = pd.DataFrame(csv, columns=columns)
            res.to_excel(writer, sheet_name='Sheet1', index=False, startrow=last_count+1, header=None)
            writer.save()
        dedup(s)

if __name__ == "__main__":
    main()
