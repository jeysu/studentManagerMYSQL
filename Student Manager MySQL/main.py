"""Import required modules."""
import mysql.connector
from mysql.connector import Error

import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import uic

class Communicate(QObject):
    """Communicate with signal to update dataframe"""
    updateDataframe = pyqtSignal(pd.DataFrame)
    updateCourseDataframe = pyqtSignal(pd.DataFrame)
    deletedCourse = pyqtSignal(str)

class mainWindow(QMainWindow):
    """Main window"""

    def __init__(self):
        # Load Main Window UI
        super(mainWindow, self).__init__()
        uic.loadUi("mainWindow.ui", self)
        self.show()

        # Trigger event for buttons in main window
        self.addButton.clicked.connect(self.addClicked)
        self.deleteButton.clicked.connect(self.deleteClicked)
        self.editButton.clicked.connect(self.editClicked)
        self.saveButton.clicked.connect(self.saveClicked)
        self.courseViewButton.clicked.connect(self.courseViewClicked)

        # Store future references to child windows
        self.courseWindow = None
        self.addWindow = None
        self.deleteWindow = None
        self.updateWindow = None

        # Create an object to communicate
        self.communicate = Communicate()

        # Initialize dataframes
        self.dataframe = self.fetchStudents()
        self.course_dataframe = self.fetchCourses()

        # Update text browser
        self.read()

    def fetchStudents(self):
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 database='database',
                                                 user='root',
                                                 password='password')
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM students")
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=['name', 'id_number', 'course', 'year', 'sex', 'status'])
            return df
        except Error as e:
            print(e)
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    def fetchCourses(self):
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 database='database',
                                                 user='root',
                                                 password='password')
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM courses")
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=['course_code', 'course_description'])
            return df
        except Error as e:
            print(e)
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    def saveDataframe(self, dataframe, table_name):
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 database='database',
                                                 user='root',
                                                 password='password')
            cursor = connection.cursor()
            for index, row in dataframe.iterrows():
                values = ', '.join(['%s'] * len(row))
                sql = f"INSERT INTO {table_name} VALUES ({values})"
                cursor.execute(sql, tuple(row.values))
            connection.commit()
            print(f"{table_name} saved successfully.")
        except Error as e:
            print(f"Error saving {table_name}: {e}")
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    def courseViewClicked(self):
        #Open course window
        self.courseWindow = courseWindow(self.dataframe, self.course_dataframe)
        #Update dataframe
        self.courseWindow.communicate.updateDataframe.connect(self.updateDataframeSlot)
        self.courseWindow.communicate.updateCourseDataframe.connect(self.updateCourseDataframeSlot)

    def read(self):
        # Clear the QTableWidget
        self.textOutput.setRowCount(0)
        self.textOutput.setColumnCount(len(self.dataframe.columns))

        # Populate the QTableWidget with the DataFrame data
        for index, row in self.dataframe.iterrows():
            row_position = self.textOutput.rowCount()
            self.textOutput.insertRow(row_position)

            for i, data in enumerate(row):
                item = QTableWidgetItem(str(data))
                self.textOutput.setItem(row_position, i, item)

        # Adjust column widths to content
        self.textOutput.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def addClicked(self):
        #Opens add window
        self.addWindow = addWindow(self.dataframe, self.course_dataframe)
        #Updates dataframe
        self.addWindow.communicate.updateDataframe.connect(self.updateDataframeSlot)

    def deleteClicked(self):
        #Opens delete window
        self.deleteWindow = deleteWindow(self.dataframe)
        #Updates dataframe
        self.deleteWindow.communicate.updateDataframe.connect(self.updateDataframeSlot)

    def editClicked(self):
        #Opens edit window
        self.editWindow = editWindow(self.dataframe, self.course_dataframe)
        #Updates dataframe
        self.editWindow.communicate.updateDataframe.connect(self.updateDataframeSlot)

    def saveClicked(self):
        #Save current dataframe to csv
        self.saveDataframe(self.dataframe, "students")

    def updateDataframeSlot(self, new_dataframe):
        #Update dataframe through signal and slot
        self.dataframe = new_dataframe
        self.read()

    def updateCourseDataframeSlot(self, new_course_dataframe):
        #Update course dataframe through signal and slot
        self.course_dataframe = new_course_dataframe
        self.read()

class addWindow(QMainWindow):
    """Add Student Window"""

    def __init__(self, dataframe, course_dataframe):
        #Load Add Window UI
        super(addWindow, self).__init__()
        uic.loadUi("addWindow.ui", self)
        #Adds the course codes from the course dataframe to the drop down combo box
        for index, row in course_dataframe.iterrows():
            value = row['course_code']
            self.courseInput.addItem(value)
        self.show()

        #Button trigger event for add window
        self.submitButton.clicked.connect(self.submitClicked)

        #Store dataframes to local class
        self.dataframe = dataframe
        self.course_dataframe = course_dataframe
        #Communicate object
        self.communicate = Communicate()

    def submitClicked(self):
        # Logic to check for duplicate ID number
        id_number = self.idNumberInput.text()
        existing_student = self.dataframe[self.dataframe["id_number"] == id_number]

        if not existing_student.empty:
            # Display error message if duplicate ID number
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("Duplicate ID Number: " + id_number)
            message.exec()
        else:
            # Logic to add new student to dataframe
            name = self.nameInput.text()
            course = self.courseInput.currentText()
            year = self.yearInput.currentText()
            sex = self.sexInput.currentText()
            if course == "No Course":
                status = "No"
            else:
                status = "Yes"
            student_data = [name, id_number, course, year, sex, status]
            column_names = ["name", "id_number", "course", "year", "sex", "status"]
            new_row = pd.DataFrame(columns=column_names)
            new_row.loc[0] = student_data
            self.dataframe = pd.concat([self.dataframe, new_row], ignore_index=True)

            # Emit signal
            self.communicate.updateDataframe.emit(self.dataframe)
            # Close window
            self.close()

class deleteWindow(QMainWindow):
    """Delete Student Window"""

    def __init__(self, dataframe):
        #Initialize Student Window UI
        super(deleteWindow, self).__init__()
        uic.loadUi("deleteWindow.ui", self)
        self.show()

        #Button trigger event for delete window
        self.submitButton.clicked.connect(self.submitClicked)

        #Store dataframe to local class
        self.dataframe = dataframe
        #Communication object
        self.communicate = Communicate()

    def submitClicked(self):
        # Logic to delete chosen student from dataframe
        student_to_delete = self.deleteInput.text()

        # Confirmation dialog for deleting a student
        reply = QMessageBox.question(self, 'Confirmation', f"Are you sure you want to delete {student_to_delete}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Proceed with deletion if yes
            self.dataframe = self.dataframe.drop(self.dataframe[self.dataframe["id_number"] == student_to_delete].index)
            self.dataframe = self.dataframe.reset_index(drop=True)
            # Emit signal and close window
            self.communicate.updateDataframe.emit(self.dataframe)
            self.close()
        else:
            # Cancel deletion if not confirmed
            return

class editWindow(QMainWindow):
    """Edit Student Window"""

    def __init__(self, dataframe, course_dataframe):
        #Initialize Student Window UI
        super(editWindow, self).__init__()
        uic.loadUi("editWindow.ui", self)
        # Adds the course codes from the course dataframe to the drop down combo box
        for index, row in course_dataframe.iterrows():
            value = row['course_code']
            self.courseInput.addItem(value)
        self.show()

        #Button trigger event for edit window
        self.submitButton.clicked.connect(self.submitClicked)
        self.editSubmitButton.clicked.connect(self.editSubmitClicked)

        #Store dataframe to local class
        self.dataframe = dataframe
        self.course_dataframe = course_dataframe
        #Communicate object
        self.communicate = Communicate()
        #Initialize row index for function use
        self.row_index = None

    def submitClicked(self):
        # Logic to output current values of a given student
        try:
            #Set disabled submit button to true if student is found
            self.editSubmitButton.setEnabled(True)
            student_to_edit = self.editInput.text()
            self.row_index = self.dataframe[self.dataframe["id_number"] == student_to_edit].index
            self.nameInput.setText(str(self.dataframe.loc[self.row_index, "name"].item()))
            self.idNumberInput.setText(str(self.dataframe.loc[self.row_index, "id_number"].item()))
            self.courseInput.setCurrentText(str(self.dataframe.loc[self.row_index, "course"].item()))
            self.yearInput.setCurrentText(str(self.dataframe.loc[self.row_index, "year"].item()))
            self.sexInput.setCurrentText(str(self.dataframe.loc[self.row_index, "sex"].item()))
            self.enrolledInput.setCurrentText(str(self.dataframe.loc[self.row_index, "status"].item()))
        except:
            #Set submit button to false if student is not found
            self.editSubmitButton.setEnabled(False)
            #Show error
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("Student not found")
            message.exec()

    def editSubmitClicked(self):
        # Logic to check for duplicate ID number
        id_number = self.idNumberInput.text()
        # Exclude the current row from the duplicate check
        modified_dataframe = self.dataframe.drop(self.row_index)
        existing_student = modified_dataframe[modified_dataframe["id_number"] == id_number]

        if not existing_student.empty:
            # Display error message if duplicate ID number is found
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("Duplicate ID Number: " + id_number)
            message.exec()
        else:
            # Logic to edit the values of a given student
            name = self.nameInput.text()
            course = self.courseInput.currentText()
            year = int(self.yearInput.currentText())  # Ensure year is converted to integer
            sex = self.sexInput.currentText()
            if course == "No Course":
                status = "No"
            else:
                status = "Yes"

            # Update dataframe with edited values
            self.dataframe.loc[self.row_index, "name"] = name
            self.dataframe.loc[self.row_index, "id_number"] = id_number
            self.dataframe.loc[self.row_index, "course"] = course
            self.dataframe.loc[self.row_index, "year"] = year
            self.dataframe.loc[self.row_index, "sex"] = sex
            self.dataframe.loc[self.row_index, "status"] = status
            # Emit signal and close window
            self.communicate.updateDataframe.emit(self.dataframe)
            self.close()

class courseWindow(QMainWindow):
    """Course View Window"""
    def __init__(self, dataframe, course_dataframe):
        #Initialize Course Window UI
        super(courseWindow, self).__init__()
        uic.loadUi("courseWindow.ui", self)
        self.show()

        #Button trigger events
        self.addButton.clicked.connect(self.addClicked)
        self.deleteButton.clicked.connect(self.deleteClicked)
        self.editButton.clicked.connect(self.editClicked)
        self.saveButton.clicked.connect(self.saveClicked)
        self.course_dataframe = course_dataframe
        self.dataframe = dataframe

        #Initialize child windows
        self.courseAddWindow = None
        self.courseDeleteWindow = None
        self.courseEditWindow = None
        #Communicate object
        self.communicate = Communicate()
        #Output initial course data
        self.read()

    def saveCourseDataFrameToDB(self, course_dataframe, table_name):
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 database='database',
                                                 user='root',
                                                 password='password')
            cursor = connection.cursor()
            cursor.execute(f"DELETE FROM {table_name};")
            for index, row in course_dataframe.iterrows():
                values = ', '.join(['%s'] * len(row))
                sql = (f"INSERT INTO {table_name} VALUES ({values})")
                cursor.execute(sql, tuple(row.values))
            connection.commit()
            print(f"{table_name} saved successfully.")
        except Error as e:
            print(f"Error saving {table_name}: {e}")
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView

    def read(self):
        # Assuming 'dataframe' is your DataFrame variable
        # Clear the QTableWidget
        self.textOutput.setRowCount(0)
        self.textOutput.setColumnCount(len(self.course_dataframe.columns))

        # Populate the QTableWidget with the DataFrame data
        for index, row in self.course_dataframe.iterrows():
            row_position = self.textOutput.rowCount()
            self.textOutput.insertRow(row_position)

            for i, data in enumerate(row):
                item = QTableWidgetItem(str(data))
                self.textOutput.setItem(row_position, i, item)

        # Adjust column widths to content
        self.textOutput.resizeColumnsToContents()

        # Optionally, adjust column widths to fill the QTableWidget
        self.textOutput.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def addClicked(self):
        #Opens Add Course Window
        self.courseAddWindow = courseAddWindow(self.course_dataframe)
        #Update course dataframe
        self.courseAddWindow.communicate.updateCourseDataframe.connect(self.updateCourseDataframeSlot)

    def deleteClicked(self):
        #Opens Delete Course Window
        self.courseDeleteWindow = courseDeleteWindow(self.course_dataframe)
        #Update course dataframe
        self.courseDeleteWindow.communicate.updateCourseDataframe.connect(self.updateCourseDataframeSlot)
        self.courseDeleteWindow.communicate.deletedCourse.connect(self.handleCourseDeletion)

    def editClicked(self):
        #Opens Edit Course Window
        self.courseEditWindow = courseEditWindow(self.dataframe, self.course_dataframe)
        #Update course dataframe
        self.courseEditWindow.communicate.updateDataframe.connect(self.updateDataframeSlot)
        self.courseEditWindow.communicate.updateCourseDataframe.connect(self.updateCourseDataframeSlot)

    def saveClicked(self):
        #Save course dataframe to csv
        self.saveCourseDataFrameToDB(self.course_dataframe, "courses")

    def updateCourseDataframeSlot(self, new_course_dataframe):
        # Update dataframe
        self.course_dataframe = new_course_dataframe
        #Updates text browser with new course dataframe
        self.read()
        #Emit signal to update course dataframe in Main Window
        self.communicate.updateCourseDataframe.emit(self.course_dataframe)

    def updateDataframeSlot(self, new_dataframe):
        # Update dataframe
        self.dataframe = new_dataframe
        #Updates text browser with new course dataframe
        self.read()
        #Emit signal to update course dataframe in Main Window
        self.communicate.updateDataframe.emit(self.dataframe)

    def handleCourseDeletion(self, deleted_course_code):
        # Find the row in the dataframe where the course code matches the deleted one
        for index, row in self.dataframe.iterrows():
            if row['course'] == deleted_course_code:
                # Set the course field to "NULL"
                self.dataframe.at[index, 'course'] = "No Course"
                self.dataframe.at[index, 'status'] = "No"
                break
        self.communicate.updateDataframe.emit(self.dataframe)

class courseAddWindow(QMainWindow):
    """Add Course Window"""
    def __init__(self, course_dataframe):
        #Initialize Add Course Window UI
        super(courseAddWindow, self).__init__()
        uic.loadUi("courseAddWindow.ui", self)
        self.show()

        #Store dataframe to local class
        self.course_dataframe = course_dataframe
        #Button trigger event
        self.submitButton.clicked.connect(self.submitClicked)
        #Communicate object
        self.communicate = Communicate()

    def submitClicked(self):
        #Logic to add new course to course datafrmae
        course_code = self.courseCodeInput.text()
        course_description = self.courseDescriptInput.text()
        course_data = [course_code, course_description]
        column_names = ["course_code", "course_description"]
        new_row = pd.DataFrame(columns=column_names)
        new_row.loc[0] = course_data
        self.course_dataframe = pd.concat([self.course_dataframe, new_row], ignore_index=True)

        #Emit signal and close window
        self.communicate.updateCourseDataframe.emit(self.course_dataframe)
        self.close()

class courseDeleteWindow(QMainWindow):
    """Delete Course Window"""
    def __init__(self, course_dataframe):
        #Initialize Delete Course Window
        super(courseDeleteWindow, self).__init__()
        uic.loadUi("courseDeleteWindow.ui", self)
        #Adds the course codes from the course dataframe to the drop down combo box
        for index, row in course_dataframe.iterrows():
            value = row['course_code']
            self.courseCodeInput.addItem(value)
        self.show()

        #Store course dataframe to local
        self.course_dataframe = course_dataframe
        #Button trigger event
        self.submitButton.clicked.connect(self.submitClicked)
        #Communicate object
        self.communicate = Communicate()

    def submitClicked(self):
        # Logic to delete a given course
        course_to_delete = self.courseCodeInput.currentText()
        # Confirmation dialog for deleting a course
        reply = QMessageBox.question(self, 'Confirmation', f"Are you sure you want to delete {course_to_delete}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # Proceed with deletion if yes
            self.course_dataframe = self.course_dataframe.drop(
                self.course_dataframe[self.course_dataframe["course_code"] == course_to_delete].index)
            self.course_dataframe = self.course_dataframe.reset_index(drop=True)
            # Emit signal and close window
            self.communicate.updateCourseDataframe.emit(self.course_dataframe)
            self.communicate.deletedCourse.emit(course_to_delete)  # Emit the custom signal with the deleted course code
            self.close()
        else:
            # Cancel deletion if no
            return

class courseEditWindow(QMainWindow):
    """Edit Course Window"""

    def __init__(self, dataframe,  course_dataframe):
        #Initialize Edit Course Window UI
        super(courseEditWindow, self).__init__()
        uic.loadUi("courseEditWindow.ui", self)
        self.show()

        #Button trigger event
        self.submitButton.clicked.connect(self.submitClicked)
        self.editButton.clicked.connect(self.editClicked)

        #Store course dataframe to local
        self.course_dataframe = course_dataframe
        self.dataframe = dataframe
        #Communicate object
        self.communicate = Communicate()
        #Initialize row index
        self.row_index = None

    def submitClicked(self):
        #Logic to edit course row
        try:
            #Set edit button to true if course is found
            self.editButton.setEnabled(True)
            course_to_edit = self.editCourseInput.text()
            self.row_index = self.course_dataframe[self.course_dataframe["course_code"] == course_to_edit].index
            self.courseCodeInput.setText(str(self.course_dataframe.loc[self.row_index, "course_code"].item()))
            self.courseDescriptInput.setText(str(self.course_dataframe.loc[self.row_index, "course_description"].item()))
        except:
            #Set edit button to false if course is not found
            self.editButton.setEnabled(False)
            #Show error
            message = QMessageBox()
            message.setWindowTitle("Error")
            message.setText("Course not found")
            message.exec()

    def editClicked(self):
        #Logic to edit given course
        course_code = self.courseCodeInput.text()
        course_description = self.courseDescriptInput.text()

        old_course_code = str(self.course_dataframe.loc[self.row_index, "course_code"].item())
        new_course_code = self.courseCodeInput.text()
        course_description = self.courseDescriptInput.text()

        self.course_dataframe.loc[self.row_index, "course_code"] = course_code
        self.course_dataframe.loc[self.row_index, "course_description"] = course_description

        print (old_course_code, new_course_code)
        # Update course_dataframe
        self.course_dataframe.loc[self.row_index, "course_code"] = new_course_code
        self.course_dataframe.loc[self.row_index, "course_description"] = course_description

        # Update references in dataframe
        self.dataframe['course'] = self.dataframe['course'].replace(old_course_code, new_course_code)
        # Emit signal and close window
        self.communicate.updateDataframe.emit(self.dataframe)
        self.communicate.updateCourseDataframe.emit(self.course_dataframe)
        self.close()

def main():
    #Run application event loop
    app = QApplication([])
    window = mainWindow()
    app.exec_()

if __name__ == "__main__":
    main()
