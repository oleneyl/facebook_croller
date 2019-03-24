from docker import FB_Page, FB_Post, EXEC_TIME
import docker

if __name__ == "__main__":
    page_id = 180446095498086
    page = FB_Page(page_id) #SNU BamBoo
    utime = docker.EXEC_TIME
    
    """
    with open("url", "w") as f:
        f.write(page.get_fb_req_url(utime, ucount = 10))
    
    print(docker.last_post_utime(page.access_data(utime, 0, ucount = 10)))
    
    """
    for _iter in range(0,1):
        postlist, utime = page.extract_every_data_in_page(3, ucount = 10, as_file = False, _utime = utime)
        posttxt = []
        print("Data Load complete :" + str(_iter))

        with open("log.dat", "w") as f:
            for i in postlist:
                f.write(i + "\n") 
        
        for post_id in postlist:
            post = FB_Post(page_id, post_id)
            posttxt.append([post_id, post.get_post_text().replace("\n", " ")])

            
        with open("data_test/posttxt" + str(_iter) + ".dat", "w") as f:
            for i in posttxt:
                f.write(str(i[0]) + " " + str(i[1]) + "\n")
     
    