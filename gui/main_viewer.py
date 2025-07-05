import os
import sys

from PyQt5.QtWidgets import (QTreeWidgetItem ,QMessageBox ,QApplication, QFileDialog, QAction, QTextBrowser, QTreeWidget, QListWidget, QTabWidget,QShortcut, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout ,QSplitter, QLabel)
from streamlit.hello.streamlit_app import dir_path

#from multipart import file_path

from core.book_parser import EPubParser

from PyQt5.QtGui import  QKeySequence, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl
from ebooklib import epub
from lxml import etree
import zipfile

from PyQt5 import uic
from Content_view import Ui_Form


# noinspection PyUnresolvedReferences
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.parser = EPubParser()

        self.setWindowTitle("Viewer_window")
        self.setGeometry(100, 100, 600, 600)

        # self.setup_debug_overlay()

        #

        self.splitter = QSplitter(Qt.Horizontal)

        self.init_ui()
        self.create_actions()
        self.create_menus()
        # self.default_view_page()


    def init_ui(self):

        """Defining Central Widget"""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) # setting the margin between the window and layout


        # self.splitter.addWidget(QLabel("left_panel"))

        self.sidebar = QWidget()
        sidebarLayout = QVBoxLayout(self.sidebar)
        sidebarLayout.setContentsMargins(5 ,5 ,5 ,5)

        #Cover image
        self.cover_label = QLabel(self)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setFixedWidth(200)
        self.cover_label.setFixedHeight(200)
        self.cover_label.setStyleSheet("background-color: #99f0f0; border: 1px solid #ddd;")
        sidebarLayout.addWidget(self.cover_label)  #It does not move with resize of the sidebar for resizing (self.cover_label,QAlignment=Qt.AllignCenter)

        # Navigation tabs
        self.nav_tabs = QTabWidget()

        #Table of Contents
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderHidden(True)
        self.toc_tree.itemClicked.connect(self.on_toc_item_clicked)
        self.nav_tabs.addTab(self.toc_tree, "&Contents")


        self.pages_list = QListWidget()
        self.pagelist = QListWidget()
        self.pages_list.itemClicked.connect(self.on_page_item_clicked)

        self.nav_tabs.addTab(self.pages_list, "Pages")

        sidebarLayout.addWidget(self.nav_tabs)




        self.content = QWidget()
        self.content_view = Ui_Form()
        self.content_view.setupUi(self.content)
        """# Automatically open or not the links clicked by user via mouse/keyboard"""
        # self.content_view.textBrowser.setOpenExternalLinks(False)
        # self.content_view.textBrowser.setOpenLinks(False)
        # # noinspection PyUnresolvedReferences
        #self.content_view.textBrowser.anchorClicked.connect(self.on_link_clicked)
        self.content_view.textBrowser.urlChanged.connect(self.on_link_clicked)

        # self.content_view.setStyleSheet("""
        #     QTextBrowser {
        #
        #         border: 4px solid #0f990f;
        #         background-color: #f669f9;
        #         border-radius: 12px;
        #
        #         padding: 5px;
        #         background-clip: border;
        #         }
        # """)


        # Add widgets to splitter
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.content)

        self.splitter.setSizes([300, 700]) # Setting the initial ratio 3:7 for the content viewer and toc table

        main_layout.addWidget(self.splitter)

        # Status bar
        self.statusBar().showMessage("Ready")
    def create_actions(self):
        # File actions
        self.open_action = QAction("&Open...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Open an EPUB file")
        self.open_action.triggered.connect(self.open_epub)

        self.exit_action = QAction("&Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Exit the application")
        self.exit_action.triggered.connect(self.close)

        # Navigation actions
        self.prev_action = QAction("&Previous", self)
        self.prev_action.setShortcut("Left")
        self.prev_action.setStatusTip("Go to previous page")
        self.prev_action.triggered.connect(self.show_previous_page)

        self.next_action = QAction("&Next", self)
        self.next_action.setShortcut("Right")
        self.next_action.setStatusTip("Go to next page")
        self.next_action.triggered.connect(self.show_next_page)

        # View actions
        self.zoom_in_action = QAction("Zoom &In", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        # self.zoom_in_action.triggered.connect(self.zoom_in)

        self.zoom_out_action = QAction("Zoom &Out", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        # self.zoom_out_action.triggered.connect(self.zoom_out)



    def create_menus(self):
        #file Menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # View menu
        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)

        # Navigation menu
        nav_menu = self.menuBar().addMenu("&Navigation")
        nav_menu.addAction(self.prev_action)
        nav_menu.addAction(self.next_action)
    def open_epub(self):
       file_path, _ = QFileDialog.getOpenFileName(
           self, "Open EPUB File", "C:/Users/bhupe/Downloads", "EPUB Files (*.epub)"
       )
       self.dir_path = os.path.dirname(file_path)
       self.file_path = file_path

       if file_path:
           try:
               self.load_epub()
           except Exception as e:
               QMessageBox.critical(self, "Error", f"Failed to load EPUB:\n{str(e)}")
    #           logger.error(f"Error loading EPUB: {e}", exc_info=True)



       self.load_epub()


    def load_epub(self):
        if self.parser.load(self.file_path):
            self.setWindowTitle(f"EPUB Viewer - {os.path.basename(self.file_path)}")
            self.display_cover()
            self.build_toc()
            self.build_pages_list()
            self.load_spine_item_by_index(0)
            self.statusBar().showMessage(f"Loaded: {os.path.basename(self.file_path)}")

    def display_cover(self):
        self.cover_label.clear()
        cover_data, _ = self.parser.get_cover_image()
        if cover_data:
            cover_ext = '.jpg'  # Default extension
            cover_path = os.path.join(self.parser.temp_dir, f"cover{cover_ext}")

            with open(cover_path, 'wb') as f:
                f.write(cover_data)

            pixmap = QPixmap(cover_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.cover_label.width() - 20,
                    self.cover_label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.cover_label.setPixmap(pixmap)

    def build_toc(self):
        self.toc_tree.clear()

        #Manually parseing toc.ncx using zipfile +lxml
        try:
            print("Opening EPUB as ZIP file...")
            with zipfile.ZipFile(self.file_path, 'r') as z:
                print("Reading META-INF/container.xml...")
                container_data = etree.fromstring(z.read('META-INF/container.xml'))
                rootfile_path = container_data.xpath('//@full-path')[0]
                print(f"rootfile path from container.xml: {rootfile_path}")

                opf_data = etree.fromstring(z.read(rootfile_path))
                nsmap = {'n': opf_data.nsmap.get(None, '')}

                ncx_path = None
                for item in opf_data.xpath('//n:manifest/n:item', namespaces = nsmap ):
                    if item.attrib.get('media-type') == 'application/x-dtbncx+xml':
                        ncx_path = item.attrib['href']
                        break
                if not ncx_path:
                    self.toc_tree.clear()
                    QTreeWidgetItem(self.toc_tree, ["No toc.ncx found in manifest."])
                    return
                base_path = '/'.join(rootfile_path.split('/')[:-1])
                full_ncx_path = f"{base_path}/{ncx_path}" if base_path else ncx_path
                print(f"Resolved full path to toc.ncx: {full_ncx_path}")
                print(base_path)

                ncx_data = etree.fromstring(z.read(full_ncx_path))
                nav_map = ncx_data.find(".//{*}navMap")
                self.toc_tree.clear()
                if nav_map is not None:
                    print("<navMap> found. Building toc_tree...")
                    self.build_tree(nav_map, self.toc_tree)
                    self.toc_tree.expandAll()
                    print("The Tree build and expandeed")
                else:
                    print("No <>navMap found in toc.ncx")
                    QTreeWidgetItem(self.toc_tree, ["No <navmap> found in manifest.>"])

        except Exception as e:
            print(f"Exception during EPUB TOC parsing: {e}")
            self.toc_tree.clear()
            QTreeWidgetItem(self.toc_tree, [f"Error TOC error: {str(e)}"])
    def build_tree(self, parent_xml, parent_widget):
        for nav_point in parent_xml.findall("{*}navPoint"):
            label = nav_point.find("{*}navLabel/{*}text")
            content = nav_point.find("{*}content")
            title = label.text if label is not None else "Untitled"
            href = content.get("src") if content is not None else ""

            print(f"Adding TOC item: {title} -> {href}")

            item = QTreeWidgetItem([title])
            item.setData(0, Qt.UserRole, href)

            if isinstance(parent_widget, QTreeWidget):
                parent_widget.addTopLevelItem(item)
            else:
                parent_widget.addChild(item)

            self.build_tree(nav_point, item)


    def build_pages_list(self):
        
        self.pages_list.clear()
        for i in range(len(self.parser.spine_items)):
            item = self.parser.get_item_by_index(i)
            print(f"Building page {i}: {item.get_name()}")
            # print(f"{item.get_name()}: ")
            # print(item.setData(0, Qt.UserRole, href))

            if item:
                 self.pages_list.addItem(item.get_name())

    def on_toc_item_clicked(self, item):
        href = item.data(0, Qt.UserRole)
        print("href",href)
       # print(item.data())
        print("inside the fuction")
        if href:
            print("navigating to href")
            self.navigate_to_href(href)


    def on_page_item_clicked(self, item):
        index = self.pages_list.row(item)
        self.load_spine_item_by_index(index)


    def on_link_clicked(self, url):
        if url.isRelative() or url.scheme() == "file":
            path = url.path()
            if '#' in path:
                path, fragment = path.split('#', 1)
            else:
                fragment = None

            # Try to find the item
            for i in range(len(self.parser.spine_items)):
                item = self.parser.get_item_by_index(i)
                if item and (item.get_name() == path or item.get_name().endswith(path)):
                    self.load_spine_item_by_index(i)
                    return


    def navigate_to_href(self, href):
        """Navigate to a specific href"""
        # Try to find in spine first
        for i in range(len(self.parser.spine_items)):
            item = self.parser.get_item_by_index(i)
            # print("inside the navigating function")
            href = href.split('#')[0]
            print("going to load spine item")
            print("item.get_name()", item.get_name())
            print("href", item.get_name().endswith(href))
            if item and (item.get_name() == href or item.get_name().endswith(href)):
                print("going to load spine item")
                print("item.get_name()",item.get_name())
                print("href",item.get_name().endswith(href))

                self.load_spine_item_by_index(i)
                print()
                return
    def show_previous_page(self):
        if self.current_spine_index > 0:
            self.load_spine_item_by_index(self.current_spine_index - 1)

    def show_next_page(self):
        if self.current_spine_index < len(self.parser.spine_items) - 1:
            self.load_spine_item_by_index(self.current_spine_index + 1)

    def load_spine_item_by_index(self, index):
        if 0 <= index < len(self.parser.spine_items):
            item = self.parser.get_item_by_index(index)
            if item:
                self.current_spine_index = index
                content = self.parser.get_item_content(item,self.file_path)
                print(QUrl.fromLocalFile(str(dir_path) + "/"))#need to change this crap
                print(QUrl.fromLocalFile(str(self.dir_path) + "/"))#need to change this crap

                print(self.file_path)
                self.content_view.textBrowser.setHtml(content,QUrl.fromLocalFile(str(self.dir_path) + "/"))

                self.pages_list.setCurrentRow(index)
                self.statusBar().showMessage(f"Displaying: {item.get_name()}")
               # self.content_view.textBrowser.verticalScrollBar().setValue(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName("EPUB Viewer")
    app.setApplicationVersion("1.0")

    viewer = MainWindow()
    viewer.show()

    # Add keyboard shortcut for reload
    shortcut = QShortcut(QKeySequence("Ctrl+R"), viewer)
    # shortcut.activated.connect(reload_app)

    sys.exit(app.exec_())