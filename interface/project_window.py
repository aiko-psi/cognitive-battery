import os
import sys
import json
from datetime import datetime

from PyQt5 import QtGui, QtWidgets
from designer import project_window_qt
from interface import battery_window, project_new_window


class ProjectWindow(QtWidgets.QMainWindow, project_window_qt.Ui_ProjectWindow):
    def __init__(self, base_dir, res_width, res_height):
        super(ProjectWindow, self).__init__()

        # Setup the main window UI
        self.setupUi(self)

        # Set app icon
        self.setWindowIcon(QtGui.QIcon(os.path.join('images', 'icon_sml.png')))

        # Keep reference to main battery and new project windows
        self.main_battery = None
        self.new_project_window = None

        self.res_width = res_width
        self.res_height = res_height
        self.base_dir = base_dir

        # Check if project file exists
        if not os.path.isfile(os.path.join(self.base_dir, 'projects.txt')):
            self.project_list = {}
            self.save_projects(self.project_list)
        else:
            self.project_list = self.refresh_projects()

        # Make info labels invisible at start
        self.researcherLabel.hide()
        self.createdLabel.hide()
        self.dirLabel.hide()

        # Handle menu bar item click events
        self.actionNewProject.triggered.connect(self.new_project)
        self.actionExit.triggered.connect(self.close)

        # Bind button events
        self.projectExpandButton.clicked.connect(self.projectTree.expandAll)
        self.projectCollapseButton.clicked.connect(self.projectTree.collapseAll)
        self.openButton.clicked.connect(self.start)
        self.deleteButton.clicked.connect(self.delete_project)

        # Project tree click event
        self.projectTree.itemClicked.connect(self.project_click)

    def new_project(self):
        self.new_project_window = project_new_window.NewProjectWindow(self.base_dir, self.project_list)
        self.new_project_window.exec_()
        self.refresh_projects()

    def project_click(self, item):
        if item.parent():
            researcher = item.parent().text(0)
            project_name = item.text(0)

            created_unix = self.project_list[researcher][project_name]["created"]
            created_time = datetime.fromtimestamp(created_unix).strftime("%d/%m/%Y @ %H:%M")
            project_path = self.project_list[researcher][project_name]["path"]

            self.projectName.setText(project_name)
            self.researcherValue.setText(researcher)
            self.createdValue.setText(created_time)
            self.dirValue.setText(project_path)

            if os.path.isdir(project_path):
                self.dirValue.setStyleSheet('QLabel {color: black;}')
                self.dirInvalid.setText("")
            else:
                self.dirValue.setStyleSheet('QLabel {color: red;}')
                self.dirInvalid.setText("(Error: invalid path)")

            # Enable buttons and labels
            self.researcherLabel.show()
            self.createdLabel.show()
            self.dirLabel.show()
            self.openButton.setEnabled(True)
            self.deleteButton.setEnabled(True)

    def start(self, event):
        if not os.path.isdir(self.dirValue.text()):
            QtWidgets.QMessageBox.warning(self, 'Error', 'Invalid project path')
        else:
            self.main_battery = battery_window.BatteryWindow(self.base_dir,
                                                             self.dirValue.text(),
                                                             self.res_width,
                                                             self.res_height)
            self.main_battery.show()
            self.close()

    def delete_project(self):
        # Check which project has been selected
        researcher = self.researcherValue.text()
        project = self.projectName.text()

        # Check number of projects for this researcher before delete
        num_projects = len(self.project_list[researcher].keys())

        # Delete selected project
        self.project_list[researcher].pop(project, None)

        # If this was the only project, remove the researcher too
        if num_projects == 1:
            self.project_list.pop(researcher, None)

        # Save file and refresh project list
        self.save_projects(self.project_list)
        self.refresh_projects()

    def save_projects(self, projects):
        # Save current project list to file
        with open(os.path.join(self.base_dir, 'projects.txt'), 'w+') as f:
            json.dump(projects, f, indent=4)

    def refresh_projects(self):
        # Load most recent saved project list from file
        with open(os.path.join(self.base_dir, 'projects.txt'), 'r') as f:
            projects = json.load(f)

        # Clear existing tree widget
        self.projectTree.clear()

        # Get all researcher names
        all_researchers = sorted(projects.keys(), key=lambda x: x.lower())

        for person in all_researchers:
            # Add researcher root node
            personItem = QtWidgets.QTreeWidgetItem([person])
            font = personItem.font(0)
            font.setBold(True)
            personItem.setFont(0, font)
            self.projectTree.addTopLevelItem(personItem)

            # Add project name for each researcher
            all_projects = sorted(projects[person].keys(), key=lambda x: x.lower())

            for project in all_projects:
                projectItem = QtWidgets.QTreeWidgetItem([project])
                personItem.addChild(projectItem)

        self.projectTree.expandAll()

        self.projectName.setText("")
        self.researcherValue.setText("")
        self.createdValue.setText("")
        self.dirValue.setText("")
        self.dirInvalid.setText("")

        # Disable buttons and labels
        self.researcherLabel.hide()
        self.createdLabel.hide()
        self.dirLabel.hide()
        self.openButton.setEnabled(False)
        self.deleteButton.setEnabled(False)

        return projects