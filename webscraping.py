import requests
import csv
import time
from bs4 import BeautifulSoup
from lxml import etree

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

BASE_SITEMAP = "https://www.1mg.com/sitemap.xml"
OUTPUT_FILE = "1mg_drugs.csv"

# -----------------------------------
# Fetch XML
# -----------------------------------
def fetch_xml(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return etree.fromstring(response.content)

# -----------------------------------
# Get drug sitemap URLs
# -----------------------------------
def get_drug_sitemaps():
    root = fetch_xml(BASE_SITEMAP)
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    return [
        loc.text
        for loc in root.xpath("//ns:sitemap/ns:loc", namespaces=ns)
        if "sitemap_drugs" in loc.text
    ]

# -----------------------------------
# Get drug URLs
# -----------------------------------
def get_drug_urls(sitemap_url):
    root = fetch_xml(sitemap_url)
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    return [
        loc.text
        for loc in root.xpath("//ns:url/ns:loc", namespaces=ns)
    ]

# -----------------------------------
# DRUG PAGE FUNCTION
# -----------------------------------
def scrape_drug_page(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # -------- Extract Drug Name --------
    drug_name = soup.find("h1")
    drug_name = drug_name.get_text(strip=True) if drug_name else ""

    # -------- Extract Marketer Name --------
    marketer_name = ""
    marketer_label = soup.find("div", string=lambda x: x and "Marketer" in x)
    if marketer_label:
        marketer_link = marketer_label.find_next("a")
        if marketer_link:
            marketer_name = marketer_link.get_text(strip=True)

    # -------- Extract Salt Composition --------
    salt_composition = ""
    salt_label = soup.find("div", string=lambda x: x and "SALT COMPOSITION" in x)
    if salt_label:
        salt_links = salt_label.find_next("div").find_all("a")
        salt_composition = " + ".join(
            [link.get_text(strip=True) for link in salt_links]
        )

    # -------- Prescription Required --------
    prescription_required = "No"
    if soup.find(string=lambda x: x and "Prescription Required" in x):
        prescription_required = "Yes"

    return {
        "drug_name": drug_name,
        "marketer": marketer_name,
        "salt_composition": salt_composition,
        "prescription_required": prescription_required
    }

# -----------------------------------
# MAIN
# -----------------------------------
def main(limit_per_sitemap=1):
    drug_sitemaps = get_drug_sitemaps()
    print(f"Found {len(drug_sitemaps)} drug sitemaps")

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "drug_name",
                "marketer",
                "salt_composition",
                "prescription_required"
            ]
        )
        writer.writeheader()

        for sitemap in drug_sitemaps:
            print(f"Processing sitemap: {sitemap}")
            drug_urls = get_drug_urls(sitemap)

            for url in drug_urls[:limit_per_sitemap]:
                try:
                    print(f"Scraping: {url}")
                    data = scrape_drug_page(url)
                    writer.writerow(data)
                    time.sleep(1)  # polite crawling
                except Exception as e:
                    print(f"Failed: {url} | {e}")

    print(f"\nData saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main(limit_per_sitemap=1)

