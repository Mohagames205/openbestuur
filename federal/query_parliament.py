#!/usr/bin/env python3
"""
Utility script to query parliament members data.
Demonstrates how to filter members by party and access their information.
"""

import json
import sys
from typing import List, Dict

def load_members(json_file='federal/parliament_members.json') -> Dict:
    """Load parliament members from JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file} not found. Run fed_scrape_parliament.py first.", file=sys.stderr)
        sys.exit(1)

def get_members_by_party(party_name: str, data: Dict) -> List[Dict]:
    """
    Filter members by party name.
    
    Args:
        party_name: Name of the party (case-insensitive)
        data: The full parliament data dictionary
        
    Returns:
        List of members belonging to the specified party
    """
    party_name_lower = party_name.lower()
    return [
        member for member in data['members']
        if member['party'].lower() == party_name_lower
    ]

def list_all_parties(data: Dict) -> List[str]:
    """Get a list of all unique parties."""
    parties = set(member['party'] for member in data['members'])
    return sorted(parties)

def display_member(member: Dict):
    """Display a single member's information."""
    print(f"  Name: {member['name']}")
    print(f"  Party: {member['party']}")
    print(f"  Picture: {member['picture_url']}")
    print(f"  Profile: {member['profile_url']}")
    print()

def main():
    """Main function for the utility script."""
    if len(sys.argv) > 1:
        party_filter = sys.argv[1]
    else:
        party_filter = None
    
    # Load data
    data = load_members()
    
    print(f"Total parliament members: {data['total_members']}\n")
    
    if party_filter:
        # Filter by party
        members = get_members_by_party(party_filter, data)
        if members:
            print(f"Members of {party_filter} ({len(members)}):")
            print("=" * 50)
            for member in members:
                display_member(member)
        else:
            print(f"No members found for party: {party_filter}")
            print("\nAvailable parties:")
            for party in list_all_parties(data):
                print(f"  - {party}")
    else:
        # Show all parties and their member counts
        print("Available parties:")
        print("=" * 50)
        parties = list_all_parties(data)
        for party in parties:
            members = get_members_by_party(party, data)
            print(f"  {party}: {len(members)} members")
        
        print("\nUsage: python3 federal/query_parliament.py [PARTY_NAME]")
        print("Example: python3 federal/query_parliament.py N-VA")

if __name__ == "__main__":
    main()
