# Federal Parliament Scraper

This module scrapes Belgian federal parliament members from the Chamber of Representatives (De Kamer) website.

## Files

- **`fed_scrape_parliament.py`**: Main scraper that fetches parliament member data
- **`query_parliament.py`**: Utility script to query and filter the scraped data
- **`parliament_members.json`**: Output file containing structured parliament member data

## Usage

### Scraping Parliament Members

```bash
python3 federal/fed_scrape_parliament.py
```

This will:
1. Fetch the list of parliament members from https://www.dekamer.be
2. Extract member information (name, party, picture URL, profile URL)
3. Save the data to `federal/parliament_members.json`

### Querying Parliament Members

List all parties and their member counts:
```bash
python3 federal/query_parliament.py
```

Filter members by party:
```bash
python3 federal/query_parliament.py N-VA
python3 federal/query_parliament.py "CD&V"
```

## Output Format

The JSON output has the following structure:

```json
{
  "total_members": 150,
  "last_updated": "2026-01-29T18:30:00.123456",
  "members": [
    {
      "name": "Jan Janssens",
      "party": "N-VA",
      "picture_url": "https://www.dekamer.be/images/deputies/001.jpg",
      "profile_url": "https://www.dekamer.be/kvvcr/cvview.cfm?key=001"
    }
  ]
}
```

Members are automatically sorted by party for easier API consumption.

Install dependencies:
```bash
pip install beautifulsoup4
```
