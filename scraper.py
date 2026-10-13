import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from jobspy import scrape_jobs

# --- METADATA LOGGING SYSTEM ---
execution_logs = []

def log_print(msg):
    print(msg)
    execution_logs.append(str(msg))

# 1. BROAD COLLECTION CONFIGURATION (To cast a wide net without triggering algorithms)
SEARCH_TERMS = [
    "Rotating Equipment",
    "Turbomachinery",
    "Reliability Engineer",
    "Condition Monitoring",
    "Vibration Analyst"
]

LOCATIONS = [
    "United Arab Emirates", "Saudi Arabia", "Qatar",
    "Kuwait", "Oman", "Bahrain"
]

GCC_KEYWORDS = [
    'uae', 'united arab emirates', 'dubai', 'abu dhabi', 'sharjah',
    'saudi', 'ksa', 'riyadh', 'jeddah', 'dammam', 'dhahran', 'khobar',
    'qatar', 'doha', 'kuwait', 'oman', 'muscat', 'bahrain', 'manama'
]

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
api_calls_used = 0
api_status = "Working (No Errors)" # Global tracker for API health

def get_uae_time():
    return datetime.now(timezone.utc) + timedelta(hours=4)

def clean_location(row):
    raw = str(row.get('location', 'N/A')).strip()
    query_country = str(row.get('query_country', 'N/A'))

    if raw.lower() in ["nan", "n/a", "none", ""]:
        return "N/A", query_country

    parts = [p.strip() for p in raw.split(',')]
    if len(parts) >= 2:
        return ", ".join(parts[:-1]), parts[-1]
    else:
        if raw.lower() == query_country.lower() or raw.lower() in GCC_KEYWORDS:
            return "N/A", raw
        else:
            return raw, query_country

def parse_relative_date(text):
    if not isinstance(text, str) or "ago" not in text:
        return text
    try:
        num = int(text.split()[0])
        uae_now = get_uae_time()
        if "hour" in text:
            return (uae_now - timedelta(hours=num)).strftime('%Y-%m-%d')
        if "day" in text:
            return (uae_now - timedelta(days=num)).strftime('%Y-%m-%d')
    except:
        pass
    return text

# --- THE STRICT BOOLEAN VERIFIER ---
def is_highly_relevant(row):
    title = str(row.get('title', '')).lower()
    desc = str(row.get('description', '')).lower()
    text = title + " " + desc

    hardware = ["turbomachinery", "rotating equipment", "gas turbine", "compressor"]
    discipline = ["vibration", "diagnostics", "condition monitoring", "system 1", "api 670", "api-670", "asset health",
                  "reliability"]

    # Standalone overrides (If a job explicitly states these highly unique terms, keep it)
    standalones = ["bently nevada", "cmrp", "vibration analyst"]

    has_hardware = any(hw in text for hw in hardware)
    has_discipline = any(disc in text for disc in discipline)
    is_standalone = any(sa in text for sa in standalones)

    return (has_hardware and has_discipline) or is_standalone

def generate_html(df):
    os.makedirs('public', exist_ok=True)
    run_date = get_uae_time().strftime("%Y-%m-%d %I:%M %p UAE")
    total_jobs = len(df)
    logs_html = "\n".join(execution_logs)

    status_class = "status-good" if "Working" in api_status else "status-bad"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GCC Turbomachinery Job Matches</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; padding: 20px; color: #333; }}
            .container {{ max-width: 1500px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-top: 0; }}
            .summary-text {{ font-size: 1.1em; font-weight: bold; color: #2c3e50; margin: 0; }}
            .filter-bar {{ display: flex; gap: 15px; margin: 20px 0; padding: 15px; background-color: #f1f3f5; border-radius: 8px; align-items: center; flex-wrap: wrap; }}
            .filter-group {{ display: flex; flex-direction: column; }}
            .filter-group label {{ font-size: 0.85em; font-weight: bold; color: #555; margin-bottom: 5px; }}
            .filter-group select {{ padding: 8px; border-radius: 4px; border: 1px solid #ccc; min-width: 140px; outline: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.95em; }}
            th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
            th {{ background-color: #2c3e50; color: white; cursor: pointer; position: sticky; top: 0; }}
            th:hover {{ background-color: #34495e; }}
            tr:hover {{ background-color: #f8f9fa; }}
            a.apply-btn {{ color: white; background-color: #3498db; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block; text-align: center; }}
            a.apply-btn:hover {{ background-color: #2980b9; }}
            .badge {{ padding: 4px 8px; border-radius: 8px; font-size: 0.8em; font-weight: bold; color: white; text-transform: uppercase; display: inline-block; text-align: center; min-width: 80px;}}
            .linkedin {{ background-color: #0077b5; }}
            .indeed {{ background-color: #2164f4; }}
            .glassdoor {{ background-color: #0caa41; }}
            .bayt {{ background-color: #005a9c; }}
            .naukrigulf {{ background-color: #ff7555; }}
            .default-site {{ background-color: #6c757d; }}
            .engine-badge {{ background-color: #34495e; color: #fff; padding: 3px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold;}}
            .api-badge {{ background-color: #e67e22; color: #fff; padding: 3px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold;}}
            .term-badge {{ background-color: #f1c40f; color: #333; padding: 3px 6px; border-radius: 4px; font-size: 0.85em; font-weight: 600; border: 1px solid #d4ac0d;}}
            .api-status-box {{ margin-top: 40px; padding: 15px; border-radius: 8px; font-weight: bold; font-size: 0.95em; }}
            .status-good {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .status-bad {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            .metadata-box {{ margin-top: 20px; padding: 20px; background: #2c3e50; color: #ecf0f1; border-radius: 8px; font-size: 0.85em; }}
            .metadata-box summary {{ cursor: pointer; color: #3498db; font-size: 1.2em; font-weight: bold; outline: none; list-style-position: inside; }}
            .metadata-box summary:hover {{ color: #5dade2; }}
            .metadata-box pre {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #34495e; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>GCC Turbomachinery & Reliability Jobs (72 Hours)</h1>

            <p class="summary-text">Total Jobs Found: <span style="color: #3498db; font-size: 1.2em;">{total_jobs}</span></p>
            <p style="margin: 5px 0 15px 0; font-size: 0.85em; color: #6c757d;">Last Updated: {run_date}</p>

            <div class="filter-bar">
                <div class="filter-group">
                    <label>Engine Filter</label>
                    <select id="engineFilter" onchange="applyFilters()"><option value="all">All Engines</option></select>
                </div>
                <div class="filter-group">
                    <label>Portal Filter</label>
                    <select id="portalFilter" onchange="applyFilters()"><option value="all">All Portals</option></select>
                </div>
                <div class="filter-group">
                    <label>Company Filter</label>
                    <select id="companyFilter" onchange="applyFilters()"><option value="all">All Companies</option></select>
                </div>
                <div class="filter-group">
                    <label>Country Filter</label>
                    <select id="countryFilter" onchange="applyFilters()"><option value="all">All Countries</option></select>
                </div>
                <button onclick="resetFilters()" style="margin-top: 18px; padding: 8px 15px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">Reset Filters</button>
            </div>

            <table id="jobTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">S.No ↕</th>
                        <th onclick="sortTable(1)">Engine ↕</th>
                        <th onclick="sortTable(2)">Portal ↕</th>
                        <th onclick="sortTable(3)">Date Posted ↕</th>
                        <th onclick="sortTable(4)">Search Term ↕</th>
                        <th onclick="sortTable(5)">Job Title ↕</th>
                        <th onclick="sortTable(6)">Company ↕</th>
                        <th onclick="sortTable(7)">City ↕</th>
                        <th onclick="sortTable(8)">Country ↕</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
    """

    for idx, (_, row) in enumerate(df.iterrows(), 1):
        title = str(row.get('title', 'N/A'))
        company = str(row.get('company', 'N/A'))
        city = str(row.get('city', 'N/A'))
        country = str(row.get('country', 'N/A'))
        url = str(row.get('job_url', '#'))
        site = str(row.get('site', 'unknown')).lower().replace(" ", "")
        engine = str(row.get('engine', 'Unknown'))
        term = str(row.get('search_term', 'Unknown'))
        date_str = str(row.get('date_posted', 'N/A'))

        badge_class = site if site in ['linkedin', 'indeed', 'glassdoor', 'bayt', 'naukrigulf'] else 'default-site'
        engine_class = "engine-badge" if engine == "JobSpy" else "api-badge"

        html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td class="engine-cell"><span class="{engine_class}">{engine}</span></td>
                        <td class="portal-cell"><span class="badge {badge_class}">{site}</span></td>
                        <td>{date_str}</td>
                        <td><span class="term-badge">{term}</span></td>
                        <td style="font-weight: 500;">{title}</td>
                        <td class="company-cell">{company}</td>
                        <td>{city}</td>
                        <td class="country-cell">{country}</td>
                        <td><a href="{url}" target="_blank" class="apply-btn">View</a></td>
                    </tr>
        """

    html_content += f"""
                </tbody>
            </table>

            <div class="api-status-box {status_class}">
                Google Jobs API (SerpApi) Status: {api_status} | API Calls Consumed This Run: {api_calls_used}
            </div>

            <details class="metadata-box">
                <summary>System Metadata & Terminal Logs (Click to Expand)</summary>
                <pre>{logs_html}</pre>
            </details>
        </div>

        <script>
            window.onload = function() {{
                let table = document.getElementById("jobTable");
                let tr = table.getElementsByTagName("tr");
                let engines = new Set(), portals = new Set(), companies = new Set(), countries = new Set();

                for (let i = 1; i < tr.length; i++) {{
                    let tdEngine = tr[i].getElementsByClassName("engine-cell")[0];
                    let tdPortal = tr[i].getElementsByClassName("portal-cell")[0];
                    let tdCompany = tr[i].getElementsByClassName("company-cell")[0];
                    let tdCountry = tr[i].getElementsByClassName("country-cell")[0];

                    if (tdEngine) engines.add(tdEngine.textContent.trim());
                    if (tdPortal) portals.add(tdPortal.textContent.trim());
                    if (tdCompany) companies.add(tdCompany.textContent.trim());
                    if (tdCountry) countries.add(tdCountry.textContent.trim());
                }}

                populateSelect("engineFilter", Array.from(engines).sort());
                populateSelect("portalFilter", Array.from(portals).sort());
                populateSelect("companyFilter", Array.from(companies).sort());
                populateSelect("countryFilter", Array.from(countries).sort());
            }};

            function populateSelect(id, items) {{
                let select = document.getElementById(id);
                items.forEach(item => {{
                    if(item && item !== "N/A") {{
                        let opt = document.createElement("option");
                        opt.value = item.toLowerCase();
                        opt.innerHTML = item;
                        select.appendChild(opt);
                    }}
                }});
            }}

            function applyFilters() {{
                let engineVal = document.getElementById("engineFilter").value;
                let portalVal = document.getElementById("portalFilter").value;
                let companyVal = document.getElementById("companyFilter").value;
                let countryVal = document.getElementById("countryFilter").value;

                let table = document.getElementById("jobTable");
                let tr = table.getElementsByTagName("tr");

                for (let i = 1; i < tr.length; i++) {{
                    let tdEngine = tr[i].getElementsByClassName("engine-cell")[0];
                    let tdPortal = tr[i].getElementsByClassName("portal-cell")[0];
                    let tdCompany = tr[i].getElementsByClassName("company-cell")[0];
                    let tdCountry = tr[i].getElementsByClassName("country-cell")[0];

                    if (tdEngine && tdPortal && tdCompany && tdCountry) {{
                        let engineMatch = (engineVal === "all") || (tdEngine.textContent.trim().toLowerCase() === engineVal);
                        let portalMatch = (portalVal === "all") || (tdPortal.textContent.trim().toLowerCase() === portalVal);
                        let companyMatch = (companyVal === "all") || (tdCompany.textContent.trim().toLowerCase() === companyVal);
                        let countryMatch = (countryVal === "all") || (tdCountry.textContent.trim().toLowerCase() === countryVal);

                        tr[i].style.display = (engineMatch && portalMatch && companyMatch && countryMatch) ? "" : "none";
                    }}
                }}
            }}

            function resetFilters() {{
                document.getElementById("engineFilter").value = "all";
                document.getElementById("portalFilter").value = "all";
                document.getElementById("companyFilter").value = "all";
                document.getElementById("countryFilter").value = "all";
                applyFilters();
            }}

            function sortTable(n) {{
                let table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("jobTable");
                switching = true;
                dir = "asc"; 
                while (switching) {{
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {{
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];

                        let xVal = x.textContent.trim().toLowerCase();
                        let yVal = y.textContent.trim().toLowerCase();

                        if (n === 0) {{
                            xVal = parseInt(xVal) || 0;
                            yVal = parseInt(yVal) || 0;
                        }}

                        if (dir == "asc") {{
                            if (xVal > yVal) {{ shouldSwitch = true; break; }}
                        }} else if (dir == "desc") {{
                            if (xVal < yVal) {{ shouldSwitch = true; break; }}
                        }}
                    }}
                    if (shouldSwitch) {{
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount ++;
                    }} else {{
                        if (switchcount == 0 && dir == "asc") {{
                            dir = "desc";
                            switching = true;
                        }}
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def get_serpapi_jobs():
    global api_calls_used, api_status
    if not SERPAPI_KEY or SERPAPI_KEY == "YOUR_SERPAPI_KEY_HERE":
        api_status = "Failed: API Key Missing or Not Configured"
        log_print("SERPAPI_KEY not found. Skipping Google Jobs API.")
        return pd.DataFrame()

    log_print("\nStarting SerpApi Google Jobs scrape...")
    api_jobs = []

    combined_terms = " OR ".join([f'"{term}"' for term in SEARCH_TERMS])

    # Unlocked to loop through all 6 GCC locations for production
    for location in LOCATIONS[:3]:
        log_print(f"Querying Google API combined terms for '{location}' (1 API Call)...")

        natural_query = f'({combined_terms}) jobs in {location} -linkedin -indeed'

        params = {
            "engine": "google_jobs",
            "q": natural_query,
            "hl": "en",
            "chips": "date_posted:3d",
            "api_key": SERPAPI_KEY
        }

        try:
            response = requests.get("https://serpapi.com/search", params=params)
            api_calls_used += 1

            if response.status_code == 401:
                api_status = "Failed: API Request Rejected (Invalid or Unauthorized Key)"
                log_print(api_status)
                break
            elif response.status_code == 429:
                api_status = "Failed: API Limit Reached (429 Too Many Requests)"
                log_print(api_status)
                break

            data = response.json()

            if "error" in data:
                if "hasn't returned any results" in data["error"]:
                    log_print(f"Google Jobs found 0 results for {location}.")
                    continue
                else:
                    api_status = f"Failed: API Error - {data['error']}"
                    log_print(api_status)
                    break

            if "jobs_results" in data:
                for job in data["jobs_results"]:
                    via = job.get("via", "").replace("via ", "").replace(".com", "").strip()

                    apply_options = job.get("apply_options", [])
                    if not via or via.lower() == "google" or via.lower() == "linkedin":
                        if apply_options and len(apply_options) > 0:
                            via = apply_options[0].get("title", "").replace(".com", "").strip()

                    if not via:
                        via = "Google"

                    posted_str = "N/A"
                    for ext in job.get("extensions", []):
                        if "ago" in ext.lower():
                            posted_str = parse_relative_date(ext)

                    job_url = apply_options[0].get("link") if apply_options else job.get("share_link", "#")

                    api_jobs.append({
                        "title": job.get("title", "N/A"),
                        "company": job.get("company_name", "N/A"),
                        "location": job.get("location", "N/A"),
                        "description": job.get("description", "N/A"),
                        "job_url": job_url,
                        "site": via,
                        "date_posted": posted_str,
                        "engine": "Google API",
                        "search_term": "Combined OR Query",
                        "query_country": location
                    })
        except Exception as e:
            api_status = f"Failed: Execution Error - {str(e)}"
            log_print(f"SerpApi Error in {location}: {e}")

    return pd.DataFrame(api_jobs)


def main():
    log_print(f"Starting job scrape at {get_uae_time().strftime('%Y-%m-%d %I:%M %p UAE')}...")
    all_jobs = []

    # 1. LOCAL JOB_SPY SCRAPE
    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            try:
                log_print(f"Scraping '{term}' in '{location}' (JobSpy)...")
                indeed_country = "uae" if location == "United Arab Emirates" else location.lower()
                jobs = scrape_jobs(
                    site_name=["linkedin", "indeed"],
                    search_term=term,
                    location=location,
                    results_wanted=10,
                    hours_old=72,
                    country_indeed=indeed_country
                )
                if not jobs.empty:
                    jobs['engine'] = 'JobSpy'
                    jobs['search_term'] = term
                    jobs['query_country'] = location
                    all_jobs.append(jobs)
            except Exception as e:
                log_print(f"Error scraping '{term}' in '{location}': {e}")

    # 2. SERPAPI SCRAPE
    serp_df = get_serpapi_jobs()
    if not serp_df.empty:
        all_jobs.append(serp_df)

    if not all_jobs:
        log_print("No jobs found across any parameters.")
        generate_html(pd.DataFrame(
            columns=['site', 'date_posted', 'search_term', 'title', 'company', 'city', 'country', 'job_url', 'engine']))
        return

    # Combine results and deduplicate
    df = pd.concat(all_jobs, ignore_index=True)
    df.drop_duplicates(subset=['title', 'company'], inplace=True)

    log_print(f"Total raw jobs collected before verification: {len(df)}")

    # 3. APPLY PYTHON BOOLEAN VERIFICATION (The Guillotine)
    df['is_relevant'] = df.apply(is_highly_relevant, axis=1)
    df = df[df['is_relevant'] == True].copy()
    df.drop(columns=['is_relevant'], inplace=True)

    log_print(f"Total jobs remaining after strict Hardware/Discipline verification: {len(df)}")

    if df.empty:
        log_print("All jobs were filtered out by the strict Boolean criteria.")
        generate_html(pd.DataFrame(
            columns=['site', 'date_posted', 'search_term', 'title', 'company', 'city', 'country', 'job_url', 'engine']))
        return

    # 4. APPLY STRICT GCC GEOGRAPHIC FILTER
    df['loc_lower'] = df['location'].astype(str).str.lower() + " " + df['query_country'].astype(str).str.lower()
    df = df[df['loc_lower'].apply(lambda x: any(gcc in x for gcc in GCC_KEYWORDS))]
    df.drop(columns=['loc_lower'], inplace=True)

    # 5. INTELLIGENT SPLIT LOCATION INTO CITY AND COUNTRY
    df[['city', 'country']] = df.apply(clean_location, axis=1, result_type="expand")

    # 6. SORT BY DATE POSTED
    if 'date_posted' in df.columns:
        df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
        df.sort_values(by='date_posted', ascending=False, inplace=True)
        df['date_posted'] = df['date_posted'].dt.strftime('%Y-%m-%d')
        df.reset_index(drop=True, inplace=True)

    df = df.astype(object)
    df.fillna("N/A", inplace=True)

    generate_html(df)

    # Corrected Python execution artifact formatting
    log_print("\n" + "=" * 40)
    log_print("SCRAPE EXECUTION COMPLETE")
    log_print("=" * 40)
    log_print(f"Total Highly Relevant Jobs Published: {len(df)}")
    log_print(f"SerpApi Calls Consumed: {api_calls_used}")
    log_print("=" * 40 + "\n")


if __name__ == "__main__":
    main()
