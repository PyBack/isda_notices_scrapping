import os
import site
import logging
import traceback
import datetime as dt


import pandas as pd
import requests

from bs4 import BeautifulSoup
from tqdm import tqdm

src_path = os.path.dirname(__file__)
pjt_home_path = os.path.join(src_path, os.pardir)
pjt_home_path = os.path.abspath(pjt_home_path)

site.addsitedir(pjt_home_path)
site.addsitedir(pjt_home_path + '/src')

from send_mail import send_mail

logger = logging.getLogger(__file__)


def get_article_data_list(list_url):
    try:
        response = requests.get(list_url)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        article_list = soup.find_all('article', {'class': "two-col-content-panel"})
        article_data_list = []

        print('article cnt:', len(article_list))

        for article in article_list:
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
            # print(article_data)

            article_data_list.append(article_data)

    except Exception as exp:
        msg = traceback.format_exc()
        print(entry_meta)
        print(msg)

        return list()

    return article_data_list


def get_isda_new_articles():
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
    df_new['pub_date'] = df_new['pub_date'].astype(str)
    df_new = df_new.sort_values('pub_date', ascending=False)
    # df_new.to_csv('isda_simm.csv', sep='|', index=False)

    return df_new


def main(args):
    df_new = get_isda_new_articles()
    df_old = pd.read_csv(pjt_home_path + '/data/isda_simm.csv', sep='|')

    max_date_old = str(df_old.pub_date.max())
    max_date_new = df_new.pub_date.max()

    print('max_date_old', max_date_old)
    print('max_date_new', max_date_new)

    df_new_only = pd.DataFrame()
    if max_date_new > max_date_old:
        df_new_only = df_new[df_new.pub_date > max_date_old]

        df = pd.concat([df_new, df_old])
        df = df.drop_duplicates('title')
        df['pub_date'] = df['pub_date'].astype(str)
        df = df.sort_values('pub_date', ascending=False)
        df.to_csv(pjt_home_path + '/data/isda_simm.csv', sep='|', index=False)
    else:
        df = df_old.copy()

    # pd.set_option('display.max_colwidth', None)

    main_text = f"""
    ==== ISDA SIMM New Notices ====
    {df_new_only}
    
    ==== ISDA SIMM Recent 5 Notices ====
    {df[['pub_date', 'subcategory', 'title']].iloc[:5].to_string()}
    """

    print(main_text)
    send_mail('ggtt7@naver.com', pwd=args.pwd + "CH",
              to_mail_list=['ggtt7@naver.com', 'hj.edward.kim@kbfg.com'],
              mail_title='ISDA SIMM Notices',
              mail_text=main_text
              )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pwd",
        type=str,
        default="",
    )

    args = parser.parse_args()
    main(args)
