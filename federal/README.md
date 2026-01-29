# Federal Parliament Tools

This module contains tools for scraping and parsing Belgian federal parliament (Chamber of Representatives / De Kamer) data.

## Files

- **`fed_scrape_parliament.py`**: Scraper that fetches parliament member data
- **`query_parliament.py`**: Utility script to query and filter the scraped member data
- **`parse_plenary_votes.py`**: Parser for extracting nominative votes from plenary session HTML files
- **`parliament_members.json`**: Output file containing structured parliament member data
- **`sample_plenary_votes.html`**: Sample HTML file showing expected format for voting data

## Features

### 1. Parliament Member Scraper

Scrapes Belgian federal parliament members from the Chamber of Representatives (De Kamer) website.

**Usage:**
```bash
python3 federal/fed_scrape_parliament.py
```

This will:
1. Fetch the list of parliament members from https://www.dekamer.be
2. Extract member information (name, party, picture URL, profile URL)
3. Save the data to `federal/parliament_members.json`

### 2. Query Parliament Members

List all parties and their member counts:
```bash
python3 federal/query_parliament.py
```

Filter members by party:
```bash
python3 federal/query_parliament.py N-VA
python3 federal/query_parliament.py "CD&V"
```

### 3. Parse Plenary Votes (NEW)

Extract nominative votes (nominatieve stemmen) from federal parliament plenary session HTML files.

**Usage:**
```bash
python3 federal/parse_plenary_votes.py <html_file> [output_json]
```

**Example:**
```bash
python3 federal/parse_plenary_votes.py plenumvergadering_2025.html federal/votes.json
```

**Features:**
- Extracts voting items/proposals from HTML
- Parses individual nominative votes (voor/tegen/onthouding)
- Links votes to deputy names with party affiliations
- Outputs structured JSON format
- Handles multiple HTML formats (tables, paragraphs, divs)

**Expected HTML Format:**

The parser can handle various HTML structures:

1. **Paragraph format with counts:**
```html
<p><strong>Voor (78):</strong> Name1; Name2; Name3</p>
<p><strong>Tegen (12):</strong> Name4; Name5</p>
<p><strong>Onthouding (5):</strong> Name6; Name7</p>
```

2. **Table format:**
```html
<table>
  <tr><td>Voor</td><td>Name1; Name2; Name3</td></tr>
  <tr><td>Tegen</td><td>Name4; Name5</td></tr>
</table>
```

**Output Format:**
```json
{
  "total_items": 3,
  "items_with_votes": 3,
  "voting_items": [
    {
      "title": "Stemming 01 - Wetsvoorstel betreffende klimaatbeleid",
      "votes": {
        "voor": {
          "count": 20,
          "names": ["Jan Jambon (N-VA)", "Alexander De Croo (Open VLD)", ...]
        },
        "tegen": {
          "count": 5,
          "names": ["Theo Francken (N-VA)", ...]
        },
        "onthouding": {
          "count": 2,
          "names": ["Kristof Calvo (Groen)", ...]
        }
      }
    }
  ]
}
```

## Installation

### Dependencies

```bash
pip install beautifulsoup4
```

## Output Format (Member Data)

The parliament members JSON has the following structure:

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

## Use Cases

- **Transparency Tools**: Track how federal deputies vote on legislation
- **Political Analysis**: Analyze voting patterns, party discipline, coalition behavior
- **Civic Engagement**: Help citizens understand their representatives' voting records
- **Research**: Study legislative decision-making in Belgian federal parliament
- **Journalism**: Data-driven political reporting

## Data Sources

- **Parliament Members**: https://www.dekamer.be
- **Plenary Votes**: HTML files from plenary session records (plenumvergadering)

