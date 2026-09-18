import base64
import json
import tkinter as tk
from tkinter import messagebox


def encrypt_val(value):
  return base64.b64encode(value.encode()).decode()


def save_config():
  server = entry_server.get()
  database = entry_db.get()

  # RadhaUser credentials
  pass_radha = entry_pass_radha.get()

  # AlokUser credentials
  pass_alok = entry_pass_alok.get()

  if not all([server, database, pass_radha, pass_alok]):
    messagebox.showerror(
        "Error", "कृपया Server, Database और दोनों Users के Password भरें!"
    )
    return

  # Dono users ko ek saath JSON file me safe save karna
  config_data = {
      "server": server,
      "database": database,
      "users": {
          "RadhaUser": {
              "user_id": "RadhaUser",
              "password": encrypt_val(pass_radha),
          },
          "AlokUser": {
              "user_id": "AlokUser",
              "password": encrypt_val(pass_alok),
          },
      },
  }

  with open("db_config.json", "w") as f:
    json.dump(config_data, f, indent=4)

  messagebox.showinfo(
      "Success",
      "RadhaUser और AlokUser दोनों की सेटिंग्स सफलतापूर्वक सेव हो गईं!",
  )
  root.destroy()


# GUI Window
root = tk.Tk()
root.title("DB Connection Setup")
root.geometry("450x540")
root.configure(bg="#2C3E50")

tk.Label(
    root,
    text="DB CONNECT TOOL",
    font=("Arial", 16, "bold"),
    fg="#ECF0F1",
    bg="#2C3E50",
).pack(pady=15)


def create_input(label_text, default_val="", show_char=None):
  tk.Label(
      root,
      text=label_text,
      font=("Arial", 10, "bold"),
      fg="#16A085",
      bg="#2C3E50",
  ).pack(anchor="w", padx=40, pady=(2, 0))
  entry = tk.Entry(
      root, font=("Arial", 11), show=show_char, bd=2, relief="groove"
  )
  entry.insert(0, default_val)
  entry.pack(padx=40, pady=(0, 6), fill="x")
  return entry


# Server & Database Info
entry_server = create_input("Server Name / System:", "RADHEY\\SQLEXPRESS")
entry_db = create_input("Database Name:", "Radha_Attendance")

# Section Divider Line
tk.Frame(root, height=2, bg="#34495E").pack(fill="x", padx=40, pady=10)

# Fixed User 1: RadhaUser
entry_pass_radha = create_input(
    "🔑 RadhaUser Password:", "Radha@123", show_char="*"
)

# Fixed User 2: AlokUser
entry_pass_alok = create_input(
    "🔑 AlokUser Password:", "Alok@123", show_char="*"
)

# Save Button
btn_save = tk.Button(
    root,
    text="SAVE BOTH USERS & CONNECT",
    font=("Arial", 12, "bold"),
    bg="#27AE60",
    fg="white",
    activebackground="#2ECC71",
    command=save_config,
)
btn_save.pack(pady=20, padx=40, fill="x")

root.mainloop()