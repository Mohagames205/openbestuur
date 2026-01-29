#!/usr/bin/env python3
"""
Parser for extracting nominative votes from Belgian municipal council meeting minutes.

This module parses council meeting minutes (gemeenteraad notulen) to extract:
- Agenda item numbers and titles
- Voting results (approved/rejected)
- Individual votes (voor/tegen/onthouding) with names
- Outputs structured JSON format
"""

import re
import json
import sys
from typing import List, Dict, Any, Optional


class VoteParser:
    """Parser for extracting nominative votes from council meeting minutes."""
    
    def __init__(self):
        self.agenda_items = []
        self.current_item = None
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a council meeting minutes file and extract voting data.
        
        Args:
            file_path: Path to the minutes file (text format)
            
        Returns:
            List of dictionaries containing agenda items with vote data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse the content of council meeting minutes.
        
        Args:
            content: Full text content of the minutes
            
        Returns:
            List of dictionaries containing agenda items with vote data
        """
        lines = content.split('\n')
        self.agenda_items = []
        self.current_item = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for agenda item number (standalone number on a line)
            if re.match(r'^[0-9]+$', line):
                item_number = line
                
                # Look ahead for title (which may span multiple lines)
                title_lines = []
                j = i + 1
                while j < len(lines) and lines[j].strip() and lines[j].strip() != 'STATUS':
                    title_lines.append(lines[j].strip())
                    # Check if this line contains the ID in parentheses
                    if re.search(r'\([^)]+\)$', lines[j].strip()):
                        break
                    j += 1
                
                # Combine title lines and extract title and ID
                if title_lines:
                    full_title = ' '.join(title_lines)
                    # Extract title and ID from format: "Title (ID)"
                    title_match = re.match(r'^(.+?)\s*\(([^)]+)\)$', full_title)
                    if title_match:
                        title = title_match.group(1).strip()
                        item_id = title_match.group(2).strip()
                        
                        self.current_item = {
                            'item_number': item_number,
                            'item_id': item_id,
                            'title': title,
                            'status': None,
                            'votes': {
                                'voor': {'count': 0, 'names': []},
                                'tegen': {'count': 0, 'names': []},
                                'onthouding': {'count': 0, 'names': []}
                            }
                        }
                        i = j  # Jump to after the title
            
            # Check for STATUS line (indicates start of voting section)
            elif line == 'STATUS' and self.current_item:
                # Look ahead for voting results
                if i + 1 < len(lines):
                    status_line = lines[i + 1].strip()
                    
                    # Check if this is an electronic vote
                    if 'elektronische stemming' in status_line.lower():
                        self.current_item['status'] = self._extract_status(status_line)
                        
                        # Parse vote details starting from next line
                        i = self._parse_vote_details(lines, i + 2)
                        
                        # Save the completed item
                        if self.current_item:
                            self.agenda_items.append(self.current_item)
                            self.current_item = None
                        continue
            
            i += 1
        
        return self.agenda_items
    
    def _extract_status(self, status_line: str) -> str:
        """Extract the decision status from the status line."""
        if 'goedgekeurd' in status_line.lower():
            return 'Goedgekeurd'
        elif 'afgekeurd' in status_line.lower() or 'verworpen' in status_line.lower():
            return 'Afgekeurd'
        else:
            return 'Onbekend'
    
    def _parse_vote_details(self, lines: List[str], start_idx: int) -> int:
        """
        Parse the vote details (voor/tegen/onthouding) from the lines.
        
        Args:
            lines: All lines from the document
            start_idx: Index to start parsing from
            
        Returns:
            Index of the last processed line
        """
        i = start_idx
        current_vote_type = None
        names_buffer = []  # Buffer to collect name fragments
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Stop if we hit the next section (like page headers or next sections)
            if line in ['BESCHRIJVING', 'BESLUIT', 'BIJLAGEN']:
                break
            if re.match(r'^[0-9]+$', line):
                break
            # Skip page headers/footers and other metadata
            if any(skip in line for skip in [
                'Notulen van de gemeenteraad',
                'Stad Leuven',
                'Professor Van Overstraetenplein',
                'pagina',
                'van 155'
            ]):
                i += 1
                continue
            
            # Check for vote type line
            # Pattern can be either:
            # - X stem(men) voor: names
            # - X onthouding(en): names (without stem(men))
            vote_match = re.match(r'^-\s*(\d+)\s*(?:stem\(men\)\s+)?(voor|tegen|onthouding(?:\(en\))?)\s*:\s*(.*)$', line)
            if vote_match:
                # First, process any buffered names from previous vote type
                if current_vote_type and names_buffer:
                    all_names_str = ' '.join(names_buffer)
                    names = self._parse_names(all_names_str)
                    if current_vote_type in self.current_item['votes']:
                        self.current_item['votes'][current_vote_type]['names'] = names
                    names_buffer = []
                
                count = int(vote_match.group(1))
                vote_type = vote_match.group(2).lower()
                # Normalize 'onthouding(en)' to just 'onthouding'
                if vote_type.startswith('onthouding'):
                    vote_type = 'onthouding'
                names_str = vote_match.group(3).strip()
                
                current_vote_type = vote_type
                
                # Start collecting names for this vote type
                if names_str:
                    names_buffer.append(names_str)
                
                if vote_type in self.current_item['votes']:
                    self.current_item['votes'][vote_type]['count'] = count
            
            # Check if this is a continuation line with more names
            elif current_vote_type and line and not line.startswith('-'):
                # This could be a continuation of names from previous line
                # Check if it looks like it contains names (contains semicolon or looks like a name)
                if ';' in line or re.search(r'^[A-Z]', line):
                    # Skip lines that look like metadata
                    if not any(skip in line for skip in [
                        'Notulen van de gemeenteraad',
                        'Stad Leuven',
                        'Professor Van Overstraetenplein',
                        'pagina',
                        'van 155',
                        '3000 Leuven'
                    ]):
                        names_buffer.append(line)
            
            i += 1
        
        # Process any remaining buffered names
        if current_vote_type and names_buffer:
            all_names_str = ' '.join(names_buffer)
            names = self._parse_names(all_names_str)
            if current_vote_type in self.current_item['votes']:
                self.current_item['votes'][current_vote_type]['names'] = names
        
        return i
    
    def _parse_names(self, names_str: str) -> List[str]:
        """
        Parse names from a semicolon-separated string.
        
        Args:
            names_str: String containing names separated by semicolons
            
        Returns:
            List of individual names
        """
        if not names_str:
            return []
        
        # Remove any metadata that might have slipped through
        metadata_patterns = [
            r'Professor Van Overstraetenplein.*',
            r'Notulen van de gemeenteraad.*',
            r'Stad Leuven.*',
            r'pagina \d+ van \d+.*',
            r'\d{4} Leuven.*'
        ]
        
        for pattern in metadata_patterns:
            names_str = re.sub(pattern, '', names_str)
        
        # Split by semicolon and clean up each name
        names = [name.strip() for name in names_str.split(';') if name.strip()]
        
        # Filter out any remaining non-name entries
        filtered_names = []
        for name in names:
            # Skip if it looks like metadata
            if any(skip in name for skip in [
                'Notulen',
                'Stad Leuven',
                'Professor',
                'pagina',
                'van 155'
            ]):
                continue
            # Only include if it looks like a proper name (contains letters)
            if re.search(r'[A-Za-z]', name):
                filtered_names.append(name)
        
        return filtered_names
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert parsed agenda items to JSON format.
        
        Args:
            indent: Number of spaces for JSON indentation
            
        Returns:
            JSON string representation
        """
        output = {
            'total_items': len(self.agenda_items),
            'items_with_votes': sum(1 for item in self.agenda_items 
                                   if item['votes']['voor']['count'] > 0 or 
                                      item['votes']['tegen']['count'] > 0 or 
                                      item['votes']['onthouding']['count'] > 0),
            'agenda_items': self.agenda_items
        }
        
        return json.dumps(output, indent=indent, ensure_ascii=False)
    
    def save_json(self, output_path: str, indent: int = 2):
        """
        Save parsed data to a JSON file.
        
        Args:
            output_path: Path to output JSON file
            indent: Number of spaces for JSON indentation
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json(indent=indent))
        
        print(f"✓ Saved {len(self.agenda_items)} agenda items to {output_path}")


def main():
    """Main function to parse council meeting minutes."""
    if len(sys.argv) < 2:
        print("Usage: python3 parse_votes.py <input_file> [output_file]")
        print("\nExample:")
        print("  python3 parse_votes.py output.txt votes.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'votes.json'
    
    print(f"Parsing votes from: {input_file}")
    
    parser = VoteParser()
    try:
        items = parser.parse_file(input_file)
        
        print(f"\n✓ Successfully parsed {len(items)} agenda items")
        
        # Print summary
        items_with_votes = sum(1 for item in items 
                              if item['votes']['voor']['count'] > 0 or 
                                 item['votes']['tegen']['count'] > 0 or 
                                 item['votes']['onthouding']['count'] > 0)
        print(f"✓ Found {items_with_votes} items with voting data")
        
        # Save to JSON
        parser.save_json(output_file)
        
        # Print sample
        if items:
            print(f"\nSample item:")
            print(f"  Item {items[0]['item_number']}: {items[0]['title'][:60]}...")
            print(f"  Status: {items[0]['status']}")
            print(f"  Votes - Voor: {items[0]['votes']['voor']['count']}, "
                  f"Tegen: {items[0]['votes']['tegen']['count']}, "
                  f"Onthouding: {items[0]['votes']['onthouding']['count']}")
    
    except FileNotFoundError:
        print(f"✗ Error: File '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error parsing file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
