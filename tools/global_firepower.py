import requests
import time
from bs4 import BeautifulSoup

def get_country_firepower(country: str) -> dict:
    """
    Scrape military data from Global Firepower
    Real numbers! Official data!
    """
    
    print(f"🔥 Fetching Global Firepower data: {country}")
    
    # Format country name for URL
    country_url = country.lower().replace(" ", "-")
    
    url = f"https://www.globalfirepower.com/country-military-strength-detail.php?country_id={country_url}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    }

    try:
        time.sleep(2)

        session = requests.Session()
        response = session.get(
            url,
            headers=headers,
            timeout=10
        )
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code}")
            return {}
        
        soup = BeautifulSoup(response.text, "lxml")
        
        data = {}
        
        # Get power index
        power_index = soup.find("div", {"class": "powerIndex"})
        if power_index:
            data["power_index"] = power_index.text.strip()
        
        # Get all stats
        stat_blocks = soup.find_all("div", {"class": "borderVerticalLeft"})
        
        for block in stat_blocks:
            label = block.find("span", {"class": "textWhite"})
            value = block.find("span", {"class": "textRed"})
            
            if label and value:
                key = label.text.strip().lower().replace(" ", "_")
                data[key] = value.text.strip()
        
        # Debug: see actual HTML structure
        print(f"Page length: {len(response.text)}")
        print(f"Sample HTML: {response.text[2000:3000]}")
        print(f"✅ Got {len(data)} data points!")
        return data
        
    except Exception as e:
        print(f"❌ Scraping error: {e}")
        return {}


def get_military_rank(country: str) -> str:
    """Get country's global military rank"""
    
    try:
        url = "https://www.globalfirepower.com/countries-listing.php"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "lxml")
        
        countries = soup.find_all("div", {"class": "countryName"})
        
        for i, c in enumerate(countries):
            if country.lower() in c.text.lower():
                print(f"✅ {country} rank: #{i+1}")
                return f"#{i+1}"
                
        return "Not ranked"
        
    except Exception as e:
        print(f"❌ Ranking error: {e}")
        return "Unknown"


def test_firepower():
    """Test Global Firepower scraper"""
    
    print("🧪 Testing Global Firepower...")
    print("="*50)
    
    # Test with UAE
    data = get_country_firepower("united-arab-emirates")
    
    print(f"\n📊 UAE Military Data:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    print("\n🏆 Getting rank...")
    rank = get_military_rank("United Arab Emirates")
    print(f"UAE Global Rank: {rank}")


if __name__ == "__main__":
    test_firepower()