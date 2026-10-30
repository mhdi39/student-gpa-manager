import csv
import json
import os
import random
import string
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False

DEFAULT_MAX_STUDENTS = 20
MAX_STUDENTS_LIMIT = 1000
DEFAULT_PASS_MARK = 10.0
GRADE_MIN = 0
GRADE_MAX = 20
CREDIT_MIN = 1
CREDIT_MAX = 10
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_manager_data.json")
DEFAULT_TXT_NAME = "all_students_report.txt"
DEFAULT_CSV_NAME = "all_students_report.csv"

DEFAULT_COURSES = [
    ("Mathematics 1", 3),
    ("Programming 1", 3),
    ("Physical Education", 1),
    ("Data Structures", 2),
    ("Computer Architecture", 2),
]

THEMES = {
    "light": {
        "bg": "#f0f0f0",
        "fg": "#1f1f1f",
        "field": "#ffffff",
        "button": "#e1e1e1",
        "button_hover": "#d3dbe8",
        "select": "#bcd7ff",
        "select_fg": "#000000",
        "border": "#b5b5b5",
        "muted": "#8a8a8a",
        "ok": "#1a7f37",
        "fail": "#c62828",
        "bar": "#4C8BF5",
        "line": "#E8453C",
    },
    "dark": {
        "bg": "#1e1f22",
        "fg": "#e3e3e3",
        "field": "#2b2d30",
        "button": "#3a3d41",
        "button_hover": "#4a4e54",
        "select": "#2f5fa8",
        "select_fg": "#ffffff",
        "border": "#4a4d52",
        "muted": "#8b8f94",
        "ok": "#6fcf7f",
        "fail": "#ff7b72",
        "bar": "#5B9DF5",
        "line": "#FF6B61",
    },
}

STUDENT_COLUMNS = (
    ("id", "ID", 75),
    ("name", "Name", 140),
    ("number", "Student No.", 100),
    ("gpa", "GPA", 55),
)


def calculate_gpa(courses):
    total_weighted = 0.0
    total_credits = 0
    for course in courses.values():
        total_weighted += course["grade"] * course["credits"]
        total_credits += course["credits"]
    if total_credits == 0:
        return 0.0
    return total_weighted / total_credits


def generate_random_id(existing_ids):
    characters = string.ascii_uppercase + string.digits
    while True:
        new_id = "".join(random.choices(characters, k=6))
        if new_id not in existing_ids:
            return new_id


def clean_student(raw):
    courses = {}
    for course_name, course in raw["courses"].items():
        courses[str(course_name)] = {
            "grade": float(course["grade"]),
            "credits": int(course["credits"]),
        }
    student = {
        "name": str(raw["name"]),
        "student_number": str(raw["student_number"]),
        "phone": str(raw["phone"]),
        "courses": courses,
    }
    student["gpa"] = calculate_gpa(courses)
    return student


def natural_key(text):
    if text.isdigit():
        return (0, int(text), "")
    return (1, 0, text.lower())


def write_student_block(file, s_id, info, line_width):
    file.write(f"System ID      : {s_id}\n")
    file.write(f"Name           : {info['name']}\n")
    file.write(f"Student number : {info['student_number']}\n")
    file.write(f"Phone          : {info['phone']}\n")
    file.write(f"GPA            : {info['gpa']:.2f}\n")
    file.write("Courses and grades:\n")
    for course_name, course in info["courses"].items():
        file.write(f"  - {course_name} ({course['credits']} credits): {course['grade']:g}\n")
    file.write("-" * line_width + "\n")


def write_single_txt(path, s_id, info):
    with open(path, "w", encoding="utf-8") as file:
        file.write("=" * 44 + "\n")
        file.write(f"Student Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write("=" * 44 + "\n")
        write_student_block(file, s_id, info, 44)


def write_all_txt(path, students):
    with open(path, "w", encoding="utf-8") as file:
        file.write("=" * 50 + "\n")
        file.write(f"Full Students Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        file.write(f"Total students: {len(students)}\n")
        file.write("=" * 50 + "\n\n")
        for s_id, info in students.items():
            write_student_block(file, s_id, info, 50)
            file.write("\n")


def write_all_csv(path, students):
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([
            "System ID", "Name", "Student Number", "Phone",
            "GPA", "Course", "Credits", "Grade",
        ])
        for s_id, info in students.items():
            base = [s_id, info["name"], info["student_number"], info["phone"], f"{info['gpa']:.2f}"]
            if not info["courses"]:
                writer.writerow(base + ["", "", ""])
                continue
            for course_name, course in info["courses"].items():
                writer.writerow(base + [course_name, course["credits"], f"{course['grade']:g}"])


class FormDialog(tk.Toplevel):
    def __init__(self, parent, title, fields, initial=None, validator=None):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        self.configure(background=ttk.Style(self).lookup("TFrame", "background"))
        self.fields = fields
        self.validator = validator
        self.result = None
        self.variables = {}
        initial = initial or {}

        body = ttk.Frame(self, padding=15)
        body.grid()
        for row, field in enumerate(fields):
            ttk.Label(body, text=field["label"]).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=4)
            variable = tk.StringVar(value=str(initial.get(field["key"], "")))
            entry = ttk.Entry(body, textvariable=variable, width=30)
            entry.grid(row=row, column=1, pady=4)
            self.variables[field["key"]] = variable
            if row == 0:
                entry.focus_set()

        buttons = ttk.Frame(body)
        buttons.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(buttons, text="OK", command=self.on_ok).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left")

        self.bind("<Return>", lambda event: self.on_ok())
        self.bind("<Escape>", lambda event: self.destroy())
        self.wait_visibility()
        self.grab_set()

    def on_ok(self):
        values = {}
        for field in self.fields:
            key = field["key"]
            label = field["label"]
            kind = field.get("type", "text")
            raw = self.variables[key].get().strip()

            if not raw:
                messagebox.showerror("Invalid input", f"'{label}' cannot be empty.", parent=self)
                return

            if kind == "text":
                values[key] = raw
                continue

            try:
                value = int(raw) if kind == "int" else float(raw)
            except ValueError:
                messagebox.showerror("Invalid input", f"'{label}' must be a valid number.", parent=self)
                return

            low = field.get("low")
            high = field.get("high")
            if low is not None and high is not None and not (low <= value <= high):
                messagebox.showerror(
                    "Invalid input",
                    f"'{label}' must be between {low} and {high}.",
                    parent=self,
                )
                return
            values[key] = value

        if self.validator:
            error = self.validator(values)
            if error:
                messagebox.showerror("Invalid input", error, parent=self)
                return

        self.result = values
        self.destroy()


def ask_form(parent, title, fields, initial=None, validator=None):
    dialog = FormDialog(parent, title, fields, initial, validator)
    parent.wait_window(dialog)
    return dialog.result


class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student GPA Manager")
        self.root.geometry("1200x740")
        self.root.minsize(1050, 660)

        self.students = {}
        self.selected_id = None
        self.max_students = DEFAULT_MAX_STUDENTS
        self.pass_mark = DEFAULT_PASS_MARK
        self.sort_column = None
        self.sort_reverse = False
        self.save_error_shown = False
        self.menus = []
        self.student_buttons = []
        self.theme = THEMES["light"]

        self.dark_mode = tk.BooleanVar(value=False)
        self.search_var = tk.StringVar()
        self.count_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.number_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.gpa_var = tk.StringVar()
        self.standing_var = tk.StringVar()
        self.stats_var = tk.StringVar()

        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.bold_font = tkfont.nametofont("TkDefaultFont").copy()
        self.bold_font.configure(weight="bold")
        self.big_font = tkfont.nametofont("TkDefaultFont").copy()
        self.big_font.configure(weight="bold", size=self.big_font.cget("size") + 2)

        startup_warning = self.load_data()
        self.build_menu()
        self.build_layout()
        self.apply_theme()
        self.search_var.trace_add("write", lambda *args: self.refresh_students())
        self.refresh_students()

        self.root.bind("<Control-n>", lambda event: self.add_student())
        self.root.bind("<Control-f>", lambda event: self.search_entry.focus_set())
        self.root.bind("<Control-d>", lambda event: self.toggle_dark_shortcut())
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        if startup_warning:
            messagebox.showwarning("Saved data problem", startup_warning)

    def load_data(self):
        if not os.path.exists(DATA_FILE):
            return None
        try:
            with open(DATA_FILE, encoding="utf-8") as file:
                data = json.load(file)
            settings = data.get("settings", {})
            students = {str(key): clean_student(value) for key, value in data.get("students", {}).items()}
            max_students = int(settings.get("max_students", DEFAULT_MAX_STUDENTS))
            pass_mark = float(settings.get("pass_mark", DEFAULT_PASS_MARK))
            dark = bool(settings.get("dark_mode", False))
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            backup = DATA_FILE + ".bak"
            try:
                os.replace(DATA_FILE, backup)
                return f"The saved data file could not be read.\nA copy was kept as:\n{backup}"
            except OSError:
                return "The saved data file could not be read."

        self.students = students
        self.max_students = min(MAX_STUDENTS_LIMIT, max(1, max_students, len(students)))
        self.pass_mark = min(max(pass_mark, GRADE_MIN), GRADE_MAX)
        self.dark_mode.set(dark)
        return None

    def save_data(self):
        data = {
            "settings": {
                "max_students": self.max_students,
                "pass_mark": self.pass_mark,
                "dark_mode": self.dark_mode.get(),
            },
            "students": self.students,
        }
        temp_path = DATA_FILE + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            os.replace(temp_path, DATA_FILE)
        except OSError as error:
            if not self.save_error_shown:
                self.save_error_shown = True
                messagebox.showerror("Auto-save failed", f"Your changes could not be saved:\n{error}")
            return False
        return True

    def commit(self, select_id=None):
        self.save_data()
        self.refresh_students(select_id=select_id)

    def build_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Add student", accelerator="Ctrl+N", command=self.add_student)
        file_menu.add_separator()
        file_menu.add_command(label="Import students from CSV...", command=self.import_csv)
        file_menu.add_command(label="Export all students to TXT...", command=self.export_all_txt)
        file_menu.add_command(label="Export all students to CSV...", command=self.export_all_csv)
        file_menu.add_command(label="Save selected chart as PNG...", command=self.save_chart_png)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_checkbutton(
            label="Dark mode", accelerator="Ctrl+D",
            variable=self.dark_mode, command=self.toggle_theme,
        )
        view_menu.add_command(label="Focus search", accelerator="Ctrl+F",
                              command=lambda: self.search_entry.focus_set())
        menu_bar.add_cascade(label="View", menu=view_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Preferences...", command=self.open_preferences)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        self.menus = [menu_bar, file_menu, view_menu, settings_menu]
        self.root.config(menu=menu_bar)

    def build_layout(self):
        status = ttk.Label(self.root, textvariable=self.stats_var, anchor="w", padding=(12, 6))
        status.pack(side="bottom", fill="x")

        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(main, text="Students", padding=8)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        left.rowconfigure(1, weight=1)

        search_row = ttk.Frame(left)
        search_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(search_row, text="Search:").pack(side="left", padx=(0, 6))
        self.search_entry = ttk.Entry(search_row, textvariable=self.search_var, width=28)
        self.search_entry.pack(side="left", fill="x", expand=True)

        tree_frame = ttk.Frame(left)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        self.students_tree = ttk.Treeview(
            tree_frame,
            columns=[column for column, _, _ in STUDENT_COLUMNS],
            show="headings",
            selectmode="browse",
            height=16,
        )
        for column, heading, width in STUDENT_COLUMNS:
            self.students_tree.heading(column, text=heading, command=lambda c=column: self.sort_by(c))
            self.students_tree.column(column, width=width, anchor="center" if column == "gpa" else "w")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=scrollbar.set)
        self.students_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.students_tree.bind("<<TreeviewSelect>>", self.on_student_select)
        self.students_tree.bind("<Delete>", lambda event: self.delete_student())

        ttk.Label(left, textvariable=self.count_var).grid(row=2, column=0, sticky="w", pady=(8, 4))

        left_buttons = ttk.Frame(left)
        left_buttons.grid(row=3, column=0, sticky="ew")
        self.add_student_button = ttk.Button(left_buttons, text="Add Student", command=self.add_student)
        self.add_student_button.pack(side="left", padx=(0, 6))
        delete_student_button = ttk.Button(left_buttons, text="Delete Student", command=self.delete_student)
        delete_student_button.pack(side="left")
        self.student_buttons.append(delete_student_button)

        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        details = ttk.LabelFrame(right, text="Student Details", padding=8)
        details.grid(row=0, column=0, sticky="ew")
        details.columnconfigure(1, weight=1)
        for row, (label, variable) in enumerate((
            ("Name:", self.name_var),
            ("Student number:", self.number_var),
            ("Phone:", self.phone_var),
        )):
            ttk.Label(details, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=2)
            ttk.Label(details, textvariable=variable).grid(row=row, column=1, sticky="w", pady=2)
        ttk.Label(details, text="GPA:").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=2)
        ttk.Label(details, textvariable=self.gpa_var, font=self.big_font).grid(row=3, column=1, sticky="w", pady=2)
        ttk.Label(details, text="Standing:").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=2)
        self.standing_label = ttk.Label(details, textvariable=self.standing_var, font=self.bold_font)
        self.standing_label.grid(row=4, column=1, sticky="w", pady=2)
        edit_student_button = ttk.Button(details, text="Edit Student", command=self.edit_student)
        edit_student_button.grid(row=0, column=2, rowspan=2, padx=(10, 0))
        self.student_buttons.append(edit_student_button)

        courses = ttk.LabelFrame(right, text="Courses", padding=8)
        courses.grid(row=1, column=0, sticky="ew", pady=8)
        courses.columnconfigure(0, weight=1)
        self.courses_tree = ttk.Treeview(
            courses,
            columns=("course", "credits", "grade"),
            show="headings",
            selectmode="browse",
            height=5,
        )
        for column, heading, width, anchor in (
            ("course", "Course", 260, "w"),
            ("credits", "Credits", 80, "center"),
            ("grade", "Grade", 80, "center"),
        ):
            self.courses_tree.heading(column, text=heading)
            self.courses_tree.column(column, width=width, anchor=anchor)
        self.courses_tree.grid(row=0, column=0, sticky="ew")
        self.courses_tree.bind("<Double-1>", lambda event: self.edit_course())

        course_buttons = ttk.Frame(courses)
        course_buttons.grid(row=1, column=0, sticky="w", pady=(8, 0))
        for text, command in (
            ("Add Course", self.add_course),
            ("Edit Course", self.edit_course),
            ("Delete Course", self.delete_course),
            ("Save Student Report (TXT)", self.save_student_report),
        ):
            button = ttk.Button(course_buttons, text=text, command=command)
            button.pack(side="left", padx=(0, 6))
            self.student_buttons.append(button)

        chart_frame = ttk.LabelFrame(right, text="Grades Chart", padding=4)
        chart_frame.grid(row=2, column=0, sticky="nsew")
        if CHART_AVAILABLE:
            self.figure = Figure(figsize=(6, 3.2), dpi=100)
            self.chart_canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
            self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            self.figure = None
            self.chart_canvas = None
            ttk.Label(
                chart_frame,
                text="Charts need matplotlib.\nInstall it with: pip install matplotlib",
                justify="center",
            ).pack(expand=True)

    def apply_theme(self):
        t = THEMES["dark" if self.dark_mode.get() else "light"]
        self.theme = t
        s = self.style

        self.root.configure(background=t["bg"])
        s.configure(
            ".", background=t["bg"], foreground=t["fg"], fieldbackground=t["field"],
            bordercolor=t["border"], lightcolor=t["bg"], darkcolor=t["bg"],
            troughcolor=t["field"], focuscolor=t["bg"], insertcolor=t["fg"],
        )
        s.configure("TLabelframe", background=t["bg"], bordercolor=t["border"])
        s.configure("TLabelframe.Label", background=t["bg"], foreground=t["fg"])
        s.configure("TButton", background=t["button"], foreground=t["fg"],
                    bordercolor=t["border"], padding=(10, 4))
        s.map(
            "TButton",
            background=[("disabled", t["bg"]), ("pressed", t["select"]), ("active", t["button_hover"])],
            foreground=[("disabled", t["muted"])],
        )
        s.configure("TEntry", fieldbackground=t["field"], foreground=t["fg"],
                    insertcolor=t["fg"], bordercolor=t["border"])
        s.configure("Treeview", background=t["field"], fieldbackground=t["field"],
                    foreground=t["fg"], bordercolor=t["border"], rowheight=24)
        s.map("Treeview", background=[("selected", t["select"])],
              foreground=[("selected", t["select_fg"])])
        s.configure("Treeview.Heading", background=t["button"], foreground=t["fg"],
                    relief="flat", bordercolor=t["border"])
        s.map("Treeview.Heading", background=[("active", t["button_hover"])])
        s.configure("TScrollbar", background=t["button"], troughcolor=t["field"],
                    bordercolor=t["border"], arrowcolor=t["fg"])

        for menu in self.menus:
            menu.configure(
                background=t["field"], foreground=t["fg"],
                activebackground=t["select"], activeforeground=t["select_fg"],
            )
        for menu in self.menus[1:]:
            menu.configure(selectcolor=t["fg"])

        self.students_tree.tag_configure("fail", foreground=t["fail"])
        self.courses_tree.tag_configure("fail", foreground=t["fail"])
        self.show_details()

    def toggle_theme(self):
        self.apply_theme()
        self.save_data()

    def toggle_dark_shortcut(self):
        self.dark_mode.set(not self.dark_mode.get())
        self.toggle_theme()

    def set_student_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        for button in self.student_buttons:
            button.config(state=state)

    def number_exists(self, number, exclude_id=None):
        for s_id, info in self.students.items():
            if s_id != exclude_id and info["student_number"] == number:
                return True
        return False

    def sort_key(self, item):
        s_id, info = item
        if self.sort_column == "gpa":
            return info["gpa"]
        if self.sort_column == "name":
            return info["name"].lower()
        if self.sort_column == "number":
            return natural_key(info["student_number"])
        return s_id

    def sort_by(self, column):
        if self.sort_column == column:
            if not self.sort_reverse:
                self.sort_reverse = True
            else:
                self.sort_column = None
                self.sort_reverse = False
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_students()

    def update_headings(self):
        for column, heading, _ in STUDENT_COLUMNS:
            text = heading
            if column == self.sort_column:
                text += " v" if self.sort_reverse else " ^"
            self.students_tree.heading(column, text=text)

    def refresh_students(self, select_id=None):
        target = select_id or self.selected_id
        query = self.search_var.get().strip().lower()

        items = []
        for s_id, info in self.students.items():
            haystack = f"{s_id} {info['name']} {info['student_number']}".lower()
            if query in haystack:
                items.append((s_id, info))
        if self.sort_column:
            items.sort(key=self.sort_key, reverse=self.sort_reverse)

        self.students_tree.delete(*self.students_tree.get_children())
        for s_id, info in items:
            tags = ("fail",) if info["gpa"] < self.pass_mark else ()
            self.students_tree.insert(
                "", "end", iid=s_id, tags=tags,
                values=(s_id, info["name"], info["student_number"], f"{info['gpa']:.2f}"),
            )

        if target and self.students_tree.exists(target):
            self.selected_id = target
            self.students_tree.selection_set(target)
            self.students_tree.see(target)
        else:
            self.selected_id = None

        self.update_headings()
        self.count_var.set(f"Students: {len(self.students)} / {self.max_students}")
        full = len(self.students) >= self.max_students
        self.add_student_button.config(state="disabled" if full else "normal")
        self.update_stats()
        self.show_details()

    def update_stats(self):
        if not self.students:
            self.stats_var.set("No students yet. Click 'Add Student' to start.")
            return
        gpas = [info["gpa"] for info in self.students.values()]
        average = sum(gpas) / len(gpas)
        top_info = max(self.students.values(), key=lambda info: info["gpa"])
        below = sum(1 for gpa in gpas if gpa < self.pass_mark)
        self.stats_var.set(
            f"Class average GPA: {average:.2f}   |   "
            f"Top student: {top_info['name']} ({top_info['gpa']:.2f})   |   "
            f"Below pass mark ({self.pass_mark:g}): {below}"
        )

    def on_student_select(self, event):
        selection = self.students_tree.selection()
        self.selected_id = selection[0] if selection else None
        self.show_details()

    def show_details(self):
        self.courses_tree.delete(*self.courses_tree.get_children())

        if self.selected_id is None or self.selected_id not in self.students:
            self.name_var.set("-")
            self.number_var.set("-")
            self.phone_var.set("-")
            self.gpa_var.set("-")
            self.standing_var.set("-")
            self.standing_label.configure(foreground=self.theme["fg"])
            self.set_student_buttons(False)
            self.draw_chart(None)
            return

        info = self.students[self.selected_id]
        self.name_var.set(info["name"])
        self.number_var.set(info["student_number"])
        self.phone_var.set(info["phone"])
        self.gpa_var.set(f"{info['gpa']:.2f}")

        higher = sum(1 for other in self.students.values() if other["gpa"] > info["gpa"])
        passed = info["gpa"] >= self.pass_mark
        status = "Passed" if passed else "Below pass mark"
        self.standing_var.set(f"{status}  (rank {higher + 1} of {len(self.students)})")
        self.standing_label.configure(foreground=self.theme["ok"] if passed else self.theme["fail"])

        for course_name, course in info["courses"].items():
            tags = ("fail",) if course["grade"] < self.pass_mark else ()
            self.courses_tree.insert(
                "", "end", iid=course_name, tags=tags,
                values=(course_name, course["credits"], f"{course['grade']:g}"),
            )
        self.set_student_buttons(True)
        self.draw_chart(info)

    def draw_chart(self, info):
        if not CHART_AVAILABLE:
            return

        t = self.theme
        self.figure.clear()
        self.figure.set_facecolor(t["bg"])
        axes = self.figure.add_subplot(111)
        axes.set_facecolor(t["field"])
        axes.tick_params(colors=t["fg"])
        for spine in axes.spines.values():
            spine.set_color(t["border"])

        if info is None or not info["courses"]:
            message = "Select a student to see the chart" if info is None else "This student has no courses"
            axes.text(0.5, 0.5, message, ha="center", va="center",
                      transform=axes.transAxes, color=t["fg"])
            axes.set_xticks([])
            axes.set_yticks([])
        else:
            names = list(info["courses"].keys())
            grades = [info["courses"][name]["grade"] for name in names]
            bars = axes.bar(names, grades, color=t["bar"])
            axes.axhline(info["gpa"], color=t["line"], linestyle="--", linewidth=2,
                         label=f"GPA = {info['gpa']:.2f}")
            axes.axhline(self.pass_mark, color=t["muted"], linestyle=":", linewidth=1.5,
                         label=f"Pass mark = {self.pass_mark:g}")
            axes.set_ylim(GRADE_MIN, GRADE_MAX + 2)
            axes.set_ylabel("Grade", color=t["fg"])
            axes.set_title(f"Grades and GPA - {info['name']}", color=t["fg"])
            legend = axes.legend(loc="lower right")
            legend.get_frame().set_facecolor(t["bg"])
            legend.get_frame().set_edgecolor(t["border"])
            for text in legend.get_texts():
                text.set_color(t["fg"])
            for bar, grade in zip(bars, grades):
                axes.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                          f"{grade:g}", ha="center", va="bottom", fontsize=9, color=t["fg"])
            for label in axes.get_xticklabels():
                label.set_rotation(15)
                label.set_ha("right")

        self.figure.tight_layout()
        self.chart_canvas.draw_idle()

    def add_student(self):
        if len(self.students) >= self.max_students:
            messagebox.showwarning(
                "Limit reached",
                f"Maximum of {self.max_students} students reached.\n"
                "You can raise the limit in Settings > Preferences.",
            )
            return

        fields = [
            {"key": "name", "label": "Full name"},
            {"key": "student_number", "label": "Student number"},
            {"key": "phone", "label": "Phone number"},
        ]
        for index, (course_name, credits) in enumerate(DEFAULT_COURSES):
            fields.append({
                "key": f"grade_{index}",
                "label": f"{course_name} grade ({credits} cr.)",
                "type": "float",
                "low": GRADE_MIN,
                "high": GRADE_MAX,
            })

        def validator(values):
            if self.number_exists(values["student_number"]):
                return "This student number is already in use."
            return None

        result = ask_form(self.root, "Add Student", fields, validator=validator)
        if result is None:
            return

        courses = {}
        for index, (course_name, credits) in enumerate(DEFAULT_COURSES):
            courses[course_name] = {"grade": result[f"grade_{index}"], "credits": credits}

        new_id = generate_random_id(self.students)
        self.students[new_id] = {
            "name": result["name"],
            "student_number": result["student_number"],
            "phone": result["phone"],
            "courses": courses,
            "gpa": calculate_gpa(courses),
        }
        self.search_var.set("")
        self.commit(select_id=new_id)

    def edit_student(self):
        if self.selected_id is None:
            return
        s_id = self.selected_id
        info = self.students[s_id]
        fields = [
            {"key": "name", "label": "Full name"},
            {"key": "student_number", "label": "Student number"},
            {"key": "phone", "label": "Phone number"},
        ]

        def validator(values):
            if self.number_exists(values["student_number"], exclude_id=s_id):
                return "This student number is already in use."
            return None

        result = ask_form(self.root, "Edit Student", fields, initial=info, validator=validator)
        if result is None:
            return
        info["name"] = result["name"]
        info["student_number"] = result["student_number"]
        info["phone"] = result["phone"]
        self.commit(select_id=s_id)

    def delete_student(self):
        if self.selected_id is None:
            return
        info = self.students[self.selected_id]
        confirmed = messagebox.askyesno(
            "Delete student",
            f"Are you sure you want to delete {info['name']}?",
        )
        if not confirmed:
            return
        del self.students[self.selected_id]
        self.selected_id = None
        self.commit()

    def course_fields(self):
        return [
            {"key": "name", "label": "Course name"},
            {"key": "credits", "label": f"Credits ({CREDIT_MIN}-{CREDIT_MAX})", "type": "int",
             "low": CREDIT_MIN, "high": CREDIT_MAX},
            {"key": "grade", "label": f"Grade ({GRADE_MIN}-{GRADE_MAX})", "type": "float",
             "low": GRADE_MIN, "high": GRADE_MAX},
        ]

    def add_course(self):
        if self.selected_id is None:
            return
        s_id = self.selected_id
        student = self.students[s_id]

        def validator(values):
            if values["name"] in student["courses"]:
                return "This course already exists."
            return None

        result = ask_form(self.root, "Add Course", self.course_fields(), validator=validator)
        if result is None:
            return
        student["courses"][result["name"]] = {"grade": result["grade"], "credits": result["credits"]}
        student["gpa"] = calculate_gpa(student["courses"])
        self.commit(select_id=s_id)

    def selected_course(self):
        selection = self.courses_tree.selection()
        if not selection:
            messagebox.showinfo("Select a course", "Please select a course from the list first.")
            return None
        return selection[0]

    def edit_course(self):
        if self.selected_id is None:
            return
        old_name = self.selected_course()
        if old_name is None:
            return
        s_id = self.selected_id
        student = self.students[s_id]
        course = student["courses"][old_name]
        initial = {"name": old_name, "credits": course["credits"], "grade": f"{course['grade']:g}"}

        def validator(values):
            if values["name"] != old_name and values["name"] in student["courses"]:
                return "A course with this name already exists."
            return None

        result = ask_form(self.root, "Edit Course", self.course_fields(), initial=initial, validator=validator)
        if result is None:
            return

        updated = {"grade": result["grade"], "credits": result["credits"]}
        student["courses"] = {
            (result["name"] if key == old_name else key): (updated if key == old_name else value)
            for key, value in student["courses"].items()
        }
        student["gpa"] = calculate_gpa(student["courses"])
        self.commit(select_id=s_id)

    def delete_course(self):
        if self.selected_id is None:
            return
        course_name = self.selected_course()
        if course_name is None:
            return
        confirmed = messagebox.askyesno("Delete course", f"Delete the course '{course_name}'?")
        if not confirmed:
            return
        student = self.students[self.selected_id]
        del student["courses"][course_name]
        student["gpa"] = calculate_gpa(student["courses"])
        self.commit(select_id=self.selected_id)

    def open_preferences(self):
        fields = [
            {"key": "max_students", "label": f"Maximum students (1-{MAX_STUDENTS_LIMIT})",
             "type": "int", "low": 1, "high": MAX_STUDENTS_LIMIT},
            {"key": "pass_mark", "label": f"Pass mark ({GRADE_MIN}-{GRADE_MAX})",
             "type": "float", "low": GRADE_MIN, "high": GRADE_MAX},
        ]

        def validator(values):
            if values["max_students"] < len(self.students):
                return (
                    f"You already have {len(self.students)} students.\n"
                    "The maximum cannot be lower than that."
                )
            return None

        initial = {"max_students": self.max_students, "pass_mark": f"{self.pass_mark:g}"}
        result = ask_form(self.root, "Preferences", fields, initial=initial, validator=validator)
        if result is None:
            return
        self.max_students = result["max_students"]
        self.pass_mark = result["pass_mark"]
        self.commit(select_id=self.selected_id)

    def save_student_report(self):
        if self.selected_id is None:
            return
        path = filedialog.asksaveasfilename(
            title="Save student report",
            defaultextension=".txt",
            initialfile=f"student_{self.selected_id}.txt",
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            return
        try:
            write_single_txt(path, self.selected_id, self.students[self.selected_id])
        except OSError as error:
            messagebox.showerror("Save failed", f"Could not save the file:\n{error}")
            return
        messagebox.showinfo("Report saved", f"Report saved to:\n{path}")

    def save_chart_png(self):
        if not CHART_AVAILABLE:
            messagebox.showinfo("Chart unavailable", "Install matplotlib first: pip install matplotlib")
            return
        if self.selected_id is None:
            messagebox.showinfo("Select a student", "Please select a student first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save chart as PNG",
            defaultextension=".png",
            initialfile=f"chart_{self.selected_id}.png",
            filetypes=[("PNG images", "*.png")],
        )
        if not path:
            return
        try:
            self.figure.savefig(path, dpi=150, facecolor=self.figure.get_facecolor())
        except (OSError, ValueError) as error:
            messagebox.showerror("Save failed", f"Could not save the chart:\n{error}")
            return
        messagebox.showinfo("Chart saved", f"Chart saved to:\n{path}")

    def export_all_txt(self):
        if not self.students:
            messagebox.showinfo("Nothing to export", "There are no students to export yet.")
            return
        path = filedialog.asksaveasfilename(
            title="Export all students to TXT",
            defaultextension=".txt",
            initialfile=DEFAULT_TXT_NAME,
            filetypes=[("Text files", "*.txt")],
        )
        if not path:
            return
        try:
            write_all_txt(path, self.students)
        except OSError as error:
            messagebox.showerror("Export failed", f"Could not save the file:\n{error}")
            return
        messagebox.showinfo("Export complete", f"All students saved to:\n{path}")

    def export_all_csv(self):
        if not self.students:
            messagebox.showinfo("Nothing to export", "There are no students to export yet.")
            return
        path = filedialog.asksaveasfilename(
            title="Export all students to CSV",
            defaultextension=".csv",
            initialfile=DEFAULT_CSV_NAME,
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return
        try:
            write_all_csv(path, self.students)
        except OSError as error:
            messagebox.showerror("Export failed", f"Could not save the file:\n{error}")
            return
        messagebox.showinfo("Export complete", f"All students saved to:\n{path}")

    def import_csv(self):
        path = filedialog.askopenfilename(
            title="Import students from CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, newline="", encoding="utf-8-sig") as file:
                rows = list(csv.DictReader(file))
        except (OSError, UnicodeDecodeError, csv.Error) as error:
            messagebox.showerror("Import failed", f"Could not read the file:\n{error}")
            return

        required = {"Name", "Student Number", "Phone", "Course", "Credits", "Grade"}
        if not rows or not required.issubset(rows[0].keys()):
            messagebox.showerror(
                "Import failed",
                "This file format is not recognised.\nUse a CSV file exported by this program.",
            )
            return

        grouped = {}
        bad_rows = 0
        for row in rows:
            number = (row.get("Student Number") or "").strip()
            name = (row.get("Name") or "").strip()
            if not number or not name:
                bad_rows += 1
                continue
            entry = grouped.setdefault(number, {
                "id": (row.get("System ID") or "").strip().upper(),
                "name": name,
                "phone": (row.get("Phone") or "").strip(),
                "courses": {},
            })
            course_name = (row.get("Course") or "").strip()
            if not course_name:
                continue
            try:
                credits = int(row["Credits"])
                grade = float(row["Grade"])
            except (TypeError, ValueError):
                bad_rows += 1
                continue
            if not (CREDIT_MIN <= credits <= CREDIT_MAX and GRADE_MIN <= grade <= GRADE_MAX):
                bad_rows += 1
                continue
            entry["courses"][course_name] = {"grade": grade, "credits": credits}

        imported = 0
        skipped = 0
        for number, entry in grouped.items():
            if self.number_exists(number) or len(self.students) >= self.max_students:
                skipped += 1
                continue
            s_id = entry["id"] if entry["id"] and entry["id"] not in self.students else generate_random_id(self.students)
            self.students[s_id] = {
                "name": entry["name"],
                "student_number": number,
                "phone": entry["phone"],
                "courses": entry["courses"],
                "gpa": calculate_gpa(entry["courses"]),
            }
            imported += 1

        self.search_var.set("")
        self.commit(select_id=self.selected_id)
        messagebox.showinfo(
            "Import finished",
            f"Imported students: {imported}\n"
            f"Skipped students (duplicate number or limit reached): {skipped}\n"
            f"Invalid rows ignored: {bad_rows}",
        )

    def on_exit(self):
        self.save_data()
        self.root.destroy()


def main():
    root = tk.Tk()
    StudentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
