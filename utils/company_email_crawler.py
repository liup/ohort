#!/usr/bin/env python

# $HeadURL: http://localhost/svn/cohorti/trunk/cohorti/utils/company_email_crawler.py $
#      $Id: company_email_crawler.py 104 2010-11-22 19:48:33Z zeke $

import sys
import pprint
import pycurl
import StringIO
import re

def curlAURL(url):
    b = StringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.HTTPHEADER, ["Accept:"])
    c.setopt(pycurl.WRITEFUNCTION, b.write)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 5)
    c.perform()
    return b.getvalue()

def searchAPattern(pattern, content):
    m = re.search(pattern, content)
    return m

def getItem(pattern, html):
    m = searchAPattern(pattern, html)
    if (m):
        return m.group(2)
    return m

def getEmail(html):
    pattern = '(.*<B>@)(.*)(</B>.*)'
    return getItem(pattern, html)

def getURL(html):
    pattern = "(.*companyURL' value=')(.*)('>.*)"
    return getItem(pattern, html)

def getName(html):
    pattern = '(.*coheader">)(.*)(</span.*)'
    return getItem(pattern, html)

def getACompany(url):
    html = curlAURL(url)
    name = getName(html)
    email = getEmail(html)
    website = getURL(html)
    return name, email, website

def getCompanyBatch(num):
    url = 'http://www.lead411.com/top-companies-list.taf?&_start=' + str(num)
    lines = re.split('\r', curlAURL(url))
    batch = []
    for line in lines:
        m = re.search("(.*width=350><A HREF=')(.*)('>.*)", line)
        if (m):
            batch.append(m.group(2))
    return batch

def getCompanies(urls):
    for url in urls:
        url = 'http://www.lead411.com/' + url
        n, e, w = getACompany(url)
        print('---------------')
        if (n):
            print('name     : ' + n)
        else:
            print('name     : N/A')
        if (e):
            print('email    : ' + e)
        else:
            print('email    : N/A')
        if (w):
            print('website  : ' + w)
        else:
            print('website  : N/A')

def main():
    pages = 0
    while (pages < 21):
        num = pages * 100 + 1
        pages = pages + 1
        urls = getCompanyBatch(num)
        getCompanies(urls)

main()
