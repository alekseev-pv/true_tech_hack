import numpy as np

import pandas as pd

from bs4 import BeautifulSoup

import requests

import json

# Берём:
# Частным клиентам
# Продукты и приложения

# Не берём:
# Бизнесу и предпринимателям
# Партнёрам


print("hi")

final_data = []

main_url = "https://support.mts.ru"

response = requests.get(main_url)
print(response)

bs = BeautifulSoup(response.text,"lxml")
#print(bs)

print("")
print("Частным клиентам 3 группы:")

for a_group in bs.find_all('div', 'services-product-groupstyles__ServicesGroupList-sc-n0cyel-2'):
    print("*")
    for a in a_group.find_all('a'):
        print("")

        product_name = a.find('div','').text
        curr_link = a['href']

        print(product_name)
        print(curr_link)

        print('')
        print('subpage')

        if 'https' not in curr_link:
            curr_url = main_url + curr_link
        else:
            print("skip")
            continue

        response = requests.get(curr_url)
        print(response)

        curr_page = BeautifulSoup(response.text,"lxml")
        
        links_field = curr_page.find('div', 'sections-viewstyles__SectionsList-sc-1blgtes-0')
        for a in links_field.find_all('a'):
            print(a['href'])
            print(a.find('span').text)

        page_data = curr_page.find('script', id="__NEXT_DATA__")

        j = json.loads(page_data.text)
                                          
        print('!!!')

        t = json.loads(j['props']['pageProps']['initialState'])

        curr_sublinks = []
        curr_all_text = ""
    
        for link in t['article']['currentProduct']['sections']:
            article_name = link['name']
            article_url = curr_url + '/' + link['sefUrl'] + '/' + link['topArticle']['sefUrl']
        
            print(article_name)
            print(article_url)

            art = requests.get(article_url)

            print("check:")
            print(art)

            curr_article = BeautifulSoup(art.text,"lxml")

            print("final sub articles:")

            for fsb in curr_article.find_all('div', 'article-view-sidebarstyles__LineWrapper-sc-64uio7-1'):

                final_article_link = fsb.find('a')

                final_url = main_url + final_article_link['href']
                final_name = final_article_link.text
                
                print(final_url)
                print(final_name)

                final_art = requests.get(final_url)
                print("check:")
                print(art)
                
                curr_article = BeautifulSoup(final_art.text,"lxml")

                article_data = curr_article.find('script', id="__NEXT_DATA__")
                
                jj = json.loads(article_data.text)
                
                sub_articles = json.loads(jj['props']['pageProps']['initialState'])

                article_content = sub_articles['article']['currentArticle']['content']

                article_content_clean = BeautifulSoup(article_content,"lxml").get_text(separator=" ", strip=True).replace(';','.')
        
                print(article_name)
                
                print("!!")
                print(article_content_clean)

                final_data.append([final_url, final_name, article_content_clean, product_name])


print("")
print("Продукты")
products = bs.find('div','segment-productsstyles__SegmentProducts-sc-5z3ye-0')

for a in products.find_all('a'):
    product_name = a.find('div','').text
    curr_link = a['href']

    print(product_name)
    print(curr_link)

    print('')
    print('subpage')

    if 'https' not in curr_link:
        curr_url = main_url + curr_link
    else:
        print("skip")
        continue
    
    response = requests.get(curr_url)
    print(response)
    curr_page = BeautifulSoup(response.text,"lxml")
    links_field = curr_page.find('div', 'sections-viewstyles__SectionsList-sc-1blgtes-0')
    for a in links_field.find_all('a'):
        print(a['href'])
        print(a.find('span').text)    

    page_data = curr_page.find('script', id="__NEXT_DATA__")

    j = json.loads(page_data.text)
                                          
    print('!!!')

    t = json.loads(j['props']['pageProps']['initialState'])
    
    curr_sublinks = []
    curr_all_text = ""
    
    for link in t['article']['currentProduct']['sections']:
        article_name = link['name']
        article_url = curr_url + '/' + link['sefUrl'] + '/' + link['topArticle']['sefUrl']
        
        print(article_name)
        print(article_url)

        art = requests.get(article_url)

        print("check:")
        print(art)

        curr_article = BeautifulSoup(art.text,"lxml")

        print("final sub articles:")

        for fsb in curr_article.find_all('div', 'article-view-sidebarstyles__LineWrapper-sc-64uio7-1'):

            final_article_link = fsb.find('a')

            final_url = main_url + final_article_link['href']
            final_name = final_article_link.text
            
            print(final_url)
            print(final_name)

            final_art = requests.get(final_url)
            print("check:")
            print(art)
            
            curr_article = BeautifulSoup(final_art.text,"lxml")

            article_data = curr_article.find('script', id="__NEXT_DATA__")
            
            jj = json.loads(article_data.text)
            
            sub_articles = json.loads(jj['props']['pageProps']['initialState'])

            article_content = sub_articles['article']['currentArticle']['content']

            article_content_clean = BeautifulSoup(article_content,"lxml").get_text(separator=" ", strip=True).replace(';','.')
        
            print(article_name)
            
            print("!!")
            print(article_content_clean)

            final_data.append([final_url, final_name, article_content_clean, product_name])


print()

# print(final_data)

with open('result.csv', 'w', encoding='utf-8') as f:
    f.write("url;name;content;product")
    f.write('\n')

    for s in final_data:
        f.write(str(';'.join(s)))
        f.write('\n')

print('final!')