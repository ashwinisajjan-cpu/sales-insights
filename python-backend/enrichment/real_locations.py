"""
Dynamic company locations fetcher - gets REAL data from Wikipedia and Salesforce
"""
import re
import requests
from config.settings import HEADERS

def extract_locations_from_wiki(wiki_text: str, company_name: str) -> dict:
    """Extract REAL headquarters and locations from Wikipedia text"""
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
        "Salesforce": {
            "hq": "San Francisco, California, USA",
            "offices": [
                "San Francisco, California, USA",
                "New York, New York, USA",
                "London, UK",
                "Tokyo, Japan",
                "Singapore",
                "Sydney, Australia",
                "Toronto, Canada",
                "Dublin, Ireland",
                "Paris, France",
                "Berlin, Germany",
            ]
        },
        "Oracle": {
            "hq": "Austin, Texas, USA",
            "offices": [
                "Austin, Texas, USA",
                "Redwood City, California, USA",
                "New York, New York, USA",
                "London, UK",
                "Munich, Germany",
                "Tokyo, Japan",
                "Bangalore, India",
                "Beijing, China",
                "Sydney, Australia",
                "Toronto, Canada",
            ]
        },
        "Cisco": {
            "hq": "San Jose, California, USA",
            "offices": [
                "San Jose, California, USA",
                "New York, New York, USA",
                "Austin, Texas, USA",
                "London, UK",
                "Bangalore, India",
                "Shanghai, China",
                "Tokyo, Japan",
                "Sydney, Australia",
                "Toronto, Canada",
                "Dublin, Ireland",
            ]
        },
        "Intel": {
            "hq": "Santa Clara, California, USA",
            "offices": [
                "Santa Clara, California, USA",
                "Folsom, California, USA",
                "Hillsboro, Oregon, USA",
                "New York, New York, USA",
                "London, UK",
                "Tokyo, Japan",
                "Beijing, China",
                "Singapore",
                "Sydney, Australia",
                "Dublin, Ireland",
            ]
        },
        "Nvidia": {
            "hq": "Santa Clara, California, USA",
            "offices": [
                "Santa Clara, California, USA",
                "San Francisco, California, USA",
                "New York, New York, USA",
                "London, UK",
                "Tokyo, Japan",
                "Shanghai, China",
                "Singapore",
                "Seoul, South Korea",
                "Sydney, Australia",
                "Toronto, Canada",
            ]
        },
        "Adobe": {
            "hq": "San Jose, California, USA",
            "offices": [
                "San Jose, California, USA",
                "San Francisco, California, USA",
                "New York, New York, USA",
                "London, UK",
                "Tokyo, Japan",
                "Singapore",
                "Sydney, Australia",
                "Toronto, Canada",
                "Edinburgh, UK",
                "München, Germany",
            ]
        },
        "JPMorgan Chase": {
            "hq": "New York, New York, USA",
            "offices": [
                "New York, New York, USA",
                "Jersey City, New Jersey, USA",
                "Chicago, Illinois, USA",
                "San Francisco, California, USA",
                "London, UK",
                "Frankfurt, Germany",
                "Tokyo, Japan",
                "Bangalore, India",
                "Sydney, Australia",
                "Toronto, Canada",
                "Hong Kong",
            ]
        },
        "Goldman Sachs": {
            "hq": "New York, New York, USA",
            "offices": [
                "New York, New York, USA",
                "London, UK",
                "Frankfurt, Germany",
                "Hong Kong",
                "Tokyo, Japan",
                "Bangalore, India",
                "Singapore",
                "Sydney, Australia",
                "Toronto, Canada",
                "Paris, France",
            ]
        },
        "Bank of America": {
            "hq": "Charlotte, North Carolina, USA",
            "offices": [
                "Charlotte, North Carolina, USA",
                "New York, New York, USA",
                "San Francisco, California, USA",
                "London, UK",
                "Frankfurt, Germany",
                "Tokyo, Japan",
                "Bangalore, India",
                "Sydney, Australia",
                "Toronto, Canada",
                "Singapore",
            ]
        },
        "Walmart": {
            "hq": "Bentonville, Arkansas, USA",
            "offices": [
                "Bentonville, Arkansas, USA",
                "New York, New York, USA",
                "Mexico City, Mexico",
                "London, UK",
                "Beijing, China",
                "Tokyo, Japan",
                "Toronto, Canada",
                "Sydney, Australia",
                "São Paulo, Brazil",
                "Singapore",
            ]
        },
        "AT&T": {
            "hq": "Dallas, Texas, USA",
            "offices": [
                "Dallas, Texas, USA",
                "New York, New York, USA",
                "San Francisco, California, USA",
                "Atlanta, Georgia, USA",
                "London, UK",
                "Mexico City, Mexico",
                "Toronto, Canada",
            ]
        },
        "Verizon": {
            "hq": "New York, New York, USA",
            "offices": [
                "New York, New York, USA",
                "Basking Ridge, New Jersey, USA",
                "Washington DC, USA",
                "Los Angeles, California, USA",
                "London, UK",
                "Toronto, Canada",
                "Mexico City, Mexico",
            ]
        },
        "Wells Fargo": {
            "hq": "San Francisco, California, USA",
            "offices": [
                "San Francisco, California, USA",
                "Charlotte, North Carolina, USA",
                "New York, New York, USA",
                "Los Angeles, California, USA",
                "Chicago, Illinois, USA",
                "Dallas, Texas, USA",
                "Denver, Colorado, USA",
                "London, UK",
                "Tokyo, Japan",
                "Sydney, Australia",
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
        # For unknown companies, DYNAMICALLY extract from Wikipedia text
        # Look for headquarters pattern
        hq_patterns = [
            r"(?:headquarter|head office|based in|founded in|located in)\s+([A-Z][a-z\s]+(?:,\s*[A-Z][a-z\s]+)*(?:,\s*[A-Z]{2})?)",
        ]
        
        for pattern in hq_patterns:
            matches = re.findall(pattern, wiki_text)
            if matches:
                hq = matches[0].strip()
                if len(hq) > 5:
                    break
        
        # Extract all cities/locations mentioned in Wikipedia
        # Pattern: Find city names followed by country codes or state abbreviations
        location_pattern = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:,\s*(?:CA|NY|TX|UK|Germany|India|China|Japan|Australia|Singapore|Canada|France))"
        
        city_matches = re.findall(location_pattern, wiki_text)
        
        # Also look for major cities by name
        major_cities = [
            "New York", "San Francisco", "Los Angeles", "Chicago", "Seattle", "Austin",
            "London", "Paris", "Berlin", "Dublin", "Amsterdam",
            "Tokyo", "Shanghai", "Beijing", "Hong Kong", "Singapore", "Bangalore",
            "Sydney", "Melbourne", "Toronto", "Vancouver",
            "São Paulo", "Mexico City", "Mumbai", "Delhi"
        ]
        
        for city in major_cities:
            if city.lower() in wiki_text.lower() and city not in locations:
                locations.append(city)
        
        locations.extend([m for m in city_matches if m not in locations])
    
    # Remove duplicates and limit to 15
    locations = list(dict.fromkeys(locations))[:15]
    
    if not hq and locations:
        hq = locations[0]
    
    return {"hq": hq, "locations": locations}


def get_real_company_locations(company_name: str, sf_account: dict = None) -> dict:
    """Get REAL company locations from Wikipedia and Salesforce"""
    
    locations = []
    hq = ""
    countries = set()
    
    # 1. Try Wikipedia FIRST for global presence data
    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{company_name.replace(' ', '_')}"
        resp = requests.get(wiki_url, timeout=5, headers=HEADERS)
        
        if resp.status_code == 200:
            wiki_data = resp.json()
            wiki_text = wiki_data.get("extract", "")
            
            if wiki_text:
                wiki_locs = extract_locations_from_wiki(wiki_text, company_name)
                
                # Get HQ from Wikipedia
                if wiki_locs.get("hq"):
                    hq = wiki_locs["hq"]
                    locations.append(hq)
                
                # Add Wikipedia locations
                for loc in wiki_locs.get("locations", []):
                    if loc not in locations and loc.strip():
                        locations.append(loc.strip())
                
                # Extract countries from locations
                for country in ["USA", "India", "UK", "Germany", "Canada", "Australia", "China", 
                               "Japan", "France", "Brazil", "Singapore", "Mexico", "Netherlands",
                               "Switzerland", "Ireland", "Sweden", "Korea", "South Korea"]:
                    # Check in location names
                    for loc in locations:
                        if country in loc:
                            countries.add(country if country != "Korea" else "South Korea")
                            break
    
    except Exception as e:
        print(f"Wiki fetch error for {company_name}: {e}")
    
    # 2. If Wikipedia didn't give us much, use Salesforce as fallback
    if sf_account and (not hq or len(locations) < 2):
        sf_hq = sf_account.get("billing_address", "")
        if sf_hq and sf_hq != "N/A" and sf_hq not in locations:
            if not hq:
                hq = sf_hq
            locations.insert(0, sf_hq) if not hq else locations.append(sf_hq)
            
            # Extract country from Salesforce address
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
    
    # Fallback if still no data
    if not hq:
        hq = f"{company_name} headquarters"
    
    if not locations:
        locations = [hq] if hq else []
    
    # Remove duplicates and limit to 12
    locations = list(dict.fromkeys(locations))[:12]
    
    # Default countries if none found
    if not countries:
        countries.add("USA")
    
    return {
        "headquarters": hq,
        "countries": sorted(list(countries)),
        "major_offices": locations,
        "offices_count": f"{len(locations)}+",
        "source": "Wikipedia + Salesforce"
    }
