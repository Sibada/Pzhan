#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import log
import re
import os
import time
import urllib as ul
import urllib2 as ul2
import cookielib as cl
from bs4 import BeautifulSoup as bs


class Pzhan(object):
    def __init__(self):
        self.base_url = "http://www.pixiv.net/"
        self.login_url = "https://www.pixiv.net/login.php"
        self.User_Agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0"
        self.pid = None
        self.psw = None
        self.login_header = {
            "Host": "www.pixiv.net",
            "User-Agent": self.User_Agent,
            "Referer": "http://www.pixiv.net/",
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive"
        }
        self.post_content = {
            "mode": "login",  
            "pixiv_id": None,  
            "pass": None,  
            "skip": "1",
            "return_to": "/",  
        }
        self.post_data = None
        self.cookie = None
        self.cookie_handler = None
        self.opener = None

        self.logined = False

        self.save_path = "~"
        self.save_prefix = "N"  # N: None, T: Time, S: Series number.

        self.pg_css = ["div.works_display", "a.multiple", "img.original-image"]
        self.title_css = ["div.layout-a", "h1.title"]
        self.pgsl_css = ["div.item-container", "a.full-size-container"]

    def login(self, pid, psw):
        self.post_content["pixiv_id"] = pid
        self.post_content["pass"] = psw
        self.post_data = ul.urlencode(self.post_content)
        self.cookie = cl.LWPCookieJar()
        self.cookie_handler = ul2.HTTPCookieProcessor(self.cookie)
        self.opener = ul2.build_opener(self.cookie_handler)

        request = ul2.Request(self.login_url, self.post_data, self.login_header)
        response = self.opener.open(request)

        abc = response.getcode()
        if abc == 200:
            log.info("Response %d: login succeed." % abc)
            self.pid = pid
            self.psw = psw
            self.logined = True
            return 0
        else:
            log.error("Response %d: login failed." % abc)
            return 1

    def set_save_path(self, save_path):
        self.save_path = save_path

    def get_html(self, url):
        request = ul2.Request(url)
        response = self.opener.open(request)
        abc = response.getcode()
        log.debug("Get html: response %d" % abc)

        html = response.read().decode('UTF-8')
        return html

    def mkdir(self, dir):
        if os.path.exists(dir):
            log.warning("%s exists." % dir)
        else:
            os.makedirs(dir)
            log.info("Create dir %s" % dir)

    def get_time(self):
        return time.strftime("%y%m%d-%H%M%S",time.localtime(time.time()))

    def save_img(self, img_url, path, referer):
        img_header = {
            'Referer': referer,
            'User-Agent': self.User_Agent
        }
        request = ul2.Request(img_url, headers=img_header)
        response = self.opener.open(request)
        abc = response.getcode()
        log.debug("Save_img: response %d" % abc)
        if abc == 200:
            data = response.read()
            with open(path, 'wb') as f:
                f.write(data)
            return True
        else:
            return False

    def get_pgs_list(self, pgsl_url):
        pgsl_html = self.get_html(pgsl_url)
        pgsl_soup = bs(pgsl_html, "lxml")

        pgs_list = pgsl_soup.select(self.pgsl_css[0])
        pgs_list = [pg.select(self.pgsl_css[1])[0].attrs["href"] for pg in pgs_list]
        return pgs_list

    def get_pic(self, pic_url, save_path):
        pic_url_c = self.base_url + pic_url
        pic_html = self.get_html(pic_url_c)
        pic_soup = bs(pic_html, "lxml")

        img_url = pic_soup.select("img")[0].attrs["src"]
        file_name = re.split("/", img_url)[-1]
        file_path = save_path+"/"+file_name

        is_save = self.save_img(img_url, file_path, pic_url_c)
        if is_save:
            log.info("Image %s saved." % file_path)

    def get_pg(self, pg_url, pfx=None):
        if self.save_prefix == "S":
            prefix = "%04d" % pfx
        if self.save_path == "T":
            prefix = self.get_time()

        pg_html = self.get_html(pg_url)
        pg_soup = bs(pg_html, "lxml")
        title = pg_soup.select(self.title_css[0])[0].select(self.title_css[1])[0].text
        title = re.sub("[\\/\?\*\"<>]", " ", title)
        title = prefix + " " + title
        save_path = self.save_path + "/" + title

        works_dis = pg_soup.select(self.pg_css[0])[0].select(self.pg_css[1])

        if len(works_dis) == 0:
            img_src = pg_soup.select(self.pg_css[2])[0].attrs["data-src"]
            ext = img_src.split(".")[-1]
            save_name = save_path + "." + ext

            log.info("\"%s\" is a single pic." % (title))
            is_save = self.save_img(img_src, save_name, pg_url)
            if is_save:
                log.info("Image %s saved." % save_name)

        else:
            pgsl_url = works_dis[0].attrs["href"]
            pgsl_url = self.base_url + pgsl_url

            pg_list = self.get_pgs_list(pgsl_url)

            log.info("\"%s\" is a pic series, nclude %d pics." % (title, len(pg_list)))
            self.mkdir(save_path)

            for pic_url in pg_list:
                self.get_pic(pic_url, save_path)

    def get_member_works_urls(self, member_url):
        member_url = re.sub("net/.+\.php", "net/member_illust.php", member_url)
        member_url = re.sub("&p=\d+", "", member_url)

        member_soup = bs(self.get_html(member_url), "lxml")
        member_name = member_soup.select("div.layout-a")[0].select("h1.user")[0].text
        log.info("Collecting works of member \"%s\"..." % member_name)

        url_list = []
        p = 1
        while True:
            if p > 1:
                subpg_url = member_url + "&p=%d" % p
            else:
                subpg_url = member_url
            subpg_soup = bs(self.get_html(subpg_url), "lxml")

            item_list = subpg_soup.select("li.image-item")
            if len(item_list) == 0:
                break

            for item in item_list:
                item_url = item.select("a")[0].attrs["href"]
                item_url = self.base_url + item_url
                url_list.append(item_url)

            p += 1
        log.info("Member \"%s\" has total %d works." % (member_name, len(url_list)))

        return url_list, member_name

    def get_member_works(self, member_url):
        works_list, member_name = self.get_member_works_urls(member_url)

        log.info("Start to get works of \"%s\"." % member_name)
        pre_path = self.save_path
        self.save_path += "/" + member_name
        self.mkdir(self.save_path)

        works_list = works_list[::-1]
        for work_url in works_list:
            log.info("Getting work %d/%d" % (works_list.index(work_url)+1, len(works_list)))
            self.get_pg(work_url)

        self.save_path = pre_path
        log.info("Works getting complete.")

