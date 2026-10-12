import os
import pandas as pd
from datetime import datetime
from jobspy import scrape_jobs

# 1. Configuration & Target Regions
SEARCH_TERMS = ["Vibration", "System 1", "Cordant", "Turbomachinery", "Rotating Equipment", "Condition Monitoring"]
LOCATIONS = ["UAE", "United Arab Emirates", "Saudi Arabia", "Qatar", "Kuwait", "Oman", "Bahrain"]
MIN_SCORE_THRESHOLD = 30  # Minimum relevance score to include in the dashboard

# 2. Resume Keyword Weighting (Extracted from Kiran Vangari Resume)
KEYWORD_WEIGHTS = {
    # Elite / Niche Certifications & Tools (High Value)
    "category iv": 25, "category 4": 25, "master vibration": 20,
    "bently nevada": 20, "system 1": 20, "system-1": 20, "api 670": 15, "api-670": 15,
    "cordant": 15, "adre": 15, "iso 18436": 15,

    # Core Domain (Medium Value)
    "turbomachinery": 15, "vibration": 10, "condition monitoring": 10,
    "predictive analytics": 10, "rotating equipment": 10, "asset health": 10,
    "compressor": 10, "gas turbine": 10, "steam turbine": 10, "generator": 10,

    # Secondary Skills (Lower Value)
    "in-situ balancing": 5, "root cause analysis": 5, "rca": 5,
    "python": 5, "aws": 5, "solutions architect": 5, "six sigma": 5
}


def calculate_relevance(description):
    """Scores a job description based on the weighted resume keywords."""
    if not isinstance(description, str):
        return 0

    desc_lower = description.lower()
    score = 0
    max_possible_score = 150  # Arbitrary ceiling for normalization

    for keyword, weight in KEYWORD_WEIGHTS.items():
        if keyword in desc_lower:
            score += weight

    # Normalize to a 100% scale and cap at 100
    normalized_score = min(int((score / max_possible_score) * 100), 100)
    return normalized_score


def generate_html(df):
    """Generates a responsive HTML dashboard from the filtered DataFrame."""
    os.makedirs('public', exist_ok=True)

    run_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GCC Turbomachinery Job Matches</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            p {{ color: #7f8c8d; font-size: 0.9em; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #2c3e50; color: #fff; cursor: pointer; }}
            th:hover {{ background-color: #34495e; }}
            tr:hover {{ background-color: #f5f5f5; }}
            a {{ color: #3498db; text-decoration: none; font-weight: bold; }}
            a:hover {{ text-decoration: underline; }}
            .score-high {{ color: #27ae60; font-weight: bold; }}
            .score-med {{ color: #f39c12; font-weight: bold; }}
            .score-low {{ color: #e74c3c; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Targeted GCC Job Matches: Kiran Vangari</h1>
            <p>Last Updated: {run_date}</p>
            <table id="jobTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Relevance Score ↕</th>
                        <th onclick="sortTable(1)">Job Title ↕</th>
                        <th onclick="sortTable(2)">Company ↕</th>
                        <th onclick="sortTable(3)">Location ↕</th>
                        <th>Apply Link</th>
                    </tr>
                </thead>
                <tbody>
    """

    for _, row in df.iterrows():
        score = row['Relevance Score']
        score_class = "score-high" if score >= 70 else ("score-med" if score >= 50 else "score-low")

        html_content += f"""
                    <tr>
                        <td class="{score_class}">{score}%</td>
                        <td>{row['title']}</td>
                        <td>{row['company']}</td>
                        <td>{row['location']}</td>
                        <td><a href="{row['job_url']}" target="_blank">View Job</a></td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>
        <script>
            function sortTable(n) {
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("jobTable");
                switching = true;
                dir = "desc"; 
                while (switching) {
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];

                        let xVal = x.innerHTML.toLowerCase();
                        let yVal = y.innerHTML.toLowerCase();

                        // Handle numeric sorting for the score column
                        if (n === 0) {
                            xVal = parseInt(xVal.replace('%', ''));
                            yVal = parseInt(yVal.replace('%', ''));
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
                        if (switchcount == 0 && dir == "desc") {
                            dir = "asc";
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
    print(f"HTML dashboard generated in public/index.html with {len(df)} jobs.")


def main():
    print("Starting job scrape...")
    all_jobs = []

    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            try:
                print(f"Scraping '{term}' in '{location}'...")
                jobs = scrape_jobs(
                    site_name=["linkedin", "indeed", "glassdoor", "bayt"],
                    search_term=term,
                    location=location,
                    results_wanted=30,  # Keep reasonable to prevent CI bans
                    hours_old=72,  # Only fetch recent postings
                    country_indeed='ae'  # Base indeed targeting
                )
                if not jobs.empty:
                    all_jobs.append(jobs)
            except Exception as e:
                print(f"Error scraping {term} in {location}: {e}")

    if not all_jobs:
        print("No jobs found across any parameters.")
        # Create an empty dashboard so GitHub Pages doesn't break
        generate_html(pd.DataFrame(columns=['Relevance Score', 'title', 'company', 'location', 'job_url']))
        return

    # Combine all results and drop duplicates
    df = pd.concat(all_jobs, ignore_index=True)
    df.drop_duplicates(subset=['job_url'], inplace=True)

    # Apply scoring
    print("Applying resume keyword matching...")
    df['Relevance Score'] = df['description'].apply(calculate_relevance)

    # Filter and sort
    filtered_df = df[df['Relevance Score'] >= MIN_SCORE_THRESHOLD].copy()
    filtered_df.sort_values(by='Relevance Score', ascending=False, inplace=True)

    # Handle missing values for HTML presentation
    filtered_df.fillna("Not specified", inplace=True)

    generate_html(filtered_df)


if __name__ == "__main__":
    main()
