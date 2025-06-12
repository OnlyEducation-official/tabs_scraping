from bs4 import BeautifulSoup
import json
import re


VALID_CLASSES_OVERVIEW = [
    "cdcms_ranking","cdcms_cut_off","cdcms_cutoff",
    "cdcms_admission_process", "cdcms_placement", "cdcms_exam_highlights","cdcms_application_process",
    "cdcms_courses","cdcms_admission_highlights","cdcms_scholarship",
    "cdcms_section2", "cdcms_section3", "cdcms_section4",
    "cdcms_section5", "cdcms_section6", "cdcms_section7", "cdcms_section8","cdcms_scholarships",
    "cdcms_section9", "cdcms_section10", "cdcms_section11", "cdcms_section12","cdcms_comparison","cdcms_faculty"
]

VALID_CLASSES_SET_OVERVIEW = set(VALID_CLASSES_OVERVIEW)

VALID_CLASSES_PLACEMENT = [
    "cdcms_ranking","cdcms_cut_off","cdcms_cutoff",
    "cdcms_admission_process", "cdcms_exam_highlights","cdcms_application_process",
    "cdcms_courses","cdcms_admission_highlights","cdcms_scholarship",
    "cdcms_section2", "cdcms_section3", "cdcms_section4",
    "cdcms_section5", "cdcms_section6", "cdcms_section7", "cdcms_section8","cdcms_scholarships",
    "cdcms_section9", "cdcms_section10", "cdcms_section11", "cdcms_section12","cdcms_comparison","cdcms_faculty"
]

VALID_CLASSES_SET_PLACEMENT = set(VALID_CLASSES_PLACEMENT)

VALID_CLASSES_ADMISSION = [
    "cdcms_application_process","cdcms_course_highlight","cdcms_setion1"
]

VALID_CLASSES_SET_ADMISSION = set(VALID_CLASSES_ADMISSION)

def remove_a_img(soup):
    
    for tag in soup.select("a"):
        tag.unwrap()

    for tag in soup.select("iframe"):
        tag.decompose()

    for tag in soup.select("img"):
        tag.decompose()

    for tag in soup.select("svg"):
        tag.decompose()

    for tag in soup.select("div.body-adslot"):
        tag.decompose()
    
    for tag in soup.select("div.bodyslot-new"):
        tag.decompose()

    faq = soup.select_one(".cdcms_faqs")
    if faq: faq.decompose()

    return soup

def extract_sections_by_class(listing_article,valid_classes_set):

    tabs_data = []
    idx = 1

    for div in listing_article.find_all("div", recursive=True):
        classes = div.get("class", [])
        
        matched = next((cls for cls in classes if cls in valid_classes_set), None)

        if matched:
            h2_tag = div.find("h2")
            if h2_tag:
                title = h2_tag.get_text(strip=True) if h2_tag else f"Section {idx}"
                h2_tag.decompose()
                tabs_data.append({
                    "title": title,
                    "content": str(div).strip()
                })
                idx += 1

    return tabs_data

def extract_dynamic_data_by_h2(section):
    
    array_data = []

    elements = section.find_all(recursive=False)

    i = 0
    flag = True
    while i < len(elements):
        tag = elements[i]
        content_parts = []

        if tag.name == "p" and flag:

            while elements[i].name == "p" and (elements[i].name != "h2" or elements[i].name != "div"):
                content_parts.append(str(elements[i]))
                i += 1

            flag = False

            array_data.append({
                "title": "Overview",
                "content": "".join(content_parts).strip()
            })

        if tag.name == "h2":
            title = tag.get_text(strip=True)

            if tag.get_text(strip=True) == "Table of Content":
                i += 2
                continue

            j = 1
            while i + j < len(elements) and elements[i + j].name != "h2":
                content_parts.append(str(elements[i + j]).strip())
                j += 1

            array_data.append({
                "title": title,
                "content": "".join(content_parts).strip()
            })

            i += j  
        else:
            i += 1

    return array_data

async def scrape_overview(page):
    
    overview = []

    all_ids = []

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    
    listing_article = soup.find("div", id="listing-article") 

    if listing_article:

        toc_heading = soup.find(string=re.compile(r'\btable of contents?\b', re.I))

        print("TOC Heading Found:", toc_heading)

        # Step 3: If found, locate the next <ol> and extract all <a> tags from <li>
        if toc_heading:
            ol_tag = toc_heading.find_next("ol")

            if ol_tag:
                a_tags = ol_tag.find_all("a")
                for a in a_tags:
                    tag_id = a.get("href")
                    all_ids.append(tag_id)

        soup = remove_a_img(soup)

        if all_ids:

            section_data = {}

            for specific_id in all_ids[:]:

                tag = listing_article.find(id=specific_id[1:])
                if tag:
                    h2_text = tag .get_text()
                    print(h2_text)

                if not tag:
                    continue

                overview = []
                
                

            #     for siblings in tag.find_next_siblings():
            #         if siblings.get("id") in all_ids:
            #             break
            #         print(siblings.name)
            #         # overview.append({
            #         #     "title":h2_text,
            #         #     "content":str(siblings)
            #         # })

            # with open("file_name.json","w",encoding="utf-8") as f:
            #     json.dump(overview,f,ensure_ascii=False,indent=2)

            # print(overview)

            

        









        # listing_article_all_div = listing_article.find_all("div", recursive=False)

        # if listing_article_all_div:
        #     section1_divs = [
        #         div for div in listing_article_all_div
        #         if any(cls in div.get("class", []) for cls in ["cdcms_section1", "cdcms_college_highlights"])
        #     ]

        #     if section1_divs:
        #         overview.extend(extract_sections_by_class(section1_divs[0],VALID_CLASSES_SET_OVERVIEW))
        #         overview.extend(extract_dynamic_data_by_h2(section1_divs[0]))

        #     if not overview:
        #         overview.extend(extract_sections_by_class(listing_article,VALID_CLASSES_SET_OVERVIEW))
        #         overview.extend(extract_dynamic_data_by_h2(listing_article))

    return overview

async def scrape_admission(page):

    admission = []

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    soup = remove_a_img(soup)
    
    listing_article = soup.find("div", id="listing-article")
    if listing_article:

        h2_tags = listing_article.find_all("h2", recursive=False)
        
        if h2_tags:
            find_all_div = listing_article.find_all("div",recursive=False)
            if find_all_div:
                find_first_div = find_all_div[0]
                target_classes = {"cdcms_admission_highlights", "cdcms_section1"}
                for cls in target_classes:
                    matched = find_first_div.find("div", class_=cls)
                    if matched:
                        admission.extend(extract_dynamic_data_by_h2(matched))
            
            admission.extend(extract_dynamic_data_by_h2(listing_article))
        else:
            admission = extract_sections_by_class(listing_article,VALID_CLASSES_SET_OVERVIEW)

    return admission

async def scrape_placements(page):

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    soup = remove_a_img(soup)

    listing_article = soup.find("div", id="listing-article")
    placement = []

    

    if listing_article:
        
        cdcms_placement = listing_article.find("div",class_="cdcms_placement",recursive=False)
        if cdcms_placement:
            placement.extend(extract_sections_by_class(listing_article,VALID_CLASSES_SET_PLACEMENT))
            placement.extend(extract_dynamic_data_by_h2(cdcms_placement))
        else:
            placement.extend(extract_sections_by_class(listing_article,VALID_CLASSES_SET_OVERVIEW))

    return placement


async def scrape_cutoff(page):

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    soup = remove_a_img(soup)
    
    listing_article = soup.find("div",id="listing-article")

    cutoff = []
    cutof = []

    if listing_article:

        cutoff = extract_dynamic_data_by_h2(listing_article)

        if not cutoff:

            cdcms_cutoff = listing_article.find_all(recursive=False)
            cutoff = extract_dynamic_data_by_h2(cdcms_cutoff[0])

        
    if not cutoff:
        jsx_3964047535_mt_4 = soup.find_all("div",class_="jsx-3964047535 mt-4",recursive=True)

        if jsx_3964047535_mt_4:
            for inside_div in jsx_3964047535_mt_4:

                all_div = inside_div.find_all("div",recursive=False)

                if all_div:

                    h2_tag = all_div[0].find("h2")
                    if h2_tag:
                        h2_text = h2_tag.get_text() if h2_tag else "Content writer needs to add title here!"
                        h2_tag.decompose()
                    
                    cutoff.append({
                        "title":h2_text,
                        "content": "".join( str(i) for i in all_div[:len(all_div) - 1])
                    })
    return cutoff

async def sub_course_data(all_td):

    sub_course_name = None
    sub_course_fees = None
    sub_course_application_date = None
    sub_course_cutoff = None

    for idx,td in enumerate(all_td,start=0):

        text = td.get_text()

        if idx == 0:
            decompose_div1 = td.find("div",class_="jsx-2530098677 pointer position-absolute top-0 right-0 fs-11 d-flex align-items-center p-1")
            decompose_div2 = td.find("div",class_="jsx-2530098677 d-flex fs-14 font-weight-medium margint-2")
            decompose_div3 = td.find("div",class_="jsx-2530098677 d-flex fs-11 font-weight-medium mt-2 font-italic")

            if decompose_div1:
                decompose_div1.decompose()
            if decompose_div2:
                decompose_div2.decompose()
            if decompose_div3:
                decompose_div3.decompose()

            sub_course_name = td.get_text(strip=True)

        elif idx == 1:
            sub_course_fees = text
        elif idx == 2:
            sub_course_application_date = text
        elif idx == 3:
            sub_course_cutoff = text
    
    return {
        "sub_course_name":sub_course_name,
        "sub_course_fees":sub_course_fees,
        "sub_course_application_date":sub_course_application_date,
        "sub_course_cutoff":sub_course_cutoff
    }

async def sub_college_fetch_table(soup2):

    data = []
    sub_courses_table = soup2.find("table",recursive=True)

    if sub_courses_table:
        sub_courses_tbody = sub_courses_table.find("tbody",recursive=False)
        if sub_courses_tbody:
            sub_courses_tr = sub_courses_tbody.find_all("tr")

            if sub_courses_tr:
                for idx, tr in enumerate(sub_courses_tr,start=0):
                    all_td = tr.find_all("td", recursive=False)
                    ok = await sub_course_data(all_td)
                    data.append(ok)

    return data

async def scrape_courses(page):

    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")
    soup = remove_a_img(soup)

    main_course = []
    courses = []
    course_info = []
    
    fees_info = soup.find("section",class_="fees-info")

    if fees_info:
        
        h2_tag = fees_info.find("h2",recursive=False)
        if h2_tag:
            h2_text = h2_tag.get_text(strip=True)
        
        course_data = soup.find("div",class_="jsx-558956768 slug-article fs-16 font-weight-normal text-primary-black mb-4")
        if course_data:
            courses.append({
                "title":h2_text,
                "sections":str(course_data)
            })

        course_table = fees_info.find("table",recursive=False)
        if course_table:
            tbody = course_table.find("tbody",recursive=False)
            all_tr = tbody.find_all("tr",recursive=False)
            modal_index = 0  

            if all_tr:
                for idx, tr in enumerate(all_tr):
                    course_name_text = None
                    course_fees = None
                    course_eligibility = None
                    course_application_date = None

                    modal_html = None
                    sub_course_info = []
                    all_td = tr.find_all("td", recursive=False)
                    if all_td:

                        for idx,td in enumerate(all_td,start=0):
                            text = td.get_text(strip=True)

                            if idx == 0:
                        
                                sub_courses = td.find("div", class_="pointer")
                                if sub_courses:
                                    try:
                                        modal_buttons = page.locator("div.jsx-558956768.pointer.text-primary-blue.fs-14.d-flex")
                                        if await modal_buttons.count() > modal_index:
                                            await modal_buttons.nth(modal_index).click()
                                        await page.wait_for_selector("div.modal-content", state="visible")

                                        await page.wait_for_timeout(1000)

                                        modal_html = await page.locator("div.modal-content").inner_html()
                                        soup2 = BeautifulSoup(modal_html, "html.parser")
                                        sub_course_info = await sub_college_fetch_table(soup2)

                                        await page.click("span.circle-cross-black-24")

                                    except Exception as e:
                                        print(f"❌ Failed on row {idx} ({course_name_text}):", e)
                                    finally:
                                        modal_index += 1 

                                if modal_html and modal_html.strip():
                                    course_name_div = td.find("div", class_="course-name")
                                    course_name_elem = course_name_div.select_one("div") if course_name_div else None
                                    course_name_text = course_name_elem.get_text(strip=True) if course_name_elem else "Unknown Course"
                                else:
                                    course_name_div = td.find("div", class_="course-name")
                                    course_name_text = course_name_div.get_text(strip=True) if course_name_div else "Unknown Course"
                            elif idx == 1:
                                button = td.find("button")
                                if button:
                                    button.decompose()
                                course_fees = text
                            elif idx == 2:
                                course_eligibility = text
                            elif idx == 3:
                                course_application_date = text

                        course_info.append({
                            "course_name" : str(course_name_text),
                            "course_fees":str(course_fees),
                            "course_eligibility":str(course_eligibility),
                            "course_application_date":str(course_application_date),
                            "sub_course_info_list":sub_course_info
                        })
                        
    main_course.append({
        "tabs":courses,
        "courses":course_info
    })

   
    return main_course
    
                                



