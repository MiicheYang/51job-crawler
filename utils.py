import requests
from typing import List
from bs4 import BeautifulSoup
import http.cookiejar as cookielib
import json

crawl_header = {"user-agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"}

# 根据工资获取中间段
def get_midfix(salary = None) -> str:
    if salary is None: midfix = '0000,000000,0000,00,9,99,%2B,2,'
    else:
        midfix = f'0000,000000,0000,00,9,{int(salary[0])}-{int(salary[1])},%2B,2,'
        print(f'工资范围：{int(salary[0])} - {int(salary[1])} (月薪/元)')
    return midfix

# 根据关键词获取后缀
# 需要添加 经验；学历；公司类型；工作类型；公司规模 关键词
def get_suffix(config: dict) -> str:
    wy, wyn = code_workyear(config['workyear'])
    if wy != '99': print('工作经验：' + wyn)
    df, dfn = code_degreefrom(config['degreefrom'])
    if df != '99': print('学历要求：' + dfn)
    ct, ctn = code_cotype(config['cotype'])
    if ct != '99': print('公司类型：' + ctn)
    jt, jtn = code_jobterm(config['jobterm'])
    if jt != '99': print('工作类型：' + jtn)
    cs, csn = code_cosize(config['cosize'])
    if cs != '99': print('公司规模：' + csn)

    suffix = f'.html?lang=c&postchannel=0000&workyear={wy}&cotype={ct}&degreefrom={df}&jobterm={jt}&companysize={cs}&ord_field=0&dibiaoid=0&line=&welfare='
    return suffix

# 将关键字转化为搜索代码
def code_content(tags: List[str], dic):
    if tags is None or '所有' in tags or len(tags) == 0: # 不加搜索限制
        return '99', '所有' 
    try:
        codes = [dic[t] for t in tags]
    except:
        return '99'
    return '%252C'.join(codes), '；'.join(tags)

def code_workyear(workyear: List[str]):
    dic = {'在校生/应届生': '01', '1-3年': '02', '3-5年': '03', '5-10年': '04',
            '10年以上': '05', '无需经验': '06'}
    return code_content(workyear, dic)

def code_cotype(cotype: List[str]):
    dic = {'国企': '04', '外资（欧美）': '01', '外资（非欧美）': '02', '上司公司': '10',
            '合资': '03', '民营公司': '05', '外企代表处': '06', '政府机关': '07', 
            '事业单位': '08', '非营利组织': '09', '创业公司': '11'}
    return code_content(cotype, dic)

def code_degreefrom(degreefrom: List[str]):
    dic = {'初中及以下': '01', '高中/中技/中专': '02', '大专': '03', '本科': '04',
            '硕士': '05', '博士': '06', '无学历要求': '07'}
    return code_content(degreefrom, dic)

def code_jobterm(jobterm: List[str]):
    dic = {'全职': '01', '兼职': '02', '实习全职': '03', '实习兼职': '04'}
    if jobterm is None: return '99', '所有'
    else:
        try:
            return dic[jobterm[0]], jobterm[0]
        except:
            return '99', '所有'

def code_cosize(cosize: List[str]):
    dic = {'少于50人': '01', '50-150人': '02', '150-500人': '03', '500-1000人': '04',
            '1000-5000人': '05', '5000-10000人': '06', '10000人以上': '07'}
    return code_content(cosize, dic)



# 输入搜索结果界面链接，输出当页搜索结果链接
def parse_search_result(url):
    web = requests.get(url, crawl_header)
    soup = BeautifulSoup(web.content,'lxml')
    body = soup.body
    result = body.find_all('script',type='text/javascript')[-1]
    dic_result = eval(result.text.replace('window.__SEARCH_RESULT__ = ','').strip())
    result_list = dic_result['engine_search_result']
    print(f'This page has {len(result_list)} results')
    return result_list

# 输入全部搜索结果界面链接，输出全部搜索结果链接
def concat_all_result(url_list):
    all_result = []
    for url in url_list:
        result = parse_search_result(url)
        all_result += result
    print(f'There are {len(all_result)} results in total')
    return all_result

# 解析搜索结果页面
def parse_web(body):
    page = body.find_all('div',class_='tCompanyPage')[0]
    center = page.find_all('div',class_='tCompany_center')[0]
    sider = page.find_all('div', class_='tCompany_sidebar')[0]
    title, salary, cname, info, tags = parse_header(center)
    com_tags = parse_com_tags(sider)
    jd, special, contact, company = parse_content(center)
    return title, salary, cname, info, tags, com_tags, jd, special, contact, company

# 解析搜索结果头部
def parse_header(center):
    header = center.find_all('div',class_='tHeader')[0].find_all('div',class_='in')[0].find_all('div',class_='cn')[0]
    try:
        title = header.find_all('h1')[0].text.strip()
    except:
        title = ''
    try:
        salary = header.find_all('strong')[0].string
    except:
        salary = ''
    try:
        cname = header.find_all('p',class_='cname')[0].find_all('a',class_='catn')[0].text.strip()
    except:
        cname = ''
    try:
        info = header.find_all('p',class_='msg')[0].text.split('\xa0\xa0|\xa0\xa0')
    except:
        info = []
    try:
        jtag = header.find_all('div',class_='jtag')[0].find_all('div',class_='t1')[0]
        tags = [t.text for t in jtag.find_all('span')]
    except:
        tags = []
    while len(info) < 5:
        info.append('')
    return title, salary, cname, info, tags

# 解析JD
def parse_job_info(div):
    main_msg = div.find_all('div',class_='bmsg job_msg inbox')[0]
    msg_list = main_msg.find_all('p',class_=None)
    msg = []
    for m in msg_list:
        if len(m.text.strip()) > 0: msg.append(m.text.strip())
    sp = main_msg.find_all('div',class_='mt10')[0].find_all('p',class_='fp') # 部分岗位有sp信息
    special = []
    try:
        for s in sp:
            title = s.find_all('span')[0].text
            content = [t.text for t in s.find_all('a')]
            special.append({'title':title, 'content':' '.join(content)})
    except:
        pass
    return '\n'.join(msg), special

def parse_contact_info(div):
    msg = div.find_all('div',class_='bmsg')[0].find_all('p',class_='fp')
    contact = []
    contact = [m.text.strip() for m in msg]
    return contact

def parse_company_info(div):
    return div.find_all('div',class_='tmsg')[0].text.strip()

def parse_content(center):
    main_text = center.find_all('div',class_='tCompany_main')[0]
    div_list = main_text.find_all('div',class_='tBorderTop_box')
    msg, special, contact, company = [], [], [], ''
    for div in div_list:
        name = div.find_all('h2')[0].find_all('span',class_='bname')[0].text.strip()
        if name == '职位信息': msg, special = parse_job_info(div)
        elif name == '联系方式': contact = parse_contact_info(div)
        elif name == '公司信息': company = parse_company_info(div)
    return msg, special, contact, company

def parse_com_tags(sider):
    box = sider.find_all('div', class_='tBorderTop_box')[0]
    tags = box.find_all('div', class_='com_tag')[0]
    com = []
    # 公司类型；公司规模；行业
    for p in tags.find_all('p'):
        try:
            com.append(p['title'])
        except:
            com.append('')
    while len(com) < 3:
        com.append('')
    return com
    
