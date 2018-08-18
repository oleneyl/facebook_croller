#! etc/bin/python3
import urllib.request as req
from bs4 import BeautifulSoup
import time, json
import os
import requests

EXEC_TIME = int(time.time())
SNU_BAMBOO = 560898400668463
SAMPLE_POSTID = '1874495922642031'

def get_utime_from_year(year):
    return 1546329602 + 31536000 * (year - 2019)

def get_year_from_utime(utime):
    delta =  (utime - 1546329602) // 31536000
    return 2019 + delta

EXEC_YEAR = get_year_from_utime(EXEC_TIME)

"""
def get_fb_req_url(pageid, ctime, ucount = 8, chattime = "04611686018427387904", has_next_page = True, user = 0, ancestor_flag = False):
    
    baseurl = "https://www.facebook.com/pages_reaction_units/more/?"
    page_id = "page_id=" + str(pageid) + "&"
    cursor = "cursor=%7B%22"
    tl_cursor = "timeline_cursor%22%3A%22"
    tl_unit = "timeline_unit" + "%3A1" + "%3A0000000000" + str(ctime) + "%3A" + chattime + "%3A09223372036854775663" + "%3A" + chattime + "%22%2C%22"
    tl_section = "timeline_section_cursor%22%3A%7B%22"    # ":{},"
    
    #For older fb data requests
    older_request = "profile_id%22%3A" + str(pageid) +  "%2C%22"
    
    _year = get_year_from_utime(ctime)
    if _year < EXEC_YEAR or ancestor_flag:
        older_request += "start%22%3A" + str(get_utime_from_year(_year) + 1) + "%2C%22" + "end%22%3A" + str(get_utime_from_year(_year) + 2) + "%2C%22"   #start ~ end will be filtered(Neglect in search area) 
    else:
        older_request += "start%22%3A" + "0" + "%2C%22" + "end%22%3A" + str(EXEC_TIME) + "%2C%22"   #start ~ end will be filtered(Neglect in search area)
        
    older_request += "query_type%22%3A" +"36" +"%2C%22"
    older_request += "filter%22%3A" + "1" + "%7D%2C%22"
    #For older fb data requests
    
    if has_next_page:
        has_npage = "has_next_page%22%3Atrue%7D&"
    else:
        has_npage = "has_next_page%22%3Afalse%7D&"
        
    surface = "surface=www_pages_home&"
    unit_count = "unit_count=" + str(ucount) + "&"
    
    misc = [
        "dpr=1&",
        "__user=" + str(user) + "&",
        "__a=1&",
        "__dyn=5V4cjLx2ByKEjgDxiWJGi9FxqeCwDKEyGgS8UR9LFGUqx-6ES2N6xvyEyeCHxC7oG5UdUW4UJu9x2axuF8iBAVXxWUPwXGt0Bx12KdwJJ4hKe-2i5-uiaAz8gCxm1iyECVoyaxG4oO3-5k2eq499oeGzVFAeCUkUCawRxmul3opAxOdyFE-2O4rGVUhxyh16fmFomhC8xm252odoKUKfy45EGdwRxC4eby9o_WUW8CwKK4ogze9Ay8gVeaDU8Jai5EylxdyopAh8GcByprx6uegiVEtwMwLx2FUO3tyV4aKUzCDKiaxObwFzGyXzo&",
        "__req=1b&",
        "__be=1&",
        "__pc=EXP2%3ADEFAULT", #"__pc=PHASED%3ADEFAULT&",
        "__rev=4102988&"
        #,"__spin_r=4102988&",
        #"__spin_b=trunk&",
        #"__spin_t=1531539270"
    ]
    
    return baseurl + page_id + cursor + tl_cursor + tl_unit + tl_section + older_request + has_npage + surface + unit_count + "".join(misc)
"""

def get_html_at_url(url):
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
    

def last_post_utime(responce_str):
    utime = int(time.time())    #Get execution utime
    loc = 0
    
    while True:
        loc = responce_str.find("data-utime", loc)
        if loc == -1:
            break
        utime = min(int(responce_str[loc + len("data-utime") + 3 : loc + len("data-utime") + 13]), utime)
        
        loc += 1        
    return utime

#Deprecated
def extract_post_in_page(page_id, post_id):
    req_url = "https://www.facebook.com/" + str(page_id) + "/posts/" + str(post_id)
    html = get_html_at_url(req_url)
    soup = BeautifulSoup(html, "html.parser")
    
    post_doc_meta = soup.find_all("div", {"class" : "hidden_elem"})[1].find("code").prettify()
    post_doc_html = post_doc_meta[post_doc_meta.find("<!--") + 4: post_doc_meta.find("-->")]
    post_soup = BeautifulSoup(post_doc_html, "html.parser").find("div", {"class":"userContent"}).find("p").text
    
    return post_soup

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

    def get_fb_req_url(self, ctime, ucount = 8, chattime = "04611686018427387904", has_next_page = True, user = 0, ancestor_flag = False):
        """Internal function : from fb GET information generate URL with given ctime, with data ucount.
        """
        baseurl = "https://www.facebook.com/pages_reaction_units/more/?"
        page_id = "page_id=" + str(self.page_id) + "&"
        cursor = "cursor=%7B%22"
        tl_cursor = "timeline_cursor%22%3A%22"
        tl_unit = "timeline_unit" + "%3A1" + "%3A0000000000" + str(ctime) + "%3A" + chattime + "%3A09223372036854775663" + "%3A" + chattime + "%22%2C%22"
        tl_section = "timeline_section_cursor%22%3A%7B%22"    # ":{},"
        
        #For older fb data requests
        older_request = "profile_id%22%3A" + str(self.page_id) +  "%2C%22"
        
        _year = get_year_from_utime(ctime)
        if _year < EXEC_YEAR or ancestor_flag:
            older_request += "start%22%3A" + str(get_utime_from_year(_year + 1)) + "%2C%22" + "end%22%3A" + str(get_utime_from_year(_year + 2)) + "%2C%22"   #start ~ end will be filtered(Neglect in search area) 
            older_request += "query_type%22%3A" +"8" +"%2C%22"
        else:
            #older_request += "start%22%3A" + "0" + "%2C%22" + "end%22%3A" + str(EXEC_TIME + 2764800) + "%2C%22"   #start ~ end will be filtered(Neglect in search area), Add 32 days.
            older_request += "start%22%3A" + "0" + "%2C%22" + "end%22%3A" + str(1533106799) + "%2C%22"   #start ~ end will be filtered(Neglect in search area), Add 32 days.
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
            "__pc=EXP2%3ADEFAULT", #"__pc=PHASED%3ADEFAULT&",
            "__rev=4102988&"
            #,"__spin_r=4102988&",
            #"__spin_b=trunk&",
            #"__spin_t=1531539270"
        ]

        return baseurl + page_id + cursor + tl_cursor + tl_unit + tl_section + older_request + has_npage + surface + unit_count + "".join(misc)

    def access_data(self, start_utime, before, ucount = 8, ancestor_flag = False):
        """Generate URL, and get POST_ID from given URL
        """
        req_url = self.get_fb_req_url(start_utime - before, ucount = ucount, ancestor_flag = ancestor_flag)
        return get_html_at_url(req_url)

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


class FB_Post():
    """
    
    Functions
    get_post_soup
    get_metadata
    get_post_text
    get_comments_with_detail
    """
    def __init__(self, page_id, post_id):
        self.page_id = page_id
        self.post_id = post_id
        self.post_soup = None    
        self._metadata = None
        
    def get_every_comments(self):
        """
        """
        comment_num = self.get_metadata()["comment"]
        return self.get_comments_with_detail(0, comment_num)
        
     
    def get_post_soup(self, force = False):
        """Get post_soup
        """
        if self.post_soup is not None and not force:
            return self.post_soup
        else:
            req_url = "https://www.facebook.com/" + str(self.page_id) + "/posts/" + str(self.post_id)
            html = get_html_at_url(req_url)
            soup = BeautifulSoup(html, "html.parser")
            self.post_soup = soup
            
        return soup
        
    def load_metadata_from_web(self, lang = "KR"):
        """Default language is KR(Korean). If you're in different environment, please specify appropriate language.
        ! This function doesnt work well (Needs authentification) Do not use this function.
        """
        soup = self.get_post_soup()
        meta_list = soup.find("div", {"class" : "_524d"}).find("a")['aria-label'].split(" ")
        lang_parser = {}
        """lang_parser : Language - specific like/comment/share parser
        "pos" : index of each value when string is splitted by SPACEBAR
        "remove" : If SPACEBAR - splitted string have redundancy, you can assign remove option that splits with remove[0] and take value at index : remove[1].
        
        You must define each values for every metadata name.
        """
        lang_parser["KR"] = {"like" : {"pos" : 1, "remove" : ["개", 0]}, "comment" : {"pos" : 3, "remove" : ["개", 0]}, "share" : {"pos" : 5, "remove" : ["회", 1]}}
        lang_parser["EN"] = {"like" : {"pos" : 0}, "comment" : {"pos" : 2}, "share" : {"pos" : 4}}
        
        def parse(lang_, name_):
            strs = meta_list[lang_parser[lang_][name_]["pos"]]
            if "remove" in lang_parser[lang_][name_]:
                strs = strs.split(lang_parser[lang_][name_]["remove"][0])[lang_parser[lang_][name_]["remove"][1]]
            return int(strs)
        
        meta = {}
        for name in lang_parser[lang]:
            meta[name] = parse(lang, name)
        
        self._metadata = meta
        return meta
    
    def load_metadata_from_preview(self):
        """Get post's metadata from web request
        """
        souptxt = self.get_post_soup().text
        nameset = {"like" : "likecount:", "share" : "sharecount:", "comment" : "commentcount:"}
        def parse(name_):
            _pos = souptxt.find(name_)
            _from = souptxt.find(":", _pos)
            _end = souptxt.find(",", _from + 1)
            return int(souptxt[_from + 1 : _end])

        meta = {}
        for name in nameset:
            meta[name] = parse(nameset[name])
        
        self._metadata = meta
        return meta
        
    def get_metadata(self, force = False):
        if self._metadata is not None and not force:
            return self._metadata
        else:
            self.load_metadata_from_preview()
            return self._metadata
        
    def get_post_text(self):
        soup = self.get_post_soup()
        post_doc_meta = soup.find_all("div", {"class" : "hidden_elem"})[1].find("code").prettify()
        post_doc_html = post_doc_meta[post_doc_meta.find("<!--") + 4: post_doc_meta.find("-->")]
        post_soup_li = BeautifulSoup(post_doc_html, "html.parser").find("div", {"class":"userContent"}).find_all("p")
        post_soup_txt = []
        for soup in post_soup_li:
            post_soup_txt.append(soup.text)
        
        return "\n".join(post_soup_txt)
        
    #Useless    
    def get_post_responce(self, offset, length):
        req_url = "https://www.facebook.com/ajax/ufi/comment_fetch.php?dpr=1"
        data = {}
        
        data["ft_ent_identifier"] = int(self.post_id)
        data["viewas"] = None
        data["source"] = 2
        data["offset"] = offset
        data["length"] = length
        data["orderingmode"] = "filtered"
        data["section"]  ="default"
        feed_context = {}
        feed_context["is_viewer_page_admin"] = False
        feed_context["is_notification_preview"] = False
        feed_context["autoplay_with_channelview_or_snowlift"] = False
        feed_context["video_player_origin"] = "permalink"
        feed_context["fbfeed_context"] = True
        feed_context["location_type"] = '5'
        feed_context["outer_object_element_id"] = "u_0_j"
        feed_context["object_element_id"] = "u_0_j"
        feed_context["is_ad_preview"] = False
        feed_context["is_editable"] = False
        feed_context["mall_how_many_post_comments"] = 2
        feed_context["bump_reason"] = 0
        feed_context["story_width"] = 502
        feed_context["tn-str"] = "-R"
        data["feed_context"] = feed_context
        data["numpagerclicks"] = None
        data["av"] = None
        data["__user"] = 0
        data["__a"] = 1
        data["__dyn"] = "5V8WXBzamaUmgDBzFHpUR1ycCzSczVbGAdyeGBXrWqF1eU8EnGdwIhEpyAubGqKi5azppEG5VGwwyKbG4V9B88x2axnGiidBAVuVRG4agPx6cAAxaFS58-EN2-iV8SdyVuF4jUCjQh38gxu9AyAUO48V2K8hqwVByFrKm4VVpV8KmuQdwCDG5qUvCypHh422q4EiVbiKaCUkV-axyHu4oth4dz8hCDK9zoGq3h6x6WLGHz5Axpu9iFrAuF9VpG8Jy9VQC25jUc98KUV1hyVriCUKbwFxC4eby9o_CDGCXV8W9xheEWbAzAulaayKjyFVEviAypFpbgjxabzpp99umh3AiUhDzA6UG8ypV9V8GcGdyUvGFUO8ggKiifrCx2VbzpHAgC78KcBx6i9AQbKbU"
        data["__req"] = 3
        data["__be"] = -1
        data["__pc"] = "PHASED:DEFAULT"
        data["__rev"] = 4104303
        data["lsd"] = "AVo-0Vqk"
        
        #res = requests.post(req_url, data = json.dumps(data))
        #print(res.status_code)
        
        #html = requests.post(req_url, data = json.dumps(data)).text
        
        return json.dumps(data)
        
    def get_comments_with_detail(self, offset, length):
        baseurl = "https://www.facebook.com/ajax/ufi/comment_fetch.php?dpr=1&"
        ftent = "ft_ent_identifier=" + str(self.post_id) + "&"
        viewas = "viewas&"
        source = "source2&"
        loc = "offset=" + str(offset) + "&length=" + str(length) + "&"
        ormode = "orderingmode=filtered&"
        section = "section=default&"
        feed_context = ["feed_context=%7B%22",
        "is_viewer_page_admin%22%3Afalse%2C%22",
        "is_notification_preview%22%3Afalse%2C%22",
        "autoplay_with_channelview_or_snowlift%22%3Afalse%2C%22"   ,
        "video_player_origin%22%3A%22",
        "permalink%22%2C%22",
        "fbfeed_context%22%3Atrue%2C%22",
        "location_type%22%3A5%2C%22",
        "outer_object_element_id%22%3A%22u_0_j%22%2C%22",
        "object_element_id%22%3A%22u_0_j%22%2C%22",
        "is_ad_preview%22%3Afalse%2C%22",
        "is_editable%22%3Afalse%2C%22",
        "mall_how_many_post_comments%22%3A2%2C%22",
        "bump_reason%22%3A0%2C%22",
        "story_width%22%3A502%2C%22",
        "tn-str%22%3A%22-R%22%7D&"
        ]
        npager = "numpagerclicks&"
        av = "av=&"
        user = "__user=0&"
        a = "__a=1&"
        dyn = "__dyn=5V8WXBzamaUmgDBzFHpUR1ycCzSczVbGAdyeGBXrWqF1eU8EnGdwIhEpyAubGqKi5azppEG5VGwwyKbG4V9B88x2axnGiidBAVuVRG4agPx6cAAxaFS58-EN2-iV8SdyVuF4jUCjQh38gxu9AyAUO48V2K8hqwVByFrKm4VVpV8KmuQdwCDG5qUvCypHh422q4EiVbiKaCUkV-axyHu4oth4dz8hCDK9zoGq3h6x6WLGHz5Axpu9iFrAuF9VpG8Jy9VQC25jUc98KUV1hyVriCUKbwFxC4eby9o_CDGCXV8W9xheEWbAzAulaayKjyFVEviAypFpbgjxabzpp99umh3AiUhDzA6UG8ypV9V8GcGdyUvGFUO8ggKiifrCx2VbzpHAgC78KcBx6i9AQbKbU&"
        reqnum = "__req=4&"    
        be = "__be=-1&"
        pc = "__pc=PHASED%3ADEFAULT&"
        rev = "__rev=4104326&"
        lsd = "lsd=AVo-0Vqk"
        
        url = baseurl + ftent + viewas + source + loc + ormode + section + "".join(feed_context) + npager + av + user + a + dyn + reqnum + be + pc + rev + lsd
        jsonstr = get_html_at_url(url)[9:]
        
        data = json.loads(jsonstr)
        c_li = data["jsmods"]["require"][0][3][1]["comments"]
        
        retlist = []
        for cmt in c_li:
            retlist.append(FB_Comment(cmt["ftentidentifier"], cmt["author"], cmt["timestamp"]["time"], cmt["fbid"], cmt["body"]["text"]))
            
        return retlist
        
class FB_Comment():
    def __init__(self, post, author, timestamp, comment_id, text):
        self.post = post
        self.author = author
        self.timestamp = timestamp
        self.comment_id = comment_id
        self.text = text
        
    def __repr__(self):
        txt = "\n----------\n"
        txt += "post : " + str(self.post) + "\n"
        txt += "author : " + str(self.author) + "\n"
        txt += "timestamp : " + str(self.timestamp) + "\n"
        txt += "comment_id : " + str(self.comment_id) + "\n"
        txt += "text : " + str(self.text)+ "\n"
        txt += "----------\n"
        
        return txt

    

if __name__ == "__main__":
    """
    value = access_data(SNU_BAMBOO, EXEC_TIME, 86400*7)
    with open("log.dat", "w") as f:
        f.write(value)
    
    url = get_fb_req_url(SNU_BAMBOO, EXEC_TIME - 86400)
    with open("url.dat", "w") as f:
        f.write(url)
        
    page_list = extract_data(value)
    with open("plist1.dat", "w") as f:
        f.write(str(page_list))
    """
    #extract_every_data_in_page(SNU_BAMBOO, 4, ucount = 4)
    post = FB_Post(SNU_BAMBOO, 1878469378911352)
    comment_every = post.get_every_comments()
    print(len(comment_every))
    with open("comment_every.txt", "w") as f:
        f.write(str(comment_every))

    

