# Student GPA Manager

A desktop app built with Python and Tkinter to manage students, calculate GPA, and view grade charts.

## Features

- Add, edit, and delete students and their courses
- Automatic GPA calculation (weighted by course credits)
- Grade chart for each student with GPA and pass mark lines
- Light and dark mode
- Configurable maximum number of students and pass mark
- Search and sort the student list
- Export reports to TXT and CSV, and import students from CSV
- Data is saved automatically between sessions

## Requirements

- Python 3.8 or newer
- matplotlib

## Installation

    pip install -r requirements.txt

## Usage

    python student_manager_gui.py

## Notes

Student data is stored locally in `student_manager_data.json` and is not uploaded to GitHub.
