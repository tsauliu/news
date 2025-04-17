#%%
import feedparser
import os
import pandas as pd
import xml.etree.ElementTree as ET # Import ElementTree for XML parsing

def read_opml_feeds_to_df(opml_file='rss_source.opml'):
    """Reads RSS feed URLs and names from an OPML file, parses feeds, and returns articles as a Pandas DataFrame."""
    articles_list = []
    sources = [] # Store {'name': name, 'url': url}

    if not os.path.exists(opml_file):
        print(f"Error: OPML file '{opml_file}' not found.")
        return pd.DataFrame(articles_list)

    print(f"Reading RSS sources from OPML file: {opml_file}")
    try:
        tree = ET.parse(opml_file)
        root = tree.getroot()
        # Find all outline elements, extract name and URL
        for outline in root.findall('.//body//outline[@xmlUrl]'):
            url = outline.get('xmlUrl')
            # Get name from 'text' attribute, fallback to 'title', then 'Unknown Source'
            name = outline.get('text', outline.get('title', 'Unknown Source'))
            if url:
                sources.append({'name': name, 'url': url})
    except ET.ParseError as e:
        print(f"Error parsing OPML file '{opml_file}': {e}")
        return pd.DataFrame(articles_list)
    except Exception as e:
        print(f"Error reading OPML file '{opml_file}': {e}")
        return pd.DataFrame(articles_list)

    if not sources:
        print("No RSS feed sources found in the OPML file.")
        return pd.DataFrame(articles_list)

    print(f"Processing {len(sources)} RSS sources from '{opml_file}'...")

    # Iterate through each source (name and url)
    for source_info in sources:
        url = source_info['url']
        source_name = source_info['name']
        print(f"  Fetching feed: {source_name} ({url})") # Log which source is being processed
        try:
            feed = feedparser.parse(url)
            if feed.bozo:
                print(f"    Warning: Potential issue parsing feed {url}. Reason: {feed.bozo_exception}")

            for entry in feed.entries:
                articles_list.append({
                    'source_name': source_name, # Add the source name
                    'published': entry.get('published'),
                    'title': entry.get('title'),
                    'link': entry.get('link'),
                })
        except Exception as e:
            print(f"    Error processing feed {url}: {e}")

    print(f"Finished processing. Extracted {len(articles_list)} articles.")
    return pd.DataFrame(articles_list)

if __name__ == "__main__":
    opml_filename = 'rss_source.opml'

    articles_df = read_opml_feeds_to_df(opml_filename)

    # Print the resulting DataFrame (or its info/head)
    if not articles_df.empty:
        print("\n--- Articles DataFrame ---")
        print(articles_df.info())
        print("\n--- First 5 Articles ---")
        print(articles_df.head())
        articles_df.to_csv('./data/rss_articles.csv', index=False)
    else:
        print("\nNo articles collected.")
