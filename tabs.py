from bs4 import BeautifulSoup

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

async def scrape_overview(soup):
    
    overview = []
    
    listing_article = soup.find("div", id="listing-article") 

    if listing_article:
        listing_article_all_div = listing_article.find_all("div", recursive=False)

        if listing_article_all_div:
            section1_divs = [
                div for div in listing_article_all_div
                if any(cls in div.get("class", []) for cls in ["cdcms_section1", "cdcms_college_highlights"])
            ]

            if section1_divs:
                overview.extend(extract_sections_by_class(section1_divs[0],VALID_CLASSES_SET_OVERVIEW))
                overview.extend(extract_dynamic_data_by_h2(section1_divs[0]))

            if not overview:
                overview.extend(extract_sections_by_class(listing_article,VALID_CLASSES_SET_OVERVIEW))
                overview.extend(extract_dynamic_data_by_h2(listing_article))

    return overview

async def scrape_admission(soup):

    admission = []
    
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

async def scrape_placements(soup):
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


async def scrape_cutoff(soup):
    
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


