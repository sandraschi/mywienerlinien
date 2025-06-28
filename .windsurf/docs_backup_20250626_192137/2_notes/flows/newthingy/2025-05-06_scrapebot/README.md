# Scrapebot: AI-Powered Website Copier

## Concept
Scrapebot is an AI-powered tool that crawls a public website (no login required), walks through its pages up to a user-specified depth, and builds a local copy of the site. It reads the DOM, rewrites links to be local, and downloads images, stylesheets, and other assets. Optionally, it can use AI to summarize, clean up, or restructure content, and to generate a site map or content overview.

---

## Features
- **Recursive Crawling:** Crawl a website up to N levels deep, following internal links.
- **DOM Parsing & Rewriting:** Parse HTML, rewrite links to local paths, and extract assets.
- **Asset Downloading:** Download images, CSS, JS, and media for offline use.
- **AI Assistance (Optional):**
  - Summarize or clean up pages.
  - Generate a site map or content summary.
  - Thematic filtering (only download relevant pages).
- **Output:** Downloadable local copy (folder or ZIP), with all links and assets working offline.

---

## Roadblocks & Challenges
1. **Dynamic Content:**
   - Many modern sites use JavaScript frameworks (React, Vue, Angular) to render content dynamically. Static HTML downloaders (requests + BeautifulSoup) won’t see this content.
   - **Solution:** Use a headless browser (Selenium, Playwright) to render pages before scraping.

2. **Asset Loading via JS:**
   - Some images/media are loaded dynamically after page load.
   - **Solution:** Wait for page to settle (network idle) before scraping. May still miss lazy-loaded assets.

3. **Link Rewriting:**
   - Need to convert all internal links, asset URLs, and references to local paths, including in CSS and JS.
   - **Solution:** Careful DOM parsing and regex for edge cases.

4. **CORS and Hotlinking:**
   - Some assets may be protected by CORS or anti-hotlinking measures.
   - **Solution:** Download assets directly, but may require user-agent spoofing or fallback.

5. **Site Structure Loops:**
   - Avoid infinite loops or crawling the same page multiple times.
   - **Solution:** Track visited URLs, respect robots.txt (optionally), and set a crawl depth limit.

6. **Legal/Ethical:**
   - Some sites may prohibit scraping in their terms of service.
   - **Solution:** User is responsible for compliance; respect robots.txt by default.

7. **Performance:**
   - Large sites can result in huge downloads and long crawl times.
   - **Solution:** Set sensible limits on depth, page count, and asset size.

---

## High-Level Architecture
- **Frontend:** Simple UI to enter URL, set crawl depth, and start the process. Shows progress and allows download of the result.
- **Backend:**
  - Crawler (requests + BeautifulSoup for static, Selenium/Playwright for dynamic).
  - Asset downloader and link rewriter.
  - AI module for summarization and filtering (optional).
  - Packaging (ZIP/folder output).
- **Output:** Local site copy, site map, and/or AI-generated summary.

---

## Future Enhancements
- Thematic or semantic crawling (AI-guided selection of relevant pages).
- Integration with other AI gadgets (summarizer, Q&A, etc).
- Option to generate a summary or podcast (see NotebookLLM).

---

## See Also
- [notebookllm](../notebookllm/): For inspiration on document ingestion, analysis, and AI-generated content (e.g., podcast creation).

