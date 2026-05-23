# 🔗 URL Categorizer & Summarizer

The **URL Categorizer & Summarizer** is an intelligent web application that allows users to input batches of URLs, automatically extracts their content, and uses AI to generate concise summaries, categories, and content types. 

Whether you are managing a mountain of reading bookmarks, gathering research links, or cataloging YouTube videos, this tool helps you organize your URLs into an actionable dataset and visual dashboard.

## ✨ Key Features

* **High-Speed Asynchronous Processing**: Built with `asyncio`, `aiohttp`, and `async_playwright` to process large batches of URLs concurrently without blocking. This non-blocking architecture massively speeds up scraping and API inference.
* **Smart Content Extraction**: Automatically selects the best extraction method based on the URL. Uses `youtube_transcript_api` for YouTube videos, and `trafilatura` (with a headless Playwright browser fallback) for standard web articles.
* **AI-Powered Analysis**: Uses OpenAI (`gpt-4o-mini` via `AsyncOpenAI`) to categorize the link, define its content type (Text, Video, or Audio), and generate a concise 3-sentence summary.
* **Smart Anti-Hallucination Guardrails**: Prompts are engineered to recognize platform contexts (e.g., treating Letterboxd as a Movie Review Platform, not a movie plot description). The AI does its best to piece together a summary from fragmented text or URLs, but gracefully returns explicit `null` values instead of inventing facts if a page provides absolutely no context.
* **Anti-Duplication URL Cleaning**: Automatically strips tracking parameters (like `utm_source` or `ref`) from input URLs to ensure you don't accidentally process and pay for the same link twice.
* **Interactive Manual Review**: If a webpage blocks scraping or the AI legitimately cannot parse the content, the app intelligently flags it. Before generating the dashboard, it presents a streamlined form for you to manually fill in the missing `null` values.
* **Cumulative Metrics & Cost Tracking**: Actively monitors your usage, providing a running tally of total processing time and an estimated API token cost burn rate across your entire session.
* **Source Identification**: Parses the root domain to cleanly extract the origin source of your content (e.g., "YouTube", "GitHub", "Medium").
* **Insightful Dashboard**: Once 10 or more URLs are processed, the app generates a high-level Plotly dashboard featuring scorecards (tracking Total, Text, Video, and Audio metrics), category distribution bar charts, and source analytics.
* **Data Export**: Seamlessly download your polished dataset as a CSV file.

## 🚀 How to Run

1. Ensure you have Python installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install the Playwright browser binaries (this is done automatically by the app, but you can run it manually if needed):
   ```bash
   playwright install chromium
   ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```
5. Paste your OpenAI API Key into the configuration sidebar and start adding URLs!

## 🔮 Future Improvements

While the app is highly functional, there are several avenues for future enhancement:

1. **Language Sensitivity**: Ensure the application can accurately categorize and summarize content across different languages, potentially translating insights or preserving the source language for the user.
2. **A Completely New Web Interface**: Migrating away from Streamlit to a fully custom frontend (e.g. Next.js, React, or Vue) for a more robust, highly-interactive, and customized user experience.
3. **Local LLM Support**: Integrating local models (via Ollama or vLLM) could entirely eliminate API token costs for users with capable hardware.
4. **Advanced Platform-Specific Scrapers**: Building dedicated extractors for heavily-gated social media platforms (like X/Twitter, Instagram, or LinkedIn) to bypass login walls.
5. **Persistent Storage / Database**: Replacing the ephemeral `session_state` with a local SQLite database or cloud database (like Supabase or Firebase) so users can close the app and return to their dataset later.
6. **Categorization Taxonomy Tuning**: Allowing users to define their own custom category buckets rather than relying purely on the LLM's dynamic grouping, ensuring the dashboard perfectly fits their specific research domain.
7. **Chat with Your Data**: Introducing a natural language search bar where you can chat with your processed table and extract insights based on the collected URL summaries and metadata.
8. **AI-Assisted Web Scraping**: Employing LLM-driven agents and AI web scraping techniques to dynamically navigate complex page layouts and gather deeper, more structured data from URLs.
9. **Prompt Engineering Optimization**: Refining and experimenting with prompt structures to improve the accuracy, consistency, and conversational quality of generated summaries and categorizations.
10. **Automated Date Extraction and Labeling**: Detecting and attaching publication dates or temporal metadata to processed URLs to provide additional context and improve chronological analysis of collected information.