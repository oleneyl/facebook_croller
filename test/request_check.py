import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
from module import parser
import time

def test_is_correct_data():

    EXEC_TIME = int(time.time())

    page = parser.FB_Page(560898400668463)
    resposne_str = page.access_jsonp(EXEC_TIME, 0, ucount = 5, ancestor_flag = False)
    
    with open('log.json', 'w') as f:
        f.write(resposne_str)

test_is_correct_data()