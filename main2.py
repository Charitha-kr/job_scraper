from dotenv import load_dotenv
import os
from datetime import datetime
import pandas as pd
import re

load_dotenv()

from scrapers.link_scrap import fetch_linkedin_jobs

def main():
    keyword = input('Enter job keyword or phrase (use quotes for exact phrase): ').strip()
    location = input('Enter location (default India): ').strip() or 'India'
    start_date_str = input('Enter START date (YYYY-MM-DD): ').strip()
    end_date_str = input('Enter END date (YYYY-MM-DD): ').strip()

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except:
        print('Invalid dates! Please use YYYY-MM-DD format.')
        return

    exact_phrase = False
    if keyword.startswith('"') and keyword.endswith('"'):
        keyword = keyword.strip('"')
        exact_phrase = True

    print("Fetching fresher jobs with Entry Level filter enabled...")
    jobs_fresher_filter = fetch_linkedin_jobs(keyword, location, start_date, end_date,
                                              max_pages=6, exact_phrase=exact_phrase,
                                              entry_level_filter=True)

    print("Fetching fresher jobs by title keyword filtering...")
    jobs_title_filter = fetch_linkedin_jobs(keyword, location, start_date, end_date,
                                            max_pages=6, exact_phrase=exact_phrase,
                                            entry_level_filter=False)

    # Combine and deduplicate all jobs by job ID and (title, company, location)
    combined_jobs = []
    seen_job_ids = set()
    seen_job_keys = set()

    for job in jobs_fresher_filter + jobs_title_filter:
        job_id = re.search(r'/jobs/view/(\d+)', job['url'])
        job_id = job_id.group(1) if job_id else job['url']
        job_key = (job['title'].lower(), job['company'].lower(), job['location'].lower())
        if job_id not in seen_job_ids and job_key not in seen_job_keys:
            seen_job_ids.add(job_id)
            seen_job_keys.add(job_key)
            combined_jobs.append(job)

    if not os.path.exists("data"):
        os.makedirs("data")

    pd.DataFrame(combined_jobs).to_csv("data/job_results.csv", index=False)

    print(f"\nSaved {len(combined_jobs)} unique fresher jobs for '{keyword}' in {location} to data/job_results.csv")

if __name__ == "__main__":
    main()
