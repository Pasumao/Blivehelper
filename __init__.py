from PySide2.QtWidgets import QApplication
from main_ui import MainWindow


room_id="24176073"
area_id="9"
area_parent_id="744"

def main():
    
    app = QApplication([])

    stats = MainWindow(debug=True)

    stats.main_ui.show()
    
    app.exec_()

if __name__ == "__main__":
    
    main()



