# 🔗 URL Categorizer & Summarizer

Welcome to the **URL Categorizer & Summarizer**, a project developed by Alagie Ceesay, Archana Gajula, Yavuz Altun, and Justyna Kawecka for TechPros Rotterdam's February cohort. Over three months, we immersed ourselves in Data Science, Web Design, and AI, culminating in the development of this innovative web application. The initial concept for this tool originated entirely from our team.

The **URL Categorizer & Summarizer** is an intelligent web application that allows users to input batches of URLs, automatically extracts their content, and leverages AI to generate concise summaries, categories, and content types.

Whether you are managing a large collection of reading bookmarks, gathering research links, or cataloging YouTube videos, this tool helps you organize your URLs into an actionable dataset and visual dashboard.

## ✨ Key Features

*   **High-Speed Asynchronous Processing**: Built with `asyncio`, `aiohttp`, and `async_playwright` to process large batches of URLs concurrently without blocking. This non-blocking architecture significantly accelerates scraping and API inference.
*   **Smart Content Extraction**: Automatically selects the most effective extraction method based on the URL. It utilizes `youtube_transcript_api` for YouTube videos and `trafilatura` (with a headless Playwright browser fallback) for standard web articles.
*   **AI-Powered Analysis**: Employs OpenAI (`gpt-4o-mini` via `AsyncOpenAI`) to categorize the link, determine its content type (Text, Video, or Audio), and generate a concise 3-sentence summary.
*   **Smart Anti-Hallucination Guardrails**: Prompts are meticulously engineered to recognize platform contexts (e.g., treating Letterboxd as a Movie Review Platform rather than a source for movie plot descriptions). The AI endeavors to construct a summary from fragmented text or URLs but gracefully returns explicit `null` values instead of fabricating facts if a page provides insufficient context.
*   **Anti-Duplication URL Cleaning**: Automatically strips tracking parameters (such as `utm_source` or `ref`) from input URLs to prevent accidental reprocessing and associated costs for the same link.
*   **Interactive Manual Review**: If a webpage blocks scraping or the AI is genuinely unable to parse the content, the application intelligently flags it. Before generating the dashboard, it presents a streamlined form for users to manually input missing `null` values.
*   **Cumulative Metrics & Cost Tracking**: Actively monitors usage, providing a running tally of total processing time and an estimated API token cost burn rate across the entire session.
*   **Source Identification**: Parses the root domain to cleanly extract the origin source of your content (e.g., "YouTube", "GitHub", "Medium").
*   **Insightful Dashboard**: Once 10 or more URLs are processed, the application generates a high-level Plotly dashboard featuring scorecards (tracking Total, Text, Video, and Audio metrics), category distribution bar charts, and source analytics.
*   **Data Export**: Seamlessly download your polished dataset as a CSV file.

## 🛠️ Tech Stack

This project leverages a robust set of technologies to deliver its functionality:

*   **Python**: The core programming language for the entire application.
*   **Antigravity**: Used for "vibecoding," enhancing the development experience.
*   **Streamlit**: Powers the user interface of the end product.
*   **Playwright**: Utilized for efficient web scraping.
*   **Asyncio**: Enables parallel processing for high-speed operations.
*   **Plotly**: Employed for generating insightful data visualizations.
*   **OpenAI**: Integrated for advanced categorization and summarization of web content.

## 🚀 How to Run

1.  Ensure you have Python installed on your system.
2.  Install the required project dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Install the Playwright browser binaries. This is often handled automatically by the application, but you can run it manually if necessary:
    ```bash
    playwright install chromium
    ```
4.  Launch the application:
    ```bash
    streamlit run app.py
    ```
5.  Paste your OpenAI API Key into the configuration sidebar within the application and begin adding URLs!

## 🔮 Future Improvements

While the application is highly functional, several exciting avenues exist for future enhancement:

1.  **Language Sensitivity**: Enhancing the application's ability to accurately categorize and summarize content across different languages, potentially offering translated insights or preserving the original language for the user.
2.  **A Completely New Web Interface**: Migrating away from Streamlit to a fully custom frontend framework (e.g., Next.js, React, or Vue) for a more robust, highly-interactive, and customized user experience.
3.  **Local LLM Support**: Integrating local Large Language Models (via Ollama or vLLM) could entirely eliminate API token costs for users with capable hardware.
4.  **Advanced Platform-Specific Scrapers**: Developing dedicated extractors for heavily-gated social media platforms (such as X/Twitter, Instagram, or LinkedIn) to bypass login walls and access content.
5.  **Persistent Storage / Database**: Replacing the ephemeral `session_state` with a local SQLite database or a cloud-based database (like Supabase or Firebase) to allow users to close the app and return to their datasets later.
6.  **Categorization Taxonomy Tuning**: Providing users with the ability to define their own custom category buckets, moving beyond reliance on the LLM's dynamic grouping, to ensure the dashboard perfectly aligns with their specific research domains.
7.  **Chat with Your Data**: Introducing a natural language search bar that enables users to interact with their processed table and extract insights based on the collected URL summaries and metadata.
8.  **AI-Assisted Web Scraping**: Employing LLM-driven agents and advanced AI web scraping techniques to dynamically navigate complex page layouts and gather deeper, more structured data from URLs.
9.  **Prompt Engineering Optimization**: Continuously refining and experimenting with prompt structures to improve the accuracy, consistency, and conversational quality of generated summaries and categorizations.
10. **Automated Date Extraction and Labeling**: Implementing features to detect and attach publication dates or other temporal metadata to processed URLs, providing additional context and improving chronological analysis of collected information.
