# coding:utf-8
import requests
from bs4 import BeautifulSoup
from typing import List
import time
import random
import pickle
import yaml
import os
import pandas as pd
import numpy as np
from utils import *

# 设置header
crawl_header = {"user-agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"}
prefix = 'https://search.51job.com/list/'
yaml_path = 'config.yaml'

def crawl(config):
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

    save_path = config['save_dir']

    all_result = {}
    for pcode in pcodes:
        print('*'*20)
        prov, urls = crawl_url(prefix, midfix, suffix, pcode)
        results = crawl_detail(urls, save_path, prov)
        all_result['prov'] = results
        
    return all_result

# 爬取全部搜索结果的url
def crawl_url(prefix, midfix, suffix, pcode):
    if pcode >= 10: pre = prefix + str(pcode) + midfix
    else: pre = prefix + '0' + str(pcode) + midfix
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
    return prov, prov_result

def crawl_detail(urls, save_path, city):

    results = []
    if not os.path.isdir(save_path): os.mkdir(save_path)
    connect, success = 0, 0
    path = save_path + '\\' + city
    if not os.path.isdir(path): os.mkdir(path)
    columns = ['ID', 'Title', 'Salary', 'Company Name', 'URL', 'City', 'Experience', 'Scholar', 
                'Capacity', 'Publish Date', 'Company Type', 'Company Size', 'Industry', 'Job Description']
    df = pd.DataFrame(columns = columns)
    print(f'******爬取 {city} 详细结果******')
    for idx in range(len(urls)):
        url = urls[idx]['url']
        jid = urls[idx]['id']
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
                line_info = [jid, title, salary, cname, url] + info + com_tags[:3] + [jd]
                results.append(line_info)
                df.loc[df.shape[0]] = dict(zip(columns, line_info))
                success += 1
            except:
                pass            
    df.to_csv(path + '\\' + city + '.csv', sep = ',', index = 0, encoding = 'utf_8_sig')  
    print(f'{city} finished\nTotal {len(urls)} results')
    print(f'共{connect}条爬取成功')
    print(f'共{success}条解析成功')
    return results

def save_data(path, data):
    pass

if __name__ == '__main__':

    with open(yaml_path, 'r', encoding = 'utf-8') as f:
        config = yaml.load(f, Loader = yaml.FullLoader)

    results = crawl(config)