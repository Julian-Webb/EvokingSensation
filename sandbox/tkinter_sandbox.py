import tkinter as tk
from tkinter import ttk

root = tk.Tk()

var = tk.StringVar(root)
var.set("4")
sb = tk.Spinbox(root, from_=1, to=12, textvariable=var)

sb.pack()

root.mainloop()