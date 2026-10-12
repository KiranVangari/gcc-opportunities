import os
import pandas as pd
from datetime import datetime
from jobspy import scrape_jobs

# 1. Simplified Configuration
SEARCH_TERMS = ["Vibration Analyst", "Turbomachinery", "Condition Monitoring"]
LOCATIONS = ["United Arab Emirates", "Saudi Arabia", "Qatar"]

def generate_html(df):
    """Generates a simple HTML dashboard from the DataFrame."""
    os.makedirs('public', exist_ok=True)
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GCC Job Matches (LinkedIn Only)</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; padding: 20px; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #2c3e50; color: white; }}
            tr:hover {{ background-color: #f5f5f5; }}
            a {{ color: #3498db; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>GCC Job Matches (LinkedIn Only)</h1>
            <p>Last Updated: {run_date}</p>
            <table>
                <thead>
                    <tr>
                        <th>Job Title</th>
                        <th>Company</th>
                        <th>Location</th>
                        <th>Apply Link</th>
                    </tr>
                </thead>
                <tbody>
    """

    for _, row in df.iterrows():
        # Handle cases where data might be missing
        title = row.get('title', 'N/A')
        company = row.get('company', 'N/A')
        location = row.get('location', 'N/A')
        url = row.get('job_url', '#')

        html_content += f"""
                    <tr>
                        <td>{title}</td>
                        <td>{company}</td>
                        <td>{location}</td>
                        <td><a href="{url}" target="_blank">View Job</a></td>
                    </tr>
        """

    html_content += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """

    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard generated with {len(df)} jobs.")

def main():
    print("Starting simplified LinkedIn job scrape...")
    all_jobs = []

    for term in SEARCH_TERMS:
        for location in LOCATIONS:
            try:
                print(f"Scraping '{term}' in '{location}'...")
                jobs = scrape_jobs(
                    site_name=["linkedin"],
                    search_term=term,
                    location=location,
                    results_wanted=15  # Keep low to avoid LinkedIn blocking the GitHub Action IP
                )
                if not jobs.empty:
                    all_jobs.append(jobs)
            except Exception as e:
                print(f"Error scraping {term} in {location}: {e}")

    if not all_jobs:
        print("No jobs found. (LinkedIn may be blocking the GitHub Actions IP).")
        generate_html(pd.DataFrame(columns=['title', 'company', 'location', 'job_url']))
        return

    # Combine results and drop duplicates based on the URL
    df = pd.concat(all_jobs, ignore_index=True)
    df.drop_duplicates(subset=['job_url'], inplace=True)
    
    # Fill missing values to prevent HTML rendering errors
    df.fillna("Not specified", inplace=True)

    generate_html(df)

if __name__ == "__main__":
    main()
