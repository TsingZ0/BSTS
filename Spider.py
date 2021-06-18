import requests
from bs4 import BeautifulSoup
import traceback
import re
import os

url = 'https://irclogs.ubuntu.com/'
root = "/home/zjq/IRClogs/"

for year in range(2004, 2022):
    for month in range(1, 13):
        for day in range(1, 32):
            M = '0'+str(month) if month < 10 else str(month)
            D = '0'+str(day) if day < 10 else str(day)
            page_url = url + str(year) + '/' + M + '/' + D + '/'
            r = requests.get(page_url)
            if r.status_code != 404:
                dir_path = root + str(year) + '/' + M + '/' + D + '/'
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.table.findAll('a'):
                    if a['href'][0] == '%':
                        file_url = page_url + a['href']
                        file_path = dir_path + a['href'][3:]
                        try:
                            if not os.path.exists(dir_path):
                                os.makedirs(dir_path)
                            if not os.path.exists(file_path):
                                r = requests.get(file_url)
                                with open(file_path, 'wb') as f:
                                    f.write(r.content)
                                    f.close()
                                    print('OK')
                            else:
                                print('Already exists')
                        except Exception as e:
                            print(e)
            else:
                print(page_url)