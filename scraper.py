import os
import pandas as pd
from datetime import datetime
from jobspy import scrape_jobs

# 1. Expanded Configuration (No Scoring, Pure Expansion)
SEARCH_TERMS = [
    "Vibration Analyst", 
    "Turbomachinery", 
    "Condition Monitoring", 
    "System 1", 
    "Rotating Equipment", 
    "Asset Health", 
    "Bently Nevada", 
    "Reliability Engineer",
    "Machinery Diagnostics",
    "Gas Turbine"
]

LOCATIONS = [
    "United Arab Emirates", 
    "Saudi Arabia", 
    "Qatar", 
    "Kuwait", 
    "Oman", 
    "Bahrain"
]

def generate_html(df):
    """Generates an interactive HTML dashboard with sorting and filtering."""
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
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-top: 0; }}
            .controls-container {{ display: flex; justify-content: space-between; align-items: center; margin: 20px 0; padding: 15px; background-color: #f1f3f5; border-radius: 8px; }}
            .summary-text {{ font-size: 1.1em; font-weight: bold; color: #2c3e50; margin: 0; }}
            .filter-box select {{ padding: 8px 12px; border-radius: 5px; border: 1px solid #ced4da; font-size: 1em; cursor: pointer; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.95em; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #dee2e6; }}
            th {{ background-color: #2c3e50; color: white; cursor: pointer; position: sticky; top: 0; }}
            th:hover {{ background-color: #34495e; }}
            tr:hover {{ background-color: #f8f9fa; }}
            a.apply-btn {{ color: white; background-color: #3498db; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block; }}
            a.apply-btn:hover {{ background-color: #2980b9; }}
            .badge {{ padding: 5px 10px; border-radius: 12px; font-size: 0.8em; font-weight: bold; color: white; text-transform: uppercase; letter-spacing: 0.5px; }}
            .linkedin {{ background-color: #0077b5; }}
            .indeed {{ background-color: #2164f4; }}
            .glassdoor {{ background-color: #0caa41; }}
            .bayt {{ background-color: #005a9c; }}
            .naukri {{ background-color: #ff7555; }}
            .default-site {{ background-color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>GCC Turbomachinery & Reliability Jobs</h1>
            
            <div class="controls-container">
                <div>
                    <p class="summary-text">Total Jobs Found: <span style="color: #3498db; font-size: 1.2em;">{total_jobs}</span></p>
                    <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #6c757d;">Last Updated: {run_date}</p>
                </div>
                <div class="filter-box">
                    <label for="countryFilter"><strong>Filter by Country: </strong></label>
                    <select id="countryFilter" onchange="filterTable()">
                        <option value="all">All Locations</option>
                        <option value="uae">UAE (Dubai/Abu Dhabi)</option>
                        <option value="saudi">Saudi Arabia</option>
                        <option value="qatar">Qatar</option>
                        <option value="kuwait">Kuwait</option>
                        <option value="oman">Oman</option>
                        <option value="bahrain">Bahrain</option>
                    </select>
                </div>
            </div>

            <table id="jobTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">S.No ↕</th>
                        <th onclick="sortTable(1)">Portal ↕</th>
                        <th onclick="sortTable(2)">Date Posted ↕</th>
                        <th onclick="sortTable(3)">Job Title ↕</th>
                        <th onclick="sortTable(4)">Company ↕</th>
                        <th onclick="sortTable(5)">Location ↕</th>
                        <th>Link</th>
                    </tr>
                </thead>
                <tbody>
    """

    # Populate table rows
    for idx, (_, row) in enumerate(df.iterrows(), 1):
        title = str(row.get('title', 'N/A'))
        company = str(row.get('company', 'N/A'))
        location = str(row.get('location', 'N/A'))
        url = str(row.get('job_url', '#'))
        site = str(row.get('site', 'unknown')).lower()
        
        # Parse date gracefully 
        date_val = row.get('date_posted')
        if pd.isna(date_val):
            date_str = "N/A"
        else:
            try:
                date_str = pd.to_datetime(date_val).strftime("%Y-%m-%d")
            except:
                date_str = str(date_val)

        # Assign CSS classes based on the portal
        badge_class = site if site in ['linkedin', 'indeed', 'glassdoor', 'bayt', 'naukri'] else 'default-site'

        html_content += f"""
                    <tr>
                        <td>{idx}</td>
                        <td><span class="badge {badge_class}">{site}</span></td>
                        <td>{date_str}</td>
                        <td style="font-weight: 500;">{title}</td>
                        <td>{company}</td>
                        <td class="loc-cell">{location}</td>
                        <td><a href="{url}" target="_blank" class="apply-btn">View</a></td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>

        <script>
            // Country Filtering Logic
            function filterTable() {
                let dropdown = document.getElementById("countryFilter");
                let filterValue = dropdown.value.toLowerCase();
                let table = document.getElementById("jobTable");
                let tr = table.getElementsByTagName("tr");

                for (let i = 1; i < tr.length; i++) {
                    let td = tr[i].getElementsByClassName("loc-cell")[0];
                    if (td) {
                        let loc = (td.textContent || td.innerText).toLowerCase();
                        let show = false;
                        
                        if (filterValue === "all") {
                            show = true;
                        } else if (filterValue === "uae" && (loc.includes("uae") || loc.includes("emirates") || loc.includes("dubai") || loc.includes("abu dhabi") || loc.includes("sharjah"))) {
                            show = true;
                        } else if (loc.includes(filterValue)) {
                            show = true;
                        }
                        
                        tr[i].style.display = show ? "" : "none";
                    }
                }
            }

            // Column Sorting Logic
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
                        
                        // Treat S.No as numeric so 10 doesn't come before 2
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

def main():
    print("Starting multi-portal job scrape...")
    all_jobs = []

    # Iterating through terms and locations prevents API overload compared to a single massive call
    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            try:
                print(f"Scraping '{term}' in '{location}'...")
                jobs = scrape_jobs(
                    site_name=["linkedin", "indeed", "glassdoor", "bayt", "naukri"], 
                    search_term=term,
                    location=location,
                    results_wanted=10,  # Keep low per iteration to avoid IP bans
                    country_indeed='ae'
                )
                if not jobs.empty:
                    all_jobs.append(jobs)
            except Exception as e:
                print(f"Error scraping '{term}' in '{location}': {e}")

    if not all_jobs:
        print("No jobs found across any parameters.")
        generate_html(pd.DataFrame(columns=['site', 'date_posted', 'title', 'company', 'location', 'job_url']))
        return

    # Combine all query results
    df = pd.concat(all_jobs, ignore_index=True)
    
    # De-duplicate based on Title and Company. 
    # (We cannot drop by URL here because Indeed and LinkedIn will have different URLs for the exact same job).
    df.drop_duplicates(subset=['title', 'company'], inplace=True)
    
    # Sort the initial output so the newest jobs are at the top
    if 'date_posted' in df.columns:
        df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
        df.sort_values(by='date_posted', ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
    
    # Fill empty data fields
    df.fillna("N/A", inplace=True)

    generate_html(df)

if __name__ == "__main__":
    main()
