# -*- coding: utf-8 -*-
import time
import random
import requests
from lxml import etree
import json
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
sys.path.append('..')
from RedisQueue import RedisQueue
from utils import get_database
from utils import get_message_queue


def main():
    queue = get_message_queue(sys.argv[1],
                              'wechat_official_account_content_queue')
    firefoxProfile = FirefoxProfile()
    # firefoxProfile.set_preference('permissions.default.stylesheet', 2)
    firefoxProfile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                                  'false')
    firefoxProfile.set_preference('permissions.default.image', 2)
    driver = webdriver.Firefox(firefoxProfile)
    # driver = webdriver.PhantomJS(service_args=['--load-images=false'])
    print('Driver is ready')
    driver.implicitly_wait(10)
    # driver.set_page_load_timeout(30)
    db = get_database(sys.argv[1]).wechat_article_list
    while 1:
        if queue.empty():
            print('Already finished')
            print('Waiting for new query ...')
        #wechat_id = queue.get().decode()
        wechat_id = 'HIT_SCIR'
        print('Crawling %s' % wechat_id)
        url = 'http://www.newrank.cn/public/info/detail.html?account=%s' % wechat_id

        try:
            driver.get(url)
        except:
            print('!!!!!!!!!!!!!Cannot get web page!!!!!!!!')
            time.sleep(3)
            continue
        if (driver.title == u'页面错误'):
            print('%s not included' % (wechat_id))
            continue
        locator = (By.XPATH, '//*[@id="info_detail_article_lastest"]//li')
        try:
            WebDriverWait(driver, 20,
                          0.5).until(EC.presence_of_element_located(locator))
            elements = driver.find_elements_by_xpath(
                '//*[@id="info_detail_article_lastest"]//li')
            data = dict()
            data['str_id'] = wechat_id
            data['article_list'] = []
            for e in elements:
                article = dict()
                article['title'] = e.find_element_by_class_name(
                    'ellipsis').get_attribute('title')
                article['href'] = e.find_element_by_class_name(
                    'ellipsis').get_attribute('href')
                article['short_text'] = e.find_element_by_class_name(
                    'article-text').find_element_by_tag_name(
                        'a').get_attribute('title')
                article['date'] = e.find_element_by_class_name(
                    'info-detail-article-date').text
                article['read_count'] = e.find_element_by_class_name(
                    'read-count').text
                article['like_count'] = e.find_element_by_class_name(
                    'links-count').text
                article['position'] = e.find_element_by_class_name(
                    'tj').find_elements_by_tag_name('span')[1].text
                data['article_list'].append(article)
            assert len(data['article_list']) > 0
            record = db.find_one({'str_id': wechat_id})
            if record is None:
                print('Not find %s in database' % wechat_id)
                db.insert(data)
            else:
                print(len(record['article_list']))
                for article in data['article_list']:
                    if article not in record['article_list']:
                        record['article_list'].append(article)
                print(len(record['article_list']))
                db.replace_one({'str_id': wechat_id}, record)
        except Exception as e:
            print('Error')
            print(e)
            with open('./fail_ids_for_article_urls.data', 'a') as fout:
                fout.write('%s\n' % wechat_id)
            print('Not find id "info_detail_article_lastest" when crawl %s' %
                  wechat_id)

        sleep_time = random.uniform(1, 3)
        time.sleep(sleep_time)


if __name__ == '__main__':
    main()
