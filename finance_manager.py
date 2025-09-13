import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
import sqlite3
import calendar
from collections import defaultdict
import hashlib

# برای نمایش صحیح فارسی
try:
    from bidi.algorithm import get_display
    import arabic_reshaper
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False
    print("برای نمایش صحیح فارسی، کتابخانه‌های زیر را نصب کنید:")
    print("pip install python-bidi arabic-reshaper")

# تابع تصحیح فارسی
def fix_persian_text(text):
    """تصحیح نمایش فارسی"""
    if not isinstance(text, str):
        return text
        
    # اگر متن انگلیسی باشه، دست نزن
    if text.replace(' ', '').replace('.', '').replace(',', '').isascii():
        return text
        
    # اگر کتابخانه‌ها نصب باشن
    if BIDI_AVAILABLE:
        try:
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        except:
            return text
    else:
        # اگر کتابخانه‌ها نصب نباشن، حداقل برعکس نکن
        return text

class UltimateFinanceManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(fix_persian_text("مدیریت مالی حرفه‌ای"))
        self.root.geometry("1000x750")
        
        # تنظیم فونت فارسی
        self.setup_persian_fonts()
        
        # متغیرهای امنیتی
        self.password = ""
        self.user_logged_in = False
        self.current_user_id = None
        
        # اتصال به دیتابیس
        self.setup_database()
        
        # متغیرها
        self.type_var = tk.StringVar(value=fix_persian_text("درآمد"))
        self.amount_var = tk.StringVar()
        self.desc_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.filter_var = tk.StringVar(value=fix_persian_text("همه"))
        self.month_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.currency_var = tk.StringVar(value="تومان")
        self.goal_amount_var = tk.StringVar()
        self.reminder_desc_var = tk.StringVar()
        self.reminder_date_var = tk.StringVar()
        
        # رنگ‌های تم
        self.colors = {
            'income': '#4CAF50',    # سبز
            'expense': '#F44336',   # قرمز
            'balance': '#2196F3',   # آبی
            'background': '#f0f0f0',
            'card': '#ffffff',
            'goal_progress': '#FF9800'  # نارنجی برای پیشرفت
        }
        
        # نمایش صفحه ورود
        self.show_login_screen()
        
    def setup_persian_fonts(self):
        """تنظیم فونت فارسی بهتر"""
        try:
            # تنظیم فونت پیش‌فرض برای رابط کاربری
            default_font = ('Tahoma', 10)
            
            # تنظیم فونت برای پنجره اصلی
            self.root.option_add('*Font', default_font)
            
        except Exception as e:
            print(f"خطا در تنظیم فونت: {e}")
        
    def setup_database(self):
        """راه‌اندازی دیتابیس SQLite"""
        self.conn = sqlite3.connect('finance.db')
        self.cursor = self.conn.cursor()
        
        # ایجاد جدول تراکنش‌ها
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                type TEXT,
                amount REAL,
                description TEXT,
                category TEXT
            )
        ''')
        
        # ایجاد جدول تنظیمات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # ایجاد جدول اهداف مالی
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_amount REAL,
                current_amount REAL DEFAULT 0,
                description TEXT,
                deadline TEXT,
                created_date TEXT
            )
        ''')
        
        # ایجاد جدول یادآوری‌ها
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                date TEXT,
                completed INTEGER DEFAULT 0
            )
        ''')
        
        # ایجاد جدول رمز عبور
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS security (
                id INTEGER PRIMARY KEY,
                password_hash TEXT
            )
        ''')
        
        self.conn.commit()
        
    def hash_password(self, password):
        """رمزگذاری رمز عبور"""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def set_password(self, password):
        """تنظیم رمز عبور"""
        password_hash = self.hash_password(password)
        self.cursor.execute("DELETE FROM security")
        self.cursor.execute("INSERT INTO security (id, password_hash) VALUES (1, ?)", (password_hash,))
        self.conn.commit()
        
    def check_password(self, password):
        """بررسی رمز عبور"""
        password_hash = self.hash_password(password)
        self.cursor.execute("SELECT password_hash FROM security WHERE id = 1")
        result = self.cursor.fetchone()
        if result:
            return result[0] == password_hash
        return False
        
    def show_login_screen(self):
        """نمایش صفحه ورود"""
        # پاک کردن صفحه فعلی
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # فریم ورود
        login_frame = ttk.Frame(self.root, padding="50")
        login_frame.pack(expand=True)
        
        ttk.Label(login_frame, text=fix_persian_text("ورود به برنامه"), 
                 font=('Tahoma', 16, 'bold')).pack(pady=(0, 20))
        
        # ورود رمز عبور
        ttk.Label(login_frame, text=fix_persian_text("رمز عبور:")).pack(anchor=tk.W)
        password_entry = ttk.Entry(login_frame, textvariable=tk.StringVar(), show="*", width=30)
        password_entry.pack(pady=(5, 15))
        
        def login():
            password = password_entry.get()
            if self.check_password(password):
                self.user_logged_in = True
                self.setup_main_ui()
            else:
                # اگر رمز عبور اولین بار تنظیم نشده، اجازه ورود با هر رمزی
                self.cursor.execute("SELECT COUNT(*) FROM security")
                if self.cursor.fetchone()[0] == 0:
                    self.set_password(password)
                    self.user_logged_in = True
                    self.setup_main_ui()
                else:
                    messagebox.showerror(fix_persian_text("خطا"), fix_persian_text("رمز عبور اشتباه است"))
        
        def on_enter(event):
            login()
            
        password_entry.bind('<Return>', on_enter)
        
        ttk.Button(login_frame, text=fix_persian_text("ورود"), command=login).pack(pady=(0, 10))
        ttk.Label(login_frame, text=fix_persian_text("اگر اولین ورود شماست، رمز جدید ایجاد می‌شود"), 
                 foreground="gray").pack()
        
    def setup_main_ui(self):
        """راه‌اندازی رابط کاربری اصلی"""
        # پاک کردن صفحه فعلی
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # تنظیم استایل
        style = ttk.Style()
        style.theme_use('clam')
        
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # منوی فایل
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=fix_persian_text("فایل"), menu=file_menu)
        file_menu.add_command(label=fix_persian_text("خروج"), command=self.root.quit)
        
        # منوی ابزار
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=fix_persian_text("ابزار"), menu=tools_menu)
        tools_menu.add_command(label=fix_persian_text("اهداف مالی"), command=self.show_goals_window)
        tools_menu.add_command(label=fix_persian_text("یادآوری‌ها"), command=self.show_reminders_window)
        tools_menu.add_command(label=fix_persian_text("تغییر رمز عبور"), command=self.change_password)
        
        # Notebook برای تب‌بندی
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # تب اصلی
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text=fix_persian_text("تراکنش‌ها"))
        
        # تب گزارش‌ها
        report_frame = ttk.Frame(notebook)
        notebook.add(report_frame, text=fix_persian_text("گزارش‌ها"))
        
        # تب آنالیز
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text=fix_persian_text("آنالیز"))
        
        # تب تنظیمات
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text=fix_persian_text("تنظیمات"))
        
        # === تب اصلی ===
        self.setup_main_tab(main_frame)
        
        # === تب گزارش‌ها ===
        self.setup_report_tab(report_frame)
        
        # === تب آنالیز ===
        self.setup_analysis_tab(analysis_frame)
        
        # === تب تنظیمات ===
        self.setup_settings_tab(settings_frame)
        
        # بارگذاری داده‌ها
        self.refresh_display()
        self.check_reminders()
        
    def setup_main_tab(self, parent):
        """راه‌اندازی تب اصلی"""
        # فریم کارت‌ها (خلاصه مالی)
        cards_frame = ttk.Frame(parent)
        cards_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # کارت درآمد
        income_card = tk.Frame(cards_frame, bg=self.colors['card'], relief='raised', bd=2)
        income_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)
        self.income_label_main = tk.Label(income_card, text=fix_persian_text("درآمد\n0 تومان"), 
                                         font=('Tahoma', 12, 'bold'), fg=self.colors['income'],
                                         bg=self.colors['card'], pady=10)
        self.income_label_main.pack()
        
        # کارت هزینه
        expense_card = tk.Frame(cards_frame, bg=self.colors['card'], relief='raised', bd=2)
        expense_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.expense_label_main = tk.Label(expense_card, text=fix_persian_text("هزینه\n0 تومان"), 
                                          font=('Tahoma', 12, 'bold'), fg=self.colors['expense'],
                                          bg=self.colors['card'], pady=10)
        self.expense_label_main.pack()
        
        # کارت موجودی
        balance_card = tk.Frame(cards_frame, bg=self.colors['card'], relief='raised', bd=2)
        balance_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        self.balance_label_main = tk.Label(balance_card, text=fix_persian_text("موجودی\n0 تومان"), 
                                          font=('Tahoma', 12, 'bold'), fg=self.colors['balance'],
                                          bg=self.colors['card'], pady=10)
        self.balance_label_main.pack()
        
        # نوار پیشرفت هدف مالی
        self.setup_goal_progress_bar(cards_frame)
        
        # بخش اضافه کردن تراکنش
        add_frame = ttk.LabelFrame(parent, text=fix_persian_text("اضافه کردن تراکنش جدید"), padding="15")
        add_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # گرید برای فرم
        add_frame.columnconfigure(1, weight=1)
        
        # نوع تراکنش
        ttk.Label(add_frame, text=fix_persian_text("نوع:")).grid(row=0, column=0, sticky=tk.W, pady=5)
        type_frame = ttk.Frame(add_frame)
        type_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Radiobutton(type_frame, text=fix_persian_text("درآمد"), variable=self.type_var, value=fix_persian_text("درآمد")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(type_frame, text=fix_persian_text("هزینه"), variable=self.type_var, value=fix_persian_text("هزینه")).pack(side=tk.LEFT)
        
        # مبلغ و واحد پول
        ttk.Label(add_frame, text=fix_persian_text("مبلغ:")).grid(row=1, column=0, sticky=tk.W, pady=5)
        amount_frame = ttk.Frame(add_frame)
        amount_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(amount_frame, textvariable=self.amount_var, font=('Tahoma', 10), width=20).pack(side=tk.LEFT)
        currency_combo = ttk.Combobox(amount_frame, textvariable=self.currency_var, 
                                    values=["تومان", "دلار", "یورو"], width=10)
        currency_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # دسته‌بندی
        ttk.Label(add_frame, text=fix_persian_text("دسته:")).grid(row=2, column=0, sticky=tk.W, pady=5)
        categories = [fix_persian_text("حقوق"), fix_persian_text("هدیه"), fix_persian_text("فروش"), 
                     fix_persian_text("غذا"), fix_persian_text("حمل‌ونقل"), fix_persian_text("سرگرمی"), 
                     fix_persian_text("خرید"), fix_persian_text("پزشکی"), fix_persian_text("آموزش"), 
                     fix_persian_text("اجاره"), fix_persian_text("بیمه"), fix_persian_text("سایر")]
        self.category_combo = ttk.Combobox(add_frame, textvariable=self.category_var, values=categories, width=20)
        self.category_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.category_combo.set(fix_persian_text("سایر"))
        
        # توضیحات
        ttk.Label(add_frame, text=fix_persian_text("توضیحات:")).grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(add_frame, textvariable=self.desc_var, font=('Tahoma', 10)).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # دکمه اضافه کردن
        ttk.Button(add_frame, text=fix_persian_text("➕ اضافه کردن تراکنش"), command=self.add_transaction).grid(row=4, column=0, columnspan=2, pady=(15, 0))
        
        # فیلتر تراکنش‌ها
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        ttk.Label(filter_frame, text=fix_persian_text("فیلتر:")).pack(side=tk.LEFT)
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                   values=[fix_persian_text("همه"), fix_persian_text("درآمد"), fix_persian_text("هزینه")] + categories, width=15)
        filter_combo.pack(side=tk.LEFT, padx=(10, 5))
        ttk.Button(filter_frame, text=fix_persian_text("اعمال فیلتر"), command=self.refresh_display).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(filter_frame, text=fix_persian_text("حذف فیلتر"), command=self.clear_filter).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(filter_frame, text="🔄", width=3, command=self.refresh_display).pack(side=tk.RIGHT, padx=(0, 5))
        
        # جدول تراکنش‌ها
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = (fix_persian_text('تاریخ'), fix_persian_text('نوع'), fix_persian_text('مبلغ'), 
                  fix_persian_text('دسته'), fix_persian_text('توضیحات'))
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
            
        # اسکرول‌بارها
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # دکمه‌های عملیات
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text=fix_persian_text("🗑️ حذف انتخاب شده"), command=self.delete_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text=fix_persian_text("💾 ذخیره به فایل"), command=self.export_data).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(button_frame, text=fix_persian_text("📂 بارگذاری از فایل"), command=self.import_data).pack(side=tk.LEFT, padx=(5, 0))
        
        # دکمه ری‌استارت
        restart_frame = ttk.Frame(parent)
        restart_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(restart_frame, text=fix_persian_text("🔄 ری‌استارت (شروع مجدد از اول)"), 
                  command=self.restart_all_data).pack(side=tk.RIGHT, padx=(0, 5))
        
        # بایند کردن کلید Enter به اضافه کردن تراکنش
        self.root.bind('<Return>', lambda e: self.add_transaction())
        
    def setup_goal_progress_bar(self, parent):
        """راه‌اندازی نوار پیشرفت هدف مالی"""
        # گرفتن هدف فعلی
        self.cursor.execute("SELECT target_amount, current_amount FROM goals ORDER BY id DESC LIMIT 1")
        goal_result = self.cursor.fetchone()
        
        if goal_result:
            target_amount, current_amount = goal_result
            progress = (current_amount / target_amount * 100) if target_amount > 0 else 0
            
            # فریم پیشرفت
            progress_frame = ttk.Frame(parent)
            progress_frame.pack(fill=tk.X, padx=5, pady=(10, 5))
            
            ttk.Label(progress_frame, text=fix_persian_text("پیشرفت به هدف مالی:")).pack(anchor=tk.W)
            
            # نوار پیشرفت
            progress_bar = ttk.Progressbar(progress_frame, length=200, mode='determinate')
            progress_bar['value'] = min(progress, 100)
            progress_bar.pack(side=tk.LEFT, pady=5)
            
            # درصد پیشرفت
            progress_label = ttk.Label(progress_frame, text=f"{progress:.1f}%")
            progress_label.pack(side=tk.LEFT, padx=(10, 0))
            
    def setup_report_tab(self, parent):
        """راه‌اندازی تب گزارش‌ها"""
        # فیلتر گزارش‌ها
        filter_frame = ttk.LabelFrame(parent, text=fix_persian_text("فیلتر گزارش‌ها"), padding="10")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # سال و ماه
        current_year = str(datetime.now().year)
        years = [str(y) for y in range(2020, int(current_year) + 2)]
        months = [fix_persian_text("همه")] + [fix_persian_text(calendar.month_name[i]) for i in range(1, 13)]
        
        ttk.Label(filter_frame, text=fix_persian_text("سال:")).grid(row=0, column=0, padx=(0, 5))
        year_combo = ttk.Combobox(filter_frame, textvariable=self.year_var, values=years, width=10)
        year_combo.grid(row=0, column=1, padx=(0, 10))
        year_combo.set(current_year)
        
        ttk.Label(filter_frame, text=fix_persian_text("ماه:")).grid(row=0, column=2, padx=(10, 5))
        month_combo = ttk.Combobox(filter_frame, textvariable=self.month_var, values=months, width=15)
        month_combo.grid(row=0, column=3, padx=(0, 10))
        month_combo.set(fix_persian_text("همه"))
        
        ttk.Button(filter_frame, text=fix_persian_text("نمایش گزارش"), command=self.generate_report).grid(row=0, column=4, padx=(10, 0))
        
        # گزارش متنی
        report_text_frame = ttk.LabelFrame(parent, text=fix_persian_text("گزارش متنی"), padding="10")
        report_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.report_text = tk.Text(report_text_frame, height=8, wrap=tk.WORD)
        report_scrollbar = ttk.Scrollbar(report_text_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=report_scrollbar.set)
        
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        report_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def setup_analysis_tab(self, parent):
        """راه‌اندازی تب آنالیز"""
        # آنالیز هوشمند
        analysis_frame = ttk.LabelFrame(parent, text=fix_persian_text("آنالیز هوشمند"), padding="15")
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # دکمه‌های آنالیز
        button_frame = ttk.Frame(analysis_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(button_frame, text=fix_persian_text("🔍 آنالیز هزینه‌ها"), command=self.analyze_expenses).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text=fix_persian_text("📊 الگوهای مصرف"), command=self.analyze_patterns).pack(side=tk.LEFT, padx=(10, 10))
        ttk.Button(button_frame, text=fix_persian_text("💡 پیشنهادات"), command=self.generate_tips).pack(side=tk.LEFT, padx=(10, 0))
        
        # نتایج آنالیز
        self.analysis_text = tk.Text(analysis_frame, height=20, wrap=tk.WORD, font=('Tahoma', 10))
        analysis_scrollbar = ttk.Scrollbar(analysis_frame, orient=tk.VERTICAL, command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=analysis_scrollbar.set)
        
        self.analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        analysis_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # پیشنهاد اولیه
        self.analysis_text.insert(tk.END, fix_persian_text("به تب آنالیز خوش آمدید!\n\nبرای دریافت تحلیل‌های هوشمند، یکی از دکمه‌های بالا را انتخاب کنید.\n"))
        
    def setup_settings_tab(self, parent):
        """راه‌اندازی تب تنظیمات"""
        settings_frame = ttk.Frame(parent, padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(settings_frame, text=fix_persian_text("تنظیمات برنامه"), font=('Tahoma', 16, 'bold')).pack(pady=(0, 20))
        
        # تنظیمات پشتیبان‌گیری
        backup_frame = ttk.LabelFrame(settings_frame, text=fix_persian_text("پشتیبان‌گیری و بازیابی"), padding="15")
        backup_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Button(backup_frame, text=fix_persian_text("💾 ایجاد پشتیبان"), command=self.create_backup).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(backup_frame, text=fix_persian_text("📤 بازیابی پشتیبان"), command=self.restore_backup).pack(side=tk.LEFT, padx=(10, 10))
        ttk.Button(backup_frame, text=fix_persian_text("🗑️ پاک کردن داده‌ها"), command=self.clear_data).pack(side=tk.LEFT, padx=(10, 0))
        
        # تنظیمات ظاهر
        appearance_frame = ttk.LabelFrame(settings_frame, text=fix_persian_text("تنظیمات ظاهر"), padding="15")
        appearance_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(appearance_frame, text=fix_persian_text("تم برنامه:")).pack(anchor=tk.W)
        theme_frame = ttk.Frame(appearance_frame)
        theme_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(theme_frame, text=fix_persian_text("روشن"), command=lambda: self.change_theme('light')).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(theme_frame, text=fix_persian_text("تیره"), command=lambda: self.change_theme('dark')).pack(side=tk.LEFT)
        
        # اطلاعات برنامه
        info_frame = ttk.LabelFrame(settings_frame, text=fix_persian_text("اطلاعات برنامه"), padding="15")
        info_frame.pack(fill=tk.X)
        
        info_text = fix_persian_text("""
نسخه: 4.0
توسعه‌دهنده: شما
زبان: پایتون
کتابخانه‌ها: tkinter, sqlite3, hashlib

این برنامه یک پروژه آموزشی است که به شما کمک می‌کند:
- مهارت‌های برنامه‌نویسی را تقویت کنید
- یک نمونه کار حرفه‌ای داشته باشید
- اولین پروژه فریلنس خود را بگیرید

ویژگی‌های جدید:
- رمز عبور و امنیت
- اهداف مالی
- یادآوری‌ها
- پشتیبان‌گیری ایمن
        """)
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.RIGHT)
        info_label.pack(anchor=tk.W)
        
    def show_goals_window(self):
        """نمایش پنجره اهداف مالی"""
        goals_window = tk.Toplevel(self.root)
        goals_window.title(fix_persian_text("اهداف مالی"))
        goals_window.geometry("500x400")
        goals_window.transient(self.root)
        goals_window.grab_set()
        
        # فرم اهداف
        form_frame = ttk.LabelFrame(goals_window, text=fix_persian_text("تعریف هدف جدید"), padding="15")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(form_frame, text=fix_persian_text("مبلغ هدف:")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.goal_amount_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(form_frame, text=fix_persian_text("واحد پول:")).grid(row=1, column=0, sticky=tk.W, pady=5)
        currency_combo = ttk.Combobox(form_frame, textvariable=self.currency_var, 
                                    values=["تومان", "دلار", "یورو"], width=15)
        currency_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        currency_combo.set("تومان")
        
        ttk.Label(form_frame, text=fix_persian_text("توضیحات:")).grid(row=2, column=0, sticky=tk.W, pady=5)
        goal_desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=goal_desc_var).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        def save_goal():
            try:
                target_amount = float(self.goal_amount_var.get())
                description = goal_desc_var.get()
                created_date = datetime.now().strftime("%Y-%m-%d")
                
                self.cursor.execute('''
                    INSERT INTO goals (target_amount, current_amount, description, created_date)
                    VALUES (?, 0, ?, ?)
                ''', (target_amount, description, created_date))
                
                self.conn.commit()
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("هدف مالی با موفقیت اضافه شد"))
                goals_window.destroy()
                self.refresh_display()
                
            except ValueError:
                messagebox.showerror(fix_persian_text("خطا"), fix_persian_text("لطفاً مبلغ را به درستی وارد کنید"))
        
        ttk.Button(form_frame, text=fix_persian_text("ذخیره هدف"), command=save_goal).grid(row=3, column=0, columnspan=2, pady=10)
        
        # لیست اهداف فعلی
        list_frame = ttk.LabelFrame(goals_window, text=fix_persian_text("اهداف فعلی"), padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # جدول اهداف
        columns = (fix_persian_text('توضیحات'), fix_persian_text('هدف'), fix_persian_text('پیشرفت'), fix_persian_text('درصد'))
        goals_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            goals_tree.heading(col, text=col)
            goals_tree.column(col, width=100)
            
        # اسکرول‌بار
        goals_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=goals_tree.yview)
        goals_tree.configure(yscrollcommand=goals_scrollbar.set)
        
        goals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        goals_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # بارگذاری اهداف
        self.cursor.execute("SELECT id, target_amount, current_amount, description FROM goals ORDER BY id DESC")
        goals = self.cursor.fetchall()
        
        for goal in goals:
            goal_id, target_amount, current_amount, description = goal
            progress = current_amount
            percentage = (current_amount / target_amount * 100) if target_amount > 0 else 0
            formatted_target = f"{target_amount:,.0f} تومان"
            formatted_progress = f"{progress:,.0f} تومان"
            formatted_percentage = f"{percentage:.1f}%"
            goals_tree.insert('', tk.END, values=(description, formatted_target, formatted_progress, formatted_percentage))
        
    def show_reminders_window(self):
        """نمایش پنجره یادآوری‌ها"""
        reminders_window = tk.Toplevel(self.root)
        reminders_window.title(fix_persian_text("یادآوری‌ها"))
        reminders_window.geometry("600x500")
        reminders_window.transient(self.root)
        reminders_window.grab_set()
        
        # فرم یادآوری
        form_frame = ttk.LabelFrame(reminders_window, text=fix_persian_text("تعریف یادآوری جدید"), padding="15")
        form_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(form_frame, text=fix_persian_text("توضیحات:")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.reminder_desc_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(form_frame, text=fix_persian_text("تاریخ یادآوری:")).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(form_frame, textvariable=self.reminder_date_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(form_frame, text=fix_persian_text("(فرمت: YYYY-MM-DD)")).grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        def save_reminder():
            try:
                description = self.reminder_desc_var.get()
                date = self.reminder_date_var.get()
                # بررسی فرمت تاریخ
                datetime.strptime(date, "%Y-%m-%d")
                
                self.cursor.execute('''
                    INSERT INTO reminders (description, date, completed)
                    VALUES (?, ?, 0)
                ''', (description, date))
                
                self.conn.commit()
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("یادآوری با موفقیت اضافه شد"))
                self.reminder_desc_var.set("")
                self.reminder_date_var.set("")
                load_reminders()
                
            except ValueError:
                messagebox.showerror(fix_persian_text("خطا"), fix_persian_text("لطفاً تاریخ را به درستی وارد کنید (YYYY-MM-DD)"))
        
        ttk.Button(form_frame, text=fix_persian_text("ذخیره یادآوری"), command=save_reminder).grid(row=2, column=0, columnspan=3, pady=10)
        
        # لیست یادآوری‌ها
        list_frame = ttk.LabelFrame(reminders_window, text=fix_persian_text("یادآوری‌های فعلی"), padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # جدول یادآوری‌ها
        columns = (fix_persian_text('توضیحات'), fix_persian_text('تاریخ'), fix_persian_text('وضعیت'))
        reminders_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            reminders_tree.heading(col, text=col)
            reminders_tree.column(col, width=150)
            
        # اسکرول‌بار
        reminders_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=reminders_tree.yview)
        reminders_tree.configure(yscrollcommand=reminders_scrollbar.set)
        
        reminders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        reminders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def load_reminders():
            # پاک کردن لیست
            for item in reminders_tree.get_children():
                reminders_tree.delete(item)
                
            # بارگذاری یادآوری‌ها
            self.cursor.execute("SELECT id, description, date, completed FROM reminders ORDER BY date")
            reminders = self.cursor.fetchall()
            
            for reminder in reminders:
                reminder_id, description, date, completed = reminder
                status = fix_persian_text("انجام شده") if completed else fix_persian_text("در انتظار")
                reminders_tree.insert('', tk.END, values=(description, date, status), tags=(reminder_id,))
                
            # رنگ‌بندی بر اساس وضعیت
            reminders_tree.tag_configure('completed', background='#e8f5e8')
            reminders_tree.tag_configure('pending', background='#ffe8e8')
        
        def mark_completed():
            selected = reminders_tree.selection()
            if selected:
                item = reminders_tree.item(selected[0])
                reminder_id = reminders_tree.item(selected[0])['tags'][0]
                
                self.cursor.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (reminder_id,))
                self.conn.commit()
                load_reminders()
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("یادآوری به عنوان انجام شده علامت گذاری شد"))
            else:
                messagebox.showwarning(fix_persian_text("هشدار"), fix_persian_text("لطفاً یک یادآوری را انتخاب کنید"))
        
        def delete_reminder():
            selected = reminders_tree.selection()
            if selected:
                if messagebox.askyesno(fix_persian_text("تأیید"), fix_persian_text("آیا از حذف این یادآوری مطمئن هستید؟")):
                    reminder_id = reminders_tree.item(selected[0])['tags'][0]
                    
                    self.cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
                    self.conn.commit()
                    load_reminders()
                    messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("یادآوری با موفقیت حذف شد"))
            else:
                messagebox.showwarning(fix_persian_text("هشدار"), fix_persian_text("لطفاً یک یادآوری را انتخاب کنید"))
        
        # دکمه‌های عملیات
        button_frame = ttk.Frame(reminders_window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text=fix_persian_text("علامت گذاری به عنوان انجام شده"), command=mark_completed).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text=fix_persian_text("حذف یادآوری"), command=delete_reminder).pack(side=tk.LEFT)
        
        # بارگذاری یادآوری‌ها
        load_reminders()
        
    def check_reminders(self):
        """بررسی یادآوری‌های امروز"""
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("SELECT description FROM reminders WHERE date = ? AND completed = 0", (today,))
        reminders = self.cursor.fetchall()
        
        if reminders:
            reminder_list = "\n".join([r[0] for r in reminders])
            messagebox.showinfo(fix_persian_text("یادآوری"), 
                              fix_persian_text(f"یادآوری‌های امروز:\n{reminder_list}"))
        
    def change_password(self):
        """تغییر رمز عبور"""
        password_window = tk.Toplevel(self.root)
        password_window.title(fix_persian_text("تغییر رمز عبور"))
        password_window.geometry("300x200")
        password_window.transient(self.root)
        password_window.grab_set()
        
        ttk.Label(password_window, text=fix_persian_text("رمز عبور فعلی:")).pack(pady=(20, 5))
        old_password = ttk.Entry(password_window, show="*", width=30)
        old_password.pack()
        
        ttk.Label(password_window, text=fix_persian_text("رمز عبور جدید:")).pack(pady=(10, 5))
        new_password = ttk.Entry(password_window, show="*", width=30)
        new_password.pack()
        
        def save_new_password():
            old_pass = old_password.get()
            new_pass = new_password.get()
            
            if self.check_password(old_pass):
                self.set_password(new_pass)
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("رمز عبور با موفقیت تغییر کرد"))
                password_window.destroy()
            else:
                messagebox.showerror(fix_persian_text("خطا"), fix_persian_text("رمز عبور فعلی اشتباه است"))
        
        ttk.Button(password_window, text=fix_persian_text("ذخیره"), command=save_new_password).pack(pady=20)
        
    def add_transaction(self):
        """اضافه کردن تراکنش جدید"""
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror(fix_persian_text("خطا"), fix_persian_text("مبلغ باید بیشتر از صفر باشد"))
                return
                
            transaction = (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                self.type_var.get(),
                amount,
                self.desc_var.get(),
                self.category_var.get()
            )
            
            self.cursor.execute('''
                INSERT INTO transactions (date, type, amount, description, category)
                VALUES (?, ?, ?, ?, ?)
            ''', transaction)
            
            self.conn.commit()
            
            # به‌روزرسانی پیشرفت هدف مالی
            if self.type_var.get() == fix_persian_text("درآمد"):
                self.cursor.execute("SELECT id, current_amount FROM goals ORDER BY id DESC LIMIT 1")
                goal_result = self.cursor.fetchone()
                if goal_result:
                    goal_id, current_amount = goal_result
                    new_amount = current_amount + amount
                    self.cursor.execute("UPDATE goals SET current_amount = ? WHERE id = ?", (new_amount, goal_id))
                    self.conn.commit()
            
            self.refresh_display()
            
            # پاک کردن فیلدها
            self.amount_var.set("")
            self.desc_var.set("")
            self.category_var.set(fix_persian_text("سایر"))
            
            # نمایش پیام موفقیت
            messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("تراکنش با موفقیت اضافه شد"))
            
        except ValueError:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text("لطفاً مبلغ را به درستی وارد کنید"))
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطایی رخ داد: {str(e)}"))
            
    def refresh_display(self):
        """به‌روزرسانی نمایش تراکنش‌ها"""
        # پاک کردن لیست
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # ساختن کوئری با فیلتر
        query = "SELECT * FROM transactions"
        params = []
        
        filter_value = self.filter_var.get()
        if filter_value != fix_persian_text("همه"):
            if filter_value in [fix_persian_text("درآمد"), fix_persian_text("هزینه")]:
                query += " WHERE type = ?"
                params = [filter_value]
            else:
                query += " WHERE category = ?"
                params = [filter_value]
                
        query += " ORDER BY date DESC"
        
        # اجرای کوئری
        self.cursor.execute(query, params)
        transactions = self.cursor.fetchall()
        
        # اضافه کردن تراکنش‌ها به جدول
        for trans in transactions:
            formatted_amount = f"{trans[3]:,.0f} " + fix_persian_text("تومان")
            self.tree.insert('', tk.END, values=(trans[1], trans[2], formatted_amount, trans[5], trans[4]))
            
        # محاسبه خلاصه
        self.update_summary()
        
    def update_summary(self):
        """به‌روزرسانی خلاصه مالی"""
        # گرفتن تمام تراکنش‌ها
        self.cursor.execute("SELECT type, amount FROM transactions")
        results = self.cursor.fetchall()
        
        income = sum(row[1] for row in results if row[0] == fix_persian_text("درآمد"))
        expense = sum(row[1] for row in results if row[0] == fix_persian_text("هزینه"))
        balance = income - expense  # تصحیح محاسبه
        
        # نمایش صحیح اعداد منفی
        income_text = f"{income:,.0f} تومان"
        expense_text = f"{expense:,.0f} تومان"
        
        # اگر موجودی منفی بود، علامت منفی رو جلوی عدد بذار
        if balance < 0:
            balance_text = f"-{abs(balance):,.0f} تومان"
        else:
            balance_text = f"{balance:,.0f} تومان"
        
        # به‌روزرسانی کارت‌ها
        self.income_label_main.config(text=fix_persian_text(f"درآمد\n{income_text}"))
        self.expense_label_main.config(text=fix_persian_text(f"هزینه\n{expense_text}"))
        self.balance_label_main.config(text=fix_persian_text(f"موجودی\n{balance_text}"))
        
    def generate_report(self):
        """تولید گزارش"""
        try:
            # ساخت کوئری بر اساس فیلتر
            query = "SELECT * FROM transactions WHERE 1=1"
            params = []
            
            # فیلتر سال
            if self.year_var.get() and self.year_var.get() != fix_persian_text("همه"):
                query += " AND date LIKE ?"
                params.append(f"{self.year_var.get()}%")
                
            # فیلتر ماه
            if self.month_var.get() and self.month_var.get() != fix_persian_text("همه"):
                month_num = list(calendar.month_name).index(self.month_var.get().replace(fix_persian_text(""), ""))
                month_str = f"{month_num:02d}"
                query += " AND date LIKE ?"
                params.append(f"%-{month_str}-%")
                
            query += " ORDER BY date DESC"
            
            self.cursor.execute(query, params)
            transactions = self.cursor.fetchall()
            
            # محاسبه آمار
            income = sum(row[3] for row in transactions if row[2] == fix_persian_text("درآمد"))
            expense = sum(row[3] for row in transactions if row[2] == fix_persian_text("هزینه"))
            balance = income - expense  # تصحیح محاسبه
            
            # نمایش صحیح اعداد منفی
            if balance < 0:
                balance_text = f"-{abs(balance):,.0f}"
            else:
                balance_text = f"{balance:,.0f}"
            
            # تجزیه و تحلیل دسته‌بندی
            category_expense = defaultdict(float)
            for row in transactions:
                if row[2] == fix_persian_text("هزینه"):
                    category_expense[row[5]] += row[3]
            
            # تولید گزارش متنی
            self.report_text.delete(1.0, tk.END)
            
            report = fix_persian_text(f"""
📊 گزارش مالی

تاریخ تولید گزارش: {datetime.now().strftime("%Y-%m-%d %H:%M")}

💰 خلاصه مالی:
درآمد کل: {income:,.0f} تومان
هزینه کل: {expense:,.0f} تومان
سود/ضرر: {balance_text} تومان

🛍️ تجزیه و تحلیل هزینه‌ها:
""")
            
            for category, amount in sorted(category_expense.items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / expense * 100) if expense > 0 else 0
                report += fix_persian_text(f"• {category}: {amount:,.0f} تومان ({percentage:.1f}%)\n")
            
            report += fix_persian_text(f"\n📈 تعداد کل تراکنش‌ها: {len(transactions)}")
            
            self.report_text.insert(tk.END, report)
            
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در تولید گزارش: {str(e)}"))
            
    def analyze_expenses(self):
        """آنالیز هزینه‌ها"""
        try:
            self.cursor.execute("SELECT category, SUM(amount) FROM transactions WHERE type = ? GROUP BY category", 
                              (fix_persian_text("هزینه"),))
            results = self.cursor.fetchall()
            
            total_expense = sum(row[1] for row in results)
            
            analysis = fix_persian_text("🔍 آنالیز هزینه‌ها:\n\n")
            
            if results:
                # مرتب‌سازی بر اساس مبلغ
                results.sort(key=lambda x: x[1], reverse=True)
                
                analysis += fix_persian_text("📊 دسته‌بندی هزینه‌ها (از بیشترین به کمترین):\n")
                for i, (category, amount) in enumerate(results, 1):
                    percentage = (amount / total_expense * 100) if total_expense > 0 else 0
                    analysis += fix_persian_text(f"{i}. {category}: {amount:,.0f} تومان ({percentage:.1f}%)\n")
                
                # پیدا کردن بیشترین و کمترین هزینه
                max_category = results[0][0]
                min_category = results[-1][0]
                
                analysis += fix_persian_text(f"\n📈 بیشترین هزینه: {max_category}\n")
                analysis += fix_persian_text(f"📉 کمترین هزینه: {min_category}\n")
                
                # میانگین هزینه
                avg_expense = total_expense / len(results)
                analysis += fix_persian_text(f"\n📊 میانگین هزینه در هر دسته: {avg_expense:,.0f} تومان\n")
            else:
                analysis += fix_persian_text("هیچ هزینه‌ای ثبت نشده است.\n")
                
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, analysis)
            
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در آنالیز هزینه‌ها: {str(e)}"))
            
    def analyze_patterns(self):
        """آنالیز الگوهای مصرف"""
        try:
            self.cursor.execute("SELECT date, type, amount, category FROM transactions ORDER BY date")
            transactions = self.cursor.fetchall()
            
            analysis = fix_persian_text("📊 آنالیز الگوهای مصرف:\n\n")
            
            if transactions:
                # تجزیه و تحلیل بر اساس زمان
                monthly_data = defaultdict(lambda: {'income': 0, 'expense': 0})
                
                for trans in transactions:
                    date = datetime.strptime(trans[0], "%Y-%m-%d %H:%M")
                    month_key = date.strftime("%Y-%m")
                    
                    if trans[1] == fix_persian_text("درآمد"):
                        monthly_data[month_key]['income'] += trans[2]
                    else:
                        monthly_data[month_key]['expense'] += trans[2]
                
                # تبدیل به لیست و مرتب‌سازی
                monthly_list = [(month, data) for month, data in monthly_data.items()]
                monthly_list.sort()
                
                analysis += fix_persian_text("📅 روند مالی ماهانه:\n")
                for month, data in monthly_list[-6:]:  # ۶ ماه اخیر
                    balance = data['income'] - data['expense']
                    # نمایش صحیح اعداد منفی
                    if balance < 0:
                        balance_text = f"-{abs(balance):,.0f}"
                    else:
                        balance_text = f"{balance:,.0f}"
                        
                    analysis += fix_persian_text(f"{month}: درآمد {data['income']:,.0f} | هزینه {data['expense']:,.0f} | موجودی {balance_text}\n")
                
                # آنالیز روزهای هفته
                weekday_expense = defaultdict(float)
                for trans in transactions:
                    if trans[1] == fix_persian_text("هزینه"):
                        date = datetime.strptime(trans[0], "%Y-%m-%d %H:%M")
                        weekday = date.weekday()  # 0=دوشنبه, 6=یکشنبه
                        weekday_expense[weekday] += trans[2]
                
                weekdays = [fix_persian_text('دوشنبه'), fix_persian_text('سه‌شنبه'), fix_persian_text('چهارشنبه'), 
                           fix_persian_text('پنج‌شنبه'), fix_persian_text('جمعه'), fix_persian_text('شنبه'), 
                           fix_persian_text('یکشنبه')]
                
                analysis += fix_persian_text("\n📅 هزینه‌های بر اساس روزهای هفته:\n")
                for i in range(7):
                    amount = weekday_expense[i]
                    analysis += fix_persian_text(f"{weekdays[i]}: {amount:,.0f} تومان\n")
                
                # پیدا کردن روز پرخرج‌ترین
                if weekday_expense:
                    max_weekday = max(weekday_expense.items(), key=lambda x: x[1])[0]
                    analysis += fix_persian_text(f"\n💰 بیشترین هزینه در: {weekdays[max_weekday]}\n")
                
            else:
                analysis += fix_persian_text("داده‌ای برای آنالیز وجود ندارد.\n")
                
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, analysis)
            
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در آنالیز الگوها: {str(e)}"))
            
    def generate_tips(self):
        """تولید پیشنهادات هوشمند"""
        try:
            self.cursor.execute("SELECT type, amount, category FROM transactions")
            transactions = self.cursor.fetchall()
            
            tips = fix_persian_text("💡 پیشنهادات هوشمند:\n\n")
            
            if transactions:
                # آنالیز هزینه‌ها
                expenses = [t for t in transactions if t[0] == fix_persian_text("هزینه")]
                incomes = [t for t in transactions if t[0] == fix_persian_text("درآمد")]
                
                total_expense = sum(t[1] for t in expenses)
                total_income = sum(t[1] for t in incomes)
                
                if total_expense > 0:
                    # تجزیه و تحلیل دسته‌بندی
                    category_expense = defaultdict(float)
                    for exp in expenses:
                        category_expense[exp[2]] += exp[1]
                    
                    # پیشنهادات بر اساس دسته‌بندی
                    tips += fix_persian_text("🎯 پیشنهادات بر اساس هزینه‌ها:\n")
                    
                    # پیدا کردن دسته‌های پرخرج
                    sorted_categories = sorted(category_expense.items(), key=lambda x: x[1], reverse=True)
                    
                    if sorted_categories:
                        max_category, max_amount = sorted_categories[0]
                        percentage = (max_amount / total_expense * 100) if total_expense > 0 else 0
                        
                        if percentage > 30:
                            tips += fix_persian_text(f"⚠️ هزینه‌های '{max_category}' ({percentage:.1f}%) بسیار بالا است. سعی کنید کاهش دهید.\n")
                        elif percentage > 20:
                            tips += fix_persian_text(f"🔔 هزینه‌های '{max_category}' ({percentage:.1f}%) نسبتاً بالا است.\n")
                    
                    # پیشنهادات کلی
                    tips += fix_persian_text("\n📋 پیشنهادات عمومی:\n")
                    
                    if total_income > total_expense:
                        tips += fix_persian_text("✅ وضعیت مالی شما خوب است. درآمد بیشتر از هزینه است.\n")
                        tips += fix_persian_text("💰 پیشنهاد می‌کنیم بخشی از سود را پس‌انداز کنید.\n")
                    elif total_income < total_expense:
                        tips += fix_persian_text("⚠️ هشدار: هزینه‌های شما بیشتر از درآمد است.\n")
                        tips += fix_persian_text("📉 لطفاً هزینه‌های غیرضروری را کاهش دهید.\n")
                    else:
                        tips += fix_persian_text("⚖️ درآمد و هزینه‌های شما متعادل است.\n")
                        tips += fix_persian_text("📈 سعی کنید درآمد خود را افزایش دهید.\n")
                    
                    # پیشنهادات بر اساس دسته‌بندی
                    tips += fix_persian_text("\n🛍️ پیشنهادات خاص:\n")
                    
                    if fix_persian_text('غذا') in category_expense:
                        food_expense = category_expense[fix_persian_text('غذا')]
                        if food_expense > total_expense * 0.25:
                            tips += fix_persian_text("🍱 هزینه‌های غذا بسیار بالا است. سعی کنید بیشتر غذا درست کنید.\n")
                    
                    if fix_persian_text('سرگرمی') in category_expense:
                        entertainment_expense = category_expense[fix_persian_text('سرگرمی')]
                        if entertainment_expense > total_expense * 0.15:
                            tips += fix_persian_text("🎮 هزینه‌های سرگرمی زیاد است. برنامه‌ریزی کنید.\n")
                    
                    if fix_persian_text('خرید') in category_expense:
                        shopping_expense = category_expense[fix_persian_text('خرید')]
                        if shopping_expense > total_expense * 0.20:
                            tips += fix_persian_text("🛍️ هزینه‌های خرید بسیار بالا است. قبل از خرید فکر کنید.\n")
                
                # پیشنهادات برای ذخیره‌سازی
                tips += fix_persian_text("\n💰 پیشنهادات ذخیره‌سازی:\n")
                tips += fix_persian_text("🏦 حداقل ۱۰٪ از درآمد را پس‌انداز کنید.\n")
                tips += fix_persian_text("🎯 اهداف مالی کوتاه‌مدت و بلندمدت تعیین کنید.\n")
                tips += fix_persian_text("📈 هر ماه گزارش مالی خود را بررسی کنید.\n")
                
            else:
                tips += fix_persian_text("هنوز تراکنشی ثبت نکرده‌اید. شروع کنید تا پیشنهادات دریافت کنید!\n")
                
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, tips)
            
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در تولید پیشنهادات: {str(e)}"))
            
    def delete_selected(self):
        """حذف تراکنش انتخاب شده"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(fix_persian_text("هشدار"), fix_persian_text("لطفاً یک تراکنش را انتخاب کنید"))
            return
            
        if messagebox.askyesno(fix_persian_text("تأیید"), fix_persian_text("آیا از حذف تراکنش انتخاب شده مطمئن هستید؟")):
            try:
                # گرفتن اطلاعات تراکنش انتخاب شده
                item = self.tree.item(selected[0])
                values = item['values']
                
                # پیدا کردن تراکنش در دیتابیس (با تاریخ و مبلغ)
                date = values[0]
                amount_text = values[2].replace(fix_persian_text(' تومان'), '').replace(',', '')
                amount = float(amount_text)
                
                # حذف از دیتابیس
                self.cursor.execute('''
                    DELETE FROM transactions 
                    WHERE date = ? AND amount = ?
                ''', (date, amount))
                
                self.conn.commit()
                self.refresh_display()
                
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("تراکنش با موفقیت حذف شد"))
                
            except Exception as e:
                messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در حذف تراکنش: {str(e)}"))
                
    def export_data(self):
        """ذخیره داده‌ها به فایل"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                self.cursor.execute("SELECT * FROM transactions")
                transactions = self.cursor.fetchall()
                
                # تبدیل به فرمت مناسب
                data = []
                for trans in transactions:
                    data.append({
                        'id': trans[0],
                        'date': trans[1],
                        'type': trans[2],
                        'amount': trans[3],
                        'description': trans[4],
                        'category': trans[5]
                    })
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("داده‌ها با موفقیت ذخیره شدند"))
                
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در ذخیره داده‌ها: {str(e)}"))
            
    def import_data(self):
        """بارگذاری داده‌ها از فایل"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # اضافه کردن داده‌های جدید
                for item in data:
                    # بررسی تکراری نبودن
                    self.cursor.execute('''
                        SELECT COUNT(*) FROM transactions 
                        WHERE date = ? AND amount = ? AND type = ?
                    ''', (item['date'], item['amount'], item['type']))
                    
                    if self.cursor.fetchone()[0] == 0:  # اگر تکراری نبود
                        self.cursor.execute('''
                            INSERT INTO transactions (date, type, amount, description, category)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (item['date'], item['type'], item['amount'], 
                              item['description'], item['category']))
                
                self.conn.commit()
                self.refresh_display()
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("داده‌ها با موفقیت بارگذاری شدند"))
                
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در بارگذاری داده‌ها: {str(e)}"))
            
    def create_backup(self):
        """ایجاد پشتیبان"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                initialfile=f"finance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            
            if filename:
                import shutil
                self.conn.commit()  # ذخیره تغییرات
                shutil.copy2('finance.db', filename)
                
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text(f"پشتیبان با موفقیت ایجاد شد:\n{filename}"))
                
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در ایجاد پشتیبان: {str(e)}"))
            
    def restore_backup(self):
        """بازیابی پشتیبان"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("Database files", "*.db"), ("All files", "*.*")]
            )
            
            if filename:
                if messagebox.askyesno(fix_persian_text("تأیید"), fix_persian_text("آیا از بازیابی پشتیبان مطمئن هستید؟ داده‌های فعلی از بین می‌روند!")):
                    import shutil
                    shutil.copy2(filename, 'finance.db')
                    
                    # بستن و دوباره باز کردن اتصال
                    self.conn.close()
                    self.setup_database()
                    self.refresh_display()
                    
                    messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("پشتیبان با موفقیت بازیابی شد"))
                
        except Exception as e:
            messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در بازیابی پشتیبان: {str(e)}"))
            
    def clear_data(self):
        """پاک کردن تمام داده‌ها"""
        if messagebox.askyesno(fix_persian_text("تأیید"), fix_persian_text("آیا از پاک کردن تمام داده‌ها مطمئن هستید؟ این عمل غیرقابل بازگشت است!")):
            try:
                self.cursor.execute("DELETE FROM transactions")
                self.cursor.execute("DELETE FROM goals")
                self.cursor.execute("DELETE FROM reminders")
                self.conn.commit()
                self.refresh_display()
                messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text("تمام داده‌ها پاک شدند"))
                
            except Exception as e:
                messagebox.showerror(fix_persian_text("خطا"), fix_persian_text(f"خطا در پاک کردن داده‌ها: {str(e)}"))
                
    def restart_all_data(self):
        """ری‌استارت کامل - پاک کردن همه داده‌ها"""
        if messagebox.askyesno(fix_persian_text("تأیید ری‌استارت"), 
                              fix_persian_text("آیا از شروع مجدد مطمئن هستید؟ تمام داده‌ها پاک خواهند شد!")):
            try:
                # پاک کردن تمام جداول
                self.cursor.execute("DELETE FROM transactions")
                self.cursor.execute("DELETE FROM goals")
                self.cursor.execute("DELETE FROM reminders")
                self.conn.commit()
                
                # به‌روزرسانی نمایش
                self.refresh_display()
                
                # پاک کردن فیلدهای ورودی
                self.amount_var.set("")
                self.desc_var.set("")
                self.category_var.set(fix_persian_text("سایر"))
                self.type_var.set(fix_persian_text("درآمد"))
                
                messagebox.showinfo(fix_persian_text("موفق"), 
                                  fix_persian_text("همه داده‌ها پاک شدند. از اول شروع کنید!"))
                
            except Exception as e:
                messagebox.showerror(fix_persian_text("خطا"), 
                                   fix_persian_text(f"خطا در ری‌استارت: {str(e)}"))
                
    def change_theme(self, theme):
        """تغییر تم برنامه"""
        if theme == 'dark':
            self.root.configure(bg='#2b2b2b')
            # تنظیمات تم تیره
        else:
            self.root.configure(bg='white')
            # تنظیمات تم روشن
            
        messagebox.showinfo(fix_persian_text("موفق"), fix_persian_text(f"تم {theme} اعمال شد"))
        
    def clear_filter(self):
        """حذف فیلتر"""
        self.filter_var.set(fix_persian_text("همه"))
        self.refresh_display()
        
    def run(self):
        """اجرا کردن برنامه"""
        self.root.mainloop()
        
    def __del__(self):
        """بستن اتصال دیتابیس"""
        if hasattr(self, 'conn'):
            self.conn.close()

# اجرای برنامه
if __name__ == "__main__":
    app = UltimateFinanceManager()
    app.run()