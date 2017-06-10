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
import pickle
import requests


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


class WechatSpider:
    def __init__(self):
        firefoxProfile = FirefoxProfile()
        # firefoxProfile.set_preference('permissions.default.stylesheet', 2)
        firefoxProfile.set_preference(
            'dom.ipc.plugins.enabled.libflashplayer.so', 'false')
        firefoxProfile.set_preference('permissions.default.image', 2)
        self.driver = webdriver.Firefox(firefoxProfile)
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(5)
        self.login()
        self.content_driver = webdriver.Firefox(firefoxProfile)
        self.content_driver.set_page_load_timeout(30)
        self.content_driver.implicitly_wait(5)

    def __del__(self):
        print('Close driver')
        self.driver.quit()
        self.content_driver.quit()

    def login(self):
        self.login_from_cookie()
        try:
            driver.find_element_by_class_name('new-header-login.unlogin')
            login_by_user()
            login_from_cookie(driver)
        except Exception as e:
            pass

    def login_by_user(self):
        firefoxProfile = FirefoxProfile()
        driver2 = webdriver.Firefox(firefoxProfile)
        driver2.get('http://www.newrank.cn/')
        driver2.find_element_by_class_name('new-header-login.unlogin').click()
        print('请在页面中登录')
        raw_input('Input Enter to continue')
        pickle.dump(driver2.get_cookies(), open('./cookies.data', 'wb'))
        driver2.quit()

    def login_from_cookie(self):
        try:
            cookie = pickle.load(open('./cookies.data', 'rb'))
        except:
            return
        self.driver.get('http://www.newrank.cn/')
        for cc in cookie:
            try:
                if cc['domain'].startswith('.'):
                    cc['domain'] = 'www' + cc['domain']
                self.driver.add_cookie(cc)
            except Exception as e:
                print(e)
                print(cc)
                print('i')
        self.driver.get('http://www.newrank.cn/')

    def get_articles(self, wechat_id):
        print('Crawling %s' % wechat_id)
        url = 'http://www.newrank.cn/public/info/detail.html?account=%s' % wechat_id
        try:
            self.driver.get(url)
        except:
            print('!!!!!!!!!!!!!Cannot get web page!!!!!!!!')
            return []
        if (self.driver.title == u'页面错误'):
            print('%s not included' % (wechat_id))
            return []
        locator = (By.XPATH, '//*[@id="info_detail_article_lastest"]//li')
        try:
            WebDriverWait(self.driver, 20,
                          0.5).until(EC.presence_of_element_located(locator))
            elements = self.driver.find_elements_by_xpath(
                '//*[@id="info_detail_article_lastest"]//li')
            article_list = []
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
                article['content'] = self.get_content(article['href'])
                article_list.append(article)
            return article_list
        except Exception as e:
            print('Error')
            print(e)
            with open('./fail_ids_for_article_urls.data', 'a') as fout:
                fout.write('%s\n' % wechat_id)
            print('Not find id "info_detail_article_lastest" when crawl %s' %
                  wechat_id)

    def get_account_info(self, wechat_id):
        print('Crawling %s' % wechat_id)
        url = 'http://www.newrank.cn/public/info/detail.html?account=%s' % wechat_id
        try:
            self.driver.get(url)
        except Exception as e:
            print(e)
            print('!!!!!!!!!!!!!Cannot get web page!!!!!!!!')
            return
        if (self.driver.title == u'页面错误'):
            print('%s not included' % (wechat_id))
            return
        locator = contain_something([
            './/*[@class="tag-name-list"]//li[1]',
            './/*[@class="tag-name-list"]//a[1]'
        ])

        try:
            WebDriverWait(self.driver, 10, 0.5).until(locator)
            info_tree = etree.HTML(
                self.driver.find_element_by_class_name('info-detail-head')
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
                self.driver.find_element_by_xpath(
                    './/*[@class="info-detail-head-classify"]//*[@class="detail-edit info-detail-edit detail-pic"]'
                ).click()
                html = self.driver.find_element_by_id(
                    'current_tag_list').get_attribute('innerHTML')
                account_info['tags'] = etree.HTML(html).xpath('.//a/text()')
            except:
                account_info['tags'] = []
            return account_info
        except Exception as e:
            print(e)

    def get_content(self, url):
        try:
            self.content_driver.get(url)
        except:
            print(url)
            print('!!!!!!!!!!!!!Cannot get web page!!!!!!!!')
            return
        locator = (By.XPATH, '//*[@id="page-content"]')
        try:
            WebDriverWait(self.content_driver, 10,
                          0.5).until(EC.presence_of_element_located(locator))
            page_content = etree.HTML(
                self.content_driver.find_element_by_id('page-content')
                .get_attribute('innerHTML'))
            if page_content == None:
                print('Not find page-content')
                print(url)
            page_content = page_content.xpath('.//*[@id="js_content"]')[0]
            p = page_content.xpath('.//p | .//img')
            content = []
            for i, pp in enumerate(p):
                t = pp.xpath('string(.)')
                if t != '':
                    content.append(t)
                imgs = pp.xpath('@data-src')
                if imgs != []:
                    content += imgs
            return content
        except Exception as e:
            print(url)
            print(e)
            print('Error')


if __name__ == '__main__':
    wechat_spider = WechatSpider()
    info = wechat_spider.get_account_info('HIT_SCIR')
    articles = wechat_spider.get_articles('HIT_SCIR')
    print(info)
    for a in articles:
        print(a)
