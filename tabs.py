from bs4 import BeautifulSoup

VALID_CLASSES_OVERVIEW = [
        "cdcms_ranking","cdcms_cut_off","cdcms_cutoff",
        "cdcms_admission_process", "cdcms_placement", "cdcms_exam_highlights","cdcms_application_process",
        "cdcms_courses","cdcms_admission_highlights","cdcms_scholarship",
        "cdcms_section2", "cdcms_section3", "cdcms_section4",
        "cdcms_section5", "cdcms_section6", "cdcms_section7", "cdcms_section8","cdcms_scholarships",
        "cdcms_section9", "cdcms_section10", "cdcms_section11", "cdcms_section12","cdcms_comparison","cdcms_faculty"
    ]

VALID_CLASSES_SET_overview = set(VALID_CLASSES_OVERVIEW)

VALID_CLASSES_ADMISSION = [
    "cdcms_application_process","cdcms_course_highlight","cdcms_setion1"
]

VALID_CLASSES_SET_ADMISSION = set(VALID_CLASSES_ADMISSION)

def extract_sections_by_class(listing_article):

    tabs_data = []
    idx = 1

    for div in listing_article.find_all("div", recursive=True):
        classes = div.get("class", [])
        
        matched = next((cls for cls in classes if cls in VALID_CLASSES_SET_overview), None)

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

def parse_article_sections(listing_article, valid_class_set=None):

    sections = []
    seen_titles = set()

    if valid_class_set:
        for div in listing_article.find_all("div", recursive=True):
            classes = div.get("class", [])
            matched = next((cls for cls in classes if cls in valid_class_set), None)

            if matched:
                h2_tag = div.find("h2")
                title = h2_tag.get_text(strip=True) if h2_tag else f"Section {len(sections)+1}"
                if h2_tag: h2_tag.decompose()

                if title not in seen_titles:
                    sections.append({
                        "title": title,
                        "content": str(div).strip(),
                        "source": "class"
                    })
                    seen_titles.add(title)

    if not sections:
        elements = listing_article.find_all(recursive=False)
        i = 0
        while i < len(elements):
            tag = elements[i]
            content_parts = []

            if tag.name == "h2":
                title = tag.get_text(strip=True)
                if title == "Table of Content":
                    i += 2
                    continue

                j = 1
                while i + j < len(elements) and elements[i + j].name != "h2":
                    content_parts.append(str(elements[i + j]))
                    j += 1

                if title not in seen_titles:
                    sections.append({
                        "title": title,
                        "content": "".join(content_parts).strip(),
                        "source": "h2"
                    })
                    seen_titles.add(title)

                i += j
            else:
                i += 1

    if not sections:
        flat_parts = []
        for el in listing_article.find_all(["p", "div"], recursive=False):
            flat_parts.append(str(el))

        if flat_parts:
            sections.append({
                "title": "Overview",
                "content": "".join(flat_parts).strip(),
                "source": "flat"
            })

    return sections


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

                overview.extend(extract_sections_by_class(section1_divs[0]))

                # if not overview:
                overview.extend(extract_dynamic_data_by_h2(section1_divs[0]))
            else:
                overview.extend(extract_sections_by_class(section1_divs[0]))

                # if not overview:
                overview.extend(extract_dynamic_data_by_h2(section1_divs[0]))
            

                    
    return overview

async def scrape_admission(soup):

    admission = []
    flag = False
    
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
                        admission = extract_dynamic_data_by_h2(matched) 
                        flag = True
            
            if not flag:
                admission = extract_dynamic_data_by_h2(listing_article) 


            for h2 in h2_tags:
                wrapper_div = h2.find_next_sibling("div")
                if not wrapper_div:
                    continue

                for inner in wrapper_div.find_all("div", recursive=False):
                    inner_classes = inner.get("class", [])
                    if VALID_CLASSES_SET_ADMISSION.intersection(inner_classes):
                        admission.append({
                            "title": h2.get_text(strip=True),
                            "content": str(inner).strip()
                        })
                        break
        else:
            admission = extract_sections_by_class(listing_article)

    return admission

async def scrape_placements(soup):
    listing_article = soup.find("div", id="listing-article")
    placement = []

    if listing_article:
        placement = parse_article_sections(listing_article, VALID_CLASSES_SET_overview)

        # cdcms_section1 = listing_article.find("div",class_="cdcms_section1",recursive=False)
        # if cdcms_section1:
        #     placement.extend(extract_sections_by_class(cdcms_section1))

        # cdcms_placement = listing_article.find("div",class_="cdcms_placement",recursive=False)
        # if cdcms_placement:
        #     placement.extend(extract_dynamic_data_by_h2(cdcms_placement))

    return placement


async def scrape_cutoff(soup):
    
    listing_article = soup.find("div",id="listing-article")

    cutoff = []

    if listing_article:

        cutoff = extract_dynamic_data_by_h2(listing_article)

        if not cutoff:

            cdcms_cutoff = listing_article.find_all(recursive=False)

            cutoff = extract_dynamic_data_by_h2(cdcms_cutoff[0])
            

    return cutoff


