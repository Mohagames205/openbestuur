#!/usr/bin/env python3
"""
Parser for extracting nominative votes from Belgian federal parliament plenary sessions.

This module parses HTML files from federal parliament (De Kamer) plenary sessions to extract:
- Voting items/proposals
- Individual nominative votes (voor/tegen/onthouding) with deputy names
- Outputs structured JSON format

Usage:
    python3 federal/parse_plenary_votes.py <html_file> [output_json]
"""

import re
import json
import sys
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


class PlenaryVoteParser:
    """Parser for extracting nominative votes from federal parliament plenary sessions."""
    
    def __init__(self):
        self.voting_items = []
    
    def parse_html_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse an HTML file containing plenary session voting data.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            List of dictionaries containing voting items with individual votes
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return self.parse_html_content(html_content)
    
    def parse_html_content(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content from a plenary session document.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            List of dictionaries containing voting items with individual votes
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        self.voting_items = []
        
        # Strategy 1: Look for voting sections/tables with class/id patterns
        # Common patterns: voting-table, vote-result, stemming, etc.
        voting_sections = self._find_voting_sections(soup)
        
        if voting_sections:
            for section in voting_sections:
                item = self._parse_voting_section(section)
                if item:
                    self.voting_items.append(item)
        else:
            # Strategy 2: Look for text patterns indicating votes
            # Search for "nominatieve stemming", "voor:", "tegen:", etc.
            self._parse_by_text_patterns(soup)
        
        return self.voting_items
    
    def _find_voting_sections(self, soup: BeautifulSoup) -> List:
        """
        Find sections in HTML that likely contain voting data.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of HTML elements containing voting sections
        """
        sections = []
        
        # Look for common voting-related classes/ids
        voting_keywords = [
            'voting', 'vote', 'stemming', 'nominatief',
            'vote-result', 'voting-result', 'roll-call'
        ]
        
        for keyword in voting_keywords:
            # Search by class
            sections.extend(soup.find_all(class_=re.compile(keyword, re.I)))
            # Search by id
            sections.extend(soup.find_all(id=re.compile(keyword, re.I)))
        
        # Look for tables that might contain voting data
        tables = soup.find_all('table')
        for table in tables:
            # Check if table contains voting-related text
            table_text = table.get_text().lower()
            if any(word in table_text for word in ['voor', 'tegen', 'onthouding', 'stemming']):
                sections.append(table)
        
        # Look for divs/sections with voting headers
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])
        for header in headers:
            header_text = header.get_text().lower()
            if any(word in header_text for word in ['stemming', 'vote', 'nominatief']):
                # Get the parent section or next siblings that contain the voting data
                parent = header.find_parent(['div', 'section', 'article'])
                if parent:
                    sections.append(parent)
        
        return sections
    
    def _parse_voting_section(self, section) -> Optional[Dict[str, Any]]:
        """
        Parse a single voting section to extract vote data.
        
        Args:
            section: BeautifulSoup element containing a voting section
            
        Returns:
            Dictionary with voting item data, or None if parsing fails
        """
        # Extract title/proposal
        title = self._extract_title(section)
        
        # Extract votes
        votes = self._extract_votes(section)
        
        if title or votes['voor']['count'] > 0 or votes['tegen']['count'] > 0:
            return {
                'title': title,
                'votes': votes
            }
        
        return None
    
    def _extract_title(self, section) -> str:
        """Extract the title/proposal from a voting section."""
        # Look for headers
        header = section.find(['h1', 'h2', 'h3', 'h4', 'h5'])
        if header:
            return header.get_text().strip()
        
        # Look for elements with title-like classes
        title_elem = section.find(class_=re.compile('title|heading|voorstel|proposal', re.I))
        if title_elem:
            return title_elem.get_text().strip()
        
        # Fallback: use first paragraph or strong text
        first_strong = section.find('strong')
        if first_strong:
            return first_strong.get_text().strip()
        
        return "Unknown Proposal"
    
    def _extract_votes(self, section) -> Dict[str, Any]:
        """
        Extract vote counts and names from a section.
        
        Returns:
            Dictionary with voor, tegen, and onthouding votes
        """
        votes = {
            'voor': {'count': 0, 'names': []},
            'tegen': {'count': 0, 'names': []},
            'onthouding': {'count': 0, 'names': []}
        }
        
        text = section.get_text()
        
        # Pattern 1: "Voor (78): Name1; Name2; Name3" format (with count in parentheses)
        voor_match = re.search(r'Voor\s*\(\d+\)\s*:\s*(.+?)(?=Tegen|Onthouding|$)', text, re.I | re.DOTALL)
        if voor_match:
            names = self._parse_name_list(voor_match.group(1))
            votes['voor']['names'] = names
            votes['voor']['count'] = len(names)
        
        # Pattern 2: "Tegen (12): Name1; Name2" format (with count in parentheses)
        tegen_match = re.search(r'Tegen\s*\(\d+\)\s*:\s*(.+?)(?=Onthouding|Voor|$)', text, re.I | re.DOTALL)
        if tegen_match:
            names = self._parse_name_list(tegen_match.group(1))
            votes['tegen']['names'] = names
            votes['tegen']['count'] = len(names)
        
        # Pattern 3: "Onthouding (5): Name1; Name2" format (with count in parentheses)
        onthouding_match = re.search(r'Onthoud(?:ing|en)\s*\(\d+\)\s*:\s*(.+?)(?=Voor|Tegen|$)', text, re.I | re.DOTALL)
        if onthouding_match:
            names = self._parse_name_list(onthouding_match.group(1))
            votes['onthouding']['names'] = names
            votes['onthouding']['count'] = len(names)
        
        # Alternative: Look for tables with vote data
        if votes['voor']['count'] == 0 and votes['tegen']['count'] == 0:
            table_votes = self._extract_votes_from_table(section)
            # Only use table votes if we actually found something
            if table_votes['voor']['count'] > 0 or table_votes['tegen']['count'] > 0:
                votes = table_votes
        
        return votes
    
    def _extract_votes_from_table(self, section) -> Dict[str, Any]:
        """Extract votes from HTML tables."""
        votes = {
            'voor': {'count': 0, 'names': []},
            'tegen': {'count': 0, 'names': []},
            'onthouding': {'count': 0, 'names': []}
        }
        
        tables = section.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            current_vote_type = None
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                
                # Check if first cell indicates vote type
                first_cell_text = cells[0].get_text().strip().lower()
                
                if 'voor' in first_cell_text:
                    current_vote_type = 'voor'
                elif 'tegen' in first_cell_text:
                    current_vote_type = 'tegen'
                elif 'onthoud' in first_cell_text:
                    current_vote_type = 'onthouding'
                
                # Extract names from cells
                if current_vote_type:
                    for cell in cells[1:]:  # Skip first cell
                        name = cell.get_text().strip()
                        if name and len(name) > 2:  # Basic validation
                            votes[current_vote_type]['names'].append(name)
            
            # Update counts
            for vote_type in ['voor', 'tegen', 'onthouding']:
                votes[vote_type]['count'] = len(votes[vote_type]['names'])
        
        return votes
    
    def _parse_by_text_patterns(self, soup: BeautifulSoup):
        """
        Parse voting data by searching for text patterns throughout the document.
        """
        # Get all text content
        all_text = soup.get_text()
        
        # Split into logical sections (by double newlines or similar)
        sections = re.split(r'\n\s*\n', all_text)
        
        for section_text in sections:
            # Check if this section contains voting information
            if any(word in section_text.lower() for word in ['stemming', 'vote', 'voor', 'tegen']):
                # Try to extract a voting item
                item = self._parse_text_section(section_text)
                if item:
                    self.voting_items.append(item)
    
    def _parse_text_section(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a text section for voting data."""
        # Look for title (often starts with number or is in first line)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return None
        
        title = lines[0]
        
        # Extract votes
        votes = {
            'voor': {'count': 0, 'names': []},
            'tegen': {'count': 0, 'names': []},
            'onthouding': {'count': 0, 'names': []}
        }
        
        # Look for vote patterns
        voor_match = re.search(r'Voor\s*[:\-]\s*([^\n]+)', text, re.I)
        if voor_match:
            names = self._parse_name_list(voor_match.group(1))
            votes['voor']['names'] = names
            votes['voor']['count'] = len(names)
        
        tegen_match = re.search(r'Tegen\s*[:\-]\s*([^\n]+)', text, re.I)
        if tegen_match:
            names = self._parse_name_list(tegen_match.group(1))
            votes['tegen']['names'] = names
            votes['tegen']['count'] = len(names)
        
        onthouding_match = re.search(r'Onthoud(?:ing|en)\s*[:\-]\s*([^\n]+)', text, re.I)
        if onthouding_match:
            names = self._parse_name_list(onthouding_match.group(1))
            votes['onthouding']['names'] = names
            votes['onthouding']['count'] = len(names)
        
        if votes['voor']['count'] > 0 or votes['tegen']['count'] > 0:
            return {
                'title': title,
                'votes': votes
            }
        
        return None
    
    def _parse_name_list(self, name_string: str) -> List[str]:
        """
        Parse a string containing names into a list.
        
        Handles various separators: commas, semicolons, newlines, etc.
        """
        # Clean up the string first
        name_string = name_string.strip()
        
        # Try different separators
        if ';' in name_string:
            names = [n.strip() for n in name_string.split(';')]
        elif ',' in name_string:
            names = [n.strip() for n in name_string.split(',')]
        elif '\n' in name_string:
            names = [n.strip() for n in name_string.split('\n')]
        else:
            # Single name
            names = [name_string.strip()]
        
        # Filter out empty names and very short ones
        names = [n for n in names if n and len(n) > 2]
        
        # Remove numbers, counts, or other metadata
        filtered_names = []
        for name in names:
            # Skip if it looks like a count "15 stemmen" or just a number
            if re.match(r'^\d+\s*(?:stem|vote)', name, re.I):
                continue
            if re.match(r'^\d+$', name):
                continue
            # Skip empty or whitespace-only entries
            if not name or not name.strip():
                continue
            # Clean up extra whitespace
            clean_name = ' '.join(name.split())
            if clean_name:
                filtered_names.append(clean_name)
        
        return filtered_names
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert parsed voting items to JSON format.
        
        Args:
            indent: Number of spaces for JSON indentation
            
        Returns:
            JSON string representation
        """
        output = {
            'total_items': len(self.voting_items),
            'items_with_votes': sum(1 for item in self.voting_items 
                                   if item['votes']['voor']['count'] > 0 or 
                                      item['votes']['tegen']['count'] > 0),
            'voting_items': self.voting_items
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
        
        print(f"✓ Saved {len(self.voting_items)} voting items to {output_path}")


def main():
    """Main function to parse federal parliament plenary votes."""
    if len(sys.argv) < 2:
        print("Usage: python3 federal/parse_plenary_votes.py <html_file> [output_json]")
        print("\nExample:")
        print("  python3 federal/parse_plenary_votes.py plenumvergadering_2025.html votes.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'federal/plenary_votes.json'
    
    print(f"Parsing federal parliament plenary votes from: {input_file}")
    
    parser = PlenaryVoteParser()
    try:
        items = parser.parse_html_file(input_file)
        
        print(f"\n✓ Successfully parsed {len(items)} voting items")
        
        # Print summary
        items_with_votes = sum(1 for item in items 
                              if item['votes']['voor']['count'] > 0 or 
                                 item['votes']['tegen']['count'] > 0)
        print(f"✓ Found {items_with_votes} items with voting data")
        
        # Save to JSON
        parser.save_json(output_file)
        
        # Print sample if available
        if items:
            print(f"\nSample item:")
            print(f"  Title: {items[0]['title'][:80]}...")
            print(f"  Votes - Voor: {items[0]['votes']['voor']['count']}, "
                  f"Tegen: {items[0]['votes']['tegen']['count']}, "
                  f"Onthouding: {items[0]['votes']['onthouding']['count']}")
            if items[0]['votes']['voor']['names']:
                print(f"  Sample names (voor): {', '.join(items[0]['votes']['voor']['names'][:3])}...")
    
    except FileNotFoundError:
        print(f"✗ Error: File '{input_file}' not found", file=sys.stderr)
        print(f"\nPlease provide the HTML file from the federal parliament plenary session.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error parsing file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
