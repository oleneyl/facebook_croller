import urllib.request as req
from bs4 import BeautifulSoup
import time, json
import os
import requests

EXEC_TIME = int(time.time())

def get_utime_from_year(year):
    return 1546329602 + 31536000 * (year - 2019)

def get_year_from_utime(utime):
    delta =  (utime - 1546329602) // 31536000
    return 2019 + delta
EXEC_YEAR = get_year_from_utime(EXEC_TIME)


class Facebook():
    @staticmethod
    def get_jsonp_from_url(url):
        req_data = req.Request(url)
        success = False
        while success is False:
            try:
                response = req.urlopen(url)
                if response.getcode() == 200:
                    success = True
            except Exception as e:
                print(e)  # want to know what error it is
                time.sleep(5)
                # print("Error for url %s : %s" % (url, datetime.datetime.now()))

        return response.read().decode(response.headers.get_content_charset())



class FB_Page():
    """
    FB_Page : Abstract Class that supports Page level requests.
    
    Available Functions..
    
    access_data  :  return html data(type : responce_str) about post information from given [start_time - before] with posts # [ucount].
    #responce-str associated functions
    
    last_post_utime : return earlist post's utime value from given responce-str
    extract_data : return list - of - post_id from given responce-str
    
    """
    def __init__(self, page_id):
        self.page_id = page_id

    def access_jsonp(self, start_utime, before, ucount = 8, ancestor_flag = False):
        """Generate URL, and get POST_ID from given URL
        """
        req_url = self.get_fb_req_url(start_utime - before, ucount = ucount, ancestor_flag = ancestor_flag)
        return Facebook.get_jsonp_from_url(req_url)[9:]

    def get_fb_req_url(self, ctime, ucount = 8, chattime = "04611686018427387904", has_next_page = True, user = 0, ancestor_flag = False):
        """Create request which fetch data that contains about post.
        :param ctime : most-recent time that post will be fetched.
        :param ucount : aiming page count in reqeust.
        :param chattime : not needed to change. Your chat timing.
        :param has_next_page : 
        :param user : Your authentication flag. Not needed when you are accessing public data.
        :param ancestor_flag : You if you are aiming to fetch old data, you must set this flag as true.
        """
        baseurl = "https://www.facebook.com/pages_reaction_units/more/?"
        page_id = "page_id=" + str(self.page_id) + "&"
        cursor = "cursor=%7B%22"
        tl_cursor = "timeline_cursor%22%3A%22"
        tl_unit = "timeline_unit" + "%3A1" + "%3A0000000000" + str(ctime) + "%3A" + chattime + "%3A09223372036854775784" + "%3A" + chattime + "%22%2C%22"
        tl_section = "timeline_section_cursor%22%3A%7B%22"    # ":{},"
        
        #For older fb data requests
        older_request = "profile_id%22%3A" + str(self.page_id) +  "%2C%22"
        
        _year = get_year_from_utime(ctime)
        if _year < EXEC_YEAR or ancestor_flag:
            older_request += "start%22%3A" + str(get_utime_from_year(_year + 1)) + "%2C%22" + "end%22%3A" + str(get_utime_from_year(_year + 2)) + "%2C%22"   #start ~ end will be filtered(Neglect in search area) 
            older_request += "query_type%22%3A" +"8" +"%2C%22"
        else:
            #older_request += "start%22%3A" + "0" + "%2C%22" + "end%22%3A" + str(EXEC_TIME + 2764800) + "%2C%22"   #start ~ end will be filtered(Neglect in search area), Add 32 days.
            older_request += "start%22%3A" + "0" + "%2C%22" + "end%22%3A" + str(1533106799) + "%2C%22"   #start ~ end will be filtered(Neglect in search area)
            older_request += "query_type%22%3A" +"36" +"%2C%22"
            
        older_request += "filter%22%3A" + "1" + "%7D%2C%22"
        #For older fb data requests
        
        if has_next_page:
            has_npage = "has_next_page%22%3Atrue%7D&"
        else:
            has_npage = "has_next_page%22%3Afalse%7D&"
        surface = "surface=www_pages_posts&"
        unit_count = "unit_count=" + str(ucount) + "&"
        
        misc = [
            "dpr=1&",
            "__user=" + str(user) + "&",
            "__a=1&",
            "__dyn=5V4cjLx2ByKEjgDxiWJGi9FxqeCwDKEyGgS8UR9LFGUqx-6ES2N6xvyEyeCHxC7oG5UdUW4UJu9x2axuF8iBAVXxWUPwXGt0Bx12KdwJJ4hKe-2i5-uiaAz8gCxm1iyECVoyaxG4oO3-5k2eq499oeGzVFAeCUkUCawRxmul3opAxOdyFE-2O4rGVUhxyh16fmFomhC8xm252odoKUKfy45EGdwRxC4eby9o_WUW8CwKK4ogze9Ay8gVeaDU8Jai5EylxdyopAh8GcByprx6uegiVEtwMwLx2FUO3tyV4aKUzCDKiaxObwFzGyXzo&",
            "__req=1b&",
            "__be=1&",
            "__pc=PHASED%3ADEFAULT&", #"__pc=PHASED%3ADEFAULT&",
            "__rev=1000526266&"
            #,"__spin_r=4102988&",
            #"__spin_b=trunk&",
            #"__spin_t=1531539270"
        ]

        return baseurl + page_id + cursor + tl_cursor + tl_unit + tl_section + older_request + has_npage + surface + unit_count + "".join(misc)


    def extract_every_data_in_page(self,  trials, ucount = 50, intervals = 86400, as_file = True, target_dir = ".", _utime = EXEC_TIME, load_interval = 1):
        """ Get post id start from _utime, total trials * ucount.
        Returns Post-list, utime(most previous)
        """
        utime = _utime
        plist = []
        ancestor_flag = False
        for i in range(trials):
            if as_file:
                os.mkdir(target_dir + "/" + str(i))
            responce_str = self.access_data(utime, 0, ucount = ucount, ancestor_flag = ancestor_flag)
            post_li = self.extract_data(responce_str)
            
            if as_file:
                for post_id in post_li:
                    with open(target_dir + "/" + str(i) + "/" + post_id, "w") as f:
                        f.write(extract_post_in_page(self.page_id, post_id))
                
            else:
                for post_id in post_li:
                    plist.append(post_id)
            
            utime_temp = last_post_utime(responce_str) - 1
            
            if utime_temp > utime:
                ancestor_flag = True
            else:
                utime = utime_temp
            
            if len(post_li) == 0:
                utime -= 86400
            
            time.sleep(load_interval)   #Prevent ip block
            
        return plist, utime



    def last_post_utime(self, responce_str):
        """Extract lat_post_utime in given responce_url
        """
        utime = int(time.time())    #Get execution utime
        loc = 0
        
        while True:
            loc = responce_str.find("data-utime", loc)
            if loc == -1:
                break
            utime = min(int(responce_str[loc + len("data-utime") + 3 : loc + len("data-utime") + 13]), utime)
            
            loc += 1        
        return utime

    def extract_data(self, responce_str):
        """Extract POST_ID from given responce_str
        """
        start = False
        li = []
        loc = 0
        
        while True:
            loc = responce_str.find("post_fbid", loc)
            pnum = responce_str[loc + len("post_fbid") + 2 : loc + len("post_fbid") + 18]
        
            if pnum.find("}") != -1:
                decimate = pnum.find("}")
                pnum = pnum[:decimate]
            try:
                a = int(pnum)
            except:
                break
            
            if start:
                if pnum == li[0]:
                    break
            else:
                start = True
    
            li.append(pnum)
            if loc == -1:
                break
            
            loc += 1        
        return li
