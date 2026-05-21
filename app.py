import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re
import json
import requests
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
# pyrefly: ignore [missing-import]
from youtube_transcript_api import YouTubeTranscriptApi
# pyrefly: ignore [missing-import]
import trafilatura
# pyrefly: ignore [missing-import]
from playwright.sync_api import sync_playwright
# pyrefly: ignore [missing-import]
from openai import OpenAI
import time
import concurrent.futures

# Setup Streamlit page configuration
st.set_page_config(page_title="URL Categorizer & Summarizer", layout="wide", page_icon="🔗")

# Try installing Playwright browsers (Specifically for Streamlit Cloud deployment)
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")
install_playwright()

st.title("🔗 URL Categorizer & Summarizer")
st.markdown("Easily extract content from web pages and YouTube videos, categorize them, and generate concise summaries using AI.")

# --- Session State ---
if 'dataset' not in st.session_state:
    st.session_state.dataset = []
if 'metrics' not in st.session_state:
    st.session_state.metrics = {'total_time': 0, 'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0}

def clean_url(url):
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    # Remove common tracking parameters like utm_ and ref
    qs_clean = {k: v for k, v in qs.items() if not k.startswith('utm_') and not k.startswith('ref')}
    parsed = parsed._replace(query=urlencode(qs_clean, doseq=True))
    cleaned = urlunparse(parsed)
    return cleaned.rstrip('/')

def get_url_source(url):
    netloc = urlparse(url).netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    parts = netloc.split('.')
    if len(parts) >= 2:
        return parts[-2].title()
    return netloc.title()

# --- Sidebar configuration & API Key ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key to enable analysis.")
    st.markdown("Get your API key from [OpenAI Developer Platform](https://platform.openai.com/).")
    
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            st.success("API Key activated!")
        except Exception as e:
            st.error(f"Error initializing client: {e}")
            client = None
    else:
        client = None

# --- Core Functions (from user's code) ---
def is_youtube_url(url):
    return "youtube.com" in url or "youtu.be" in url

def get_youtube_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/)([\w-]+)", url)
    return match.group(1) if match else None

def extract_youtube_text(url):
    video_id = get_youtube_video_id(url)
    if not video_id:
        return None
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        text = " ".join([item.text for item in transcript]) 
        return text[:5000]
    except Exception as e:
        print("Transcript error:", e)
        return None

def extract_with_trafilatura(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        return trafilatura.extract(response.text)
    except:
        return None

def extract_with_playwright(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            content = page.content()
            browser.close()
        return trafilatura.extract(content)
    except:
        return None

def is_valid_content(text):
    if not text:
        return False
    lower_text = text.lower()
    if "security service" in lower_text and "bot" in lower_text: return False
    if "verification page" in lower_text or "waiting for a response from" in lower_text: return False
    if "just a moment..." in lower_text and "enable javascript" in lower_text: return False
    if "turn on javascript" in lower_text or "checking your browser" in lower_text: return False
    return True

def extract_text_smart(url):
    if is_youtube_url(url):
        text = extract_youtube_text(url)
        if text:
            return text, "youtube"
        else:
            return None, "youtube_failed"

    text = extract_with_trafilatura(url)
    if is_valid_content(text):
        return text, "trafilatura"

    text = extract_with_playwright(url)
    if is_valid_content(text):
        return text, "playwright"

    return None, None

def analyze_content(text, url, force_video=False):
    if not client:
        return "{}", 0, 0
    
    content_type_instruction = ""
    if force_video:
        content_type_instruction = 'The content_type MUST be "video".'

    prompt = f"""
Analyze the content extracted from this URL: {url}
Return ONLY valid JSON with this structure:

{{
  "category": "...", 
  "content_type": "...",
  "summary": "max 3 sentences"
}}

Instructions:
- "category" MUST identify the genre AND the nature/platform of the page. For example, if it's Letterboxd, it's a "Movie Review Platform", not a movie description. Recognize other platforms like GitHub (Code), YouTube (Video), etc.
- "content_type" MUST be exactly one of: "Text", "Video", or "Audio". If a text article offers a "listen" feature, it is still "Text". Only use "Audio" for dedicated podcast/music pages.
- "summary" MUST explain what the page is generally doing or presenting. Don't just summarize a plot, state what the page itself is about.
- ANTI-HALLUCINATION RULE: Do NOT invent facts. However, do your best to infer a helpful summary from the available text or URL. Only return "null" for category or summary if the page provides absolutely no context.
{content_type_instruction}

Extracted Content:
{text[:4000]}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    usage = response.usage
    return response.choices[0].message.content, usage.prompt_tokens, usage.completion_tokens

def analyze_url_only(url):
    if not client:
        return "{}", 0, 0
        
    prompt = f"""
You couldn't access the webpage.

Infer from the URL and return JSON:

{{
  "category": "...",
  "content_type": "...",
  "summary": "inferred summary"
}}

Instructions:
- "content_type" MUST be exactly one of: "Text", "Video", or "Audio". Only use "Audio" for dedicated podcast/music URLs, not articles with audio options.
- ANTI-HALLUCINATION RULE: Do NOT invent facts. However, do your best to infer a helpful summary and category from the URL structure. Only return "null" if the URL provides absolutely no context. Recognize platform URLs (e.g. letterboxd.com is a "Movie Review Platform").

URL: {url}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={ "type": "json_object" }
    )
    usage = response.usage
    return response.choices[0].message.content, usage.prompt_tokens, usage.completion_tokens

def safe_parse_json(response_text):
    try:
        response_text = response_text.strip().removeprefix('```json').removesuffix('```').strip()
        return json.loads(response_text)
    except:
        return {
            "category": "null",
            "content_type": "Unknown",
            "summary": "null"
        }

def normalize_categories(dataset):
    if not client or not dataset:
        return dataset
    
    unique_categories = list(set([item.get("category", "Uncategorized") for item in dataset]))
    if not unique_categories:
        return dataset
        
    prompt = f"""
I have the following list of web page categories:
{json.dumps(unique_categories)}

Please group these into a smaller, concise list of high-level parent categories (e.g., 'Education', 'News', 'Entertainment', 'Recipes', 'Technology').
Return ONLY a valid JSON dictionary where the keys are the original categories provided, and the values are the new high-level categories.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        usage = response.usage
        st.session_state.metrics['prompt_tokens'] += usage.prompt_tokens
        st.session_state.metrics['completion_tokens'] += usage.completion_tokens
        
        mapping_text = response.choices[0].message.content.strip()
        mapping_text = mapping_text.removeprefix('```json').removesuffix('```').strip()
        mapping = json.loads(mapping_text)
        
        # Apply mapping
        for item in dataset:
            cat = item.get("category")
            if cat in mapping and isinstance(mapping[cat], str):
                item["category"] = mapping[cat]
                
    except Exception as e:
        print(f"Failed to normalize categories: {e}")
        
    return dataset

def process_single_url(url):
    source = get_url_source(url)
    try:
        text, method = extract_text_smart(url)
        
        if text:
            force_video = (method == "youtube")
            analysis_raw, p_tokens, c_tokens = analyze_content(text, url=url, force_video=force_video)
            parsed = safe_parse_json(analysis_raw)
            
            if method == "youtube":
                parsed["content_type"] = "Video"
            else:
                ctype = str(parsed.get("content_type", "Text")).title()
                if ctype not in ["Text", "Video", "Audio"]:
                    ctype = "Text"
                parsed["content_type"] = ctype
                
            cat = str(parsed.get("category", "null"))
            sumry = str(parsed.get("summary", "null"))
            needs_review = cat.lower() in ["null", "uncategorized", "unknown", ""] or sumry.lower() in ["null", "n/a", ""]
            
            return {
                "success": True,
                "method": method,
                "p_tokens": p_tokens,
                "c_tokens": c_tokens,
                "entry": {
                    "url": url,
                    "source": source,
                    "category": cat if cat.lower() not in ["null", "uncategorized", "unknown", ""] else "null",
                    "content_type": parsed.get("content_type", "Text"),
                    "summary": sumry if sumry.lower() not in ["null", "n/a", ""] else "null",
                    "needs_review": needs_review
                }
            }
        else:
            analysis_raw, p_tokens, c_tokens = analyze_url_only(url)
            parsed = safe_parse_json(analysis_raw)
            ctype = str(parsed.get("content_type", "Text")).title()
            if ctype not in ["Text", "Video", "Audio"]:
                ctype = "Text"
            parsed["content_type"] = ctype
            
            cat = str(parsed.get("category", "null"))
            sumry = str(parsed.get("summary", "null"))
            needs_review = cat.lower() in ["null", "uncategorized", "unknown", ""] or sumry.lower() in ["null", "n/a", ""]
            
            return {
                "success": True,
                "method": "url_inference",
                "p_tokens": p_tokens,
                "c_tokens": c_tokens,
                "entry": {
                    "url": url,
                    "source": source,
                    "category": cat if cat.lower() not in ["null", "uncategorized", "unknown", ""] else "null",
                    "content_type": parsed.get("content_type", "Text"),
                    "summary": sumry if sumry.lower() not in ["null", "n/a", ""] else "null",
                    "needs_review": needs_review
                }
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }

# --- UI & Interaction ---
st.markdown("### 📥 Add New URLs")
url_input = st.text_area("Enter URLs (one per line)", height=150, placeholder="https://example.com\nhttps://youtube.com/watch?v=abcd")

if st.button("🚀 Process URLs", type="primary"):
    if not api_key:
        st.error("⚠️ Please provide your OpenAI API Key in the sidebar before processing.")
    elif url_input.strip():
        url_list = [url.strip() for url in url_input.split("\n") if url.strip()]
        
        # Start timing without resetting accumulated metrics
        start_time = time.time()
        
        # Setup progress indicators
        progress_text = "Processing URLs..."
        my_bar = st.progress(0, text=progress_text)
        
        success_count = 0
        existing_urls = {item['url'] for item in st.session_state.dataset}
        
        unique_urls_to_process = []
        for raw_url in url_list:
            url = clean_url(raw_url)
            if url in existing_urls:
                st.write(f"⏭️ Skipping already processed URL: {url}")
            elif url in unique_urls_to_process:
                pass # Deduplicate within the same batch
            else:
                unique_urls_to_process.append(url)
                
        if unique_urls_to_process:
            st.write("---")
            with st.status("Extracting and Analyzing...") as status:
                futures = {}
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    for url in unique_urls_to_process:
                        future = executor.submit(process_single_url, url)
                        futures[future] = url
                        
                    completed_count = 0
                    total_to_process = len(unique_urls_to_process)
                    
                    for future in concurrent.futures.as_completed(futures):
                        completed_count += 1
                        url = futures[future]
                        
                        my_bar.progress(completed_count / total_to_process, text=f"Processing {completed_count}/{total_to_process}")
                        
                        res = future.result()
                        if res.get("success"):
                            method = res["method"]
                            if method == "url_inference":
                                st.write(f"⚠️ Extracted via URL inference: {url}")
                            else:
                                st.write(f"✅ Success ({method}): {url}")
                                
                            st.session_state.metrics['prompt_tokens'] += res["p_tokens"]
                            st.session_state.metrics['completion_tokens'] += res["c_tokens"]
                            st.session_state.dataset.append(res["entry"])
                            success_count += 1
                        else:
                            st.write(f"❌ Failed processing {url}: {res.get('error')}")
                
                st.write("🤖 Normalizing categories...")
                st.session_state.dataset = normalize_categories(st.session_state.dataset)
                status.update(label="Processing Complete!", state="complete", expanded=False)
        else:
            st.info("No new URLs to process.")
        my_bar.progress(1.0, text="Done!")
        
        end_time = time.time()
        run_time = end_time - start_time
        st.session_state.metrics['total_time'] += run_time
        
        # Calculate cost for gpt-4o-mini
        p_cost = (st.session_state.metrics['prompt_tokens'] / 1_000_000) * 0.150
        c_cost = (st.session_state.metrics['completion_tokens'] / 1_000_000) * 0.600
        st.session_state.metrics['cost'] = p_cost + c_cost
        
        st.success(f"Processing finished! Successfully processed: {success_count} new URLs.")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Time Taken", f"{st.session_state.metrics['total_time']:.1f}s")
        with col_m2:
            st.metric("Estimated Cost", f"${st.session_state.metrics['cost']:.4f}")
    else:
        st.warning("⚠️ Please enter at least one URL.")

# --- Results Presentation ---
if st.session_state.dataset:
    df = pd.DataFrame(st.session_state.dataset)
    
    # Check if there are any URLs that need manual review
    needs_review_mask = df.get('needs_review', pd.Series([False]*len(df))) == True
    
    if needs_review_mask.any():
        st.markdown("---")
        st.header("⚠️ Manual Review Needed")
        st.warning("Some URLs couldn't be fully categorized or scraped. Please fill them out manually before proceeding to the dashboard.")
        
        # Display editable dataframe only for those needing review
        review_cols = ['url', 'category', 'content_type', 'summary']
        review_df = df[needs_review_mask][review_cols]
        edited_review_df = st.data_editor(review_df, use_container_width=True)
        
        if st.button("🚀 Proceed to Dashboard", type="primary"):
            # Update dataset with edited values
            for idx, row in edited_review_df.iterrows():
                # Update main dataset in session state
                for item in st.session_state.dataset:
                    if item['url'] == row['url']:
                        item['category'] = row['category']
                        item['content_type'] = row['content_type']
                        item['summary'] = row['summary']
                        item['needs_review'] = False
            st.rerun()
    else:
        st.markdown("---")
        st.header("📊 Analyzed Dataset")
        
        # Drop the internal needs_review column for display
        display_df = df.drop(columns=['needs_review'], errors='ignore')
        
        col_dl, col_clear = st.columns([8, 2])
        with col_dl:
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download dataset as CSV",
                data=csv,
                file_name='extracted_links.csv',
                mime='text/csv',
            )
        with col_clear:
            if st.button("🗑️ Clear All Links", type="primary", use_container_width=True):
                st.session_state.dataset = []
                st.session_state.metrics = {'total_time': 0, 'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0}
                st.rerun()
                
        st.caption("💡 **Tip**: To drop/remove a specific link, check the box on its left and click the trash icon (or press Delete). You can also edit the text!")
        edited_df = st.data_editor(display_df, use_container_width=True, num_rows="dynamic")
        
        # Sync deletions or edits back to the session state
        if len(edited_df) != len(display_df) or not edited_df.equals(display_df):
            # Re-add needs_review column (all False at this point) before syncing
            edited_df['needs_review'] = False
            st.session_state.dataset = edited_df.to_dict('records')
            st.rerun()
            
        # --- Dashboard (when 10 or more entries) ---
        if len(display_df) >= 10:
            st.markdown("---")
            st.header("📈 URL Insights Dashboard")
            st.markdown("High-level metrics for your collected URLs.")
            
            # Ensure consistent types string normalization
            display_df['type_clean'] = display_df['content_type'].fillna('Unknown').astype(str).str.lower().str.strip()
            
            # Row for Scorecards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Total URLs Processed", value=len(display_df))
            with col2:
                # Count anything that isn't explicitly a video or audio as an article/text page
                articles_count = len(display_df[~display_df['type_clean'].str.contains('video|youtube|audio|podcast', case=False, na=False)])
                st.metric(label="Articles / Text URLs", value=articles_count)
            with col3:
                # Safely capture any variation of "video" or "youtube"
                video_count = len(display_df[display_df['type_clean'].str.contains('video|youtube', case=False, na=False)])
                st.metric(label="Video URLs", value=video_count)
            with col4:
                audio_count = len(display_df[display_df['type_clean'].str.contains('audio|podcast', case=False, na=False)])
                st.metric(label="Audio URLs", value=audio_count)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Row for Bar Charts (Categories and Sources)
            c_left, c_right = st.columns(2)
            
            with c_left:
                st.subheader("Categories Distribution")
                cat_counts = display_df['category'].value_counts().reset_index()
                cat_counts.columns = ['Category', 'Count']
                
                fig_cats = px.bar(cat_counts, x='Count', y='Category', orientation='h',
                                   text='Count', color='Category')
                fig_cats.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, xaxis_title="Count", yaxis_title="")
                fig_cats.update_traces(textposition='outside')
                st.plotly_chart(fig_cats, use_container_width=True)
                
            with c_right:
                st.subheader("Sources Distribution")
                if 'source' in display_df.columns:
                    source_counts = display_df['source'].value_counts().reset_index()
                    source_counts.columns = ['Source', 'Count']
                    
                    fig_sources = px.bar(source_counts, x='Count', y='Source', orientation='h',
                                       text='Count', color='Source')
                    fig_sources.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, xaxis_title="Count", yaxis_title="")
                    fig_sources.update_traces(textposition='outside')
                    st.plotly_chart(fig_sources, use_container_width=True)
