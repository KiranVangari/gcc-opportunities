# ⚙️ GCC Turbomachinery & Reliability Job Tracker

An automated, high-precision job scraping pipeline designed to find highly specific mechanical engineering roles (Turbomachinery, Vibration, Condition Monitoring, Reliability) across the Gulf Cooperation Council (GCC) region. 

This project bypasses the notoriously poor Boolean search capabilities of native job boards by casting a wide initial net and then executing a strict, locally hosted **"Python Guillotine" Boolean filter** to eliminate irrelevant IT, medical, and pharmacy roles.

The results are published to a fully interactive static HTML dashboard hosted on GitHub Pages, with automated email notifications sent upon completion.

---

## 🌟 Key Features

*   **Multi-Engine Scraping:** Pulls data from LinkedIn and Indeed (via `jobspy`) and regional boards like Bayt, Naukrigulf, Glassdoor, and direct corporate sites (via Google Jobs / `SerpApi`).
*   **The "Python Guillotine" Filter:** Uses internal Python logic to read job titles and descriptions, mathematically verifying that a job contains both a required *Hardware* term AND a *Discipline* term before publishing it.
*   **72-Hour Rolling Window:** Always searches for jobs posted within the last 3 days to ensure data freshness.
*   **Interactive Dual-Dashboard:** 
    *   **Highly Relevant Jobs:** The strictly filtered, cream-of-the-crop results.
    *   **Raw Unfiltered Jobs:** A collapsed view of every job pulled before the filter was applied (useful for auditing what was cut).
*   **Zero-Backend Web App:** Client-side JavaScript handles all sorting, filtering by country/company/engine, and Excel (CSV) exports.
*   **100% Automated:** Runs entirely in the cloud via GitHub Actions every 3 days.

---

## 🧠 How the Search Logic Works

Native job platforms (like LinkedIn) frequently ignore complex `AND/OR` logic, resulting in "Reliability Engineer" queries returning IT Cloud Developers, or "Condition Monitoring" returning Hospital Nurses.

To fix this, the script operates in two phases:

### Phase 1: Broad Collection
The scraper asks the APIs for generic terms: `"Rotating Equipment"`, `"Turbomachinery"`, `"Reliability Engineer"`, etc. This prevents the job boards' "zero-result fallback algorithms" from panicking and returning spam.

### Phase 2: The Verification Filter (Inside `job_scraper.py`)
The `is_highly_relevant(row)` function analyzes the downloaded jobs using the following logic:

**`(HARDWARE AND DISCIPLINE) OR STANDALONE`**

*   **Hardware Required:** e.g., Turbomachinery, Rotating Equipment, Gas Turbine, Compressor.
*   **Discipline Required:** e.g., Vibration, Diagnostics, Condition Monitoring, API 670, Reliability.
*   **Standalones:** If a job explicitly mentions highly unique industry terms (e.g., "Bently Nevada", "CMRP"), it automatically passes the filter.

---

## 🛠️ Setup & Configuration

This repository relies on GitHub Actions and GitHub Secrets to securely execute code and send emails without exposing your API keys.

### 1. Required GitHub Secrets
Go to **Settings > Secrets and variables > Actions** and ensure the following Repository Secrets are set:

| Secret Name | Description |
| :--- | :--- |
| `SERPAPI_KEY` | Your API key from [SerpApi](https://serpapi.com/) for scraping Google Jobs. |
| `EMAIL_USERNAME` | The full Gmail address used to send the notification emails. |
| `EMAIL_PASSWORD` | A 16-character **Google App Password**. *(Note: This must be entered as a continuous 16-letter string with NO SPACES).* |

### 2. The GitHub Actions Workflow
The automation is controlled by `.github/workflows/scrape_and_deploy.yml`. 
*   **Schedule:** It is configured to run automatically using CRON: `'0 8 */3 * *'` (Every 3 days at 08:00 UTC).
*   **Quota Protection:** Running every 3 days results in ~10 runs per month. At ~6 SerpApi calls per run, this consumes ~60 API credits, keeping you safely below SerpApi's 100 free monthly limit.
*   **Publishing:** It commits the generated `public/index.html` to the `gh-pages` branch.
*   **Notifications:** It pauses for 120 seconds to allow GitHub's servers to update the live URL before emailing you the notification link.

---

## 💻 Local Development & Testing

If you want to run or test the script on your local machine (e.g., in PyCharm):

1. Clone the repository.
2. Install the requirements: `pip install -r requirements.txt`.
3. Set your local environment variable for the API key, or temporarily hardcode it at the top of `job_scraper.py`:
   `SERPAPI_KEY = "your_actual_key_here"`
4. Run the script: `python job_scraper.py`.
5. Open the newly generated `public/index.html` file in your web browser.

**Note on Local Errors:** If you see `429 Too Many Requests` errors in your terminal while testing locally, this means LinkedIn has temporarily rate-limited your personal IP address. This is normal and usually does not occur when the script runs on GitHub Actions' datacenter IPs.

---

## 📝 Modifying the Project in the Future

*   **Adding Countries:** Edit the `LOCATIONS` list at the top of `job_scraper.py`. Note that adding more locations *will* increase your SerpApi credit consumption.
*   **Adding Keywords:** To pull different types of jobs, edit the `SEARCH_TERMS` list for the broad scrape, AND update the `hardware`, `discipline`, or `standalones` lists inside the `is_highly_relevant()` function.
*   **Changing the Email Recipient:** In the `.yml` workflow file, change the `to: ${{ secrets.EMAIL_USERNAME }}` field to whatever destination email address you prefer.
