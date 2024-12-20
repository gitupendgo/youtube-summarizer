import streamlit as st
from playwright.sync_api import sync_playwright
import time
import subprocess
import os

st.set_page_config(page_title="YouTube Video Summarizer", layout="wide")

def install_browser():
    try:
        import playwright
        subprocess.run(
            ["python3", "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except Exception as e:
        st.error(f"Browser installation error: {str(e)}")
        return False

def launch_browser(playwright):
    try:
        return playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-dev-shm-usage',
                '--no-zygote',
                '--single-process',
                '--headless=new'
            ]
        )
    except Exception as e:
        st.error(f"Browser launch error: {str(e)}")
        return None

# Initialize browser installation flag in session state
if 'browser_installed' not in st.session_state:
    st.session_state.browser_installed = install_browser()

st.title("YouTube Video Summarizer")

# Text area for input
links_text = st.text_area(
    "Paste YouTube links (one per line)", 
    height=150,
    placeholder="https://youtu.be/example1\nhttps://youtu.be/example2"
)

if st.button("Generate Summaries", type="primary"):
    if not st.session_state.browser_installed:
        st.error("Browser setup failed. Please try reloading the page.")
        st.stop()
        
    if not links_text.strip():
        st.error("Please paste some YouTube links first!")
        st.stop()
    
    # Parse links
    links = [link.strip() for link in links_text.splitlines() if link.strip()]
    
    if not links:
        st.error("No valid links found!")
        st.stop()
    
    progress = st.progress(0)
    status = st.empty()
    summaries = []
    total = len(links)
    
    try:
        with sync_playwright() as p:
            browser = launch_browser(p)
            if not browser:
                st.error("Failed to launch browser. Please try again.")
                st.stop()
                
            context = browser.new_context()
            page = context.new_page()
            
            for idx, link in enumerate(links, 1):
                status.write(f"Processing video {idx} of {total}...")
                clean_link = link.split('?')[0]
                
                try:
                    # Process the video
                    page.goto('https://notegpt.io/youtube-video-summarizer', 
                             timeout=60000,
                             wait_until='networkidle')
                    
                    # Input the link
                    input_box = page.locator('input[type="text"]')
                    input_box.fill(clean_link)
                    
                    # Generate summary
                    generate_button = page.get_by_text('Generate Summary')
                    generate_button.click()
                    
                    # Wait for result with better error handling
                    try:
                        copy_button = page.get_by_text('Copy')
                        copy_button.wait_for(state='visible', timeout=60000)
                        
                        # Get the summary
                        transcript = page.locator('.markdown-body').text_content()
                        summaries.append(f"Summary for {clean_link}:\n{transcript}\n{'='*50}\n")
                    except Exception as wait_error:
                        st.warning(f"Timeout waiting for summary of {clean_link}. Moving to next video...")
                        summaries.append(f"Timeout waiting for summary of {clean_link}\n{'='*50}\n")
                    
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
