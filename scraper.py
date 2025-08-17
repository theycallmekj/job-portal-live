# AapkaRojgar Tools - Automated JSON Content Scraper (V33.1 - Final Correction)

import requests
from bs4 import BeautifulSoup
import time
import os
import re
import json
import shutil
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil.parser import parse as date_parser
from urllib.parse import urljoin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- 1. Configuration ---
URL_FILE = 'links.txt'
SEEN_URLS_FILE = 'seen_urls.txt'
DATA_JSON_FILE = 'data.json'
CONSOLIDATED_CONTENT_DIR = 'consolidated_content'
GEMINI_RESPONSE_DIR = 'gemini_responses'
CHECK_INTERVAL_SECONDS = 3600
GROUPING_SIMILARITY_THRESHOLD = 0.75

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- THIS IS THE ONLY CHANGE ---
# The model name is not a secret, so we can set it directly in the code.
GEMINI_MODEL = "gemini-2.5-flash-lite"

# --- 2. AI Prompt (V33.0 - The Complete, Final Version) ---
CUSTOM_PROMPT = """
You are a master data synthesis AI for a government job portal. Your output MUST be perfect, detailed, and strictly follow the schema.

--- ! GOLDEN RULE: ZERO TOLERANCE FOR PLACEHOLDERS & SCHEMA VIOLATIONS ! ---
1.  **NO PLACEHOLDERS:** If information is not in the text, the JSON value MUST be `null`. NEVER output the string "NA", "Not Available", "Various", or "Notify Soon". This is a critical failure.
2.  **STRICT SCHEMA ENFORCEMENT:** You MUST place all data inside the schema exactly as shown. Only use the keys provided in the schemas. Do not invent new keys.

--- CRITICAL DIRECTIVES ---
1.  **CLASSIFY FIRST:** Correctly CLASSIFY the content `type`.
2.  **SYNTHESIZE COMPLEX DATA:** For posts with many sub-roles, list each one's requirements. Create structured tables for breakdowns. Do not just copy a wall of text.
3.  **COMPLETE FAQS:** Every FAQ item MUST have both a `question` and a valid `answer`. If you cannot find an answer, do not include that FAQ item.
4.  **NULL DATES FOR NON-APPLICATIONS:** For types like "result" or "admit_card", the top-level `last_date` MUST be `null`.
5.  **INCLUDE CREATION DATE:** Include a `creation_date` field, using today's date provided in the text.

--- ! --- STRICT JSON SCHEMAS BY TYPE --- ! ---

> "job" or "upcoming_job" SCHEMA:
{
  "type": "job", "id": "indian-navy-ssc-officer-june-2026", "title": "Indian Navy SSC Officer Recruitment June 2026 for 260 Posts", "last_date": "2025-09-01", "creation_date": "2025-08-17", "new": true,
  "details": {
    "post_name": "Indian Navy SSC Officer June 2026", "post_subtitle": "Join Indian Navy (Nausena Bharti)",
    "at_a_glance_summary": { "Post Name": "SSC Officer in various branches", "Application Dates": "09 August 2025 - 01 September 2025", "Application Fee": "No fee", "Total Vacancies": "260" },
    "eligibility_criteria": { "education": ["SSC General Service (GS/X): BE / B.Tech in Any Discipline with 60% Marks."], "age_limit": ["General Service (GS/X): Born between 02/01/2001 and 01/07/2006"] },
    "vacancy_details": { "total_posts_summary": "A total of 260 positions are available.", "breakdown": [{ "Branch": "Executive Branch", "Total Posts": "153" }] },
    "how_to_fill_form": ["Read the notification carefully.", "Visit the official Indian Navy website.", "Fill in the required details."],
    "important_links": { "Apply Online": "...", "Download Notification": "...", "Official Website": "..." },
    "faq": [{"question": "What is the last date to apply?", "answer": "The last date is September 1, 2025."}]
  }
}

> "result" SCHEMA:
{
  "type": "result", "id": "ssc-cgl-tier-1-result-2025", "title": "SSC CGL 2024 Tier 1 Result with Marks & Cutoff 2025", "last_date": null, "creation_date": "2025-08-15", "new": true,
  "details": {
    "post_name": "SSC Combined Graduate Level Tier 1 Result 2025", "post_subtitle": "Staff Selection Commission (SSC)",
    "result_summary": { "Exam Name": "SSC CGL 2024-25", "Tier 1 Exam Held On": "October 2024", "Result Released": "15 August 2025", "Marks Available": "20 August 2025" },
    "how_to_check_result": [ "Click on the 'Download Result' link provided below.", "A PDF file will open containing the roll numbers of qualified candidates.", "Use Ctrl+F to search for your roll number." ],
    "important_links": { "Download Result (List 1)": "...", "Download Cutoff": "...", "Check Marks / Score Card": "...", "Official Website": "..." },
    "faq": [{"question": "When will the Tier 2 exam be held?", "answer": "The schedule for the Tier 2 exam will be announced shortly."}]
  }
}

> "admit_card" SCHEMA:
{
  "type": "admit_card", "id": "rrb-alp-stage-2-admit-card-2025", "title": "Railway RRB ALP Stage 2 Exam Date & Admit Card 2025", "last_date": null, "creation_date": "2025-09-15", "new": true,
  "details": {
    "post_name": "RRB Assistant Loco Pilot (ALP) CBT 2 Admit Card 2025", "post_subtitle": "Railway Recruitment Board (RRB)",
    "admit_card_summary": { "Post Name": "Assistant Loco Pilot", "Exam Date": "25-28 September 2025", "Admit Card Available": "21 September 2025", "Exam City Details": "Available from 15 September 2025" },
    "how_to_download": [ "Click on the 'Download Admit Card' link.", "Enter your Registration Number and Date of Birth.", "Your admit card will be displayed. Download and print it." ],
    "important_links": { "Download Admit Card": "...", "Check Exam City / Date": "...", "Official Website": "..." },
    "faq": [{"question": "What documents do I need to carry to the exam?", "answer": "You must carry a printed copy of your admit card along with a valid photo ID proof in original."}]
  }
}

> "answer_key" SCHEMA:
{
  "type": "answer_key", "id": "up-police-constable-answer-key-2025", "title": "UP Police Constable Exam Answer Key 2025", "last_date": null, "creation_date": "2025-08-22", "new": true,
  "details": {
    "post_name": "UP Police Constable Answer Key 2025", "post_subtitle": "Uttar Pradesh Police Recruitment and Promotion Board (UPPRPB)",
    "answer_key_summary": {"Exam Date": "18-19 August 2025", "Answer Key Released": "22 August 2025", "Objection Window": "22 Aug 2025 to 25 Aug 2025"},
    "how_to_download_and_challenge": ["Click the 'Download Answer Key' link.", "Login with your credentials.", "To challenge a question, use the 'File Objection' link before the deadline."],
    "important_links": {"Download Answer Key": "...", "File Objection": "...", "Official Website": "..."},
    "faq": [{"question": "What is the fee for challenging an answer?", "answer": "There is typically a fee per question challenged, which is mentioned in the official notice."}]
  }
}

> "syllabus" SCHEMA:
{
  "type": "syllabus", "id": "nda-2-syllabus-2025", "title": "UPSC NDA 2 Exam Syllabus & Pattern 2025", "last_date": null, "creation_date": "2025-05-10", "new": true,
  "details": {
    "post_name": "UPSC NDA & NA II Syllabus 2025", "post_subtitle": "Union Public Service Commission (UPSC)",
    "exam_pattern_summary": {"Paper I": "Mathematics (300 Marks, 2.5 Hours)", "Paper II": "General Ability Test (600 Marks, 2.5 Hours)", "Total": "900 Marks", "Negative Marking": "Yes (1/3rd)"},
    "syllabus_details": { "Mathematics": ["Algebra", "Matrices and Determinants", "Trigonometry"], "General Ability (GK)": ["Physics", "Chemistry", "History"] },
    "important_links": {"Download Syllabus PDF": "...", "Official Website": "..."}
  }
}

> "admission" SCHEMA:
{
  "type": "admission", "id": "up-polytechnic-admission-2025", "title": "UP Polytechnic JEECUP Online Admission Form 2025", "last_date": "2025-08-30", "creation_date": "2025-08-01", "new": true,
  "details": {
    "post_name": "Joint Entrance Examination Council (Polytechnic), Uttar Pradesh (JEECUP) 2025", "post_subtitle": "JEECUP Admissions",
    "admission_summary": {"Application Start": "01 Aug 2025", "Application End": "30 Aug 2025", "Exam Date": "September 2025", "Application Fee": "General/OBC: 300/-, SC/ST: 200/-"},
    "important_links": {"Apply Online": "...", "Download Notification": "...", "Official Website": "..."}
  }
}

> "important_document" SCHEMA:
{
  "type": "important_document", "id": "eci-bihar-voter-list-2025", "title": "ECI Bihar Draft Voter List 2025", "last_date": "2025-09-01", "creation_date": "2025-08-17", "new": true,
  "details": {
    "post_name": "ECI Bihar SIR Draft Voter List 2025", "post_subtitle": "Election Commission of India",
    "document_summary": {"Correction/Objection Phase": "01 Aug – 01 Sep 2025", "Final List Date": "30-09-2025"},
    "important_links": {"Download Document": "...", "Official Website": "..."}
  }
}
--- ARTICLE CONTENT ---
"""

# --- (The rest of the script is unchanged) ---
# --- 3. Archiving Logic & Helpers ---
ARCHIVE_CONFIG = {
    "latest_jobs": {"key": "last_date", "days_after": 0},
    "admission": {"key": "last_date", "days_after": 0},
    "admit_card": {"key": "details.admit_card_summary.Exam Date", "days_after": 7},
    "answer_key": {"key": "details.answer_key_summary.Objection Window", "days_after": 15},
    "result": {"key": "creation_date", "days_after": 90},
    "syllabus": {"key": "creation_date", "days_after": 365},
    "upcoming_jobs": {"key": "creation_date", "days_after": 365},
    "important_documents": {"key": "creation_date", "days_after": 180},
}
def get_nested_value(data_dict, key_string):
    keys = key_string.split('.')
    for key in keys:
        try:
            data_dict = data_dict[key]
        except (KeyError, TypeError):
            return None
    return data_dict
def get_latest_date_from_string(date_str):
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        matches = re.findall(r'\d{1,2}[ -/]\w+[ -/]\d{4}|\d{4}[ -/]\d{2}[ -/]\d{2}', date_str)
        if not matches:
            return date_parser(date_str).date()
        return date_parser(matches[-1]).date()
    except (ValueError, TypeError):
        return None
def run_archiving_process(data_file_path):
    print("\n--- Running Universal Archiving Process ---")
    if not os.path.exists(data_file_path):
        print(f"  -> {data_file_path} not found. Skipping archiving for this cycle.")
        return
    try:
        with open(data_file_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            today = datetime.now().date()
            if "archived_content" not in data:
                data["archived_content"] = {}
            total_archived_count = 0
            for category, config in ARCHIVE_CONFIG.items():
                if category not in data or not data[category]:
                    continue
                active_items, items_to_archive = [], []
                print(f"  -> Checking category: '{category}'")
                for item in data.get(category, []):
                    should_archive = False
                    date_str = get_nested_value(item, config['key'])
                    expiry_date = get_latest_date_from_string(date_str)
                    if expiry_date:
                        archive_on_date = expiry_date + timedelta(days=config['days_after'])
                        if archive_on_date < today:
                            should_archive = True
                    if should_archive:
                        items_to_archive.append(item)
                    else:
                        active_items.append(item)
                if items_to_archive:
                    print(f"    - Archiving {len(items_to_archive)} item(s).")
                    if category not in data["archived_content"]:
                        data["archived_content"][category] = []
                    data["archived_content"][category] = items_to_archive + data["archived_content"][category]
                    data[category] = active_items
                    total_archived_count += len(items_to_archive)
            if total_archived_count == 0:
                print("  -> No content to archive in this cycle.")
                return
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate()
            print(f"  -> Archiving complete. Moved a total of {total_archived_count} items.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  -> Could not run archiving: {e}")

# --- 4. Core Scraper & File Functions ---
def generate_slug(text):
    text = text.lower(); text = re.sub(r'\s+', '-', text); text = re.sub(r'[^a-z0-9-]', '', text)
    return text[:80]
def get_json_from_gemini(content):
    if not GEMINI_API_KEY: print("  -> ERROR: GOOGLE_API_KEY not set."); return None, None
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    full_prompt = CUSTOM_PROMPT + content
    try:
        print(f"  -> Contacting Gemini (Model: {GEMINI_MODEL})...")
        response = model.generate_content(full_prompt)
        raw_response_text = response.text.strip()
        json_match = re.search(r'\{.*\}', raw_response_text, re.DOTALL)
        if json_match: return json.loads(json_match.group(0)), raw_response_text
        else: print("  -> ERROR: No valid JSON object in AI response."); print("  -> Raw Response:", raw_response_text); return None, raw_response_text
    except Exception as e:
        print(f"  -> FATAL ERROR with Gemini API: {e}"); return None, f"Error: {e}"
def load_seen_urls():
    if not os.path.exists(SEEN_URLS_FILE): return set()
    with open(SEEN_URLS_FILE, 'r') as f: return set(line.strip() for line in f)
def save_seen_url(url):
    with open(SEEN_URLS_FILE, 'a') as f: f.write(url + '\n')
def read_urls_from_file(filename):
    if not os.path.exists(filename): return []
    with open(filename, 'r') as f: return [line.strip() for line in f if line.strip()]
def load_data_json():
    try:
        with open(DATA_JSON_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Warning: {DATA_JSON_FILE} not found/invalid. Creating new.")
        return {"latest_jobs": [], "result": [], "admit_card": [], "answer_key": [], "syllabus": [], "admission": [], "upcoming_jobs": [], "important_documents": [], "archived_content": {}}
def save_data_json(data):
    with open(DATA_JSON_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> SUCCESS: data.json has been updated.")
def save_gemini_response(slug, response_text):
    if not os.path.exists(GEMINI_RESPONSE_DIR): os.makedirs(GEMINI_RESPONSE_DIR)
    timestamp = int(time.time() * 1000)
    filepath = os.path.join(GEMINI_RESPONSE_DIR, f"{slug}-{timestamp}.json")
    with open(filepath, 'w', encoding='utf-8') as f: f.write(response_text)
    print(f"  -> Saved Gemini response to: {filepath}")
def scrape_website_for_new_links(base_url, seen_urls):
    new_articles, current_year = [], datetime.now().year
    RELEVANT_KEYWORDS = ['police', 'constable', 'ssc', 'ibps', 'railway', 'recruitment', 'admit card', 'result', 'notification', 'vacancy', 'bharti', 'answer key', 'syllabus', 'admission', 'apply online', 'download', 'cgl', 'chsl', 'mts', 'teacher', 'officer']
    GENERIC_LINK_TEXTS = {'admit card', 'result', 'latest jobs', 'answer key', 'syllabus', 'admission', 'sarkariresult tools', 'sarkariresult', 'rojgar result', 'sarkari result', 'privacy policy'}
    try:
        response = requests.get(base_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            original_link_text = link.get_text(strip=True)
            link_text_lower = original_link_text.lower()
            if len(link_text_lower.split()) < 2 or any(generic in link_text_lower for generic in GENERIC_LINK_TEXTS): continue
            if any(keyword in link_text_lower for keyword in RELEVANT_KEYWORDS):
                years_in_title = re.findall(r'\b(202\d)\b', original_link_text)
                if years_in_title and any(int(year) < current_year for year in years_in_title):
                    if not any(int(year) >= current_year for year in years_in_title):
                       print(f"  -> SKIPPING (Outdated Year): '{original_link_text}'"); continue
                link_href = urljoin(base_url, link['href'])
                if link_href not in seen_urls:
                    print(f"  -> Found new post link: '{original_link_text}'")
                    new_articles.append({'title': original_link_text, 'url': link_href})
                    seen_urls.add(link_href)
    except requests.RequestException as e: print(f"Error scraping {base_url}: {e}")
    return new_articles
def scrape_article_and_links(article_url):
    try:
        print(f"  -> Scraping content & links from: {article_url}")
        response = requests.get(article_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        important_links = {}
        link_keywords = ['apply online', 'notification', 'official website', 'login', 'click here', 'download result', 'admit card', 'answer key', 'syllabus']
        for link in soup.find_all('a', href=True):
            link_text_clean = re.sub(r'\s+', ' ', link.get_text(strip=True)).strip()
            if any(keyword in link_text_clean.lower() for keyword in link_keywords):
                if link_text_clean not in important_links:
                     important_links[link_text_clean] = urljoin(article_url, link['href'])
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'form', 'aside']): element.decompose()
        main_content = soup.find('article') or soup.find('main') or soup.find(id='post') or soup.find(class_=re.compile(r'content|post|entry|article')) or soup.body
        if main_content: text = main_content.get_text(separator='\n', strip=True)
        else: print(f"  -> WARN: Could not find main content for {article_url}."); text = ""
        if important_links:
            text += "\n\n--- EXTRACTED LINKS ---\n"
            for link_text, url in important_links.items(): text += f'"{link_text}": "{url}"\n'
        return text
    except requests.RequestException as e: print(f"  -> ERROR fetching {article_url}: {e}"); return ""

# --- 5. Main Execution ---
def run_automation_cycle():
    print(f"--- AapkaRojgar Scraper V33.1 (Final Correction) ---")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting new scan...")
    run_archiving_process(DATA_JSON_FILE)
    website_urls = read_urls_from_file(URL_FILE)
    if not website_urls: print(f"FATAL: No URLs in {URL_FILE}. Exiting."); return
    seen_urls = load_seen_urls()
    print(f"Loaded {len(seen_urls)} previously seen URLs.")
    all_new_articles_meta = []
    for url in website_urls:
        print(f"\nScraping {url} for new links...")
        new_links = scrape_website_for_new_links(url, seen_urls)
        for link_info in new_links:
            content_with_links = scrape_article_and_links(link_info['url'])
            if content_with_links and len(content_with_links) > 200:
                all_new_articles_meta.append({'title': link_info['title'], 'content': content_with_links, 'url': link_info['url']})
            else: save_seen_url(link_info['url'])
    if not all_new_articles_meta: print("\nScan complete. No new valid articles."); return
    print(f"\n--- PHASE 2: Grouping {len(all_new_articles_meta)} articles by similarity ---")
    corpus = [meta['content'] for meta in all_new_articles_meta]
    vectorizer = TfidfVectorizer(stop_words='english').fit_transform(corpus)
    similarity_matrix = cosine_similarity(vectorizer)
    groups, visited_indices = [], set()
    for i in range(len(all_new_articles_meta)):
        if i in visited_indices: continue
        similar_indices = {i}
        queue = [i]; visited_in_group = {i}
        while queue:
            current_index = queue.pop(0)
            for j in range(len(all_new_articles_meta)):
                if j not in visited_in_group and similarity_matrix[current_index, j] > GROUPING_SIMILARITY_THRESHOLD:
                    similar_indices.add(j); visited_in_group.add(j); queue.append(j)
        current_group = [all_new_articles_meta[idx] for idx in sorted(list(similar_indices))]
        groups.append(current_group)
        for idx in similar_indices: visited_indices.add(idx)
    print(f"\n--- PHASE 3 & 4: Consolidating {len(groups)} groups for AI Analysis ---")
    if not os.path.exists(CONSOLIDATED_CONTENT_DIR): os.makedirs(CONSOLIDATED_CONTENT_DIR)
    today_date_str = datetime.now().strftime("%Y-%m-%d")
    for i, group in enumerate(groups):
        print(f"\n--- Processing Group {i+1}/{len(groups)} ---")
        consolidated_content, group_urls = "", []
        consolidated_content += f"IMPORTANT CONTEXT: Today's date is {today_date_str}. Use this for the 'creation_date' field and to determine if a job is current or upcoming.\n\n"
        for article_meta in group:
            print(f"  - Combining: {article_meta['title']}")
            consolidated_content += f"\n--- Source: {article_meta['url']} ---\n\n{article_meta['content']}"
            group_urls.append(article_meta['url'])
        group_slug = generate_slug(group[0]['title'])
        consolidated_filepath = os.path.join(CONSOLIDATED_CONTENT_DIR, f"{group_slug}.txt")
        with open(consolidated_filepath, 'w', encoding='utf-8') as f: f.write(consolidated_content)
        print(f"  -> Saved consolidated content to: {consolidated_filepath}")
        new_json_entry, raw_response = get_json_from_gemini(consolidated_content)
        if raw_response: save_gemini_response(group_slug, raw_response)
        if not new_json_entry or not isinstance(new_json_entry, dict):
            print("  -> RESULT: AI failed to produce a valid JSON object. Discarding group.")
            for url in group_urls: save_seen_url(url)
            continue
        new_json_entry['creation_date'] = today_date_str
        entry_type = new_json_entry.get("type")
        category_key_map = {
            "job": "latest_jobs", "upcoming_job": "upcoming_jobs", "result": "result", 
            "admit_card": "admit_card", "answer_key": "answer_key", "syllabus": "syllabus", 
            "admission": "admission", "important_document": "important_documents"
        }
        category_key = category_key_map.get(entry_type)
        if not category_key: 
            print(f"  -> SKIPPING GROUP: AI returned unknown type '{entry_type}'.")
            for url in group_urls: save_seen_url(url)
            continue
        if not new_json_entry.get("id"): 
            print(f"  -> SKIPPING GROUP: AI failed to generate 'id'.")
            for url in group_urls: save_seen_url(url)
            continue
        master_data = load_data_json()
        if any(entry.get('id') == new_json_entry.get('id') for entry in master_data.get(category_key, [])):
            print(f"  -> RESULT: Duplicate ID '{new_json_entry.get('id')}' found. Discarding.")
        else:
            print(f"  -> RESULT: Unique post. Adding to '{category_key}'.")
            if category_key not in master_data: master_data[category_key] = []
            master_data[category_key].insert(0, new_json_entry)
            save_data_json(master_data)
        for url in group_urls: save_seen_url(url)
    print("\n--- All new articles processed. ---")

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("CRITICAL ERROR: The GOOGLE_API_KEY is not set in your .env file.")
    else:
        for directory in [GEMINI_RESPONSE_DIR, CONSOLIDATED_CONTENT_DIR]:
            if not os.path.exists(directory): os.makedirs(directory)
        while True:
            run_automation_cycle()
            run_archiving_process(DATA_JSON_FILE)
            print(f"\nCycle complete. Next scan will start in {CHECK_INTERVAL_SECONDS // 60} minutes.")
            time.sleep(CHECK_INTERVAL_SECONDS)
