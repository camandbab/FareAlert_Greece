import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

import schedule
import time
import datetime
import os
cwd = os.getcwd()
chromedriver = cwd + "\mlprojects\chromedriver.exe"

keyfile = open('iftttkey.txt', 'r')
iftttkey = keyfile.read()

import logging
logging.basicConfig(filename='farealert.log',level=logging.DEBUG)
logging.debug('This message should go to the log file')
logging.info('second log message')
logging.warning('third log message')
logging.warning('print to console')  # will print a message to the console
logging.info('if this prints then youre doing it wrong')  # will not print anything

def check_flights():
	tomorrowsdate = datetime.datetime.now() + datetime.timedelta(days=1)
	tomorrowsdate = tomorrowsdate.strftime("%Y-%m-%d")
	url ="https://www.google.com/flights/explore/#explore;f=BOS;t=r-Greece-0x135b4ac711716c63%253A0x363a1775dc9a2d1d;li=5;lx=10;d="+tomorrowsdate
	
	#set up the driver and headless browswer
	options = webdriver.ChromeOptions()
	options.add_argument('headless')
	# set the window size
	options.add_argument('window-size=1200x600')
	# initialize the driver
	driver = webdriver.Chrome(executable_path=chromedriver,chrome_options=options)
	
	driver.implicitly_wait(20)
	driver.get(url)
	
	driver.implicitly_wait(20)
	wait = WebDriverWait(driver, 20)
	wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,"span.CTPFVNB-v-c")))
	
	s = BeautifulSoup(driver.page_source, "lxml")
	
	best_price_tags = s.findAll('div', 'CTPFVNB-w-e')
	
	#check if scrape worked - alert if it fails and shutdown
	if len(best_price_alert) < 4:
		print('failed to load page data')
		requests.post("https://maker.ifttt.com/trigger/fare_alert/with/key/" + iftttkey,
			data={"value1": "script", "value2": "failed", "value3": ""})
		sys.exit(0)
	else:
		print("successfully loaded page data")
	
	best_prices = []
	for tag in best_price_tags:
		best_prices.append(int(tag.text.replace('$','').replace(',','')))
	best_price = best_prices[0]

	best_height_tags = s.findAll('div', 'CTPFVNB-w-f')
	best_heights = []
	for t in best_height_tags:
		best_heights.append(float(t.attrs['style']\
			.split('height:')[1].replace('px;','')))
	best_height = best_heights[0]
	
	pph = np.array(best_price)/np.array(best_height)
	
	cities = s.findAll('div', 'CTPFVNB-w-o')
	hlist = []
	for bar in cities[0].findAll('div', 'CTPFVNB-w-x'):
		hlist.append(float(bar['style']\
			.split('height:')[1].replace('px;',''))*pph)
	
	fares = pd.DataFrame(hlist, columns=['price'])
	px = [x for x in fares['price']]
	ff = pd.DataFrame(px, columns=['fare']).reset_index()
	
	X = StandardScaler().fit_transform(ff)
	db = DBSCAN(eps=1, min_samples=1).fit(X)
	
	labels = db.labels_
	clusters = len(set(labels))
	unique_labels = set(labels)
	
	pf  = pd.concat([ff, pd.DataFrame(db.labels_, columns=['cluster'])], axis=1)
	rf = pf.groupby('cluster')['fare']\
		.agg(['min','count']).sort_values('min', ascending=True)

	if clusters > 1\
		and ff['fare'].min() == rf.iloc[0]['min']\
		and rf.iloc[0]['count'] < rf['count'].quantile(.10)\
		and rf.iloc[0]['fare'] + 100 < rf.iloc[1]['fare']:
			city = s.find('span', 'CTPFVNB-v-c').text
			fare = s.find('div', 'CTPFVNB-w-e').text
			requests.post("https://maker.ifttt.com/trigger/fare_alert/with/key/" + iftttkey,
				data={"value1": city, "value2": fare, "value3":""})
	else:
		print('no alert triggered')
	
	#set up the scheduler to run our code every 60 min
	schedule.every(60).minutes.do(check_flights)
	
	while 1:
		schedule.run_pending()
		time.sleep(1)

#look into logging: https://docs.python.org/2/howto/logging.html
	print("Successfully Build")
