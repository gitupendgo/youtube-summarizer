from playwright.sync_api import sync_playwright
import time

def get_video_summaries(youtube_links):
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Set to True to run in background
        context = browser.new_context()
        page = context.new_page()
        
        summaries = []
        
        for link in youtube_links:
            # Clean the link (remove everything after ?)
            clean_link = link.split('?')[0]
            
            try:
                # Navigate to the website
                page.goto('https://notegpt.io/youtube-video-summarizer')
                
                # Input the YouTube link
                input_box = page.locator('input[type="text"]')
                input_box.fill(clean_link)
                
                # Click the generate button
                generate_button = page.get_by_text('Generate Summary')
                generate_button.click()
                
                # Wait for the copy button to appear (indicates summary is ready)
                copy_button = page.get_by_text('Copy')
                copy_button.wait_for(state='visible', timeout=60000)  # Wait up to 60 seconds
                
                # Get the transcript text
                transcript = page.locator('.markdown-body').text_content()
                summaries.append(f"Summary for {clean_link}:\n{transcript}\n{'='*50}\n")
                
                # Wait a bit between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing {clean_link}: {str(e)}")
                summaries.append(f"Failed to get summary for {clean_link}\n{'='*50}\n")
        
        browser.close()
        return summaries

# Example usage
if __name__ == "__main__":
    # Read links from a text file (one link per line)
    with open('youtube_links.txt', 'r') as f:
        links = [line.strip() for line in f if line.strip()]
    
    # Get summaries
    summaries = get_video_summaries(links)
    
    # Save results to a file
    with open('video_summaries.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(summaries))
