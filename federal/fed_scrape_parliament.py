from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import json
import sys
from urllib.error import URLError
from datetime import datetime

def scrape_parliament_members(url):
    """
    Scrape Belgian parliament members from the Chamber of Representatives website.
    
    Args:
        url: The URL to scrape parliament members from
        
    Returns:
        A list of dictionaries containing member information
    """
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html_page = urlopen(req, timeout=30).read()
        soup = BeautifulSoup(html_page, "html.parser")
    except URLError as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        print("Using local test data instead...", file=sys.stderr)
        # Fallback to local test data for development
        try:
            with open('test_data/sample_parliament.html', 'r') as f:
                html_page = f.read()
            soup = BeautifulSoup(html_page, 'html.parser')
        except FileNotFoundError:
            print("Error: Could not load test data either", file=sys.stderr)
            return []
    
    members = []
    
    # Find all table rows in the page
    table = soup.find('table')
    if not table:
        print("Error: No table found in HTML", file=sys.stderr)
        return []
    
    rows = table.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        
        # Skip rows that don't have the expected structure
        if len(cells) < 3:
            continue
        
        member = {}
        
        # Extract picture URL from first cell
        img = cells[0].find('img')
        if img and img.get('src'):
            img_url = img.get('src')
            # Make relative URLs absolute
            if not img_url.startswith('http'):
                img_url = 'https://www.dekamer.be' + ('' if img_url.startswith('/') else '/') + img_url
            member['picture_url'] = img_url
        else:
            member['picture_url'] = None
        
        # Extract name and profile URL from second cell
        link = cells[1].find('a')
        if link:
            member['name'] = link.get_text().strip()
            profile_url = link.get('href')
            # Make relative URLs absolute
            if profile_url and not profile_url.startswith('http'):
                base_url = 'https://www.dekamer.be/kvvcr/'
                member['profile_url'] = base_url + profile_url
            else:
                member['profile_url'] = profile_url
        else:
            # If no link, just get text from cell
            member['name'] = cells[1].get_text().strip()
            member['profile_url'] = None
        
        # Extract party from third cell
        member['party'] = cells[2].get_text().strip()
        
        # Only add member if we got at least a name
        if member.get('name'):
            members.append(member)
    
    return members

def save_to_json(members, output_file='federal/parliament_members.json'):
    """
    Save parliament members to a JSON file.
    
    Args:
        members: List of member dictionaries
        output_file: Path to output JSON file
    """
    # Sort members by party for easier API filtering
    members_sorted = sorted(members, key=lambda x: x.get('party', ''))
    
    output_data = {
        'total_members': len(members),
        'last_updated': datetime.now().isoformat(),
        'members': members_sorted
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(members)} members to {output_file}")
    
    # Print summary by party
    parties = {}
    for member in members:
        party = member.get('party', 'Unknown')
        parties[party] = parties.get(party, 0) + 1
    
    print("\nMembers by party:")
    for party in sorted(parties.keys()):
        print(f"  {party}: {parties[party]}")

def main():
    """Main function to scrape and save parliament members."""
    url = "https://www.dekamer.be/kvvcr/showpage.cfm?section=/depute&language=nl&cfm=cvlist54.cfm?legis=56&today=y"
    
    print(f"Scraping parliament members from: {url}")
    members = scrape_parliament_members(url)
    
    if members:
        save_to_json(members)
        print(f"\n✓ Successfully scraped {len(members)} parliament members")
    else:
        print("✗ No members found", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()