from newspaper import Article
import pandas as pd
import multiprocessing as mp
import uuid


def save_article(link):
    try:
        article = Article(link)
        article.download()
        article.parse()
        title = article.title
        publish_date = article.publish_date
        text = article.text
        pd.DataFrame(
            {'date': [publish_date],
             'title': [title],
             'text': [text],
             'link': [link]}
        ).set_index('date').to_csv('data/articles/{}.csv'.format(uuid.uuid4()))
    except:
        pass


with open('data/aapl_links.txt', 'r') as f:
    content = f.readlines()
f.close()

links = [i.strip() for i in content]

if __name__ == '__main__':
    pool = mp.Pool(mp.cpu_count())
    pool.map(save_article, links)
