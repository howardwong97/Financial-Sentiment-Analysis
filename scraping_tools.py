def get_tweets(query: str, since_date: str, until_date: str, username='', max_tweets=0):
    import GetOldTweets3 as got
    import pandas as pd
    import time
    from datetime import timedelta
    import sys

    since_date = pd.to_datetime(since_date)
    until_date = pd.to_datetime(until_date)
    delta = until_date - since_date
    days = []
    for i in range(delta.days + 1):
        days += [(since_date + timedelta(days=i)).strftime('%Y-%m-%d')]

    # Trying to avoid rate limits, so create a date range:
    sleep_mins = 15
    max_attempts = 3
    error = None

    text = []
    user = []
    date = []
    retweets = []
    favorites = []

    for day in days:
        attempts_at_date = 0
        if error != 'KeyboardInterrupt':
            if attempts_at_date < max_attempts:
                attempts_at_date += 1
                try:
                    if username == '':
                        tweetCriteria = got.manager.TweetCriteria().setQuerySearch(query) \
                            .setSince(since_date) \
                            .setUntil(until_date) \
                            .setMaxTweets(max_tweets) \
                            .setEmoji('unicode') \
                            .setLang('en')
                    else:
                        tweetCriteria = got.manager.TweetCriteria().setQuerySearch(query) \
                            .setSince(since_date) \
                            .setUntil(until_date) \
                            .setMaxTweets(max_tweets) \
                            .setEmoji('unicode') \
                            .setLang('en') \
                            .setUsername(username)

                    tweet = got.manager.TweetManager.getTweets(tweetCriteria)

                    for i in tweet:
                        text += [i.text]
                        user += [i.username]
                        date += [i.date]
                        retweets += [i.retweets]
                        favorites += [i.favorites]
                except KeyboardInterrupt:
                    error = 'KeyboardInterrupt'
                    break
                except:
                    try:
                        print('Twitter is getting suspicious...')
                        print('Error retrieving date {}. Sleeping for {} minutes.'.format(day, sleep_mins))
                        for t in range(1, sleep_mins + 1):
                            sys.stdout.write(str(t) + '.. ')
                            sys.stdout.flush()
                            time.sleep(60)
                    except KeyboardInterrupt:
                        break
        else:
            print('Attempt {} at {} failed. Exiting.'.format(max_attempts, day))

    df = pd.DataFrame({'Date': date, 'User': user, 'Tweet': text, 'Favorites': favorites, 'Retweets': retweets})
    df.set_index('Date', inplace=True)
    df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S', utc=True)
    df.sort_index(inplace=True)
    df.drop_duplicates(subset="Tweet", keep=False, inplace=True)
    print(len(df), "relating to", query, "were found.")
    return df


def get_stocktwits(ticker: str, date: str):
    # Library imports
    from selenium import webdriver
    from datetime import datetime, timedelta
    from bs4 import BeautifulSoup
    import pandas as pd
    import numpy as np
    import pytz
    from pytz import timezone
    import time
    import os
    import re
    driver = webdriver.Chrome()
    url = 'https://stocktwits.com/symbol/{}'.format(str(ticker))
    driver.get(url)
    time.sleep(5)
    driver.implicitly_wait(30)
    # Scroll until the date is found
    find_date = pd.to_datetime(date)
    looking_for_element = True

    while looking_for_element:
        for i in range(0, 500):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.2)

        soup = BeautifulSoup(driver.page_source, 'lxml')
        each_post = soup.find_all('div', class_="st_29E11sZ st_jGV698i st_1GuPg4J st_qEtgVMo st_2uhTU4W")
        t = each_post[-1].find('a',
                               class_="st_28bQfzV st_1E79qOs st_3TuKxmZ st_3Y6ESwY st_GnnuqFp st_1VMMH6S").get_text()

        if pd.to_datetime(t[:-10]) < find_date:
            looking_for_element = False
        else:
            print("Current date:", pd.to_datetime(t[:-10]))
            print("Scrolling down")
            time.sleep(2)
            body = driver.find_element_by_css_selector('body')
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    dates = []
    post = []
    tag = []
    est = pytz.timezone('US/Eastern')

    for i in each_post:
        k = i.find('a', class_="st_28bQfzV st_1E79qOs st_3TuKxmZ st_3Y6ESwY st_GnnuqFp st_1VMMH6S").get_text()
        if (len(k) > 3) and (len(k) <= 8):
            k = pd.to_datetime(datetime.today().strftime('%Y-%m-%d')).replace(hour=pd.to_datetime(k).hour,
                                                                              minute=pd.to_datetime(
                                                                                  k).minute).tz_localize(est)
        elif len(k) <= 3:
            try:
                k = pd.to_datetime(datetime.now(timezone('Singapore'))).tz_convert(est) - timedelta(minutes=int(k[:-1]))
            except:
                k = pd.to_datetime(datetime.now(timezone('Singapore'))).tz_convert(est)
        else:
            k = pd.to_datetime(k).tz_localize(est)
        dates += [k]

        post += [i.find('div', class_="st_3SL2gug").get_text()]

        try:
            tag_info = i.find('div', class_="lib_XwnOHoV lib_3UzYkI9 lib_lPsmyQd lib_2TK8fEo").get_text()
        except:
            tag_info = np.nan

        tag += [tag_info]

    df = pd.DataFrame({'Timestamp': dates, 'Text': post, 'Tag': tag}).set_index('Timestamp').sort_index(ascending=False)
    print('Found', len(df), 'stocktwits about', ticker)
    driver.close()
    return df


def removeNonAscii(s): return "".join(i for i in s if ord(i) < 128)


def get_WSJ(query: str, start_date: str, end_date: str):
    from selenium import webdriver
    from bs4 import BeautifulSoup
    import pandas as pd
    from dateutil.tz import gettz
    from dateutil import parser
    from datetime import datetime, timedelta
    import numpy as np
    from pytz import timezone

    start_date = pd.to_datetime(start_date).strftime('%Y/%m/%d')
    end_date = pd.to_datetime(end_date).strftime('%Y/%m/%d')
    driver = webdriver.Chrome()
    driver.implicitly_wait(30)

    search_term = ''

    for i in query.split():
        if i == query:
            search_term = query
            break
        else:
            if i == query.split()[-1]:
                search_term = search_term + i
            else:
                search_term = search_term + i + '%20'

    page_no = 1
    timestamps = []
    headlines = []
    descriptions = []

    while True:

        url = "https://www.wsj.com/search/term.html?KEYWORDS={}".format(search_term) + "&min-date={}".format(
            str(start_date)) + "&max-date={}".format(str(
            end_date)) + "&isAdvanced=true&andor=AND&sort=date-desc&source=wsjarticle,wsjblogs,wsjvideo,interactivemedia,sitesearch,wsjpro&page={}".format(
            str(page_no))

        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        print('Scraping: ', url)
        # Get headline
        for i in soup.find_all('h3', class_='headline'):
            headlines += [removeNonAscii(i.get_text()[1:-1])]

        # Get summary
        for i in soup.find_all('div', class_="summary-container"):
            descriptions += [removeNonAscii(i.get_text()[1:-1])]

        # Get timestamp information
        tzinfos = {"EST": gettz("EST")}
        for i in soup.find_all('time', class_="date-stamp-container"):
            timestamp = i.get_text().replace('ET', 'EST')
            if len(timestamp) <= 12:
                timestamps += [(datetime.now(timezone('EST')) - timedelta(hours=int(timestamp.split()[0]))).strftime(
                    "%Y-%m-%d %H:%M:%S %Z")]
            else:
                timestamps += [parser.parse(timestamp, tzinfos=tzinfos).strftime("%Y-%m-%d %H:%M:%S %Z")]

        # If descriptions is missing for this particular iteration
        if len(descriptions) < len(timestamps):
            descriptions += [np.nan]

        # Check if need to go to next page
        try:
            current_page = soup.find_all('li', class_='results-count')[0].get_text().replace('-', ' ').split()
        except:
            break
        numbers = []
        for word in current_page:
            if word.isdigit():
                numbers.append(int(word))

        if numbers[1] == numbers[2]:
            break
        else:
            page_no += 1
    try:
        print('Total Articles Returned:', len(timestamps))
        print('From:', timestamps[0])
        print('To:', timestamps[-1])
        df = pd.DataFrame({'Timestamp': timestamps, 'Headline': headlines, 'Summary': descriptions}).set_index(
            'Timestamp').sort_index(ascending=False)
        print('Completed!')
        return df
    except:
        pass
    driver.close()
    driver.quit()


def get_FT_news(query: str, start_date: str, end_date: str):
    from bs4 import BeautifulSoup
    import pandas as pd
    import numpy as np
    import requests
    import time
    import re
    '''
    Scrape news from Financial Times. 

    ------------ INPUTS --------------
    query      : (str) desired search term
    start_date : (str) 'YYYY-MM-DD'
    end_date   : (str) 'YYYY-MM-DD'
    Returns a Pandas DataFrame with:

    ----------- OUTPUTS -------------
    Pandas DataFrame:
    Timestamps      : Index (Pandas DateTime object)
    Headlines       : (str)
    Summary         : (str)

    '''
    page_no = 1
    timestamps = []
    headlines = []
    descriptions = []

    while True:

        url = 'https://www.ft.com/search?q=' + query + '&page={}&'.format(
            str(page_no)) + 'contentType=article&dateTo=' + end_date + \
              '&dateFrom=' + start_date + '&sort=relevance&expandRefinements=true'
        time.sleep(5)
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')

        # See whether all pages have been scraped yet:
        string = re.sub('\s+', ' ', soup.find('h2', class_="o-teaser-collection__heading "
                                                           "o-teaser-collection__heading--half-width").get_text(

        )).replace('‒', ' ')
        numbers = []

        for word in string.split():
            if word.isdigit():
                numbers.append(int(word))

        try:
            if numbers[0] > numbers[2]:
                break

        except:
            print('No results found.')
            break

        print('Scraping: ', url)

        for i in soup.find_all('time', class_='o-teaser__timestamp-date'):
            timestamps += [pd.to_datetime(i['datetime'])]

        for i in soup.find_all('a', class_='js-teaser-heading-link'):
            headlines += [i.get_text()]

        for i in soup.find_all('a', class_="js-teaser-standfirst-link"):
            descriptions += [re.sub('\s+', ' ', i.get_text()).replace('...', '')]

        if len(timestamps) < len(headlines) and len(timestamps) < len(descriptions):
            timestamps += [np.nan]
        if len(headlines) < len(timestamps) and len(headlines) < len(descriptions):
            headlines += [np.nan]
        if len(descriptions) < len(timestamps) and len(descriptions) < len(headlines):
            descriptions += [np.nan]

        page_no += 1

    df = pd.DataFrame({'Timestamp': timestamps, 'Headline': headlines, 'Summary': descriptions}).set_index(
        'Timestamp').sort_index(ascending=False)
    return df


def get_reddit_comments(search_terms: list, subreddits: list):
    import praw
    from psaw import PushshiftAPI
    import pandas as pd
    import numpy as np
    import sys

    reddit = praw.Reddit(client_id="t6zhrU4Kfc2nRA",
                         client_secret="hosJ2fHU1z47MVfxRF-onhwxqpQ",
                         user_agent="sentiment_analysis")

    api = PushshiftAPI(reddit)
    body, timestamp, subreddit_name = [], [], []

    for query in search_terms:

        for subreddit in subreddits:
            print('Searching ' + subreddit + ' for:', query)
            gen = api.search_submissions(q=query, subreddit=subreddit)
            comment_counter = 0
            submission_counter = 0

            for submission in list(gen):
                submission.comments.replace_more(limit=None)
                submission_counter += 1
                sys.stdout.write("\033[F")  # back to previous line
                sys.stdout.write("\033[K")  # clear line
                print(str(submission_counter) + ' posts found')

                for comment in list(submission.comments):
                    body += [comment.body]
                    timestamp += [pd.to_datetime(int(comment.created_utc), unit='s').tz_localize('UTC')]
                    subreddit_name += [comment.subreddit.display_name]
                    comment_counter += 1
                    sys.stdout.write("\033[F")  # back to previous line
                    sys.stdout.write("\033[K") # clear line
                    print(str(comment_counter) + ' comments found')
                    # Check that all are same length, otherwise just add a nan
                    if len(body) < len(timestamp) or len(body) < len(subreddit_name):
                        body += [np.nan]
                    elif len(timestamp) < len(body) or len(timestamp) < len(subreddit_name):
                        timestamp += [np.nan]
                    elif len(subreddit_name) < len(body) or len(subreddit_name) < len(timestamp):
                        subreddit_name += [np.nan]

    df = pd.DataFrame({'Timestamp': timestamp, 'Body': body, 'Subreddit': subreddit_name}).dropna()
    df.set_index('Timestamp', inplace=True)
    df.sort_index(inplace=True)
    df = df.drop_duplicates()
    return df