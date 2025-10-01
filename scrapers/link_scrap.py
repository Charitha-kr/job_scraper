import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time

def extract_linkedin_job_id(url):
    match = re.search(r'/jobs/view/(\d+)', url)
    return match.group(1) if match else url

def convert_to_absolute_date(date_str):
    today = datetime.today().date()
    lower = date_str.lower()
    if 'just now' in lower or 'today' in lower:
        return today.strftime('%Y-%m-%d')
    if 'hour' in lower:
        return today.strftime('%Y-%m-%d')
    if 'day' in lower:
        m = re.search(r'(\d+)\s+day', date_str)
        days_ago = int(m.group(1)) if m else 0
        return (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    if 'week' in lower:
        m = re.search(r'(\d+)\s+week', date_str)
        weeks_ago = int(m.group(1)) if m else 0
        return (today - timedelta(weeks=weeks_ago)).strftime('%Y-%m-%d')
    return today.strftime('%Y-%m-%d')

def is_fresher_title(title):
    whitelist = [
        'fresher', 'trainee', 'graduate', 'new grad', 'recent graduate', 'entry level',
        'intern', 'apprentice', 'junior', 'campus', 'no experience', "management trainee"
    ]
    blacklist = [
        'senior', 'lead', 'director', 'vp', 'head',
        '2 year', '3 year', '4 year', '5 year', '6 year', '7 year', '8 year', '9 year', '10 year', 'plus year', 'yrs experience'
    ]
    t = title.lower()
    allow = any(w in t for w in whitelist)
    deny = any(b in t for b in blacklist)
    return allow and not deny

def fetch_linkedin_jobs(keyword, location="India", start_date=None, end_date=None,
                        max_pages=6, exact_phrase=False, entry_level_filter=False):
    if exact_phrase:
        keyword_url = f'%22{keyword}%22'  # exact phrase
    else:
        keyword_url = keyword.replace(' ', '%20')
    location_url = location.replace(' ', '%20')
    headers = {"User-Agent": "Mozilla/5.0"}

    all_jobs = []
    seen_job_ids = set()
    seen_job_keys = set()

    # Add f_E=1 for entry level filter
    filter_str = "&f_E=1" if entry_level_filter else ""

    for page in range(max_pages):
        start = page * 25
        url = (f"https://www.linkedin.com/jobs/search/?keywords={keyword_url}"
               f"&location={location_url}{filter_str}&start={start}")
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"Failed to fetch page {page+1} (status {resp.status_code})")
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", class_="base-card")
        if not cards:
            break

        for card in cards:
            try:
                title_tag = card.find("h3", class_="base-search-card__title")
                company_tag = card.find("h4", class_="base-search-card__subtitle")
                link_tag = card.find("a", class_="base-card__full-link")
                posted_el = card.find("time")

                title = title_tag.get_text(strip=True) if title_tag else ''
                # For second fetch (entry_level_filter=False), apply fresher title filter
                if not entry_level_filter:
                    if not is_fresher_title(title):
                        continue

                company = company_tag.get_text(strip=True) if company_tag else ''
                url_job = link_tag['href'] if link_tag else ''
                job_id = extract_linkedin_job_id(url_job)

                if posted_el and posted_el.has_attr("datetime"):
                    post_date_str = posted_el["datetime"][:10]
                else:
                    date_span = card.find("span", string=lambda s: s and ("ago" in s or "today" in s.lower()))
                    post_date_str = convert_to_absolute_date(date_span.text if date_span else "today")

                location_tag = card.find("span", class_="job-search-card__location")
                job_loc = location
                if location_tag:
                    loc_val = location_tag.get_text(strip=True)
                    bangalore_keywords = [
        "bengaluru", "bangalore", "greater bangalore area",
        "north bangalore", "south bangalore"
    ]
                    if not any(keyword in loc_val.lower() for keyword in bangalore_keywords):
                        continue
                    job_loc = loc_val
                    
                if start_date and end_date:
                    try:
                        post_date = datetime.strptime(post_date_str, '%Y-%m-%d').date()
                        if not (start_date <= post_date <= end_date):
                            continue
                    except:
                        continue

                job_key = (title.lower(), company.lower(), job_loc.lower())

                if job_id not in seen_job_ids and job_key not in seen_job_keys:
                    seen_job_ids.add(job_id)
                    seen_job_keys.add(job_key)
                    all_jobs.append({
                        "title": title,
                        "company": company,
                        "url": url_job,
                        "location": job_loc,
                        "date": post_date_str,
                        "source": "LinkedIn"
                    })
            except Exception as e:
                print("Parse error:", e)
                continue
        time.sleep(2)

    return all_jobs
