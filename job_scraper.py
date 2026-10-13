import os
import time
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
api_status = "Working (No Errors)"  # Global tracker for API health


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

    # Standalone overrides
    standalones = ["bently nevada", "cmrp", "vibration analyst"]

    has_hardware = any(hw in text for hw in hardware)
    has_discipline = any(disc in text for disc in discipline)
    is_standalone = any(sa in text for sa in standalones)

    return (has_hardware and has_discipline) or is_standalone


def generate_table_rows(df, show_search_term=True):
    """Helper function to generate HTML rows for both tables"""
    rows_html = ""
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

        term_td = f'<td><span class="term-badge">{term}</span></td>' if show_search_term else ""

        rows_html += f"""
                    <tr>
                        <td>{idx}</td>
                        <td class="engine-cell"><span class="{engine_class}">{engine}</span></td>
                        <td class="portal-cell"><span class="badge {badge_class}">{site}</span></td>
                        <td>{date_str}</td>
                        {term_td}
                        <td style="font-weight: 500;">{title}</td>
                        <td class="company-cell">{company}</td>
                        <td>{city}</td>
                        <td class="country-cell">{country}</td>
                        <td><a href="{url}" target="_blank" class="apply-btn">View</a></td>
                    </tr>
        """
    return rows_html


def generate_html(relevant_df, raw_df, duration_str="N/A"):
    os.makedirs('public', exist_ok=True)
    run_date = get_uae_time().strftime("%Y-%m-%d %I:%M %p UAE")
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
            .container {{ max-width: 1500px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-top: 0; }}
            .summary-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            .summary-text {{ font-size: 1.1em; font-weight: bold; color: #2c3e50; margin: 0; }}
            .export-btn {{ background-color: #27ae60; color: white; border: none; padding: 8px 15px; border-radius: 5px; font-weight: bold; cursor: pointer; }}
            .export-btn:hover {{ background-color: #2ecc71; }}
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
            .api-status-box {{ padding: 15px; border-radius: 8px; font-weight: bold; font-size: 0.95em; }}
            .status-good {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .status-bad {{ background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}

            /* Enforcing block display for collapsibles to prevent side-by-side rendering */
            .metadata-box {{ display: block; width: 100%; margin-top: 20px; padding: 20px; background: #2c3e50; color: #ecf0f1; border-radius: 8px; font-size: 0.85em; box-sizing: border-box; }}
            .metadata-box summary {{ cursor: pointer; color: #3498db; font-size: 1.2em; font-weight: bold; outline: none; list-style-position: inside; }}
            .metadata-box summary:hover {{ color: #5dade2; }}
            .metadata-box pre {{ margin-top: 15px; padding-top: 15px; border-top: 1px solid #34495e; overflow-x: auto; }}
            .raw-section {{ display: block; width: 100%; margin-top: 20px; padding: 20px; background: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; box-sizing: border-box; }}
            .raw-section summary {{ cursor: pointer; color: #e67e22; font-size: 1.3em; font-weight: bold; outline: none; }}

            .disclaimer-box {{ background-color: #fff3cd; color: #856404; border-left: 5px solid #ffeeba; padding: 12px 15px; border-radius: 4px; font-size: 0.9em; margin-bottom: 20px; line-height: 1.4; display: block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>GCC Turbomachinery & Reliability Jobs</h1>

            <div class="summary-header">
                <div>
                    <p class="summary-text">Highly Relevant Jobs: <span style="color: #3498db; font-size: 1.2em;">{len(relevant_df)}</span></p>
                    <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #6c757d;">Last Updated: {run_date}</p>
                </div>
                <button class="export-btn" onclick="exportTableToCSV('jobTable', 'Highly_Relevant_Jobs.csv')">📥 Export to Excel</button>
            </div>

            <div class="disclaimer-box">
                <strong>Disclaimer:</strong> This dashboard displays jobs posted within the last 3 days. Because relevancy is determined by an automated keyword matching script, absolute accuracy cannot be guaranteed. You may need to expand the <strong>Unfiltered Raw Jobs Listing</strong> section at the bottom of the page to review all jobs collected prior to the strict boolean filtering.
            </div>

            <div class="filter-bar">
                <div class="filter-group">
                    <label>Engine Filter</label>
                    <select id="engineFilter" onchange="applyFilters('jobTable', 'engineFilter', 'portalFilter', 'companyFilter', 'countryFilter')"><option value="all">All Engines</option></select>
                </div>
                <div class="filter-group">
                    <label>Portal Filter</label>
                    <select id="portalFilter" onchange="applyFilters('jobTable', 'engineFilter', 'portalFilter', 'companyFilter', 'countryFilter')"><option value="all">All Portals</option></select>
                </div>
                <div class="filter-group">
                    <label>Company Filter</label>
                    <select id="companyFilter" onchange="applyFilters('jobTable', 'engineFilter', 'portalFilter', 'companyFilter', 'countryFilter')"><option value="all">All Companies</option></select>
                </div>
                <div class="filter-group">
                    <label>Country Filter</label>
                    <select id="countryFilter" onchange="applyFilters('jobTable', 'engineFilter', 'portalFilter', 'companyFilter', 'countryFilter')"><option value="all">All Countries</option></select>
                </div>
                <button onclick="resetFilters('jobTable', 'engineFilter', 'portalFilter', 'companyFilter', 'countryFilter')" style="margin-top: 18px; padding: 8px 15px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">Reset Filters</button>
            </div>

            <table id="jobTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('jobTable', 0)">S.No ↕</th>
                        <th onclick="sortTable('jobTable', 1)">Search Engine ↕</th>
                        <th onclick="sortTable('jobTable', 2)">Jobs Portal ↕</th>
                        <th onclick="sortTable('jobTable', 3)">Date Posted ↕</th>
                        <th onclick="sortTable('jobTable', 4)">Job Title ↕</th>
                        <th onclick="sortTable('jobTable', 5)">Company ↕</th>
                        <th onclick="sortTable('jobTable', 6)">City ↕</th>
                        <th onclick="sortTable('jobTable', 7)">Country ↕</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
                    {generate_table_rows(relevant_df, show_search_term=False)}
                </tbody>
            </table>

            <!-- RAW JOBS SECTION -->
            <details class="raw-section">
                <summary>Unfiltered Raw Jobs Listing (Click to Expand)</summary>
                <div style="margin-top: 20px;">
                    <div class="summary-header">
                        <div>
                            <p class="summary-text">Raw Jobs Found: <span style="color: #e67e22; font-size: 1.2em;">{len(raw_df)}</span></p>
                            <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #6c757d;">Jobs pulled before strict boolean guillotine applied.</p>
                        </div>
                        <button class="export-btn" onclick="exportTableToCSV('rawJobTable', 'Raw_Unfiltered_Jobs.csv')">📥 Export Raw to Excel</button>
                    </div>

                    <div class="filter-bar">
                        <div class="filter-group">
                            <label>Engine Filter</label>
                            <select id="rawEngineFilter" onchange="applyFilters('rawJobTable', 'rawEngineFilter', 'rawPortalFilter', 'rawCompanyFilter', 'rawCountryFilter')"><option value="all">All Engines</option></select>
                        </div>
                        <div class="filter-group">
                            <label>Portal Filter</label>
                            <select id="rawPortalFilter" onchange="applyFilters('rawJobTable', 'rawEngineFilter', 'rawPortalFilter', 'rawCompanyFilter', 'rawCountryFilter')"><option value="all">All Portals</option></select>
                        </div>
                        <div class="filter-group">
                            <label>Company Filter</label>
                            <select id="rawCompanyFilter" onchange="applyFilters('rawJobTable', 'rawEngineFilter', 'rawPortalFilter', 'rawCompanyFilter', 'rawCountryFilter')"><option value="all">All Companies</option></select>
                        </div>
                        <div class="filter-group">
                            <label>Country Filter</label>
                            <select id="rawCountryFilter" onchange="applyFilters('rawJobTable', 'rawEngineFilter', 'rawPortalFilter', 'rawCompanyFilter', 'rawCountryFilter')"><option value="all">All Countries</option></select>
                        </div>
                        <button onclick="resetFilters('rawJobTable', 'rawEngineFilter', 'rawPortalFilter', 'rawCompanyFilter', 'rawCountryFilter')" style="margin-top: 18px; padding: 8px 15px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">Reset Filters</button>
                    </div>

                    <table id="rawJobTable">
                        <thead>
                            <tr>
                                <th onclick="sortTable('rawJobTable', 0)">S.No ↕</th>
                                <th onclick="sortTable('rawJobTable', 1)">Search Engine ↕</th>
                                <th onclick="sortTable('rawJobTable', 2)">Jobs Portal ↕</th>
                                <th onclick="sortTable('rawJobTable', 3)">Date Posted ↕</th>
                                <th onclick="sortTable('rawJobTable', 4)">Search Term ↕</th>
                                <th onclick="sortTable('rawJobTable', 5)">Job Title ↕</th>
                                <th onclick="sortTable('rawJobTable', 6)">Company ↕</th>
                                <th onclick="sortTable('rawJobTable', 7)">City ↕</th>
                                <th onclick="sortTable('rawJobTable', 8)">Country ↕</th>
                                <th>Link</th>
                            </tr>
                        </thead>
                        <tbody>
                            {generate_table_rows(raw_df, show_search_term=True)}
                        </tbody>
                    </table>
                </div>
            </details>

            <!-- Natively Collapsed Log Box -->
            <details class="metadata-box">
                <summary>System Metadata & Terminal Logs (Click to Expand)</summary>

                <div class="api-status-box {status_class}" style="margin-top: 15px; margin-bottom: 0;">
                    Google Jobs API (SerpApi) Status: {api_status} | API Calls Consumed: {api_calls_used} | Total Run Time: {duration_str}
                </div>

                <pre>{logs_html}</pre>
            </details>
        </div>

        <script>
            window.onload = function() {{
                initFilters("jobTable", "engineFilter", "portalFilter", "companyFilter", "countryFilter");
                initFilters("rawJobTable", "rawEngineFilter", "rawPortalFilter", "rawCompanyFilter", "rawCountryFilter");
            }};

            function initFilters(tableId, engineId, portalId, companyId, countryId) {{
                let table = document.getElementById(tableId);
                if(!table) return;
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

                populateSelect(engineId, Array.from(engines).sort());
                populateSelect(portalId, Array.from(portals).sort());
                populateSelect(companyId, Array.from(companies).sort());
                populateSelect(countryId, Array.from(countries).sort());
            }}

            function populateSelect(id, items) {{
                let select = document.getElementById(id);
                if(!select) return;
                items.forEach(item => {{
                    if(item && item !== "N/A") {{
                        let opt = document.createElement("option");
                        opt.value = item.toLowerCase();
                        opt.innerHTML = item;
                        select.appendChild(opt);
                    }}
                }});
            }}

            function applyFilters(tableId, engineId, portalId, companyId, countryId) {{
                let engineVal = document.getElementById(engineId).value;
                let portalVal = document.getElementById(portalId).value;
                let companyVal = document.getElementById(companyId).value;
                let countryVal = document.getElementById(countryId).value;

                let table = document.getElementById(tableId);
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

            function resetFilters(tableId, engineId, portalId, companyId, countryId) {{
                document.getElementById(engineId).value = "all";
                document.getElementById(portalId).value = "all";
                document.getElementById(companyId).value = "all";
                document.getElementById(countryId).value = "all";
                applyFilters(tableId, engineId, portalId, companyId, countryId);
            }}

            function sortTable(tableId, n) {{
                let table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById(tableId);
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

            function exportTableToCSV(tableId, filename) {{
                let table = document.getElementById(tableId);
                let rows = table.querySelectorAll("tr");
                let csv = [];
                for (let i = 0; i < rows.length; i++) {{
                    if (rows[i].style.display === "none") continue;

                    let row = [], cols = rows[i].querySelectorAll("td, th");
                    for (let j = 0; j < cols.length; j++) {{
                        let cellText = cols[j].innerText.replace(/(\\r\\n|\\n|\\r)/gm, " ").trim();
                        if (cols[j].querySelector('a')) {{
                            cellText = cols[j].querySelector('a').href;
                        }}
                        row.push('"' + cellText.replace(/"/g, '""') + '"');
                    }}
                    csv.push(row.join(","));
                }}

                let csvFile = new Blob([csv.join("\\n")], {{type: "text/csv"}});
                let downloadLink = document.createElement("a");
                downloadLink.download = filename;
                downloadLink.href = window.URL.createObjectURL(csvFile);
                downloadLink.style.display = "none";
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
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

    for location in LOCATIONS:
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
                error_msg = data["error"]
                if "hasn't returned any results" in error_msg or "couldn't get valid results" in error_msg:
                    log_print(f"Google Jobs found 0 results for {location}.")
                else:
                    log_print(f"SerpApi localized error in {location}: {error_msg}")
                continue

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
    start_time = time.time()
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

    def get_duration():
        elapsed_sec = int(time.time() - start_time)
        mins, secs = divmod(elapsed_sec, 60)
        return f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

    if not all_jobs:
        log_print("No jobs found across any parameters.")
        empty_df = pd.DataFrame(
            columns=['site', 'date_posted', 'search_term', 'title', 'company', 'city', 'country', 'job_url', 'engine'])
        generate_html(empty_df, empty_df, duration_str=get_duration())
        return

    # Combine results and deduplicate
    raw_df = pd.concat(all_jobs, ignore_index=True)
    raw_df.drop_duplicates(subset=['title', 'company'], inplace=True)

    log_print(f"Total raw jobs collected before verification: {len(raw_df)}")

    # Pre-process RAW data (Filters + Location Splitting + Sorting) before Guillotine
    raw_df['loc_lower'] = raw_df['location'].astype(str).str.lower() + " " + raw_df['query_country'].astype(
        str).str.lower()
    raw_df = raw_df[raw_df['loc_lower'].apply(lambda x: any(gcc in x for gcc in GCC_KEYWORDS))]
    raw_df.drop(columns=['loc_lower'], inplace=True)

    # Safety Check: Return clean empty HTML if geographic filter removes all results
    if raw_df.empty:
        log_print("All jobs were filtered out by the geographic GCC keyword filter.")
        empty_df = pd.DataFrame(
            columns=['site', 'date_posted', 'search_term', 'title', 'company', 'city', 'country', 'job_url', 'engine'])
        generate_html(empty_df, empty_df, duration_str=get_duration())
        return

    raw_df[['city', 'country']] = raw_df.apply(clean_location, axis=1, result_type="expand")

    if 'date_posted' in raw_df.columns:
        raw_df['date_posted'] = pd.to_datetime(raw_df['date_posted'], errors='coerce')
        raw_df.sort_values(by='date_posted', ascending=False, inplace=True)
        raw_df['date_posted'] = raw_df['date_posted'].dt.strftime('%Y-%m-%d')
        raw_df.reset_index(drop=True, inplace=True)

    raw_df = raw_df.astype(object)
    raw_df.fillna("N/A", inplace=True)

    # 3. APPLY PYTHON BOOLEAN VERIFICATION (The Guillotine) to create the Highly Relevant DF
    raw_df['is_relevant'] = raw_df.apply(is_highly_relevant, axis=1)
    relevant_df = raw_df[raw_df['is_relevant'] == True].copy()

    # Drop the temporary column from both dataframes
    relevant_df.drop(columns=['is_relevant'], inplace=True)
    raw_df.drop(columns=['is_relevant'], inplace=True)

    log_print(f"Total jobs remaining after strict Hardware/Discipline verification: {len(relevant_df)}")

    duration_str = get_duration()

    # Pass both dataframes and the elapsed duration to the HTML generator
    generate_html(relevant_df, raw_df, duration_str=duration_str)

    log_print("\n" + "=" * 40)
    log_print("SCRAPE EXECUTION COMPLETE")
    log_print("=" * 40)
    log_print(f"Total Highly Relevant Jobs Published: {len(relevant_df)}")
    log_print(f"SerpApi Calls Consumed: {api_calls_used}")
    log_print(f"Total Execution Time: {duration_str}")
    log_print("=" * 40 + "\n")


if __name__ == "__main__":
    main()
