import codecs
import os
import time
from datetime import date, datetime, timedelta
from urllib.parse import urljoin
import shutil
import chromedriver_binary
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.alert import Alert
from webdriver_manager.chrome import ChromeDriverManager

url="http://www.jepx.org/market/"

os.chdir("C:\\Users\\f-apl-admin\\Downloads")
browser = webdriver.Chrome(ChromeDriverManager().install())#バージョンが違っても自動でアップデートしてくれる
browser.implicitly_wait(3)

browser.get(url)
time.sleep(1)
browser_form = browser.find_element_by_xpath('/html/body/div[2]/div[1]/div[1]/div[8]/table/tbody/tr[2]/td[2]/a')#翌日のボタン
browser_form.click()
time.sleep(6) 
browser.close()
time.sleep(2)


df = pd.read_csv('spot_2021.csv',encoding="shift_jis")
df = df.tail(48)
df = df[['年月日','時刻コード','エリアプライス東京(円/kWh)']]
df = df.reset_index(drop=True)
print(df)

day = str(df.iat[0,0]).replace('/','')

time = []
for i in df['時刻コード']:
    if i <48:
        t = timedelta(hours=i/2)
        time.append(str(t))
    if i == 48:
        time.append('00:00:00')


df['時刻']=time
time_2 = []

for i,j in zip(df['年月日'],df['時刻']):
    t = str(i).replace('/','-')
    if j =='00:00:00':
        x = datetime.strptime(t,'%Y-%m-%d')
        y = x +timedelta(days=1)
        time_2.append(y)    
    else:
        n = t +' '+ str(j)
        time_2.append(n)
df['時刻']=time_2
df = df[['時刻','エリアプライス東京(円/kWh)']]#これ以外はdrop

filename = 'JEPX価格'+day+'.csv'
df.to_csv(filename,encoding="shift_jis")
shutil.move(filename, 'C:\\Users\\f-apl-admin\\JEPX\\JEPX日毎確定価格')

os.remove('spot_2021.csv')

