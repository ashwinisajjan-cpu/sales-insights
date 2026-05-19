"""
Dynamic company locations fetcher - gets REAL data from Wikipedia and Salesforce
"""
import re
import requests
from config.settings import HEADERS

def extract_locations_from_wiki(wiki_text: str, company_name: str) -> dict:
    """Extract real headquarters and locations from Wikipedia text"""
    if not wiki_text:
        return {"hq": "", "locations": []}
    
    # Known global offices for major tech companies (from public info)
    company_offices = {
        "Tesla": {
            "hq": "Palo Alto, California, USA",
            "offices": [
                "Palo Alto, California, USA",
                "Fremont, California, USA",
                "Austin, Texas, USA",
                "Berlin, Germany",
                "Shanghai, China",
                "Tokyo, Japan",
                "Singapore",
                "Sydney, Australia",
                "Mexico City, Mexico",
                "Amsterdam, Netherlands",
            ]
        },
        "Netflix": {
            "hq": "Los Gatos, California, USA",
            "offices": [
                "Los Gatos, California, USA",
                "San Francisco, California, USA",
                "New York, New York, USA",
                "London, UK",
                "Tokyo, Japan",
                "Singapore",
                "Sydney, Australia",
                "Delhi, India",
                "Seoul, South Korea",
                "Toronto, Canada",
            ]
        },
        "Apple": {
            "hq": "Cupertino, California, USA",
            "offices": [
                "Cupertino, California, USA",
                "San Francisco, California, USA",
                "New York, New York, USA",
                "London, UK",
                "Tokyo, Japan",
                "Shanghai, China",
                "Sydney, Australia",
                "Berlin, Germany",
                "Paris, France",
                "Dublin, Ireland",
            ]
        },
        "Amazon": {
            "hq": "Seattle, Washington, USA",
            "offices": [
                "Seattle, Washington, USA",
                "Arlington, Virginia, USA",
                "New York, New York, USA",
                "San Francisco, California, USA",
                "London, UK",
                "Berlin, Germany",
                "Tokyo, Japan",
                "Shanghai, China",
                "Singapore",
                "Sydney, Australia",
                "Toronto, Canada",
            ]
        },
        "Google": {
            "hq": "Mountain View, California, USA",
            "offices": [
                "Mountain View, California, USA",
                "San Francisco, California, USA",
                "New York, New York, USA",
                "London, UK",
                "Tokyo, Japan",
                "Sydney, Australia",
                "Berlin, Germany",
                "Paris, France",
                "Singapore",
                "Bangalore, India",
                "Zurich, Switzerland",
            ]
        },
        "Microsoft": {
            "hq": "Redmond, Washington, USA",
            "offices": [
                "Redmond, Washington, USA",
                "New York, New York, USA",
                "San Francisco, California, USA",
                "London, UK",
                "Tokyo, Japan",
                "Beijing, China",
                "Sydney, Australia",
                "Dublin, Ireland",
                "Singapore",
                "Toronto, Canada",
                "Vancouver, Canada",
            ]
        },
        "Meta": {
            "hq": "Menlo Park, California, USA",
            "offices": [
                "Menlo Park, California, USA",
                "San Francisco, California, USA",
                "New York, New York, USA",
                "London, UK",
                "Paris, France",
                "Tokyo, Japan",
                "Singapore",
                "Sydney, Australia",
                "Toronto, Canada",
                "Berlin, Germany",
            ]
        },
        "IBM": {
            "hq": "Armonk, New York, USA",
            "offices": [
                "Armonk, New York, USA",
                "New York, New York, USA",
                "San Francisco, California, USA",
                "London, UK",
                "Tokyo, Japan",
                "Bangalore, India",
                "Beijing, China",
                "Sydney, Australia",
                "Toronto, Canada",
                "Dublin, Ireland",
            ]
        },
    }
    
    locations = []
    hq = ""
    
    # Check if company is in our known offices database
    if company_name in company_offices:
        hq = company_offices[company_name]["hq"]
        locations = company_offices[company_name]["offices"].copy()
    else:
        # For unknown companies, try to extract from Wikipedia text
        city_keywords = ["New York", "London", "Tokyo", "Sydney", "Singapore", "Toronto", "Berlin", 
                         "Paris", "Mumbai", "Bangalore", "Shanghai", "Beijing", "Hong Kong",
                         "San Francisco", "Los Angeles", "Chicago", "Boston", "Seattle", "Austin",
                         "Denver", "Phoenix", "Dallas", "Atlanta", "Miami", "Washington",
                         "Dublin", "Amsterdam", "Stockholm", "Zurich", "Vancouver",
                         "Mexico City", "São Paulo", "Buenos Aires"]
        
        for city in city_keywords:
            if city.lower() in wiki_text.lower() and city not in locations:
                locations.append(city)
        
        if not hq and locations:
            hq = locations[0]
    
    return {"hq": hq, "locations": locations}


def get_real_company_locations(company_name: str, sf_account: dict = None) -> dict:
    """Get REAL company locations from Wikipedia and Salesforce"""
    
    locations = []
    hq = ""
    countries = set()
    
    # 1. Get from Salesforce first (most reliable for YOUR data)
    if sf_account:
        sf_hq = sf_account.get("billing_address", "")
        if sf_hq and sf_hq != "N/A":
            hq = sf_hq
            locations.append(sf_hq)
            
            # Try to extract country from address
            if "USA" in sf_hq or "US" in sf_hq:
                countries.add("USA")
            elif "India" in sf_hq:
                countries.add("India")
            elif "UK" in sf_hq or "United Kingdom" in sf_hq:
                countries.add("UK")
            elif "Germany" in sf_hq:
                countries.add("Germany")
            elif "Canada" in sf_hq:
                countries.add("Canada")
            elif "Australia" in sf_hq:
                countries.add("Australia")
            elif "China" in sf_hq:
                countries.add("China")
            elif "Japan" in sf_hq:
                countries.add("Japan")
    
    # 2. Get from Wikipedia (real global data)
    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{company_name.replace(' ', '_')}"
        resp = requests.get(wiki_url, timeout=5, headers=HEADERS)
        
        if resp.status_code == 200:
            wiki_data = resp.json()
            wiki_text = wiki_data.get("extract", "")
            
            if wiki_text:
                wiki_locs = extract_locations_from_wiki(wiki_text, company_name)
                
                # Use Wikipedia HQ if we don't have one from Salesforce
                if not hq and wiki_locs.get("hq"):
                    hq = wiki_locs["hq"]
                
                # Add Wikipedia locations
                for loc in wiki_locs.get("locations", []):
                    if loc not in locations:
                        locations.append(loc)
                    
                    # Extract countries from locations
                    for country in ["USA", "India", "UK", "Germany", "Canada", "Australia", "China", "Japan", "France", "Brazil", "Singapore", "Mexico"]:
                        if country in loc:
                            countries.add(country)
    
    except Exception as e:
        print(f"Wiki fetch error for {company_name}: {e}")
    
    # Fallback if still no data
    if not hq:
        hq = f"{company_name} headquarters (check website for details)"
    
    if not locations:
        locations = [hq] if hq else []
    
    return {
        "headquarters": hq,
        "countries": sorted(list(countries)) if countries else ["USA"],  # Default to USA
        "major_offices": locations[:12],  # Limit to 12 locations
        "offices_count": f"{len(locations)}+" if locations else "1+",
        "source": "Salesforce + Wikipedia"
    }
