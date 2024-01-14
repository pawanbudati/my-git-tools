import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QTextEdit, QFileDialog, QScrollArea
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import subprocess
class CommandThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self, command, message, parent=None):
        super().__init__(parent)
        self.command = command
        self.message = message

    def run(self):
        result = ""
        try:
            result = subprocess.check_output(self.command, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            result = f"Error: {e.output}"
        self.finished.emit(result)

class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Create widgets
        label = QLabel('Folders', self)
        self.select_folder_button = QPushButton('Select Folder', self)
        self.select_folder_button.setStyleSheet("QPushButton { border: none; outline: none; }")
        self.subfolder_layouts = []
        self.terminal = QTextEdit(self)
        self.terminal.setReadOnly(True)

        self.footer = QHBoxLayout()


        # Create layout
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.select_folder_button)
        self.vbox.addWidget(label)

        # Create a subfolder container layout within a scroll area
        self.subfolder_scroll_area = QScrollArea(self)
        self.subfolder_container_widget = QWidget(self)
        self.subfolder_container_layout = QVBoxLayout(self.subfolder_container_widget)
        self.subfolder_scroll_area.setWidgetResizable(True)
        self.subfolder_scroll_area.setWidget(self.subfolder_container_widget)

        # Create push buttons
        self.always_on_top_button = QPushButton('Set Top', self)
        self.dark_mode_button = QPushButton('Dark Mode', self)
        self.always_on_top_button.setStyleSheet("QPushButton { border: none; outline: none; }")
        self.dark_mode_button.setStyleSheet("QPushButton { border: none; outline: none; }")

        # Set layout for the main window
        self.setLayout(self.vbox)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Set window properties
        self.setGeometry(1000, 300, 800, 600)
        self.setWindowTitle('Git Tools')

        # Connect button click events to functions
        self.select_folder_button.clicked.connect(self.onSelectFolderButtonClick)
        self.always_on_top_button.clicked.connect(self.toggleAlwaysOnTop)
        self.dark_mode_button.clicked.connect(self.toggleDarkMode)

        # Display subfolders in separate layouts
        subfolders = [f for f in os.listdir(os.getcwd()) if os.path.isdir(f)]
        self.populateSubfolderLayouts(subfolders, self.subfolder_container_layout)

        # Add the subfolder scroll area to the main layout
        self.vbox.addWidget(self.subfolder_scroll_area)

        # Add the terminal widget to the main layout
        self.vbox.addWidget(self.terminal)


        self.footer.addStretch(5)
        self.footer.addWidget(self.always_on_top_button)
        self.footer.addWidget(self.dark_mode_button)
        self.vbox.addLayout(self.footer)

        # Show the window
        self.show()

    def toggleAlwaysOnTop(self):
        # Function to be called when the "Always on Top" button is clicked
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(Qt.Widget)
            self.always_on_top_button.setText("Set Top")
        else:
            self.always_on_top_button.setText("Remove Top")
            self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.show()

    def toggleDarkMode(self):
        # Function to be called when the "Dark Mode" button is clicked
        if self.styleSheet() == darkTheme:
            self.setStyleSheet(lightTheme)
            self.dark_mode_button.setText("Dark Mode")
        else:
            self.setStyleSheet(darkTheme)
            self.dark_mode_button.setText("Light Mode")
   
    def onSelectFolderButtonClick(self):
        # Function to be called when the "Select Folder" button is clicked
        folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
        if folder:
            self.select_folder_button.setText(folder.split("/")[-1] if folder.split("/")[-1] else folder )
            os.chdir(folder)
            self.appendTerminalText(f"Changed directory to: {folder}")

            # Clear existing subfolder layouts
            for layout in self.subfolder_layouts:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()

            # Clear the list of subfolder layouts
            self.subfolder_layouts.clear()

            # Display subfolders in separate layouts
            subfolders = [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]
            self.populateSubfolderLayouts(subfolders, self.subfolder_container_layout)

    def populateSubfolderLayouts(self, subfolders, container_layout):
        # Create a new layout for each subfolder
        for subfolder in subfolders:
            subfolder_layout = QHBoxLayout()
            subfolder_layout.setAlignment(Qt.AlignTop)

            # Set subfolder name as heading
            heading_label = QLabel(subfolder)
            subfolder_layout.addWidget(heading_label)

            # Create buttons for each action
            pullBtn = QPushButton('Pull')
            guiBtn = QPushButton('GUI')
            gitkBtn = QPushButton('GitK')

            heading_label.mouseDoubleClickEvent = lambda event, folder=subfolder: self.executeCommand(f"cd {folder} && git pull && cd ..", f"Pulling {folder}")
            pullBtn.clicked.connect(lambda _, folder = subfolder : self.executeCommand(f"cd {folder} && git pull && cd ..", f"Pulling {folder}"))
            guiBtn.clicked.connect( lambda _, folder = subfolder : self.executeCommand(f"cd {folder} && git gui && cd ..", f"Opening GUI for {folder}"))
            gitkBtn.clicked.connect(lambda _, folder = subfolder : self.executeCommand(f"cd {folder} && gitk && cd ..", f"Opening GitK for {folder}"))

            # Add buttons to the layout
            subfolder_layout.addStretch(1)
            subfolder_layout.addWidget(pullBtn)
            subfolder_layout.addWidget(guiBtn)
            subfolder_layout.addWidget(gitkBtn)

            # Add the layout to the container layout
            container_layout.addLayout(subfolder_layout)

            # Save the layout reference for later clearing
            self.subfolder_layouts.append(subfolder_layout)
    
    def executeCommand(self, command, message):
            if message:
                self.appendTerminalText(message)

            # Pass 'self' as the parent to the CommandThread
            command_thread = CommandThread(command, message, self)
            command_thread.finished.connect(self.onCommandFinished)
            command_thread.start()
    
    def onCommandFinished(self, result):
        self.appendTerminalText(result + "\n" + "-" * 100)

    def appendTerminalText(self, text):
        self.terminal.append(text)
        # self.terminal.moveCursor(7)  # Move cursor to the end for better visibility

    def dragEnterEvent(self, event):
        # Accept only file or directory drops
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        # Get the first file or directory dropped
        path = event.mimeData().urls()[0].toLocalFile()

        # Change the command prompt directory
        os.chdir(path)
        self.appendTerminalText(f"Changed directory to: {path}")

        # Clear existing layouts
        for layout in self.subfolder_layouts:
            layout.setParent(None)

        # Clear existing subfolder container layout
        for i in reversed(range(self.subfolder_container_layout.count())):
            layout_item = self.subfolder_container_layout.itemAt(i)
            if layout_item:
                layout = layout_item.layout()
                if layout:
                    for j in reversed(range(layout.count())):
                        item = layout.itemAt(j)
                        if item:
                            widget = item.widget()
                            if widget:
                                widget.setParent(None)

                    layout.setParent(None)

        # Display subfolders in separate layouts
        subfolders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
        self.populateSubfolderLayouts(subfolders, self.subfolder_container_layout)

if __name__ == '__main__':
    darkTheme = open("dark theme.qss","r").read()
    lightTheme = open("light theme.qss","r").read()
    app = QApplication(sys.argv)
    app.setStyleSheet(lightTheme)
    window = MyApp()
    sys.exit(app.exec_())
