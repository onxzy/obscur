# Configuration

The configuration system uses YAML files to define projects, sites, mirrors, and routes for web scraping.

## Default configuration: `default.yaml`

This file contains global settings for the application:

```yaml
tor:
  tmp_path: /tmp/tor_scraper     # temp folder for the scraper
  screenshot_quality: 100        # png: 100, jpeg: 0-95

storage:
  bucket:
    content: pages.content       # bucket name to store scraped pages html content 
    screenshot: pages.screenshot # bucket name to store scraped pages screenshots

rss:
  server_url: https://feed.example.fr # RSS Server url, used for stix object link
  max_items: 50  # Maximum number of items to keep in the RSS feed
```

## Project configuration: `project-name.yaml`

Create a `.yaml` or `.yml` file for each project following this template:

```yaml
project:
  name: tag.project_name
  take_screenshot: false    # default take_screenshot value for all routes
  stix_details:             # STIX 2.1 malware details
    name: "Malware Name"    # Optional - Name of the malware
    aliases:                # Optional - List of aliases for the malware
      - "Alias1"
      - "Alias2"
    is_family: true         # Optional - Whether this is a malware family (defaults to false)

sites:
  site_name:
    mirrors:                # List of mirror URLs for this site
      - http://mirror1.onion/
      - http://mirror2.onion/
    content_filters:        # Site-level content filters (applied to all routes)
      - ["filter_pattern1"]
      - ["filter_pattern2", "filter_pattern3"]
    take_screenshot: false  # Optional - override project default for this site
    
    routes:
      route_name:
        path: example/path.html  # Path to append to site mirrors
                                 # If empty, 'index.html' will be used
        take_screenshot: true    # Optional - override site/project default
        content_filters:         # Optional - route-specific content filters
          - ["route_filter1"]    # Overrides site-level filters if specified
        mirrors:                 # Optional - route-specific mirrors
          - http://mirror1.onion/special-path/
          - http://mirror2.onion/special-path/
      
      index:                # Example route using default values and standard path
        path: index.html
```

## Configuration Structure

### Projects

Each project can contain multiple sites and must include STIX malware details for threat intelligence purposes.

### STIX Details

The `stix_details` field is required and contains information about malware in STIX format:

- `name`: Optional - Primary name of the malware
- `aliases`: Optional - List of alternative names or identifiers for the malware
- `is_family`: Optional - Boolean indicating whether this is a malware family (defaults to false if not specified)

### Sites

A site represents a web property that may have multiple mirror URLs (for example, different .onion addresses).

### Routes

Routes represent specific pages within a site. Each route:
- Can inherit mirrors from the parent site (concatenating the site mirror URL with the route path)
- Can define its own specific mirror URLs
- Can have content filters that override site-level filters
- Can control whether screenshots are taken

### Content Filters

Content filters are used to extract HTML elements whose class names match the specified regex patterns. They help target specific content sections within scraped pages.

```yaml
content_filters:
  - ["^main-content$"]                   # Single filter pattern
  - ["^entry-content$", "--description$"] # Multiple filter patterns in one filter group
```

Each inner list represents a group of patterns that are applied together. The patterns within a group are applied as a logical AND condition, while different groups are treated as a logical OR.

In the above example:
- HTML elements with class matching `^main-content$` will be extracted
- OR elements with classes matching BOTH `^entry-content$` AND `--description$` will be extracted

This selective extraction helps focus on relevant content while ignoring navigation elements, ads, or other unwanted page sections.
