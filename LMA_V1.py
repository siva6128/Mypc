import requests
import smtplib
import pymysql
#import datetime
import sys
import configparser
from datetime import date
from datetime import timedelta
from requests import get
from requests.exceptions import ConnectionError
import json
from simplejson import JSONDecodeError

from bs4 import BeautifulSoup as Soup
import re
import uuid
from bs4 import BeautifulSoup 
#headers = requests.utils.default_headers()
#headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})

'''conn = pymysql.connect(host = 'mysql.dev.wonderwe.com',
                            port=33076,
                           user='trinesh',
                           password='trinesh1$',
                           db='wonderwe_development')
cursor = conn.cursor()'''

conn = pymysql.connect(host = '127.0.0.1',
                           port = 3306,
                           user = 'Aurobindo',
                           password='Aurobindo1@',
                           db = 'literaturemonitoring')
cursor = conn.cursor()

def retry(url):
    i = 0
    while i < 10:
        req = requests.get(url, proxies=proxies)
        print('i ',i)
        i+= 1
    print('Exit')

# current weekday
weekday = date.today().weekday()
#weekday = 0
print("weekday",weekday)

proxies = {'http': 'http://guest00242:Welcome12@10.0.1.85:3128/'}

#to_date ='2019-11-20'
to_date = date.today()
print('todays date', to_date)

from_date = to_date - timedelta(days=7)
#from_date='2019-10-31'
duration = str(from_date)
print('from_date ',from_date)

# sql query to check duplicates
date_check = ("select count(*) from lm_search_article  where sourced_date = " + "'" + str(to_date) + "'" )
print('date_check ',date_check)

cursor.execute(date_check)
result = cursor.fetchone()
date = []
print('Result ',result)

count = 0

#if (result[0] == 0):
print("job sucessfully started")

if weekday == 0:
    terms =  ("SELECT distinct search_criteria FROM lm_product_info WHERE product_name REGEXP '^[A-B].*$';")
    type_of_article = 'Approved'
    date = 7
    #date = to_date.day - from_date.day
    print('date ',date)

elif weekday == 1:
    terms =  ("SELECT distinct search_criteria FROM lm_product_info WHERE product_name REGEXP '^[F-J].*$';")
    type_of_article = 'Approved'
    #date=8
    date = to_date.day - from_date.day
    print('date ',date)

elif weekday == 2:
    terms =  ("SELECT distinct search_criteria FROM lm_product_info WHERE product_name REGEXP '^[O-U].*$';")
    type_of_article = 'Approved'
    #date=8
    date = to_date.day - from_date.day
    print('date ',date)

else:
    terms = ("SELECT distinct search_criteria FROM lm_newfiling_product_info;")
    type_of_article = 'New filling'
    date = to_date.day - from_date.day
    print('date ',date)

cursor.execute(terms)
result_query = cursor.fetchall()
options = []

for row in result_query:
    options.append(row[0])

for term in options:
    product_options = [term.replace('and',',').replace('+',' ').split(',') for term in options]
    product_list = [product.strip() for sublist in product_options for product in sublist]


#print(product_list)
print()

molecule_list_1= []

if weekday == 0:
    print('weekday ',weekday)
    for elements in product_list:
        new_list = re.findall('^[A-B].*$', elements)
        for molecule_test in new_list:
            molecule_list_1.append(molecule_test)

elif weekday == 1:
    print('weekday ',weekday)
    for elements in product_list:
        new_list = re.findall('^[F-J].*$', elements)
        for molecule_test in new_list:
            molecule_list_1.append(molecule_test)

elif weekday == 2:
    print('weekday ',weekday)
    for elements in product_list:
        new_list = re.findall('^[O-U].*$', elements)
        for molecule_test in new_list:
            molecule_list_1.append(molecule_test)

else:
    print('weekday ',weekday)
    #molecule_list.append(product_list)
    molecule_list_1 = product_list

molecule_list = list(dict.fromkeys(molecule_list_1))
print(molecule_list)   
print('length ',len(molecule_list))


for molecule in molecule_list:
    #print('molecule ',molecule)
    try:
        url ='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=' + \
molecule + '&reldate='+str(date) +'&datetype=pdat&retmax=100000&retmode=json'

        print('url :',url)

        page = get(url, proxies = proxies)
    except ConnectionError as e:
        print('page not found')
        continue
    try:   
        idlist = page.json()['esearchresult']['idlist']
        print(idlist, molecule)
    except (JSONDecodeError,KeyError) as j:
        pass

    for ids in idlist:
        count = count + 1
        print('çount ',count)
        try:
            url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=' + \
                ids + '&retmode=json&rettype=xml'
            print('id_urls :',url)
            page = get(url, proxies = proxies)

        except ConnectionError as e:
            retry(url)
            pass

        soup = Soup((page.content).decode("utf-8"), 'lxml')
        PubmedArticles = soup.find_all('pubmedarticle')
        fulljournalinformation = ''

        for PubmedArticle in PubmedArticles:
            pubmedid = PubmedArticle.find(
                'articleid', {
                    'idtype': 'pubmed'}).text.strip()
            try:
                doi = PubmedArticle.find(
                    'articleid', {
                    'idtype': 'doi'}).text.strip()
            except BaseException:
                doi = ''
            try:
                journal = PubmedArticle.find('medlineta').text
                print('journal ',journal)
            except AttributeError:
                journal = 'not available'
                print('journal ',journal)
                continue

            try:
                journalinformation = PubmedArticle.find('isoabbreviation').text
            except AttributeError:
                continue


            #print("journalinformation:",journalinformation)

            publicationdate = PubmedArticle.find('pubdate').text
            publicationdate = '-'.join(publicationdate.strip().split('\n')[::-1])

            fulljournalinformation =  str(journalinformation) + " " + str(publicationdate) + " " + str(doi)

            result_title = PubmedArticle.find('articletitle').text.strip()
            print()
            #print('result_title ',result_title)
            try:
                result_abstract = PubmedArticle.find('abstract').text.strip().strip()
                #print('result_abstract :',result_abstract)
            except BaseException:
                result_abstract = ''

            authorlist = PubmedArticle.findAll('author')
            authors = ''
            affliation_info = ''

            #print("successfull")

            for a in authorlist:
                try:
                    initial = a.find('initials').text.encode('utf-8').strip()
                except BaseException:
                    initial = ''

                try:
                    forename = a.find('forename').text.encode('utf-8').strip()
                except BaseException:
                    forename = ''

                try:
                    lastname = a.find('lastname').text.encode('utf-8').strip()
                except BaseException:
                    lastname = ''

                authors += (str(initial) + " " + str(forename) + " " + str(lastname) + ", ")
                temp = str(initial) + " " + str(forename) + " " + str(lastname)

                for t in a.findAll('affiliation'):
                    affliation_info += str(temp) + " " + str(t.text.encode('utf-8').strip()) + " "

        currentweek = to_date.isocalendar()[1]
        #print('currentweek ',currentweek)

        sourced_date = to_date
        #print('sourced_date ',sourced_date)
        try:
            url = "https://www.ncbi.nlm.nih.gov/pubmed/"+ids
            print('url ',url)
        except ConnectionError as e:
            retry(url)
            pass
        req = requests.get(url, proxies=proxies)
        soup = BeautifulSoup(req.content, 'html.parser')
        #print('list ',list(soup.find_all("a",journal=journal)))
        #print()
        link = list(soup.find_all("a",journal=str(journal)))
        #print('link ',link)
        #print()
        myString = str(link)
        #print('myString ',myString)
        #print()
        try:
            full_text_link = re.search('(?P<url>https?://[^\s]+)', myString).group("url").strip('"')
            print('full_text_link :',full_text_link)

        except AttributeError as a:
            full_text_link = 'full_text_link not available'
            print('full_text_link :', full_text_link)

        
            '''print(
            '\n term :', molecule,
            '\n fulljournalinformation :', fulljournalinformation,
            '\n pubmedid :', pubmedid,
            '\n url :', url,
            '\n doi :', doi,
            '\n publicationdate :', publicationdate,
            '\n result_title :', result_title,
            '\n result_abstract :', result_abstract,
            '\n authors :', authors,
            '\n affliation_info :', affliation_info,
            '\n sourced_date :', sourced_date,
            '\n duration :', duration,
            '\n currentweek :', currentweek,
            '\n type_of_article:', type_of_article
            )'''

        cursor.execute(
                "insert into lm_search_article(search_term,journal_information,result_title,result_abstract,url,sourced_date,author,pubmedid,doi,publicationdate,duration_date,current_week,type_of_article, full_text_link) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (molecule,
                fulljournalinformation,
                result_title,
                result_abstract,
                url,
                sourced_date,
                affliation_info,
                pubmedid,
                doi,
                publicationdate,
                duration,
                currentweek,
                type_of_article,
                full_text_link
                ))
        conn.commit()
        print('inserted')
        print()
print('successful')
       

    
'''request_id = str(uuid.uuid1())
print('request_id ',request_id)
cursor.execute("insert into request_status (request_id,requested_for,articles_count) values (%s,%s,%s)", (request_id,'PUBMED',count))
conn.commit()
print('çount_',count)

try:
    get = requests.get('http://localhost:3000/api/generatereport')
    print(get.json)
except BaseException:
        print('err')                    
try:
    post = requests.get('http://localhost:3000/api/pubmedautoassignment')
    print(post.json)
except BaseException:
    print('err')
print("job completed")'''
