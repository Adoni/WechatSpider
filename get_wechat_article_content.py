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


def get_content(page_content):
    page_content = page_content.xpath('.//*[@id="js_content"]')[0]
    p = page_content.xpath('.//p | .//img')
    content = []
    print(len(p))
    for i, pp in enumerate(p):
        # print(i)
        t = pp.xpath('string(.)')
        if t != '':
            content.append(t)
        imgs = pp.xpath('@data-src')
        if imgs != []:
            content += imgs
    return content


def main():
    queue = get_message_queue(sys.argv[1], 'wechat_article_content_queue')
    firefoxProfile = FirefoxProfile()
    firefoxProfile.set_preference('permissions.default.stylesheet', 2)
    firefoxProfile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                                  'false')
    firefoxProfile.set_preference('permissions.default.image', 2)
    # driver = webdriver.Firefox(firefoxProfile)
    driver = webdriver.PhantomJS(service_args=['--load-images=false'])
    print('Driver is ready')
    driver.implicitly_wait(5)
    db = get_database(sys.argv[1]).article_contents
    finished_count = 0
    while 1:
        # time.sleep(random.uniform(1, 1))
        if queue.empty():
            print('Already finished')
            print('Waiting for new query ...')
        url = queue.get().decode()
        print('start')
        try:
            driver.get(url)
        except:
            print(url)
            print('!!!!!!!!!!!!!Cannot get web page!!!!!!!!')
            continue
        if driver.title.strip() == '':
            print(url)
            print('Empty title')
            continue
        locator = (By.XPATH, '//*[@id="page-content"]')
        try:
            WebDriverWait(driver, 10,
                          0.5).until(EC.presence_of_element_located(locator))
            data = dict()
            data['href'] = url
            page_content = etree.HTML(
                driver.find_element_by_id('page-content')
                .get_attribute('innerHTML'))
            if page_content == None:
                print('Not find page-content')
                print(url)
                continue
            data['title'] = ''.join(
                page_content.xpath('//*[@id="activity-name"]/text()')).strip()
            data['post-user'] = ''.join(
                page_content.xpath('//*[@id="post-user"]/text()')).strip()
            data['post-date'] = ''.join(
                page_content.xpath('//*[@id="post-date"]/text()')).strip()
            data['origin'] = ''.join(
                page_content.xpath('//*[@id="copyright_logo"]/text()')).strip()
            data['title2'] = ''.join(
                page_content.xpath(
                    '//*[@class="rich_media_meta rich_media_meta_text"]/text()'
                )).strip()
            data['content'] = get_content(page_content)
            # print(data)
            print('end')
            assert (len(data['content']) > 0)
            db.insert_one(data)
            finished_count += 1
            if finished_count % 100 == 0:
                print('Quit driver')
                driver.quit()
                time.sleep(random.random() * 3 + 1)
                driver = webdriver.PhantomJS(
                    service_args=['--load-images=false'])
                print('Driver is ready')
                driver.implicitly_wait(5)
        except Exception as e:
            print(url)
            print('Error')
            print(e)
            with open('./fail_ids_for_article_content.data', 'a') as fout:
                fout.write('%s\n' % url)
            time.sleep(random.random() * 3 + 1)


if __name__ == '__main__':
    main()
