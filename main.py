import sys
import os
import time

# PREVENT PYINSTALLER BACKGROUND CRASH
if getattr(sys, 'stdout', None) is None:
    sys.stdout = open(os.devnull, "w")
if getattr(sys, 'stderr', None) is None:
    sys.stderr = open(os.devnull, "w")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QComboBox, QListWidget, 
                             QPushButton, QAbstractItemView, QListWidgetItem,
                             QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QIcon

from printer_utils import get_installed_printers, print_pdf
from pdf_processor import prepare_pdf_for_custom_duplex

class PrintWorker(QThread):
    progress = pyqtSignal(int, str, str) # index, status, message
    finished = pyqtSignal()
    
    def __init__(self, queue_items, printer_name, temp_dir):
        super().__init__()
        self.queue_items = queue_items # list of (index, filepath)
        self.printer_name = printer_name
        self.temp_dir = temp_dir
        self.running = True

    def run(self):
        for index, filepath in self.queue_items:
            if not self.running:
                break
                
            filename = os.path.basename(filepath)
            self.progress.emit(index, "processing", f"Processing: {filename}")
            
            temp_pdf = os.path.join(self.temp_dir, f"temp_{int(time.time())}_{filename}")
            try:
                # 1. Prepare PDF
                prepare_pdf_for_custom_duplex(filepath, temp_pdf)
                self.progress.emit(index, "printing", f"Printing: {filename}")
                
                # 2. Print PDF
                success, msg = print_pdf(temp_pdf, self.printer_name)
                
                if success:
                    self.progress.emit(index, "done", f"Done: {filename}")
                else:
                    self.progress.emit(index, "error", f"Print Error: {filename}")
                    print(f"Error printing {filename}: {msg}")
            except Exception as e:
                self.progress.emit(index, "error", f"Process Error: {filename}")
                print(f"Error processing {filename}: {e}")
            finally:
                if os.path.exists(temp_pdf):
                    try:
                        os.remove(temp_pdf)
                    except:
                        pass
            
            # Pause between jobs ensures printer catches up cleanly
            time.sleep(1.5)
            
        self.finished.emit()

    def stop(self):
        self.running = False


class DragDropListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # Enable internal reordering natively
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #aaaaaa;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #cce8ff;
                color: black;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Only accept if there are PDFs
            has_pdf = any(url.isLocalFile() and url.toLocalFile().lower().endswith('.pdf') 
                          for url in event.mimeData().urls())
            if has_pdf:
                event.acceptProposedAction()
                return
        # Also need to accept internal moves
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith('.pdf'):
                    filepath = url.toLocalFile()
                    filename = os.path.basename(filepath)
                    item = QListWidgetItem(f"📄 {filename}")
                    # Store data for later
                    item.setData(Qt.ItemDataRole.UserRole, filepath)
                    self.addItem(item)
            event.acceptProposedAction()
        else:
            # Handle internal move
            super().dropEvent(event)


class AutoPrintApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Invoice Print Queue")
        self.resize(650, 450)
        
        self.temp_dir = os.path.join(os.path.expanduser("~"), ".autoprint_tmp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.worker = None
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # --- Top: Printer Selection ---
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Select Printer:"))
        self.printer_combo = QComboBox()
        self.printer_combo.addItem("Default Printer")
        self.printer_combo.addItems(get_installed_printers())
        top_layout.addWidget(self.printer_combo, stretch=1)
        main_layout.addLayout(top_layout)
        
        # --- Middle: Queue and Controls ---
        queue_layout = QHBoxLayout()
        
        # List
        self.queue_list = DragDropListWidget()
        queue_layout.addWidget(self.queue_list, stretch=1)
        
        # Controls
        controls_layout = QVBoxLayout()
        
        self.btn_up = QPushButton("⬆ Move Up")
        self.btn_up.clicked.connect(self.move_up)
        
        self.btn_down = QPushButton("⬇ Move Down")
        self.btn_down.clicked.connect(self.move_down)
        
        self.btn_remove = QPushButton("❌ Remove")
        self.btn_remove.clicked.connect(self.remove_selected)
        
        self.btn_clear = QPushButton("🗑 Clear All")
        self.btn_clear.clicked.connect(self.queue_list.clear)
        
        controls_layout.addWidget(self.btn_up)
        controls_layout.addWidget(self.btn_down)
        controls_layout.addWidget(self.btn_remove)
        controls_layout.addWidget(self.btn_clear)
        controls_layout.addStretch()
        
        queue_layout.addLayout(controls_layout)
        main_layout.addLayout(queue_layout, stretch=1)
        
        # --- Bottom: Print Button and Status ---
        bottom_layout = QHBoxLayout()
        
        self.status_label = QLabel("Drag PDFs into the queue, sort them, then Print.")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        bottom_layout.addWidget(self.status_label, stretch=1)
        
        self.btn_print = QPushButton("🖨 PRINT QUEUE")
        self.btn_print.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.btn_print.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        self.btn_print.clicked.connect(self.start_printing)
        bottom_layout.addWidget(self.btn_print)
        
        main_layout.addLayout(bottom_layout)
        
        self.setCentralWidget(central_widget)

    def move_up(self):
        current_row = self.queue_list.currentRow()
        if current_row > 0:
            item = self.queue_list.takeItem(current_row)
            self.queue_list.insertItem(current_row - 1, item)
            self.queue_list.setCurrentRow(current_row - 1)
            
    def move_down(self):
        current_row = self.queue_list.currentRow()
        if current_row >= 0 and current_row < self.queue_list.count() - 1:
            item = self.queue_list.takeItem(current_row)
            self.queue_list.insertItem(current_row + 1, item)
            self.queue_list.setCurrentRow(current_row + 1)
            
    def remove_selected(self):
        for item in self.queue_list.selectedItems():
            self.queue_list.takeItem(self.queue_list.row(item))

    def start_printing(self):
        if self.queue_list.count() == 0:
            QMessageBox.information(self, "Queue Empty", "Please add PDFs to the queue first.")
            return
            
        # Collect items that are pending
        items_to_print = []
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            # Skip if already printed successfully
            if "✅" not in item.text():
                filepath = item.data(Qt.ItemDataRole.UserRole)
                items_to_print.append((i, filepath))
                
                filename = os.path.basename(filepath)
                item.setText(f"⏳ Pending: {filename}")
                item.setForeground(Qt.GlobalColor.black)
                
        if not items_to_print:
            QMessageBox.information(self, "Done", "All items in the queue are already printed.")
            return

        printer_name = self.printer_combo.currentText()
        if printer_name == "Default Printer":
            printer_name = None
            
        # UI Lockdown
        self.btn_print.setEnabled(False)
        self.queue_list.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop) # disable sorting while printing
        self.btn_up.setEnabled(False)
        self.btn_down.setEnabled(False)
        self.btn_remove.setEnabled(False)
        self.btn_clear.setEnabled(False)
        
        self.status_label.setText("Printing queue...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        
        self.worker = PrintWorker(items_to_print, printer_name, self.temp_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.printing_finished)
        self.worker.start()

    def update_progress(self, index, status, message):
        item = self.queue_list.item(index)
        if status == "processing":
            item.setText(f"⚙️ {message}")
            item.setForeground(Qt.GlobalColor.blue)
        elif status == "printing":
            item.setText(f"🖨️ {message}")
            item.setForeground(Qt.GlobalColor.darkMagenta)
        elif status == "done":
            item.setText(f"✅ {message}")
            item.setForeground(Qt.GlobalColor.darkGreen)
        elif status == "error":
            item.setText(f"❌ {message}")
            item.setForeground(Qt.GlobalColor.red)
            # QMessageBox.warning(self, "Print Error", message) # Remove so it doesnt block queue

    def printing_finished(self):
        self.btn_print.setEnabled(True)
        self.queue_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.btn_up.setEnabled(True)
        self.btn_down.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.btn_clear.setEnabled(True)
        self.status_label.setText("Queue processing complete.")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = AutoPrintApp()
    
    # Try forcing it on top temporarily when opened
    window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    window.show()
    window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
