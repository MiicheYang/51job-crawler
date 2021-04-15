# coding:utf-8
import requests
from bs4 import BeautifulSoup
from typing import List
import time
import http.cookiejar as cookielib
import urllib
import random
from datetime import datetime
import json
import pickle
import yaml
from utils import *

# 设置header
crawl_header = {"user-agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"}
prefix = 'https://search.51job.com/list/'
yaml_path = 'config.yaml'

# 爬取全部搜索结果的url
def crawl_url(config):
    # 获取中间和后缀
    print('******检索关键词******')
    midfix = get_midfix(config['salary'])
    suffix = get_suffix(config)

    # 需要爬取的城市
    with open('provs.pkl', 'rb') as f:
        provs = pickle.load(f)
    if config['city'] is None:
        pcodes = [provs[p] for p in provs]
        print('爬取全国所有城市')
    else:
        pcodes = [provs[p] for p in config['city']]
        print(f'爬取城市：' + '；'.join(config['city']))

    print('******开始爬取URL******')
    total_result = {}
    count = 0
    for pro_idx in pcodes:
        if pro_idx >= 10: pre = prefix + str(pro_idx) + midfix
        else: pre = prefix + '0' + str(pro_idx) + midfix
        url = pre + '1' + suffix
        web = requests.get(url,headers=crawl_header)
        soup = BeautifulSoup(web.content,'lxml')
        body = soup.body
        # 获取省份信息
        prov = str(soup.find_all("title")[0]).split('【')[1].split('招聘')[0]
        print(f'爬取 {prov} 岗位链接...')
        # 获取总页数
        search_result = body.find_all('script',type='text/javascript')[-1]
        pages = eval(str(search_result).replace('<script type="text/javascript">\r\nwindow.__SEARCH_RESULT__ = ','').replace('</script>','').strip())['total_page']
        pages = int(pages)
        print(f'搜索结果共{pages}页')
        # 获取工作链接
        all_result = []
        for page in range(1,pages+1):
            url = pre + str(page) + suffix
            web = requests.get(url,headers=crawl_header)
            soup = BeautifulSoup(web.content,'lxml')
            body = soup.body
            result = body.find_all('script',type='text/javascript')[-1]
            dic_result = eval(str(result).replace('<script type="text/javascript">\r\nwindow.__SEARCH_RESULT__ = ','').replace('</script>','').strip())
            result_list = dic_result['engine_search_result']
            all_result += result_list
            if(page%50 == 0): print(f'Current Process: {page}/{pages}')
        prov_result = [{'id': r['jobid'], 'url': r['job_href'].replace('\\','')} for r in all_result]
        print(f'{prov} 共有 {len(prov_result)} 条结果')
        total_result[prov] = prov_result
        count += len(prov_result)
    print(f'总计 {count} Jobs')
    return total_result

def crawl(config):
    urls = crawl_url(config)
    save_path = config['save_dir']

    results = []
    if not os.path.isdir(save_path): os.mkdir(save_path)
    for p in urls:
        connect, success = 0, 0
        path = save_path + '\\' + p
        if not os.path.isdir(path): os.mkdir(path)

        print(f'******爬取 {p}******')
        for idx in range(len(urls[p])):
            url = urls[p][idx]['url']
            jid = urls[p][idx]['id']
            if not os.path.exists(path + '\\' + jid + '.txt'):
                try:
                    web = requests.get(url.strip(),headers=crawl_header)
                    soup = BeautifulSoup(web.content,'lxml')
                    with open(path + '\\' + jid + '.txt','w',encoding='utf-8') as f:
                        f.write(str(soup))
                    with open(path + '\\' + jid + '.url.txt', 'w', encoding='utf-8') as f:
                        f.write(url + '\n')
                    connect += 1

                    # 解析
                    title, salary, cname, info, tags, com_tags, jd, _, _, _ = parse_web(soup) # 暂不爬取特殊信息、公司信息和联系方式
                    line_info = [jid, title, salary, cname, url] + com_tags[:3] + [jd]
                    results.append(line_info)
                    success += 1
                except:
                    pass              
                
        print(f'{p} finished\nTotal {len(urls[p])} results')
        print(f'共{connect}条爬取成功')
        print(f'共{success}条解析成功')
    return results

def save_data(path, data):
    pass

if __name__ == '__main__':

    with open(yaml_path, 'r', encoding = 'utf-8') as f:
        config = yaml.load(f, Loader = yaml.FullLoader)

    all_url = crawl_url(config)
    save_path = config['save_dir']

    results = crawl(config)