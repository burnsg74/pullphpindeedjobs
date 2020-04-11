import argparse
import json
import re
from datetime import datetime
from os import path
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def filecheck(filename):
    if not path.exists(filename):
        with open(filename, 'w') as outfile:
            json.dump([], outfile)


def main():
    indeedJobKeysfile = Path('/home/greg/notes/jobs/leads/indeed-job-keys.json')
    filecheck(indeedJobKeysfile)
    with open(indeedJobKeysfile) as json_file:
        existingJobKeys = json.load(json_file)
    print(type(existingJobKeys))

    indeedJobfile = Path('/home/greg/notes/jobs/leads/indeed-jobs.json')
    filecheck(indeedJobfile)
    with open(indeedJobfile) as json_file:
        indeedJobs = json.load(json_file)

    parser = argparse.ArgumentParser(description='Web Scrape Indeed php jobs!')
    parser.add_argument("--a", default=1, type=int, help="From Age: Number of days back in time to search.")
    parser.add_argument("--search", default='php', type=str, help="Search Query: The text you want to search for.")

    args = parser.parse_args()
    searchQueryText = args.search
    searchQueryAge = args.a

    print('Search for [' + searchQueryText + '] ' + str(searchQueryAge) + ' days ago to present.')

    # Get jk ids
    jobKeys = []
    start: int = 0
    while True:
        URL = 'https://www.indeed.com/jobs?q=' + str(args.search) + '&sort=date&limit=50&fromage=' + \
              str(args.a) + '&start=' + str(start)
        print(URL)
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        jobDivs = soup.find_all('div', 'jobsearch-SerpJobCard')

        for div in jobDivs:
            jobKey = div.attrs['data-jk']
            print('Job Key : ' + jobKey)
            if jobKey in existingJobKeys:
                print('Already got it skip')
                continue
            jobKeys.append(jobKey)
            existingJobKeys.append(jobKey)

        # Goto Next Page
        if soup.find('span', text=re.compile('Next')) is not None:
            start += 50
            print(start)
        else:
            break

    with open(indeedJobKeysfile, 'w') as outfile:
        json.dump(existingJobKeys, outfile)

    for jobKey in jobKeys:

        # @TODO Add check if request fails
        print('Pulling data for Job :' + jobKey)
        response = requests.get('https://www.indeed.com/viewjob?from=vjs&vjs=1&jk=' + jobKey)
        print(response.status_code)
        jobDetails = response.json()

        # @TODO Add check if request fails
        response = requests.get('https://www.indeed.com/viewjob?jk=' + jobKey)
        print(response.status_code)
        soup = BeautifulSoup(response.content, 'html.parser')
        descDiv = soup.find(id='jobDescriptionText')
        if descDiv:
            details = str(descDiv)
        else:
            details = ''

        job = {
            "job_key": jobKey,
            "title": jobDetails['jobTitle'],
            "status": 'Lead',
            "salary": jobDetails['ssT'],
            "company": jobDetails['sicm']['cmN'],
            "location": jobDetails['jobLocation'],
            "link": 'https://www.indeed.com/viewjob?jk=' + jobKey,
            "ts": datetime.now().timestamp()
        }
        indeedJobs.append(job)

        f = open('/home/greg/notes/jobs/leads/indeed-job-' + jobKey + '.html', "w")
        f.write(details)
        f.close()

    print('Saving Jobs to file.')
    with open(indeedJobfile, 'w') as outfile:
        json.dump(indeedJobs, outfile)


if __name__ == "__main__":
    main()
