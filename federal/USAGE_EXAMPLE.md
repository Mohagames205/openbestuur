# Usage Example: Federal Parliament Vote Parser

## Quick Start

Parse voting data from a federal parliament plenary session HTML file:

```bash
python3 federal/parse_plenary_votes.py plenumvergadering_2025.html federal/votes_output.json
```

## Example with Sample Data

Using the included sample file:

```bash
python3 federal/parse_plenary_votes.py federal/sample_plenary_votes.html federal/sample_output.json
```

## Output Format

The parser generates JSON with this structure:

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
          "names": [
            "Jan Jambon (N-VA)",
            "Alexander De Croo (Open VLD)",
            "Bart De Wever (N-VA)",
            ...
          ]
        },
        "tegen": {
          "count": 4,
          "names": [
            "Theo Francken (N-VA)",
            ...
          ]
        },
        "onthouding": {
          "count": 5,
          "names": [
            "Kristof Calvo (Groen)",
            ...
          ]
        }
      }
    }
  ]
}
```

## Use Cases

### 1. Analyze Voting Patterns

```python
import json

with open('federal/votes_output.json', 'r') as f:
    data = json.load(f)

# Count votes by party
party_votes = {}
for item in data['voting_items']:
    for name in item['votes']['voor']['names']:
        # Extract party from "Name (Party)" format
        if '(' in name:
            party = name.split('(')[-1].replace(')', '').strip()
            party_votes[party] = party_votes.get(party, 0) + 1

print("Votes by party:", party_votes)
```

### 2. Track Individual Deputy Votes

```python
# Find all items where a specific deputy voted
deputy_name = "Jan Jambon"
deputy_votes = []

for item in data['voting_items']:
    for vote_type in ['voor', 'tegen', 'onthouding']:
        if any(deputy_name in name for name in item['votes'][vote_type]['names']):
            deputy_votes.append({
                'title': item['title'],
                'vote': vote_type
            })

print(f"{deputy_name} voted on {len(deputy_votes)} items")
```

### 3. Export to CSV

```python
import csv

with open('votes.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Title', 'Deputy', 'Vote'])
    
    for item in data['voting_items']:
        for vote_type in ['voor', 'tegen', 'onthouding']:
            for name in item['votes'][vote_type]['names']:
                writer.writerow([item['title'], name, vote_type])
```

## Expected HTML Format

The parser handles various HTML structures:

### Format 1: Paragraphs with vote counts
```html
<div class="voting-section">
  <h3>Stemming 01 - Title</h3>
  <p><strong>Voor (20):</strong> Name1; Name2; Name3</p>
  <p><strong>Tegen (5):</strong> Name4; Name5</p>
  <p><strong>Onthouding (2):</strong> Name6; Name7</p>
</div>
```

### Format 2: Tables
```html
<table>
  <tr><td>Voor</td><td>Name1; Name2; Name3</td></tr>
  <tr><td>Tegen</td><td>Name4; Name5</td></tr>
  <tr><td>Onthouding</td><td>Name6</td></tr>
</table>
```

## Tips

1. **Name Format**: Names are expected in "Firstname Lastname (Party)" format
2. **Separators**: Names should be separated by semicolons (`;`)
3. **Vote Types**: Recognized as "Voor", "Tegen", and "Onthouding" (case-insensitive)
4. **Multiple Sections**: The parser automatically detects and processes multiple voting items in a single HTML file

## Troubleshooting

**Problem**: Parser returns 0 items
- **Solution**: Check that your HTML contains recognizable voting sections with headers like "Stemming 01" or tables with vote data

**Problem**: Names are not split correctly
- **Solution**: Ensure names are separated by semicolons in the HTML

**Problem**: Duplicate items in output
- **Solution**: This should be fixed in the latest version. If still occurring, the HTML may have nested voting sections.
