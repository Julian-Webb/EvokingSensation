import os

import tkinter as tk
from tkinter import ttk, font


class AppStyle(ttk.Style):
    """Singleton class for style"""

    def __init__(self):
        super().__init__()

        base_font = 'TkDefaultFont'

        # change standard font size
        font.nametofont('TkDefaultFont').configure(size=14)
        font.nametofont('TkTextFont').configure(size=14)

        # Configure different heading styles
        self.configure("Heading1.TLabel", font=(base_font, 24, "bold"))
        self.configure("Heading2.TLabel", font=(base_font, 20, "bold"))
        self.configure("Heading3.TLabel", font=(base_font, 16, "bold"))

        self.configure("Bold.TLabel", font=(base_font, 14, 'bold'))
        self.configure("Italic.TLabel", font=(base_font, 14, 'italic'))
        self.configure("Body.TLabel", font=(base_font, 14))
        self.configure("Small.TLabel", font=(base_font, 10))

        self.configure("Italic.TButton", font=(base_font, 14, 'italic'))
        self.configure("ErrorText.TLabel", font=(base_font, 14), foreground="red")
        self.configure("SmallWarning.TButton", font=(base_font, 12), foreground="#EF6A6A"
)
        self.configure("EnabledStopButton.TButton", background="red", foreground="red")

# app_style = AppStyle()
