from typing import Dict, Optional

from classifier import CategoryMatch
import re

# Catpuccin color palette
CATPPUCCIN_COLORS = {
    "rosewater": "#f5e0dc",
    "flamingo": "#f2cdcd",
    "pink": "#f5c2e7",
    "mauve": "#cba6f7",
    "red": "#f38ba8",
    "maroon": "#eba0ac",
    "peach": "#fab387",
    "yellow": "#f9e2af",
    "green": "#a6e3a1",
    "teal": "#94e2d5",
    "sky": "#89dceb",
    "sapphire": "#74c7ec",
    "blue": "#89b4fa",
    "lavender": "#b4befe",
    "text": "#4c4f69",
    "surface0": "#ccd0da",
    "base": "#eff1f5",
}

class HtmlFormatter:
  def run(self, text: str, ttps: list[CategoryMatch], capacities: list[CategoryMatch], 
        stix_url: str,
        prev_ttps: Optional[list[CategoryMatch]] = None, prev_capacities: Optional[list[CategoryMatch]] = None,
        summary: Optional[str] = None):
    html = []

    html.append('<script src="https://unpkg.com/stixview/dist/stixview.bundle.js" type="text/javascript"></script>')
    html.append("<h2>Stix2 Graph</h2>")
    html.append(f"""
      <div data-stix-url="{stix_url}"
        data-show-sidebar=true
        data-enable-mouse-zoom=false
        data-graph-height=300>
      </div>
    """)
    
    # Add comparison section if we have previous data  
    # Add CSS styles for comparison section
    html.append(f"""
    <style>
      .comparison-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin-bottom: 20px;
      }}
      .comparison-box {{
        flex: 1;
        min-width: 300px;
        background-color: {CATPPUCCIN_COLORS['surface0']};
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      }}
      .comparison-title {{
        font-weight: bold;
        margin-bottom: 10px;
        color: {CATPPUCCIN_COLORS['text']};
      }}
      .added {{
        color: {CATPPUCCIN_COLORS['green']};
        font-weight: bold;
      }}
      .removed {{
        color: {CATPPUCCIN_COLORS['red']};
        font-weight: bold;
      }}
      .tag {{
        display: inline-block;
        padding: 3px 8px;
        margin: 3px;
        border-radius: 4px;
      }}
      .tag-added {{
        background-color: {CATPPUCCIN_COLORS['green']};
        // color: white;
      }}
      .tag-removed {{
        background-color: {CATPPUCCIN_COLORS['red']};
        // color: white;
      }}
      .tag-unchanged {{
        background-color: {CATPPUCCIN_COLORS['blue']};
        // color: white;
      }}
    </style>
    """)
    
    # Find new and deleted TTPs
    current_ttp_names = [t['name'] for t in ttps]
    prev_ttp_names = [t['name'] for t in prev_ttps] if prev_ttps else []
    
    new_ttps = [t for t in current_ttp_names if t not in prev_ttp_names]
    deleted_ttps = [t for t in prev_ttp_names if t not in current_ttp_names]
    unchanged_ttps = [t for t in current_ttp_names if t in prev_ttp_names]
    
    # Find new and deleted capacities
    current_capacity_names = [c['name'] for c in capacities]
    prev_capacity_names = [c['name'] for c in prev_capacities] if prev_capacities else []
    
    new_capacities = [c for c in current_capacity_names if c not in prev_capacity_names]
    deleted_capacities = [c for c in prev_capacity_names if c not in current_capacity_names]
    unchanged_capacities = [c for c in current_capacity_names if c in prev_capacity_names]

    html.append('<div class="comparison-container">')
    
    # TTPs comparison box
    html.append('<div class="comparison-box">')
    html.append('<div class="comparison-title">TTPs Comparison</div>')
    
    if new_ttps or deleted_ttps or unchanged_ttps:
      if new_ttps:
        # html.append('<div><span class="added">+ Added:</span></div>')
        html.append('<div>')
        for ttp in new_ttps:
          html.append(f'<span class="tag tag-added">{ttp}</span>')
        html.append('</div>')
      
      if deleted_ttps:
        # html.append('<div><span class="removed">- Removed:</span></div>')
        html.append('<div>')
        for ttp in deleted_ttps:
          html.append(f'<span class="tag tag-removed">{ttp}</span>')
        html.append('</div>')
      
      if unchanged_ttps:
        # html.append('<div><span>= Unchanged:</span></div>')
        html.append('<div>')
        for ttp in unchanged_ttps:
          html.append(f'<span class="tag tag-unchanged">{ttp}</span>')
        html.append('</div>')
    else:
      html.append('<div>No TTPs detected</div>')
    
    html.append('</div>')
    
    # Capacities comparison box
    html.append('<div class="comparison-box">')
    html.append('<div class="comparison-title">Capabilities Comparison</div>')
    
    if new_capacities or deleted_capacities or unchanged_capacities:
      if new_capacities:
        # html.append('<div><span class="added">+ Added:</span></div>')
        html.append('<div>')
        for cap in new_capacities:
          html.append(f'<span class="tag tag-added">{cap}</span>')
        html.append('</div>')
      
      if deleted_capacities:
        # html.append('<div><span class="removed">- Removed:</span></div>')
        html.append('<div>')
        for cap in deleted_capacities:
          html.append(f'<span class="tag tag-removed">{cap}</span>')
        html.append('</div>')
      
      if unchanged_capacities:
        # html.append('<div><span>= Unchanged:</span></div>')
        html.append('<div>')
        for cap in unchanged_capacities:
          html.append(f'<span class="tag tag-unchanged">{cap}</span>')
        html.append('</div>')
    else:
      html.append('<div>No Capabilities detected</div>')
    
    html.append('</div>')
    html.append('</div>')

    # Add summary if available
    if summary:
      html.append("<h2>Changes Since Last Analysis</h2>")
      html.append(f"<p>{summary.replace('\n', '<br/>')}</p>")

    html.append("<h2>Details</h2>")
    html.append("<h3>Found Capabilities</h3>")
    html.append(self.highlight_categories(text, capacities))
    
    return "".join(html)     
  

  def highlight_categories(self, text: str, categories: list[CategoryMatch], color_mode="predefined"):
    """
    Highlight capacity matches in text with HTML span tags.
    
    Args:
      text (str): The original text to highlight
      capacities (List[Capacities]): The list of capacities with their matches
      color_mode (str): The color mode to use ('hsl', 'rgb', 'predefined')
    
    Returns:
      str: HTML formatted text with highlights
    """
    # Generate a color for each capacity
    capacity_colors = {}
    all_capacity_names = list(set(cap['name'] for cap in categories))
    
    if color_mode == "hsl":
      # Generate colors evenly distributed in HSL color space
      for i, name in enumerate(all_capacity_names):
        hue = int(360 * i / len(all_capacity_names))
        capacity_colors[name] = f"hsla({hue}, 70%, 70%, 0.5)"
    elif color_mode == "rgb":
      # Generate colors using RGB values
      for i, name in enumerate(all_capacity_names):
        r = (155 + (100 * ((i * 3) % 11) // 10)) % 256 
        g = (155 + (100 * ((i * 5) % 11) // 10)) % 256
        b = (155 + (100 * ((i * 7) % 11) // 10)) % 256
        capacity_colors[name] = f"rgba({r}, {g}, {b}, 0.5)"
    else:  # predefined mode or fallback
      # Use Catpuccin colors
      predefined = [
        CATPPUCCIN_COLORS["rosewater"], CATPPUCCIN_COLORS["flamingo"], 
        CATPPUCCIN_COLORS["pink"], CATPPUCCIN_COLORS["mauve"], 
        CATPPUCCIN_COLORS["red"], CATPPUCCIN_COLORS["maroon"],
        CATPPUCCIN_COLORS["peach"], CATPPUCCIN_COLORS["yellow"], 
        CATPPUCCIN_COLORS["green"], CATPPUCCIN_COLORS["teal"],
        CATPPUCCIN_COLORS["sky"], CATPPUCCIN_COLORS["sapphire"], 
        CATPPUCCIN_COLORS["blue"], CATPPUCCIN_COLORS["lavender"]
      ]
      for i, name in enumerate(all_capacity_names):
        capacity_colors[name] = predefined[i % len(predefined)]
    
    # Create a list of all matches with their details
    all_matches = []
    for capacity in categories:
      capacity_name = capacity['name']
      color = capacity_colors.get(capacity_name, "#FF0000")
      
      for match in capacity['details']:
        start_idx = match['start']
        end_idx = match['end']
        keyword = match.get('keyword', 'unknown')
        matched_text = match.get('matched_text', text[start_idx:end_idx])
        match_type = match.get('match_type', 'unknown')
        confidence = match.get('confidence', 100)
        
        all_matches.append({
          'capacity_name': capacity_name,
          'start': start_idx,
          'end': end_idx,
          'keyword': keyword,
          'matched_text': matched_text,
          'match_type': match_type,
          'confidence': confidence,
          'color': color
        })
    
    # Group matches by their start and end positions
    grouped_matches = {}
    for match in all_matches:
      key = (match['start'], match['end'])
      if key not in grouped_matches:
        grouped_matches[key] = []
      grouped_matches[key].append(match)
    
    # Combine keywords for matches at the same position
    consolidated_matches = []
    for (start, end), matches in grouped_matches.items():
      # Use the first match as the base
      base_match = matches[0].copy()
      
      # Collect all keywords and their info
      keywords = []
      capacities_info = []
      
      for m in matches:
        keywords.append(m['keyword'])
        capacities_info.append({
          'capacity': m['capacity_name'],
          'keyword': m['keyword'],
          'match_type': m['match_type'],
          'confidence': m['confidence']
        })
      
      base_match['keywords'] = keywords
      base_match['capacities_info'] = capacities_info
      consolidated_matches.append(base_match)
    
    # Sort matches by start position and then by length (descending) for overlaps
    consolidated_matches.sort(key=lambda m: (m['start'], -(m['end'] - m['start'])))
    
    # Handle overlaps by keeping only non-overlapping matches
    used_positions = set()
    filtered_matches = []
    
    for match in consolidated_matches:
      positions = set(range(match['start'], match['end']))
      if not positions.intersection(used_positions):
        filtered_matches.append(match)
        used_positions.update(positions)

    filtered_matches = consolidated_matches
    
    # Create markers for the filtered matches
    markers = []
    for match in filtered_matches:
      # Create formatted string of all keywords
      keywords_str = ', '.join(match['keywords'])
      
      # Create formatted string for all capacities and their keywords in the tooltip
      tooltip_info = []
      for info in match['capacities_info']:
        tooltip_info.append(f"Capacity: {info['capacity']}\nKeyword: {info['keyword']}\n"
                          f"Match type: {info['match_type']}\nConfidence: {info['confidence']}%")
      
      tooltip_content = '\n\n'.join(tooltip_info)
      tooltip_content += f"\n\nMatched: {match['matched_text']}"
      
      
      start_tag = (
        f'<span class="highlight" '
        f'style="background-color: {match["color"]};" '
        f'data-capacity="{match["capacity_name"]}" '
        f'data-keywords="{keywords_str}" '
        f'data-match-type="{match["match_type"]}" '
        f'data-confidence="{match["confidence"]}" '
        f'title="{tooltip_content}">'
      )

      start_tag = start_tag.replace('\n', '{_n}')
      
      markers.append({'position': match['start'], 'is_start': True, 'tag': start_tag})
      markers.append({'position': match['end'], 'is_start': False, 'tag': '</span>'})
    
    # Sort markers by position (ends before starts at same position)
    markers.sort(key=lambda m: (m['position'], not m['is_start']))
    
    # Build the HTML output
    result = []
    last_pos = 0
    for marker in markers:
      pos = marker['position']
      if pos > last_pos:
        result.append(text[last_pos:pos])
      result.append(marker['tag'])
      last_pos = pos
    
    # Add any remaining text
    if last_pos < len(text):
      result.append(text[last_pos:])
    
    # Join the result and convert newlines to HTML breaks
    result_text = ''.join(result).replace('\n', '<br>').replace('{_n}', '\n')
      
    # # Remove multiple consecutive blank lines
    # result_text = re.sub(r'(<br>){3,}', '<br>', result_text)
      
    return result_text


