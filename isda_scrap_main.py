import os
import logging
import traceback
import datetime as dt

import pandas as pd
import requests

from bs4 import BeautifulSoup
from tqdm import tqdm


logger = logging.getLogger(__file__)


def get_article_data_list(list_url):
    try:
        response = requests.get(list_url)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        article_list = soup.find_all('article', {'class': "two-col-content-panel"})
        article_data_list = []

        for article in tqdm(article_list):
            entry_meta = article.find('div', {'class': 'entry-meta'})
            published_date = entry_meta.find('span', {'class': 'published-date'})
            if published_date is None:
                # ToDo: event & online 케이스 분기 처리 추가 필요
                continue
            else:
                published_date = published_date.text
            published_date = published_date.replace('\n', '').replace('\t', '')
            published_date = dt.datetime.strptime(published_date, '%B %d, %Y')
            published_date = published_date.strftime("%Y%m%d")

            subcategory_name = entry_meta.find('a').text
            subcategory_link = entry_meta.find('a').attrs['href']

            entry_title = article.find('h3', {'class': 'entry-title'})
            entry_link = entry_title.find('a').attrs['href']
            entry_title_text = entry_title.find('a').text
            entry_title_text = entry_title_text.replace('\n', '').replace('\t', '')

            entry_tags = article.find('p', {'class': 'default-tags-list'})
            tags_list = entry_tags.find_all('a')
            tags_list = [tags.text for tags in tags_list]
            tags_list_text = ','.join(tags_list)

            article_data = [published_date, subcategory_name, entry_title_text, tags_list_text, entry_link]
            print(article_data)

            article_data_list.append(article_data)

    except Exception as exp:
        msg = traceback.format_exc()
        print(entry_meta)
        print(msg)

        return list()

    return article_data_list


base_url = 'https://www.isda.org'
sub_url_list = ['/category/margin/isda-simm',
                '/tag/isda-simm/',
                '/tag/simm', ]

article_data_list = []
for sub_url in sub_url_list:
    list_url = base_url + sub_url
    article_data_list = article_data_list + get_article_data_list(list_url)

df_new = pd.DataFrame(article_data_list, columns=['pub_date', 'subcategory', 'title', 'tags_list', 'url'])
df_new = df_new.drop_duplicates('title')
df_new = df_new.sort_values('pub_date', ascending=False)
# df_new.to_csv('isda_simm.csv', sep='|', index=False)

df_old = pd.read_csv('isda_simm.csv', sep='|')
max_date_old = str(df_old.pub_date.max())
max_date_new = df_new.pub_date.max()

print('max_date_old', max_date_old)
print('max_date_new', max_date_new)

df_new_only = pd.DataFrame()
if max_date_new > max_date_old:
    df_new_only = df_new[df_new.pub_date > max_date_old]

    df = pd.concat([df_new, df_old])
    df = df.drop_duplicates('title')
    df = df.sort_values('pub_date', ascending=False)
    df.to_csv('isda_simm.csv', sep='|', index=False)
else:
    df = df_old.copy()

print('==== ISDA SIMM New Notices ====')
print(df_new_only)
print()
print('==== ISADA SIMM Recent 5 Notices ====')
print(df[['pub_date', 'subcategory', 'title']].head())
