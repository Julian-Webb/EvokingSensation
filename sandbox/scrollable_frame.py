import sys
import tkinter as tk
from tkinter import ttk


class ScrollableFrame(tk.Frame):
    def __init__(self):
        super().__init__( highlightbackground='green', highlightthickness=2,)

        self.canvas = tk.Canvas(self, highlightbackground='blue', highlightthickness=2,)
        self.main_frame = tk.Frame(self.canvas,  highlightbackground='red', highlightthickness=2,)
        self.canvas.create_window(0, 0, anchor='nw', window=self.main_frame)

        # link canvas and scrollbar
        scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        # Make the entire canvas scrollable
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.main_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        # Add mousewheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)


        # add labels
        tk.Label(self.main_frame, text='=== Top ===').grid(row=0, column=0)
        self.labels_frame = tk.Frame(self.main_frame, relief='sunken', borderwidth=1, )
        self.labels_frame.grid(row=1, column=0)
        ttk.Button(self.main_frame, text='Add Label', command=self.add_label).grid(row=2, column=0)

        self.count = 0
        for _ in range(20):
            self.add_label()

    def _on_mousewheel(self, event):
        if sys.platform == 'darwin': # mac
            delta = -1 * int(event.delta)
        else: # windows
            delta = -1 * int(event.delta // 120)
        self.canvas.yview_scroll(delta, "units")

    def add_label(self):
        text = f'Label {self.count}'
        if self.count >= 20:
            text +=  '-------------------------------------------------------------------------------------------------------------------'
        tk.Label(self.labels_frame, text=text).pack()
        self.count += 1


if __name__ == '__main__':
    root = tk.Tk()
    sf = ScrollableFrame()
    sf.pack(fill='both', expand=True)
    root.mainloop()