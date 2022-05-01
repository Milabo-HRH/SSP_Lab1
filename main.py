import os
import traceback

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import mysql.connector

site = "https://www.complaintsboard.com"
os.makedirs("./images", exist_ok=True)
conn = mysql.connector.connect(user='root', password='110611', database='OSN_Lab')
cur = conn.cursor()
create = "CREATE TABLE IF NOT EXISTS complaints( \
            `id` INT UNSIGNED AUTO_INCREMENT,\
            `header` VARCHAR(200) NOT NULL,\
            `name` VARCHAR(40) ,\
            `address` VARCHAR(40) ,\
            `date` VARCHAR(40), \
            `company` VARCHAR(100) NOT NULL, \
            `text` TEXT NOT NULL,   \
            `res` CHAR(1),\
            `rep` CHAR(1),\
            `imgSRC` VARCHAR(100), \
            PRIMARY KEY ( `id` )\
         )ENGINE=InnoDB DEFAULT CHARSET=utf8;"

cur.execute(create)
img_index = 0
option = Options()
option.add_argument("--headless")


def scratch(t):
    imgSrc = ''
    global img_index
    res = 'F'
    rep = 'F'
    name = t.find('span', {'class': 'complaint-header__name'}).text
    try:
        address = t.find('span', {'itemprop': 'address'}).text
    except:
        address = ""
    date = t.find('span', {'class': 'complaint-header__date'}).text
    header = t.find('span', {'class': 'complaint-main__header-name'}).text
    company = t.find('span', {'class': 'complaint-main__header-company'}).text
    text = t.find('p', {'class': 'complaint-main__text'}).text.replace('\n', ' ')
    re = t.findAll('span', {'class': 'complaint-statuses__text'})
    for r in re:
        if r.text == "Resolved":
            res = 'T'
            # print("{0}: resolved.".format(header))
        if r.text == "Replied":
            rep = 'T'
    images = t.findAll('a', {'class': 'complaint-attachments__link'})
    begin = img_index
    fl = False
    for im in images:
        fl = True
        src = site + im['href']
        proxies = {"http": None, "https": None}
        r = requests.get(src, proxies=proxies)
        with open('./images/' + str(img_index) + '.' + src[src.rfind('.') + 1:], mode='wb') as f:
            f.write(r.content)
        img_index += 1
    if fl:
        imgSrc = str(begin) + ' ' + str(img_index)
    try:
        sql = "INSERT INTO complaints(`header`,`name`, `address`, `date`, `company`, `text`, `res`, `rep`, `imgSRC`)\
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

        val = (header[:200], name, address[:40], date, company, text, res, rep, imgSrc)

        cur.execute(sql, val)
        conn.commit()
    except:
        traceback.print_exc()
        conn.rollback()


def link_handle(s):
    try:
        brows = webdriver.Chrome(options=option)
        brows.get(s)
        soup_i = BeautifulSoup(brows.page_source, 'html.parser')
        n = soup_i.findAll('a', {'class': 'bn-complaints__pagination-item'})
        if len(n) > 2:
            n = int(n[-2].text)
        else:
            n = 1
        temp = soup_i.findAll('div', {'class': 'complaint-list-block'})
        for t in temp:
            scratch(t)
        brows.close()
        return n
    except:
        return link_handle(s)


browser1 = webdriver.Chrome(options=option)
browser1.get(site + "/bycategory/business-finances")
soup = BeautifulSoup(browser1.page_source, 'html.parser')

links = soup.findAll('a', {'class': 'block item-row bname-row'})
for i in range(len(links)):
    links[i] = links[i]['href']

for i in range(len(links)):
    s = site + links[i]
    n = link_handle(s)
    for j in range(2, n + 1):
        page = s + "/page/" + str(j)
        link_handle(page)

browser1.close()
