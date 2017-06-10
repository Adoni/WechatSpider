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
import pickle


def login_by_user():
    firefoxProfile = FirefoxProfile()
    driver2 = webdriver.Firefox(firefoxProfile)
    driver2.get('http://www.newrank.cn/')
    driver2.find_element_by_class_name('new-header-login.unlogin').click()
    print('请在页面中登录')
    raw_input('Input Enter to continue')
    pickle.dump(driver2.get_cookies(), open('./cookies.data', 'wb'))
    driver2.quit()


def login_from_cookie(driver):
    try:
        cookie = pickle.load(open('./cookies.data', 'rb'))
    except:
        return
    driver.get('http://www.newrank.cn/')
    for cc in cookie:
        try:
            if cc['domain'].startswith('.'):
                cc['domain'] = 'www' + cc['domain']
            driver.add_cookie(cc)
        except Exception as e:
            print(e)
            print(cc)
            print('i')
    driver.get('http://www.newrank.cn/')


class contain_something(object):
    """An expectation for checking the title of a page.
    title is the expected title, which must be an exact match
    returns True if the title matches, false otherwise."""

    def __init__(self, xpathes):
        self.xpathes = xpathes

    def __call__(self, driver):
        for xpath in self.xpathes:
            try:
                driver.find_element_by_xpath(xpath)
                return True
            except:
                continue
        return False


def main():
    queue = get_message_queue(sys.argv[1], 'wechat_account_info_queue')
    db = get_database(sys.argv[1]).wechat_account_info
    firefoxProfile = FirefoxProfile()
    # firefoxProfile.set_preference('permissions.default.stylesheet', 2)
    firefoxProfile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so',
                                  'false')
    firefoxProfile.set_preference('permissions.default.image', 2)
    driver = webdriver.Firefox(firefoxProfile)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)
    login_from_cookie(driver)
    try:
        driver.find_element_by_class_name('new-header-login.unlogin')
        login_by_user()
        login_from_cookie(driver)
    except Exception as e:
        pass
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
        locator = contain_something([
            './/*[@class="tag-name-list"]//li[1]',
            './/*[@class="tag-name-list"]//a[1]'
        ])

        try:
            WebDriverWait(driver, 10, 0.5).until(locator)
            info_tree = etree.HTML(
                driver.find_element_by_class_name('info-detail-head')
                .get_attribute('innerHTML'))
            account_info = dict()
            account_info['_id'] = wechat_id
            account_info['str_id'] = wechat_id
            account_info['name'] = info_tree.xpath(
                './/*[@class="info-detail-head-weixin-name"]/span')[0].xpath(
                    'string(.)').strip()
            account_info['description'] = info_tree.xpath(
                './/*[@class="info-detail-head-weixin-fun-introduce ellipsis"]/@title'
            )[0]
            account_info['category'] = info_tree.xpath(
                './/*[@class="info-detail-head-classify-subname"]/a/text()')
            account_info['fans_count'] = info_tree.xpath(
                './/*[@class="detail-fans-counts"]/@data')[0]
            try:
                driver.find_element_by_xpath(
                    './/*[@class="info-detail-head-classify"]//*[@class="detail-edit info-detail-edit detail-pic"]'
                ).click()
                html = driver.find_element_by_id(
                    'current_tag_list').get_attribute('innerHTML')
                account_info['tags'] = etree.HTML(html).xpath('.//a/text()')
            except:
                account_info['tags'] = []
            print(account_info)
            continue
            db.insert_one(account_info)
        except Exception as e:
            print(e)
            print('Error')
            with open('./fail_ids_for_user_info.dat', 'a') as fout:
                fout.write('%s\n' % wechat_id)
        # time.sleep(random.uniform(1, 3))


if __name__ == '__main__':
    main()
