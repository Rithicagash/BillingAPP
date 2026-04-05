import os
import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import pandas as pd
from PIL import Image, ImageTk
import pystray
from pystray import MenuItem as item
import threading
import shutil


STUDIO_NAME = "FOCUS STUDIO"
STUDIO_ADDRESS =("POIYERIKARAI,PUTHUKADU ROAD,\n"
                 "NEAR VAO OFFICE,G.S COLONY(PO),\n"
                 "ANTHIYUR(TK),ERODE(DT),638501.")
STUDIO_CONTACT = "Phone: +91 9659108483,6382023179,04256 234483 | Email: focusstudio8483@gmail.com"
THEME_ORANGE = colors.HexColor("#F57C00")  # Orange
THEME_BLACK = colors.black
current_day = datetime.now().strftime("%d-%m-%Y")

# Create bills folder if it doesn't exist
BILLS_FOLDER = "bills"
if not os.path.exists(BILLS_FOLDER):
    os.makedirs(BILLS_FOLDER)

def reset_form():
    customer_entry.delete(0, tk.END)

    for service, var in service_vars.items():
        var.set(0)
        qty_entries[service].delete(0, tk.END)
        qty_entries[service].insert(0, "1")

    total_var.set("0")

def check_new_day():
    global current_day

    today = datetime.now().strftime("%d-%m-%Y")

    if today != current_day:
        current_day = today
        reset_form()
        messagebox.showinfo(
            "New Day Started",
            "New day detected.\nBilling data has been reset for today."
        )

    app.after(60000, check_new_day)  # check every 1 minute

def export_daily_bills():
    today = datetime.now().strftime("%d-%m-%Y")

    # Fetch today's bills
    cur.execute("""
        SELECT id AS Bill_No,
               customer AS Customer_Name,
               total AS Total_Amount,
               date AS Bill_Date
        FROM bills
        WHERE date LIKE ?
    """, (f"{today}%",))

    rows = cur.fetchall()

    if not rows:
        messagebox.showinfo("No Data", "No bills found for today")
        return

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=["Bill No", "Customer Name", "Total Amount (RS.)", "Date & Time"])

    # Create daily folder for Excel files
    daily_excel_folder = os.path.join("reports", today)
    if not os.path.exists(daily_excel_folder):
        os.makedirs(daily_excel_folder)

    # File name
    filename = f"Daily_Bills_{today}.xlsx"
    filepath = os.path.join(daily_excel_folder, filename)

    try:
        df.to_excel(filepath, index=False)
        messagebox.showinfo(
            "Export Successful",
            f"Daily bills exported successfully!\n\nFile saved at:\n{filepath}"
        )
    except Exception as e:
        messagebox.showerror("Export Failed", str(e))

# Load Excel data
try:
    df = pd.read_excel("services.xlsx")
    services = dict(zip(df["Service Name"], df["Price"]))
except:
    messagebox.showerror("Excel Error", "services.xlsx not found or invalid")
    services = {}

# Database - WITH CORRECT TABLE STRUCTURE
conn = sqlite3.connect("billing.db")
cur = conn.cursor()

# Check if table exists and has the pdf_path column
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bills'")
table_exists = cur.fetchone()

if table_exists:
    # Check if pdf_path column exists
    cur.execute("PRAGMA table_info(bills)")
    columns = [column[1] for column in cur.fetchall()]
    
    if 'pdf_path' not in columns:
        # Add the missing column
        cur.execute("ALTER TABLE bills ADD COLUMN pdf_path TEXT")
        conn.commit()
        print("Added pdf_path column to existing bills table")
else:
    # Create table if it doesn't exist
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT,
        total REAL,
        date TEXT,
        pdf_path TEXT
    )
    """)
    conn.commit()

# -------- UI --------
app = tk.Tk()
app.title("Photography Billing Software")
app.geometry("600x800")
app.resizable(False, False)

# Logo
try:
    logo_img = Image.open("water mark.jpeg")
    logo_img = logo_img.resize((150, 80))
    logo = ImageTk.PhotoImage(logo_img)

    logo_label = tk.Label(app, image=logo)
    logo_label.image = logo
    logo_label.pack(pady=5)
except Exception as e:
    print(f"Could not load logo: {e}")

tk.Label(app, text="Photography Billing Software",
         font=("Arial", 16, "bold")).pack(pady=10)

# Customer
tk.Label(app, text="Customer Name").pack()
customer_entry = tk.Entry(app, width=40)
customer_entry.pack(pady=5)

# Services Frame
service_frame = tk.LabelFrame(app, text="Select Services", padx=10, pady=10)
service_frame.pack(pady=10, fill="x")

service_vars = {}
qty_entries = {}

row = 0
tk.Label(service_frame, text="Service").grid(row=0, column=0)
tk.Label(service_frame, text="Price").grid(row=0, column=1)
tk.Label(service_frame, text="Quantity").grid(row=0, column=2)

for service, price in services.items():
    var = tk.IntVar()
    service_vars[service] = var

    tk.Checkbutton(service_frame, text=service, variable=var)\
        .grid(row=row+1, column=0, sticky="w")

    tk.Label(service_frame, text=f"RS. {price}")\
        .grid(row=row+1, column=1)

    qty = tk.Entry(service_frame, width=5)
    qty.insert(0, "1")
    qty.grid(row=row+1, column=2)
    qty_entries[service] = qty

    row += 1

# Total Label
total_var = tk.StringVar(value="0")
tk.Label(app, text="Total Amount (RS.)",
         font=("Arial", 12, "bold")).pack()
tk.Label(app, textvariable=total_var,
         font=("Arial", 14)).pack(pady=5)

# Calculate Total
def calculate_total():
    total = 0
    for service, var in service_vars.items():
        if var.get():
            try:
                qty = int(qty_entries[service].get())
                if qty <= 0:
                    raise ValueError
            except:
                messagebox.showerror("Invalid Quantity",f"Enter valid quantity for {service}")
                return

            total += services[service] * qty
    total_var.set(str(total))

tk.Button(app, text="Calculate Total",
          command=calculate_total).pack(pady=5)
date_time_var = tk.StringVar()

after_job = None

def update_datetime():
    global after_job
    now = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
    date_time_var.set(f"Date & Time: {now}")
    after_job = app.after(1000, update_datetime)

tk.Label(app, textvariable=date_time_var,
         font=("Arial", 10)).pack(pady=3)

update_datetime()

# Generate Bill
def generate_bill():
    customer = customer_entry.get()
    if not customer:
        messagebox.showerror("Error", "Enter customer name")
        return

    selected = []
    total = 0

    for service, var in service_vars.items():
        if var.get():
            qty = int(qty_entries[service].get())
            price = services[service]
            amount = price * qty
            selected.append((service, qty, price, amount))
            total += amount

    if not selected:
        messagebox.showerror("Error", "Select at least one service")
        return

    date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    date_only = datetime.now().strftime("%d-%m-%Y")
    
    # Create daily folder
    daily_folder = os.path.join(BILLS_FOLDER, date_only)
    if not os.path.exists(daily_folder):
        os.makedirs(daily_folder)

    # Insert bill into database WITHOUT pdf_path initially
    cur.execute("INSERT INTO bills (customer, total, date) VALUES (?,?,?)",
                (customer, total, date))
    conn.commit()

    bill_no = cur.lastrowid
    
    # Generate PDF filename with date folder
    filename = f"Bill_{bill_no}.pdf"
    filepath = os.path.join(daily_folder, filename)

    # Create PDF
    try:
        c = canvas.Canvas(filepath, pagesize=A4)
        
        # -------- WATERMARK --------
        try:
            c.saveState()  # Save current canvas state
            c.setFillAlpha(0.12)   # 🔥 LOW transparency (0.05–0.1 is ideal)
            c.setStrokeAlpha(0.12)

            # Center watermark
            c.drawImage(
                "water mark.jpeg",
                100, 250,            # X, Y position
                width=400,
                height=300,
                mask='auto'
            )
            c.restoreState()  # Restore canvas state
        except Exception as e:
            print(f"Watermark error: {e}")

        # 🔶 Header background (White)
        c.setFillColor(colors.white)
        c.rect(0, 760, 595, 80, fill=1, stroke=0)

        # Optional: thin orange border under header
        c.setStrokeColor(THEME_ORANGE)
        c.setLineWidth(2)
        c.line(0, 755, 590, 755)

        # Logo
        try:
            c.drawImage("water mark.jpeg", 460, 775, width=100, height=50, mask='auto')
        except Exception as e:
            print(f"Logo error: {e}")

        # Studio Name (Black text on orange)
        c.setFillColor(THEME_ORANGE)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, 810, STUDIO_NAME)

        # Address & Contact
        c.setFillColor(THEME_BLACK)
        c.setFont("Helvetica", 10)
        y_address = 795
        for line in STUDIO_ADDRESS.split("\n"):
            c.drawString(40, y_address, line)
            y_address -= 10
        
        c.drawString(40, y_address - 5, STUDIO_CONTACT)
        content_start_y = y_address - 25
        
        # Bill Title
        c.setFillColor(THEME_ORANGE)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(300, content_start_y, "PAYMENT RECEIPT")

        # Bill Info
        c.setFillColor(THEME_BLACK)
        c.setFont("Helvetica", 11)
        c.drawString(50, content_start_y - 25, f"Bill No: {bill_no}")
        c.drawString(350, content_start_y - 25, f"Date: {date}")
        c.drawString(50, content_start_y - 45, f"Customer: {customer}")

        # ================= SERVICE TABLE =================
        table_x = 40
        table_y = content_start_y - 90
        row_height = 22
        col_widths = [210, 60, 90, 120]  # Service | Qty | Price | Amount
        table_width = sum(col_widths)

        # Header background
        c.setFillColor(THEME_ORANGE)
        c.rect(table_x, table_y, table_width, row_height, fill=1, stroke=0)

        # Header text
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        headers = ["Service", "Qty", "Price", "Amount"]
        x = table_x
        for i, h in enumerate(headers):
            c.drawString(x + 5, table_y + 7, h)
            x += col_widths[i]

        # Table border (outer)
        c.setStrokeColor(THEME_BLACK)
        c.setLineWidth(1.2)
        c.rect(table_x, table_y, table_width, row_height)

        # Rows
        y = table_y - row_height
        c.setFont("Helvetica", 11)
        c.setFillColor(THEME_BLACK)

        for service, qty, price, amount in selected:
            x = table_x
            row_data = [
                service,
                str(qty),
                f"RS. {price}",
                f"RS. {amount}"
            ]

            for i, data in enumerate(row_data):
                c.drawString(x + 5, y + 7, data)
                c.rect(x, y, col_widths[i], row_height)  # cell border
                x += col_widths[i]

            y -= row_height

        # ================= TOTAL =================
        c.setLineWidth(1.5)
        c.line(table_x + col_widths[0] + col_widths[1],
            y - 5,
            table_x + table_width,
            y - 5)

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(THEME_ORANGE)
        c.drawString(table_x + col_widths[0] + col_widths[1] + 10, y - 25, "TOTAL:")
        c.drawString(table_x + col_widths[0] + col_widths[1] + 90, y - 25, f"RS. {total}")


        # Footer
        c.setFont("Helvetica", 10)
        c.setFillColor(THEME_BLACK)
        c.drawCentredString(300, 80, "Thank you for choosing us!")
        c.drawCentredString(300, 65, "FOCUS STUDIO")

        c.save()
        
        # Update database with PDF path
        cur.execute("UPDATE bills SET pdf_path = ? WHERE id = ?", (filepath, bill_no))
        conn.commit()

        # Also copy PDF to root directory for easy access
        try:
            root_copy_path = os.path.join(os.getcwd(), filename)
            shutil.copy2(filepath, root_copy_path)
            
            messagebox.showinfo("Success", 
                               f"Bill Generated Successfully!\n\n"
                               f"Bill No: {bill_no}\n"
                               f"Saved in: {daily_folder}\n"
                               f"Also copied to: {filename}")
        except Exception as e:
            messagebox.showinfo("Success", 
                               f"Bill Generated Successfully!\n\n"
                               f"Bill No: {bill_no}\n"
                               f"Saved in: {daily_folder}\n"
                               f"Note: Could not create root copy: {str(e)}")
        
        # Reset form after successful bill generation
        reset_form()
        
    except Exception as e:
        messagebox.showerror("PDF Creation Error", f"Failed to create PDF: {str(e)}")
        # Rollback the database insertion
        conn.rollback()

tk.Button(app, text="Generate & Print Bill",
          bg="green", fg="white",
          font=("Arial", 12),
          command=generate_bill).pack(pady=20)

tk.Button(
    app,
    text="Export Today's Bills to Excel",
    bg="orange",
    fg="black",
    font=("Arial", 11, "bold"),
    command=export_daily_bills).pack(pady=5)

def hide_window():
    app.withdraw()   # hide window
    show_tray_icon()

def show_window(icon, item):
    icon.stop()
    app.after(0, app.deiconify)

def quit_app(icon, item):
    icon.stop()
    app.after(0, app.destroy)

def show_tray_icon():
    try:
        image = Image.open("logo.jpeg")  # tray icon
    except:
        # Create a simple default icon if logo doesn't exist
        image = Image.new('RGB', (64, 64), color='orange')
    
    menu = (
        item("Open Billing App", show_window),
        item("Exit", quit_app)
    )

    icon = pystray.Icon(
        "FocusStudioBilling",
        image,
        "Focus Studio Billing",
        menu
    )

    threading.Thread(target=icon.run, daemon=True).start()

def on_app_close():
    try:
        if after_job:
            app.after_cancel(after_job)
    except:
        pass

    try:
        conn.close()   # Close SQLite properly
    except:
        pass

    app.destroy()     # Destroy window
    os._exit(0)       # FORCE exit Python process


# Create reports folder if it doesn't exist
if not os.path.exists("reports"):
    os.makedirs("reports")

check_new_day()
app.protocol("WM_DELETE_WINDOW", on_app_close)

app.mainloop()

# Close database connection when app closes
conn.close()