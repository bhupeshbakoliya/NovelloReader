# import sys
#
# import ebooklib
# from ebooklib import epub
# from ebooklib.utils import debug
#
# book = epub.read_epub("C:/Users/bhupe/Downloads/Harry.epub")
#
# debug(book.metadata)
# debug(book.spine)
# debug(book.toc)
# #
# for x in  book.get_items_of_type(ebooklib.ITEM_IMAGE):
#     debug(x)
#     print(x)
#
# # for x in  book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
# #     debug(x)
# #     print(x)
#
#
# print(book.title)
#
# print(book.spine)
# print(book.toc)
# print(book.direction)


import os
import logging
import ebooklib
import tempfile
import mimetypes
from PyQt5.QtCore import QUrl
from urllib.parse import unquote
from bs4 import BeautifulSoup
from ebooklib import epub

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class EPubParser:
    def __init__(self):
        self.book = None
        self.temp_dir = None
        self.resource_map = {}
        self.spine_items = []
        self.toc_items = []

    def load(self, file_path):
        """Load and parse the EPUB file"""
        self.cleanup()
        self.temp_dir = tempfile.mkdtemp(prefix='epub_viewer_')
        self.book = epub.read_epub(file_path)
        self.extract_resources()
        self.process_spine()
        return True

    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(self.temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {e}")

        self.resource_map = {}
        self.book = None

    def extract_resources(self):
        """Extract all resources from the EPUB to temp directory"""
        for item in self.book.get_items():
            try:
                if item.get_type() in (ebooklib.ITEM_IMAGE, ebooklib.ITEM_STYLE, ebooklib.ITEM_FONT):
                    self.save_resource(item)
            except Exception as e:
                logger.warning(f"Failed to extract resource {item.get_name()}: {e}")

    def save_resource(self, item):
        """Save a resource to temp directory and track its path"""
        original_path = unquote(item.get_name())
        safe_path = original_path.replace('../', '').replace('..\\', '')

        # Determine file extension
        base, ext = os.path.splitext(safe_path)
        if not ext:
            ext = mimetypes.guess_extension(item.media_type) or ''
            if ext == '.jpe':
                ext = '.jpg'

        # Create safe filename
        safe_filename = f"{base}{ext}"
        temp_path = os.path.join(self.temp_dir, safe_filename)

        # Create directory if needed
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)

        # Save file
        with open(temp_path, 'wb') as f:
            f.write(item.get_content())

        # Map all possible path variations
        path_variants = [
            original_path,
            safe_path,
            os.path.normpath(original_path),
            os.path.normpath(safe_path),
            safe_filename,
            os.path.basename(original_path)
        ]

        for variant in path_variants:
            if variant not in self.resource_map:
                self.resource_map[variant] = temp_path

    def process_spine(self):
        """Process the spine items"""
        self.spine_items = list(self.book.spine)

    def get_metadata(self, field):
        """Get specific metadata field"""
        meta = self.book.get_metadata('DC', field)
        return meta[0][0] if meta else ''

    def get_cover_image(self):
        """Get the cover image data"""
        try:
            cover_id = None
            meta_cover = self.book.get_metadata('OPF', 'cover')
            if meta_cover:
                cover_id = meta_cover[0][0]

            cover_item = None
            if cover_id:
                cover_item = self.book.get_item_with_id(cover_id)
            else:
                for item in self.book.get_items():
                    if 'cover' in item.get_name().lower():
                        cover_item = item
                        break

            if cover_item and cover_item.get_type() == ebooklib.ITEM_IMAGE:
                return cover_item.get_content(), cover_item.media_type
        except Exception as e:
            logger.warning(f"Failed to get cover image: {e}")
        return None, None

    def get_toc(self):
        """Get the table of contents structure"""
        self.toc_items = []
        toc_structure = []

        def process_toc_items(items):
            result = []
            for item in items:
                if isinstance(item, tuple):
                    # Section with children
                    section = (str(item[0]), item[1] if len(item) > 1 else None)
                    children = process_toc_items(item[2]) if len(item) > 2 else []
                    result.append((section[0], section[1], children))
                    self.toc_items.append((str(item[0]), str(item[1]) if len(item) > 1 and item[1] else None))
                elif isinstance(item, epub.Link):
                    # Single item
                    result.append((str(item.title), str(item.href)))
                    self.toc_items.append((str(item.title), str(item.href)))
            return result

        if self.book.toc:
            return process_toc_items(self.book.toc)
        return None

    def get_item_by_index(self, index):
        """Get spine item by index"""
        if 0 <= index < len(self.spine_items):
            item_id, _ = self.spine_items[index]
            return self.book.get_item_with_id(item_id)
        return None

    # def get_item_content(self, item, file_path):
    #     """Get processed content for an item"""
    #     print(file_path)
    #     try:
    #         content = item.get_content().decode('utf-8', errors='replace')
    #         soup = BeautifulSoup(content, 'html.parser')
    #         print("inside ")
    #         # Clean HTML
    #         for tag in soup.find_all():
    #             if tag.name.lower() in ['script', 'iframe', 'object', 'noscript']:
    #                 tag.decompose()
    #                 print(f"inside{tag.name} ")
    #             else:
    #                 # Remove problematic attributes
    #                 print("inside 00")
    #                 for attr in list(tag.attrs):
    #                     if attr.lower().startswith('on'):
    #                         del tag.attrs[attr]
    #
    #         # Fix resource references
    #         self.fix_resource_references(soup)
    #
    #         # Detect cover-only image page
    #         is_cover_page = False
    #         body = soup.body
    #
    #         if body:
    #             body_classes = body.get('class', [])
    #
    #             # Check for class='cover' or cover1 div
    #             if 'cover' in body_classes:
    #                 is_cover_page = True
    #             elif len(body.find_all('img')) == 1 and len(body.find_all(['p', 'h1', 'h2', 'span', 'div'])) <= 2:
    #                 # Allow one image, and one wrapping div maybe
    #                 is_cover_page = True
    #
    #         # Inject external CSS (relative to item’s href or root path)
    #         css_paths = ['../stylesheet.css', '../page_styles.css']
    #         print("inside ")
    #         css_combined = ""
    #         for css_item in self.book.get_items_of_type(ebooklib.ITEM_STYLE):
    #             css_combined += css_item.get_content().decode('utf-8', errors='replace') + "\n"
    #         print("CSS length:", len(css_combined))
    #         print("CSS preview:", css_combined[:300])
    #         # Add custom responsive styling to fix image overflow
    #         if is_cover_page:
    #             css_combined += """
    #             img {
    #               display: block;
    #               margin: auto;
    #               max-height: 95vh;
    #               width: auto;
    #               height: auto;
    #               object-fit: contain;
    #             }
    #             body {
    #               display: flex;
    #               justify-content: center;
    #               align-items: center;
    #               height: 100vh;
    #               margin: 0;
    #               background: #fff;
    #             }
    #             """
    #         else:
    #             css_combined += """
    #             img {
    #               max-width: 100%;
    #               height: auto;
    #               display: block;
    #               object-fit: contain;
    #               margin-left: auto;
    #               margin-right: auto;
    #             }
    #             body {
    #               margin: 1em;
    #               font-family: serif;
    #               line-height: 1.5;
    #               background: #fff;
    #             }
    #             """
    #
    #         if css_combined:
    #             style_tag = soup.new_tag("style", type="text/css")
    #             style_tag.string = css_combined
    #             head = soup.head
    #             if not head:
    #                 head = soup.new_tag("head")
    #                 if soup.html:
    #                     soup.html.insert(0, head)
    #                 else:
    #                     soup.insert(0, head)
    #             head.append(style_tag)
    #         #print(str(soup))
    #         final_html = str(soup)
    #         print(final_html[:1000])  # print preview of rendered HTML
    #
    #         return str(soup)
    #
    #     except Exception as e:
    #         print(f"[ERROR] Failed to parse content: {e}")
    #         return f"<h1>Error</h1><p>{str(e)}</p>"
    #
    #
    def get_item_content(self, item, book_path=None):
        """Get processed content for an item"""
        try:
            content = item.get_content().decode('utf-8', errors='replace')
            soup = BeautifulSoup(content, 'html.parser')

            # Clean up scripts, dangerous tags, and inline JS
            for tag in soup.find_all():
                if tag.name.lower() in ['script', 'iframe', 'object', 'noscript']:
                    tag.decompose()
                else:
                    for attr in list(tag.attrs):
                        if attr.lower().startswith('on'):
                            del tag.attrs[attr]

            # Fix references like image paths
            self.fix_resource_references(soup)

            # --- Detect if page is a cover-only page ---
            is_cover_page = False
            body = soup.body

            if body:
                images = body.find_all('img')
                text_content = body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div'])

                if 'cover' in body.get('class', []):
                    is_cover_page = True
                elif len(images) == 1 and len(text_content) <= 2:
                    is_cover_page = True
                elif any('cover' in (div.get('class', [''])[0]) for div in body.find_all('div')):
                    is_cover_page = True

            # --- Load EPUB CSS from internal EPUB ---
            css_combined = ""
            for css_item in self.book.get_items_of_type(ebooklib.ITEM_STYLE):
                try:
                    css_combined += css_item.get_content().decode('utf-8', errors='replace') + "\n"
                except Exception as e:
                    print("[WARNING] CSS decode failed:", e)

            # --- Add Responsive CSS ---
            if is_cover_page:
                css_combined += """
                img {
                  display: block;
                  margin: auto;
                  max-height: 95vh;
                  height: auto;
                  width: auto;
                  object-fit: contain;
                }
                body {
                  display: flex;
                  justify-content: center;
                  align-items: center;
                  height: 100vh;
                  margin: 0;
                  background: #fff;
                }
                """
            else:
                css_combined += """
                img {
                  display: block !important;
                  margin-left: auto !important;
                  margin-right: auto !important;
                  height: auto !important;
                  max-width: 100% !important;
                  object-fit: contain !important;
                }
                body {
                  margin: 1em;
                  font-size: 16px;
                  font-family: serif;
                  line-height: 1.6;
                  background: #fff;
                }
                """

            # --- Inject CSS into <head> ---
            style_tag = soup.new_tag("style", type="text/css")
            style_tag.string = css_combined

            if soup.head:
                soup.head.append(style_tag)
            else:
                head = soup.new_tag("head")
                head.append(style_tag)
                if soup.html:
                    soup.html.insert(0, head)
                else:
                    soup.insert(0, head)

            return str(soup)

        except Exception as e:
            print(f"[ERROR] Failed to parse content: {e}")
            return f"<h1>Error displaying content</h1><p>{str(e)}</p>"


    def fix_resource_references(self, soup):
        """Fix all resource references in the HTML"""
        for img in soup.find_all('img'):
            if 'src' in img.attrs:
                self.fix_single_reference(img, 'src')

        for link in soup.find_all('link'):
            if 'href' in link.attrs:
                self.fix_single_reference(link, 'href')

        for a in soup.find_all('a'):
            if 'href' in a.attrs:
                href = a['href']
                if not href.startswith(('http:', 'https:', 'mailto:')):
                    a['href'] = self.fix_href_reference(href)

    def fix_single_reference(self, tag, attr):
        """Fix a single resource reference"""
        original_ref = unquote(tag[attr])
        for path_variant in [
            original_ref,
            os.path.normpath(original_ref),
            original_ref.replace('../', '').replace('..\\', ''),
            os.path.basename(original_ref)
        ]:
            if path_variant in self.resource_map:
                tag[attr] = QUrl.fromLocalFile(self.resource_map[path_variant]).toString()
                return

        basename = os.path.basename(original_ref)
        for resource_path, local_path in self.resource_map.items():
            if os.path.basename(resource_path) == basename:
                tag[attr] = QUrl.fromLocalFile(local_path).toString()
                return

    def fix_href_reference(self, href):
        """Fix an href reference (for internal links)"""
        href = href.split('#')[0]
        for path_variant in [
            href,
            os.path.normpath(href),
            href.replace('../', '').replace('..\\', ''),
            os.path.basename(href)
        ]:
            if path_variant in self.resource_map:
                return QUrl.fromLocalFile(self.resource_map[path_variant]).toString()
        return href


