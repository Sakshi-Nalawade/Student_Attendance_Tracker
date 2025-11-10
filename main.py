import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from db_config import get_connection

PRIMARY_BG = "#f5f7fa"
CONTAINER_BG = "#e4e7ec"
HEADER_BG = "#205375"
ACCENT = "#358fdb"
SUCCESS = "#5cb85c"
DANGER = "#df4759"
MUTED = "#a6b1bb"
PRIMARY_TEXT = "#23272f"
BUTTON_HOVER_BG = "#dde6f6"
HEADER_ROW_BG = "#cdd7e0"
FONT_FAMILY = "Segoe UI"


def apply_hover(widget, normal_bg, hover_bg):
    widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
    widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))


class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Attendance Tracker")
        self.geometry("900x600")
        self.configure(bg=PRIMARY_BG)
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                self.attributes("-fullscreen", True)
        self.resizable(True, True)
        self.minsize(900, 600)
        container = tk.Frame(self, bg=CONTAINER_BG, bd=2, relief="ridge")
        container.pack(fill="both", expand=True, padx=22, pady=15)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (LoginPage, FacultyInfoPage, FacultyAttendancePage, StudentAttendancePage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(LoginPage)

    def show_frame(self, page):
        frame = self.frames[page]
        frame.tkraise()


class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=PRIMARY_BG)
        self.controller = controller

        header = tk.Frame(self, bg=HEADER_BG)
        header.pack(fill="x")
        title = tk.Label(
            header,
            text="🎓 Student Attendance Tracker",
            font=(FONT_FAMILY, 22, "bold"),
            bg=HEADER_BG,
            fg="white",
            padx=16,
            pady=10,
        )
        title.pack()

        content = tk.Frame(self, bg=CONTAINER_BG, bd=2, relief="groove")
        content.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            content, text="Select User Type:", font=(FONT_FAMILY, 12), bg=CONTAINER_BG
        ).pack(pady=8)
        self.user_type = ttk.Combobox(
            content, values=["Faculty", "Student"], state="readonly", width=25, font=(FONT_FAMILY, 11)
        )
        self.user_type.pack(pady=5)
        self.user_type.bind("<<ComboboxSelected>>", self.toggle_division_field)

        tk.Label(
            content, text="Username:", bg=CONTAINER_BG, font=(FONT_FAMILY, 12)
        ).pack(pady=(10, 2))
        self.username = ttk.Entry(content, width=30, font=(FONT_FAMILY, 11))
        self.username.pack(pady=3)

        self.div_label = tk.Label(content, text="Division:", bg=CONTAINER_BG, font=(FONT_FAMILY, 12))
        self.div_entry = ttk.Entry(content, width=30, font=(FONT_FAMILY, 11))
        self.div_label.pack_forget()
        self.div_entry.pack_forget()

        tk.Label(
            content, text="Password:", bg=CONTAINER_BG, font=(FONT_FAMILY, 12)
        ).pack(pady=(10, 2))
        self.password = ttk.Entry(content, width=30, font=(FONT_FAMILY, 11), show="*")
        self.password.pack(pady=3)

        login_btn = tk.Button(
            content,
            text="Login",
            font=(FONT_FAMILY, 12, "bold"),
            bg=ACCENT,
            fg="white",
            relief="flat",
            width=15,
            command=self.login,
        )
        login_btn.pack(pady=22)
        apply_hover(login_btn, ACCENT, BUTTON_HOVER_BG)

    def toggle_division_field(self, event=None):
        self.div_label.pack_forget()
        self.div_entry.pack_forget()

    def login(self):
        user_type = self.user_type.get().strip()
        username = self.username.get().strip().upper()
        password = self.password.get().strip()
        division = None

        if not user_type or not username or not password:
            messagebox.showwarning("Missing Info", "Please fill all required fields!")
            return

        if user_type == "Faculty":
            if password != username:
                messagebox.showerror("Invalid Password", "Faculty password is your name.")
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS faculty_prefs (
                    faculty_name VARCHAR(100) PRIMARY KEY,
                    subject VARCHAR(100),
                    year VARCHAR(20),
                    division VARCHAR(10)
                )
                """
            )
            conn.commit()
            cursor.execute(
                "SELECT subject, year, division FROM faculty_prefs WHERE faculty_name=%s", (username,)
            )
            pref = cursor.fetchone()
            conn.close()
            if pref and pref[0] and pref[2]:
                subject, _year, division = pref
                attendance_page = self.controller.frames[FacultyAttendancePage]
                attendance_page.set_subject(subject, division)
                self.controller.show_frame(FacultyAttendancePage)
            else:
                faculty_page = self.controller.frames[FacultyInfoPage]
                faculty_page.set_faculty_name(username)
                self.controller.show_frame(FacultyInfoPage)
        else:
            if password != "cse@123":
                messagebox.showerror("Invalid Password", "Incorrect student password!")
                return

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT student_id, name, division FROM students WHERE urn_no=%s", (username,)
            )
            result = cursor.fetchone()
            conn.close()
            if not result:
                messagebox.showerror("Access Denied", "Invalid URN or not registered.")
                return

            student_id, name, division = result
            student_page = self.controller.frames[StudentAttendancePage]
            student_page.set_student_info(name, division, username)
            self.controller.show_frame(StudentAttendancePage)


class FacultyInfoPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=CONTAINER_BG)
        self.controller = controller
        self.faculty_name = ""

        header = tk.Frame(self, bg=HEADER_BG)
        header.pack(fill="x")
        tk.Label(
            header,
            text="🧑🏫 Faculty Section",
            font=(FONT_FAMILY, 20, "bold"),
            bg=HEADER_BG,
            fg="white",
            pady=12,
        ).pack()

        form = tk.Frame(self, bg=CONTAINER_BG, bd=2, relief="ridge")
        form.pack(pady=16)

        tk.Label(form, text="Subject:", font=(FONT_FAMILY, 12), bg=CONTAINER_BG).grid(
            row=0, column=0, padx=10, pady=8, sticky="e"
        )
        # Subject dropdown (fetch subjects from DB)
        self.subject_entry = ttk.Combobox(form, width=28, font=(FONT_FAMILY, 11), state="readonly")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subject_name FROM subjects")
        subjects = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.subject_entry["values"] = subjects
        self.subject_entry.grid(row=0, column=1, pady=8)

        tk.Label(form, text="Year:", font=(FONT_FAMILY, 12), bg=CONTAINER_BG).grid(
            row=1, column=0, padx=10, pady=8, sticky="e"
        )
        self.year_entry = ttk.Entry(form, width=28, font=(FONT_FAMILY, 11))
        self.year_entry.grid(row=1, column=1, pady=8)

        tk.Label(form, text="Division:", font=(FONT_FAMILY, 12), bg=CONTAINER_BG).grid(
            row=2, column=0, padx=10, pady=8, sticky="e"
        )
        self.div_entry = ttk.Combobox(form, width=28, font=(FONT_FAMILY, 11), state="readonly", values=["A", "B"])
        self.div_entry.grid(row=2, column=1, pady=8)

        btn = tk.Button(
            self,
            text="Proceed →",
            font=(FONT_FAMILY, 12, "bold"),
            bg=SUCCESS,
            fg="white",
            relief="flat",
            width=15,
            command=self.proceed,
        )
        btn.pack(pady=18)
        apply_hover(btn, SUCCESS, BUTTON_HOVER_BG)

        back_btn = tk.Button(
            self,
            text="← Back",
            font=(FONT_FAMILY, 12),
            bg=DANGER,
            fg="white",
            relief="flat",
            command=lambda: controller.show_frame(LoginPage),
        )
        back_btn.pack()
        apply_hover(back_btn, DANGER, BUTTON_HOVER_BG)

    def set_faculty_name(self, name):
        self.faculty_name = name

    def proceed(self):
        subject = self.subject_entry.get().strip()
        division = self.div_entry.get().strip().upper()
        if not subject or not division:
            messagebox.showwarning("Missing Info", "Fill all required details!")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS faculty_prefs (
                faculty_name VARCHAR(100) PRIMARY KEY,
                subject VARCHAR(100),
                year VARCHAR(20),
                division VARCHAR(10)
            )
            """
        )
        conn.commit()
        cursor.execute(
            """
            INSERT INTO faculty_prefs (faculty_name, subject, year, division)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE subject=VALUES(subject), year=VALUES(year), division=VALUES(division)
            """,
            (self.faculty_name, subject, self.year_entry.get().strip(), division),
        )
        conn.commit()
        conn.close()
        attendance_page = self.controller.frames[FacultyAttendancePage]
        attendance_page.set_subject(subject, division)
        self.controller.show_frame(FacultyAttendancePage)


class FacultyAttendancePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=PRIMARY_BG)
        self.controller = controller
        self.subject_name = None
        self.division = None
        self.attendance_vars = {}

        header = tk.Frame(self, bg=HEADER_BG)
        header.pack(fill="x", pady=(0, 4))
        tk.Label(
            header,
            text="📋 Mark Attendance",
            font=(FONT_FAMILY, 20, "bold"),
            bg=HEADER_BG,
            fg="white",
            pady=8,
        ).pack()

        info = tk.Frame(self, bg=PRIMARY_BG)
        info.pack(pady=5)
        self.info_label = tk.Label(
            info, text="", font=(FONT_FAMILY, 13), bg=PRIMARY_BG, fg=PRIMARY_TEXT
        )
        self.info_label.pack()
        self.date_label = tk.Label(
            info, text="", font=(FONT_FAMILY, 11), bg=PRIMARY_BG, fg=MUTED
        )
        self.date_label.pack()

        container = tk.Frame(self, bg=CONTAINER_BG, bd=1, relief="ridge")
        container.pack(fill="both", expand=True, padx=20, pady=12)
        self.canvas = tk.Canvas(container, bg=CONTAINER_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=CONTAINER_BG)
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.scroll_window_id = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            delta = 0
            if getattr(event, "num", None) == 4:
                delta = -1
            elif getattr(event, "num", None) == 5:
                delta = 1
            elif hasattr(event, "delta"):
                delta = -1 * int(event.delta / 120)
            self.canvas.yview_scroll(delta, "units")

        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.canvas.bind_all("<Button-4>", _on_mousewheel)
        self.canvas.bind_all("<Button-5>", _on_mousewheel)

        def _resize_inner(event):
            try:
                self.canvas.itemconfig(self.scroll_window_id, width=event.width)
            except Exception:
                pass

        self.canvas.bind("<Configure>", _resize_inner)

        header_frame = tk.Frame(self.scroll_frame, bg=HEADER_ROW_BG)
        header_frame.pack(fill="x", pady=(0, 5))
        for col in range(4):
            header_frame.grid_columnconfigure(col, weight=1, uniform="hdr")
        tk.Label(
            header_frame, text="URN", font=(FONT_FAMILY, 12, "bold"), bg=HEADER_ROW_BG, anchor="center"
        ).grid(row=0, column=0, padx=5, sticky="nsew")
        tk.Label(
            header_frame, text="Roll No", font=(FONT_FAMILY, 12, "bold"), bg=HEADER_ROW_BG, anchor="center"
        ).grid(row=0, column=1, padx=5, sticky="nsew")
        tk.Label(
            header_frame, text="Name", font=(FONT_FAMILY, 12, "bold"), bg=HEADER_ROW_BG, anchor="center"
        ).grid(row=0, column=2, padx=5, sticky="nsew")
        tk.Label(
            header_frame, text="Mark Attendance", font=(FONT_FAMILY, 12, "bold"), bg=HEADER_ROW_BG, anchor="center"
        ).grid(row=0, column=3, padx=5, sticky="nsew")

        self.students_table_frame = tk.Frame(self.scroll_frame, bg=CONTAINER_BG)
        self.students_table_frame.pack(fill="x")
        for col in range(4):
            self.students_table_frame.grid_columnconfigure(col, weight=1, uniform="tbl")

        btns = tk.Frame(self, bg=PRIMARY_BG)
        btns.pack(pady=17)
        submit_btn = tk.Button(
            btns,
            text="Submit Attendance",
            font=(FONT_FAMILY, 12, "bold"),
            bg=ACCENT,
            fg="white",
            relief="flat",
            width=18,
            command=self.submit_attendance,
        )
        submit_btn.grid(row=0, column=0, padx=8)
        apply_hover(submit_btn, ACCENT, BUTTON_HOVER_BG)

        change_btn = tk.Button(
            btns,
            text="Change Preferences",
            font=(FONT_FAMILY, 12),
            bg=MUTED,
            fg="white",
            relief="flat",
            command=lambda: controller.show_frame(FacultyInfoPage),
        )
        change_btn.grid(row=0, column=1, padx=8)
        apply_hover(change_btn, MUTED, BUTTON_HOVER_BG)

        back_btn = tk.Button(
            btns,
            text="← Back",
            font=(FONT_FAMILY, 12),
            bg=DANGER,
            fg="white",
            relief="flat",
            command=lambda: controller.show_frame(LoginPage),
        )
        back_btn.grid(row=0, column=2, padx=8)
        apply_hover(back_btn, DANGER, BUTTON_HOVER_BG)

    def set_subject(self, subject, division):
        self.subject_name = subject
        self.division = division
        self.info_label.config(text=f"Subject: {subject} | Division: {division}")
        self.date_label.config(text=f"Date: {datetime.date.today():%d-%m-%Y}")
        self.attendance_vars.clear()
        for widget in self.students_table_frame.winfo_children():
            widget.destroy()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT student_id, urn_no, roll_no, name FROM students WHERE division=%s ORDER BY roll_no",
                       (division,))
        students = cursor.fetchall()
        conn.close()
        row_bg_default = CONTAINER_BG
        if not students:
            tk.Label(
                self.students_table_frame,
                text=f"No students found in Division {division}.",
                font=(FONT_FAMILY, 12),
                bg=CONTAINER_BG,
                fg="red"
            ).pack()
            return
        for i, (student_id, urn_no, roll_no, name) in enumerate(students):
            var = tk.BooleanVar()
            self.attendance_vars[student_id] = var
            tk.Label(self.students_table_frame, text=str(urn_no), font=(FONT_FAMILY, 11), bg=row_bg_default, anchor="center").grid(row=i, column=0, padx=5, pady=3, sticky="ew")
            tk.Label(self.students_table_frame, text=str(roll_no), font=(FONT_FAMILY, 11), bg=row_bg_default, anchor="center").grid(row=i, column=1, padx=5, sticky="ew")
            tk.Label(self.students_table_frame, text=name, font=(FONT_FAMILY, 11), bg=row_bg_default, anchor="center").grid(row=i, column=2, padx=5, sticky="ew")
            chk_wrap = tk.Frame(self.students_table_frame, bg=row_bg_default)
            chk_wrap.grid(row=i, column=3, padx=5, sticky="nsew")
            chk_wrap.grid_columnconfigure(0, weight=1)
            tk.Checkbutton(chk_wrap, variable=var, bg=row_bg_default).grid(row=0, column=0, sticky="")

    def submit_attendance(self):
        if not self.subject_name or not self.division:
            messagebox.showerror("Error", "No subject or division selected!")
            return
        if not self.attendance_vars:
            messagebox.showwarning("No Students", "No students to mark attendance for!")
            return
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", (self.subject_name,))
        result = cursor.fetchone()
        if result:
            subject_id = result[0]
        else:
            cursor.execute("INSERT INTO subjects(subject_name) VALUES(%s)", (self.subject_name,))
            conn.commit()
            subject_id = cursor.lastrowid
        today = datetime.date.today()
        student_ids = list(self.attendance_vars.keys())
        if student_ids:
            placeholders = ",".join(["%s"] * len(student_ids))
            delete_sql = (
                f"DELETE a FROM attendance a "
                f"JOIN students st ON a.student_id = st.student_id "
                f"WHERE a.subject_id=%s AND a.date=%s AND st.division=%s AND a.student_id IN ({placeholders})"
            )
            cursor.execute(delete_sql, (subject_id, today, self.division, *student_ids))
        for student_id, var in self.attendance_vars.items():
            status = "Present" if var.get() else "Absent"
            cursor.execute(
                "INSERT INTO attendance (student_id, subject_id, date, status) VALUES (%s, %s, %s, %s)",
                (student_id, subject_id, today, status)
            )
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Attendance recorded successfully!")


class StudentAttendancePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=CONTAINER_BG)
        self.controller = controller
        self.student_name = ""
        self.division = ""
        self.student_urn = ""

        header = tk.Frame(self, bg=HEADER_BG)
        header.pack(fill="x")
        tk.Label(
            header,
            text="👩🎓 Student Attendance Portal",
            font=(FONT_FAMILY, 18, "bold"),
            bg=HEADER_BG,
            fg="white",
            pady=10,
        ).pack()

        body = tk.Frame(self, bg=CONTAINER_BG, bd=2, relief="ridge")
        body.pack(expand=True, fill="both", pady=20)

        self.name_label = tk.Label(body, text="", font=(FONT_FAMILY, 14, "bold"), bg=CONTAINER_BG, fg=PRIMARY_TEXT)
        self.name_label.pack(pady=(0, 20))

        table_frame = tk.Frame(body, bg="white", bd=1, relief="solid")
        table_frame.pack(pady=10, padx=50, fill="x")
        style = ttk.Style()
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 12, "bold"))
        style.configure("Treeview", font=(FONT_FAMILY, 11), rowheight=28)
        self.tree = ttk.Treeview(table_frame, columns=("Subject", "Attendance"), show="headings", height=8)
        self.tree.heading("Subject", text="Subject")
        self.tree.heading("Attendance", text="Attendance (%)")
        self.tree.column("Subject", anchor="center", width=350)
        self.tree.column("Attendance", anchor="center", width=180)
        self.tree.pack(padx=10, pady=10, fill="x")

        btn_frame = tk.Frame(body, bg=CONTAINER_BG)
        btn_frame.pack(pady=20)
        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            font=(FONT_FAMILY, 12, "bold"),
            bg=SUCCESS,
            fg="white",
            relief="flat",
            width=12,
            command=self.update_table,
        )
        refresh_btn.grid(row=0, column=0, padx=10)
        apply_hover(refresh_btn, SUCCESS, BUTTON_HOVER_BG)

        back_btn = tk.Button(
            btn_frame,
            text="← Back",
            font=(FONT_FAMILY, 12, "bold"),
            bg=DANGER,
            fg="white",
            relief="flat",
            width=12,
            command=lambda: controller.show_frame(LoginPage),
        )
        back_btn.grid(row=0, column=1, padx=10)
        apply_hover(back_btn, DANGER, BUTTON_HOVER_BG)

    def set_student_info(self, name, division, urn):
        self.student_name = name
        self.division = division
        self.student_urn = urn
        self.name_label.config(text=f"Welcome, {name} ({division}) 👋")
        self.update_table()

    def update_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT s.subject_name,
                   (SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS percentage
            FROM attendance a
            JOIN subjects s ON a.subject_id = s.subject_id
            JOIN students st ON a.student_id = st.student_id
            WHERE st.urn_no = %s
            GROUP BY s.subject_name
        """
        cursor.execute(query, (self.student_urn,))
        records = cursor.fetchall()
        conn.close()
        if not records:
            self.tree.insert("", "end", values=("No records", "0%"))
            return
        for subject, percent in records:
            self.tree.insert("", "end", values=(subject, f"{percent:.2f}%"))


if __name__ == "__main__":
    app = AttendanceApp()
    app.mainloop()
