import streamlit as st
from playwright.sync_api import sync_playwright
import time
import subprocess
import os

st.set_page_config(page_title="YouTube Video Summarizer", layout="wide")

# Function to ensure browser is installed
def ensure_browser():
    try:
        # Try to install browser if not already installed
        if not os.path.exists("/home/appuser/.cache/ms-playwright"):
            st.info("First run detected. Installing browser...")
            subprocess.run(["playwright", "install", "chromium"], check=True)
            subprocess.run(["playwright", "install-deps", "chromium"], check=True)
            st.success("Browser installed successfully!")
        return True
    except Exception as e:
        st.error(f"Failed to install browser: {str(e)}")
        return False

st.title("YouTube Video Summarizer")

# Text area for input
links_text = st.text_area(
    "Paste YouTube links (one per line)", 
    height=150,
    placeholder="https://youtu.be/example1\nhttps://youtu.be/example2"
)

if st.button("Generate Summaries", type="primary"):
    if not links_text.strip():
        st.error("Please paste some YouTube links first!")
        st.stop()
    
    # Ensure browser is installed
    if not ensure_browser():
        st.error("Could not set up the browser. Please try again or contact support.")
        st.stop()
    
    # Parse links
    links = [link.strip() for link in links_text.splitlines() if link.strip()]
    
    if not links:
        st.error("No valid links found!")
        st.stop()
    
    # Show progress
    progress = st.progress(0)
    status = st.empty()
    
    summaries = []
    total = len(links)
    
    try:
        with sync_playwright() as p:
            # Launch browser with specific arguments for cloud environment
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context()
            page = context.new_page()
            
            for idx, link in enumerate(links, 1):
                status.write(f"Processing video {idx} of {total}...")
                clean_link = link.split('?')[0]
                
                try:
                    # Process the video
                    page.goto('https://notegpt.io/youtube-video-summarizer')
                    
                    # Input the link
                    input_box = page.locator('input[type="text"]')
                    input_box.fill(clean_link)
                    
                    # Generate summary
                    generate_button = page.get_by_text('Generate Summary')
                    generate_button.click()
                    
                    # Wait for result
                    copy_button = page.get_by_text('Copy')
                    copy_button.wait_for(state='visible', timeout=60000)
                    
                    # Get the summary
                    transcript = page.locator('.markdown-body').text_content()
                    summaries.append(f"Summary for {clean_link}:\n{transcript}\n{'='*50}\n")
                    
                    # Update progress
                    progress.progress(idx / total)
                    time.sleep(2)
                    
                except Exception as e:
                    st.error(f"Error processing {clean_link}: {str(e)}")
                    summaries.append(f"Failed to get summary for {clean_link}\n{'='*50}\n")
            
            browser.close()
        
        # Show results
        if summaries:
            status.write("✅ All done! Here are your summaries:")
            result_text = "\n".join(summaries)
            
            # Results in copyable text area
            st.text_area(
                "Summaries (Click to copy all)", 
                value=result_text,
                height=400
            )
            
            # Download option
            st.download_button(
                "📥 Download summaries as text file",
                result_text,
                file_name="summaries.txt",
                mime="text/plain"
            )
        else:
            st.error("No summaries were generated. Please try again.")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please try again. If the error persists, check if all links are valid YouTube URLs.")
