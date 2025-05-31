import os
import requests
import tempfile
from urllib.parse import urlparse
import subprocess
import logging

ALLOWED_EXTENSIONS = {'pdf', 'epub'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(file_path):
    """Get file size in MB"""
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)

def convert_url_to_pdf(url, output_path):
    """
    Convert a web page to PDF using wkhtmltopdf
    Returns (success: bool, error_message: str)
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False, "Invalid URL format"
        
        # Ensure URL has a scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Try to access the URL first
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code >= 400:
                return False, f"Cannot access URL (HTTP {response.status_code})"
        except requests.RequestException as e:
            return False, f"Cannot access URL: {str(e)}"
        
        # Use wkhtmltopdf command line tool
        cmd = [
            'wkhtmltopdf',
            '--page-size', 'A4',
            '--margin-top', '0.75in',
            '--margin-right', '0.75in',
            '--margin-bottom', '0.75in',
            '--margin-left', '0.75in',
            '--encoding', 'UTF-8',
            '--quiet',
            '--enable-local-file-access',
            '--load-error-handling', 'ignore',
            '--load-media-error-handling', 'ignore',
            url,
            output_path
        ]
        
        # Try wkhtmltopdf first
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True, None
            else:
                logging.warning(f"wkhtmltopdf failed: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logging.warning("wkhtmltopdf not available or timed out")
        
        # Use weasyprint as primary method
        try:
            import weasyprint
            from weasyprint import HTML, CSS
            
            # Add user agent to avoid blocks
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Create PDF using WeasyPrint with better styling
            html_doc = HTML(url=url, encoding='utf-8')
            css = CSS(string='''
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }
                img {
                    max-width: 100%;
                    height: auto;
                }
            ''')
            
            html_doc.write_pdf(output_path, stylesheets=[css])
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:  # At least 1KB
                return True, None
            else:
                return False, "Generated PDF is too small or empty"
                
        except ImportError:
            return False, "PDF conversion library not available. Please contact support."
        except Exception as e:
            logging.error(f"WeasyPrint conversion error: {str(e)}")
            return False, f"PDF conversion failed: {str(e)}"
            
    except Exception as e:
        logging.error(f"URL to PDF conversion error: {str(e)}")
        return False, f"Conversion failed: {str(e)}"

def convert_epub_to_pdf(epub_path, pdf_path):
    """
    Convert EPUB to PDF
    Returns True if successful, False otherwise
    """
    try:
        import ebooklib
        from ebooklib import epub
        import weasyprint
        from bs4 import BeautifulSoup
        import tempfile
        
        # Read EPUB file
        book = epub.read_epub(epub_path)
        
        # Extract text content
        content_html = []
        content_html.append('<html><head><meta charset="UTF-8"></head><body>')
        
        # Get all items from the book
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Parse HTML content
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # Extract text and basic formatting
                if soup.body:
                    content_html.append(str(soup.body))
                else:
                    content_html.append(str(soup))
        
        content_html.append('</body></html>')
        
        # Combine all content
        full_html = '\n'.join(content_html)
        
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
            temp_html.write(full_html)
            temp_html_path = temp_html.name
        
        try:
            # Convert HTML to PDF using WeasyPrint
            html_doc = weasyprint.HTML(filename=temp_html_path)
            html_doc.write_pdf(pdf_path)
            
            # Clean up temporary file
            os.unlink(temp_html_path)
            
            return os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
            raise e
            
    except ImportError as e:
        logging.error(f"Missing required libraries for EPUB conversion: {e}")
        return False
    except Exception as e:
        logging.error(f"EPUB to PDF conversion error: {str(e)}")
        return False
