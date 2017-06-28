#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import log
from .utils import create_gif
import re
import os
import time
import json
import zipfile as zf
import requests as rq
from bs4 import BeautifulSoup as bs

class Pzhan(object):
    def __init__(self, save_path = None):
        self.ses = rq.session()    
        
        self.base_url = "http://www.pixiv.net/"
        self.login_base_url = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
        self.login_url = "https://accounts.pixiv.net/api/login?lang=zh"
        self.User_Agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0"
        self.pid = None
        self.psw = None
        self.post_key = None
        
        self.login_header = {
            "Host": "accounts.pixiv.net",
            "User-Agent": self.User_Agent,
            "Referer": "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index",
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive"
        }
        self.post_content = {
            "pixiv_id": None,  
            "password": None,
            "post_key": None,
            "return_to": self.base_url,  
        }
        self.post_data = None
        self.cookie = None
        self.cookie_handler = None
        self.opener = None

        self.logined = False

        self.save_path = "~"
        if save_path is not None:
            self.save_path = save_path
        self.save_prefix = "S"  # N: None, T: Time, S: Series number.
        self.create_gif = True

        self.pg_css = ["div.works_display", "a.multiple", "img.original-image", "canvas"]
        self.title_css = ["div.layout-a", "h1.title"]
        self.pgsl_css = ["div.item-container", "a.full-size-container"]

    def login(self, pid, psw):
        login_html = self.ses.get(self.login_base_url)
        pattern = re.compile('<input type="hidden".*?value="(.*?)">', re.S)  
        result = re.search(pattern, login_html.text)  
        self.post_key = result.group(1)
        
        self.post_content["pixiv_id"] = pid
        self.post_content["password"] = psw
        self.post_content["post_key"] = self.post_key
        self.ses.post(self.login_url, data = self.post_content, headers = self.login_header)

        tst_html = self.ses.get(self.base_url).text
        prodiv = tst_html.find("user-name-container")
        
        if prodiv < 0:
            log.error(self.pid)
            return False

        log.info("Login succeed.")
        self.pid = pid
        self.psw = psw
        self.logined = True
        return True


    def set_save_path(self, save_path):
        has_path = os.path.exists(save_path)
        if not has_path:
            try:
                os.makedirs(save_path)
            except OSError:
                log.error("Could not create saving path.")
            return
        log.info("Saving path has set to %s" % save_path)
        self.save_path = save_path

    def get_html(self, url):
        response = self.ses.get(url)
        
        sc = response.status_code
        log.debug("Get html: response %d" % sc)

        html = response.content.decode('UTF-8')
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
        response = self.ses.get(img_url, headers = img_header)
        sc = response.status_code
        log.debug("Save_img: response %d" % sc)
        
        if sc == 200:
            with open(path, "wb") as f:
                    f.write(response.content)        
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
        if pfx is None:
            prefix = ""
        elif self.save_prefix == "S":
            prefix = "%04d " % pfx
        elif self.save_path == "T":
            prefix = self.get_time() + " "

        pg_html = self.get_html(pg_url)
        pg_soup = bs(pg_html, "lxml")
        title = pg_soup.select(self.title_css[0])[0].select(self.title_css[1])[0].text
        title = re.sub("[\\/\?\*\"<>]", " ", title)
        title = prefix + title
        save_path = self.save_path + "/" + title

        dpg_info_t = re.findall(r"pixiv\.context\.ugokuIllustFullscreenData\s*=\s*\{.+\}", pg_html)
        works_dis = pg_soup.select(self.pg_css[0])[0].select(self.pg_css[1])

        if len(dpg_info_t) > 0:
            dpg_info = dpg_info_t[0]
            dpg_info = re.findall(r"\{.+\}", dpg_info)[0]
            dpg_info = json.loads(dpg_info)

            zip_url = re.sub("\\\\", "", dpg_info["src"])
            delays = [frame["delay"] for frame in dpg_info["frames"]]
            files = [frame["file"] for frame in dpg_info["frames"]]

            log.info("\"%s\" is a dynamic pic." % (title))
            self.get_dpc(zip_url, save_path, pg_url)

            # Create GIF file.
            if self.create_gif:
                log.info("Creating GIF file...")
                create_gif(save_path, files, delays)
                log.info("GIF file created.")

        elif len(works_dis) == 0:
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
                log.info("Saving pic %d/%d" % (pg_list.index(pic_url)+1, len(pg_list)))
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

            for i in range(10):
                try:
                    subpg_html = self.get_html(subpg_url)
                    break
                except Exception:
                    log.info('Re try...')

            subpg_soup = bs(subpg_html, "lxml")

            item_list = subpg_soup.select("li.image-item")
            if len(item_list) == 0:
                break
            item_list = item_list[::-1]

            for item in item_list:
                item_url = item.select("a")[0].attrs["href"]
                item_url = self.base_url + item_url
                url_list.append(item_url)

            log.info("Up to %d works." % len(url_list))
            p += 1
            url_list = url_list[::-1]
        log.info("Member \"%s\" has total %d works." % (member_name, len(url_list)))

        return url_list, member_name

    def get_member_works(self, member_url):
        works_list, member_name = self.get_member_works_urls(member_url)
        ori_list = works_list[:]
        fail_list = []

        log.info("Start to get works of \"%s\"." % member_name)
        pre_path = self.save_path
        self.save_path += "/" + member_name
        self.mkdir(self.save_path)

        for i in range(6):
            for work_url in works_list:
                log.info("Getting work %d/%d" % (works_list.index(work_url)+1, len(works_list)))
                try:
                    self.get_pg(work_url, (ori_list.index(work_url)+1))
                except Exception:
                    log.error("Work %d/%d fail." % (works_list.index(work_url)+1, len(works_list)))
                    fail_list.append(work_url)
                    log.info("Total fail: %d" % len(fail_list))
            works_list = fail_list[:]
            fail_list = []
        
        for fail_url in works_list:
            log.info("Fail %s" % fail_url)
        self.save_path = pre_path
        log.info("Works getting complete.")

    def get_dpc(self, zip_url, path, referer):
        options_header = {
            'User-Agent': self.User_Agent,
            'Accept-Encoding': 'gzip, deflate',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'range'
        }

        get_header = {
            'User-Agent': self.User_Agent,
            'Referer': referer,
            'Connection': 'keep-alive'
        }

        req = self.ses.options(zip_url, headers=options_header)
        if not req.ok:
            log.error("Getting zip fail.")
            log.debug("Fail in OPTIONS")
            return False
        req.close()

        req = self.ses.get(zip_url, headers=get_header)
        if not req.ok:
            log.error("Getting zip fail.")
            log.debug("Fail in GET")
            return False
        zip_file = path + ".zip"
        log.info("Downloading %s" % zip_file)
        with open(zip_file, "wb") as f:
            f.write(req.content)

        log.debug("Unziping %s..." % zip_file)
        self.mkdir(path)

        dpc_zip = zf.ZipFile(zip_file, "r")
        for fn in dpc_zip.namelist():
            file(path + "/" + fn, "wb").write(dpc_zip.read(fn))

        os.remove(zip_file)
        log.info("Flames of %s has all unzipped." % zip_file)

        return True

