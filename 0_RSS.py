#%%
import feedparser
import os
import pandas as pd
import xml.etree.ElementTree as ET  # Import ElementTree for XML parsing
from parameters import friday_date, get_filename
from bs4 import BeautifulSoup

# Set up output folder (created only when running in RSS mode)
local_folder_path = f'./data/2_raw_mds/{friday_date}'

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

    # Ensure output dir exists when actually processing
    os.makedirs(local_folder_path, exist_ok=True)

    # Iterate through each source (name and url)
    for source_info in sources:
        url = source_info['url']
        source_name = source_info['name']
        print(f"  Fetching feed: {source_name} ({url})") # Log which source is being processed
        # try:
        feed = feedparser.parse(url)
        if feed.bozo:
            print(f"    Warning: Potential issue parsing feed {url}. Reason: {feed.bozo_exception}")

        for entry in feed.entries:
            articles_list.append({
                'source_name': source_name, # Add the source name
                'published': entry.get('published'),
                'title': entry.get('title'),
                'link': entry.get('link')
            })
            try:
                content=entry.get('content')[0]['value']
                soup = BeautifulSoup(content, 'html.parser')
                text_content = soup.get_text()
                filename = f"{get_filename(entry.get('link'),'rss')}.md"
                output_path = os.path.join(local_folder_path, filename)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
            except Exception as e:
                print(f"Error processing feed {url}: {e}")

        # except Exception as e:
        #     print(f"    Error processing feed {url}: {e}")

    print(f"Finished processing. Extracted {len(articles_list)} articles.")
    return pd.DataFrame(articles_list)


# if __name__ == "__main__":
#      url='https://wechat2rss.cyber-icewinddale.cc/feed/3867515558.xml'
#      feed = feedparser.parse(url)
#      soup = BeautifulSoup(feed.entries[0].get('content')[0]['value'], 'html.parser')
#      text_content = soup.get_text()
#      print(text_content)

if __name__ == "__main__":
    opml_filename = 'rss_source.opml'

    articles_df = read_opml_feeds_to_df(opml_filename)

    # Print the resulting DataFrame (or its info/head)
    if not articles_df.empty:
        articles_df['published'] = pd.to_datetime(articles_df['published'], errors='coerce')
        articles_df = articles_df.sort_values(by='published', ascending=False)

        print("\n--- Articles DataFrame ---")
        print(articles_df.info())
        print("\n--- First 5 Articles ---")
        print(articles_df.head())
        
        # Check if the output file already exists
        output_file = './data/rss_articles.csv'
        if os.path.exists(output_file):
            # Read existing data
            existing_df = pd.read_csv(output_file)
            # Convert published to datetime for proper comparison
            existing_df['published'] = pd.to_datetime(existing_df['published'], errors='coerce')
            
            # Combine existing and new data
            combined_df = pd.concat([existing_df, articles_df])
            # Remove duplicates based on title and link
            combined_df = combined_df.drop_duplicates(subset=['title', 'link'], keep='first')
            # Sort by published date
            combined_df = combined_df.sort_values(by='published', ascending=False)
            
            print(f"Added {len(combined_df) - len(existing_df)} new articles to existing {len(existing_df)} articles.")
            combined_df.to_csv(output_file, index=False)
        else:
            # If file doesn't exist, just save the current data
            articles_df.to_csv(output_file, index=False)
            print(f"Created new file with {len(articles_df)} articles.")
    else:
        print("\nNo articles collected.")
