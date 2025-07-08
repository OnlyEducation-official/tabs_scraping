**How to run - python main.py**

**-------- WHAT IS USED --------**

**1. Python
2. Playwright
3. Beautiful Soup 4**
   
**-------- USE OF THIS REPO --------**

1. This repo will scrape tabs data of college dunia
2. College dunia website is dynamic, so the attributes change. Check all the current attributes while scraping, test it on local machine thoroughly and then run it on server.
3. This script scrapes total 5 tabs, 
  - **Overview
  - Admission
  - Placements
  - CuttOff
  - Courses & Fees**
4. Run this script in 2 ways

  **A) Scrape Overview, admission, placements, cuttoff. **
  
    - These tabs are light, so we can use EC2 medium instance
    
  **B) Scrape only courses & fees tab. **
  
    - This is very heavy, because we are opening and closing models.Which is heavy and dynamic.
    - I scraped it on my local, (took 19 hours), havent tried it on EC2 Server. So, figure it our by try and error.
    - I have added batch processing, so if you use ec2.medium, it might work. Again, do try and error.
    
5. Where to get the url of all the colleges 18000+
6. Use the output of OnlyEducation-official/combine_all_scraped_url and paste it in this folder and run. Automatic batch processing will start.
7. I used 4 process at a time. If you have a good pc or good server, we can use more processes to scrape data faster
8. Each process will store data in batch of 100.

- **IF YOU CAN OPTIMIZE THIS CODE. YOU ARE WELCOME!!!!** -








