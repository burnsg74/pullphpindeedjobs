import json
from datetime import datetime

import mysql.connector
import requests
from bs4 import BeautifulSoup
import re

# Get jk ids
jobKeys = []
start: int = 0
while True:
    URL = 'https://www.indeed.com/jobs?q=php&sort=date&limit=50&fromage=30&start=' + str(start)
    print(URL)
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    jobDivs = soup.find_all('div', 'jobsearch-SerpJobCard')

    for div in jobDivs:
        jobKeys.append(div.attrs['data-jk'])

    if soup.find('span', text=re.compile('Next')) is not None:
        start += 50
        print(start)
    else:
        break

# Connect database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="lpm"
)
cursor = db.cursor()
query = 'INSERT IGNORE INTO indeed_jobs (job_key, title, salary, details, company, location, age, link, ' \
        'json, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'

for jobKey in jobKeys:
    print('Pulling data for Job :' + jobKey)
    response = requests.get('https://www.indeed.com/viewjob?from=vjs&vjs=1&jk=' + jobKey)
    print(response.status_code)
    jobDetails = response.json()

    response = requests.get('https://www.indeed.com/viewjob?jk=' + jobKey)
    print(response.status_code)
    soup = BeautifulSoup(response.content, 'html.parser')
    descDiv = soup.find(id='jobDescriptionText')
    if descDiv:
        details = str(descDiv)
    else:
        details = ''

    title = jobDetails['jobTitle']
    salary = jobDetails['ssT']
    company = jobDetails['sicm']['cmN']
    location = jobDetails['jobLocation']
    age = jobDetails['vfvm']['jobAgeRelative']
    link = 'https://www.indeed.com/viewjob?jk=' + jobKey
    jsonStr = json.dumps(jobDetails)
    ts = datetime.now().timestamp()

    values = (jobKey, title, salary, details, company, location, age, link, jsonStr, ts, ts)
    cursor.execute(query, values)
    db.commit()

db.close()
