import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from jobspy import scrape_jobs

# 1. Configuration
SEARCH_TERMS = [
    "Vibration", "Turbomachinery", "Condition Monitoring", "System 1", 
    "Rotating Equipment", "Asset Health", "Bently Nevada", 
    "Reliability Engineer", "Machinery Diagnostics", "Cordant", 
    "AHM", "APM", "Reliability", "CMRP"
]

LOCATIONS = [
    "United Arab Emirates", "Saudi Arabia", "Qatar", 
    "Kuwait", "Oman", "Bahrain"
]

# We combine core terms into a single boolean query for the API to save credits (1 call per country)
API_SEARCH_QUERY = '"Vibration" OR "Turbomachinery" OR "Condition Monitoring" OR "Rotating Equipment"'

GCC_KEYWORDS = [
    'uae', 'united arab emirates', 'dubai', 'abu dhabi', 'sharjah', 
    'saudi', 'ksa', 'riyadh', 'jeddah', 'dammam', 'dhahran', 'khobar',
    'qatar', 'doha', 'kuwait', 'oman', 'muscat', 'bahrain', 'manama'
]

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

def split_location(loc_str):
    loc_str = str(loc_str).strip()
    if pd.isna(loc_str) or loc_str.lower() in ["nan", "n/a", "none", ""]:
        return "N/A", "N/A"
    parts = [p.strip() for p in loc_str.split(',')]
    if len(parts) >= 2:
        return ", ".join(parts[:-1]), parts[-1]
    return "N/A", parts[0]

def parse_relative_date(text):
    """Converts '3 days ago' into a YYYY-MM-DD format for proper sorting."""
    if not isinstance(text, str) or "ago" not in text:
        return text
    try:
        num = int(text.split()[0])
        if "hour" in text:
            return (datetime.now() - timedelta(hours=num)).strftime('%Y-%m-%d')
        if "day" in text:
            return (datetime.now() - timedelta(days=num)).strftime('%Y-%m-%d')
    except:
        pass
    return text

def generate_html(df):
    os.makedirs('public', exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    total_jobs = len(df)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GCC Turbomachinery Job Matches</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; padding: 20px; color: #333; }}
            .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-top: 0; }}
            .summary-text {{ font-size: 1.1em; font-weight: bold; color: #2c3e50; margin: 0; }}
            .filter-bar {{ display: flex; gap: 15px; margin: 20px 0; padding: 15px; background-color: #f1f3f5; border-radius: 8px; align-items: center; flex-wrap: wrap; }}
            .filter-group {{ display: flex; flex-direction: column; }}
            .filter-group label {{ font-size: 0.85em; font-weight: bold; color: #555; margin-bottom: 5px; }}
            .filter-group select {{ padding: 8px; border-radius: 4px; border: 1px solid #ccc; min-width: 150px; outline: none; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.95em; }}
            th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
            th {{ background-color: #2c3e50; color: white; cursor: pointer; position: sticky; top: 0; }}
            th:hover {{ background-color: #34495e; }}
            tr:hover {{ background-color: #f8f9fa; }}
            a.apply-btn {{ color: white; background-color: #3498db; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block; text-align: center; }}
            a.apply-btn:hover {{ background-color: #2980b9; }}
            .badge {{ padding: 4px 8px; border-radius: 8px; font-size: 0.8em; font-weight: bold; color: white; text-transform: uppercase; }}
            .linkedin {{ background-color: #0077b5; }}
            .indeed {{ background-color: #2164f4; }}
            .glassdoor {{ background-color: #0caa41; }}
            .bayt {{ background-color: #005a9c; }}
            .naukrigulf {{ background-color: #ff7555; }}
            .default-site {{ background-color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>GCC Turbomachinery & Reliability Jobs</h1>
            
            <p class="summary-text">Total Jobs Found: <span style="color: #3498db; font-size: 1.2em;">{total_jobs}</span></p>
            <p style="margin: 5px 0 15px 0; font-size: 0.85em; color: #6c757d;">Last Updated: {run_date}</p>

            <div class="filter-bar">
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
                        <th onclick="sortTable(1)">Portal ↕</th>
                        <th onclick="sortTable(2)">Date Posted ↕</th>
                        <th onclick="sortTable(3)">Job Title ↕</th>
                        <th onclick="sortTable(4)">Company ↕</th>
                        <th onclick="sortTable(5)">City ↕</th>
                        <th onclick="sortTable(6)">Country ↕</th>
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
        date_str = str(row.get('date_posted', 'N/A'))

        badge_class = site if site in ['linkedin', 'indeed', 'glassdoor', 'bayt', 'naukrigulf'] else 'default-site'

        html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td class="portal-cell"><span class="badge {badge_class}">{site}</span></td>
                        <td>{date_str}</td>
                        <td style="font-weight: 500;">{title}</td>
                        <td class="company-cell">{company}</td>
                        <td>{city}</td>
                        <td class="country-cell">{country}</td>
                        <td><a href="{url}" target="_blank" class="apply-btn">View</a></td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>

        <script>
            window.onload = function() {
                let table = document.getElementById("jobTable");
                let tr = table.getElementsByTagName("tr");
                let portals = new Set(), companies = new Set(), countries = new Set();

                for (let i = 1; i < tr.length; i++) {
                    let tdPortal = tr[i].getElementsByClassName("portal-cell")[0];
                    let tdCompany = tr[i].getElementsByClassName("company-cell")[0];
                    let tdCountry = tr[i].getElementsByClassName("country-cell")[0];

                    if (tdPortal) portals.add(tdPortal.textContent.trim());
                    if (tdCompany) companies.add(tdCompany.textContent.trim());
                    if (tdCountry) countries.add(tdCountry.textContent.trim());
                }

                populateSelect("portalFilter", Array.from(portals).sort());
                populateSelect("companyFilter", Array.from(companies).sort());
                populateSelect("countryFilter", Array.from(countries).sort());
            };

            function populateSelect(id, items) {
                let select = document.getElementById(id);
                items.forEach(item => {
                    if(item && item !== "N/A") {
                        let opt = document.createElement("option");
                        opt.value = item.toLowerCase();
                        opt.innerHTML = item;
                        select.appendChild(opt);
                    }
                });
            }

            function applyFilters() {
                let portalVal = document.getElementById("portalFilter").value;
                let companyVal = document.getElementById("companyFilter").value;
                let countryVal = document.getElementById("countryFilter").value;
                
                let table = document.getElementById("jobTable");
                let tr = table.getElementsByTagName("tr");

                for (let i = 1; i < tr.length; i++) {
                    let tdPortal = tr[i].getElementsByClassName("portal-cell")[0];
                    let tdCompany = tr[i].getElementsByClassName("company-cell")[0];
                    let tdCountry = tr[i].getElementsByClassName("country-cell")[0];

                    if (tdPortal && tdCompany && tdCountry) {
                        let portalMatch = (portalVal === "all") || (tdPortal.textContent.trim().toLowerCase() === portalVal);
                        let companyMatch = (companyVal === "all") || (tdCompany.textContent.trim().toLowerCase() === companyVal);
                        let countryMatch = (countryVal === "all") || (tdCountry.textContent.trim().toLowerCase() === countryVal);

                        tr[i].style.display = (portalMatch && companyMatch && countryMatch) ? "" : "none";
                    }
                }
            }

            function resetFilters() {
                document.getElementById("portalFilter").value = "all";
                document.getElementById("companyFilter").value = "all";
                document.getElementById("countryFilter").value = "all";
                applyFilters();
            }

            function sortTable(n) {
                let table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("jobTable");
                switching = true;
                dir = "asc"; 
                while (switching) {
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];

                        let xVal = x.textContent.trim().toLowerCase();
                        let yVal = y.textContent.trim().toLowerCase();

                        if (n === 0) {
                            xVal = parseInt(xVal) || 0;
                            yVal = parseInt(yVal) || 0;
                        }

                        if (dir == "asc") {
                            if (xVal > yVal) { shouldSwitch = true; break; }
                        } else if (dir == "desc") {
                            if (xVal < yVal) { shouldSwitch = true; break; }
                        }
                    }
                    if (shouldSwitch) {
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount ++;
                    } else {
                        if (switchcount == 0 && dir == "asc") {
                            dir = "desc";
                            switching = true;
                        }
                    }
                }
            }
        </script>
    </body>
    </html>
    """
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard generated with {total_jobs} jobs.")


def get_serpapi_jobs():
    """Fetches regional jobs (Bayt, Naukri, Glassdoor) via Google Jobs API."""
    if not SERPAPI_KEY:
        print("SERPAPI_KEY not found. Skipping Google Jobs API.")
        return pd.DataFrame()
        
    print("Starting SerpApi Google Jobs scrape...")
    api_jobs = []
    
    for location in LOCATIONS:
        print(f"Querying Google Jobs API for {location}...")
        params = {
            "engine": "google_jobs",
            "q": API_SEARCH_QUERY,
            "location": location,
            "hl": "en",
            "api_key": SERPAPI_KEY
        }
        
        try:
            response = requests.get("https://serpapi.com/search", params=params)
            data = response.json()
            
            if "jobs_results" in data:
                for job in data["jobs_results"]:
                    # Extract the source portal (e.g. "via Bayt.com" -> "Bayt")
                    via = job.get("via", "Google").replace("via ", "").replace(".com", "")
                    
                    # Extract relative posting date
                    posted_str = "N/A"
                    for ext in job.get("extensions", []):
                        if "ago" in ext.lower():
                            posted_str = parse_relative_date(ext)
                            
                    api_jobs.append({
                        "title": job.get("title", "N/A"),
                        "company": job.get("company_name", "N/A"),
                        "location": job.get("location", "N/A"),
                        "job_url": job.get("share_link", "#"),
                        "site": via,
                        "date_posted": posted_str
                    })
        except Exception as e:
            print(f"SerpApi Error for {location}: {e}")
            
    return pd.DataFrame(api_jobs)


def main():
    print("Starting multi-portal job scrape (Last 7 Days)...")
    all_jobs = []

    # 1. LOCAL JOB_SPY SCRAPE (LinkedIn & Indeed)
    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            try:
                print(f"Scraping '{term}' in '{location}' (JobSpy)...")
                indeed_country = "uae" if location == "United Arab Emirates" else location.lower()
                jobs = scrape_jobs(
                    site_name=["linkedin", "indeed"],
                    search_term=term,
                    location=location,
                    results_wanted=10, 
                    hours_old=168, 
                    country_indeed=indeed_country
                )
                if not jobs.empty:
                    all_jobs.append(jobs)
            except Exception as e:
                print(f"Error scraping '{term}' in '{location}': {e}")

    # 2. SERPAPI SCRAPE (Bayt, Naukri, Glassdoor, Corporate Sites)
    serp_df = get_serpapi_jobs()
    if not serp_df.empty:
        all_jobs.append(serp_df)

    if not all_jobs:
        print("No jobs found across any parameters.")
        generate_html(pd.DataFrame(columns=['site', 'date_posted', 'title', 'company', 'city', 'country', 'job_url']))
        return

    # Combine results and deduplicate
    df = pd.concat(all_jobs, ignore_index=True)
    df.drop_duplicates(subset=['title', 'company'], inplace=True)

    # 3. APPLY STRICT GCC GEOGRAPHIC FILTER
    df['loc_lower'] = df['location'].astype(str).str.lower()
    df = df[df['loc_lower'].apply(lambda x: any(gcc in x for gcc in GCC_KEYWORDS))]
    df.drop(columns=['loc_lower'], inplace=True)

    # 4. SPLIT LOCATION INTO CITY AND COUNTRY
    df['city'], df['country'] = zip(*df['location'].apply(split_location))

    # 5. SORT BY DATE POSTED
    if 'date_posted' in df.columns:
        # Convert parsed relative dates back to datetime for accurate sorting
        df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
        df.sort_values(by='date_posted', ascending=False, inplace=True)
        df['date_posted'] = df['date_posted'].dt.strftime('%Y-%m-%d')
        df.reset_index(drop=True, inplace=True)

    df = df.astype(object)
    df.fillna("N/A", inplace=True)

    generate_html(df)

if __name__ == "__main__":
    main()
