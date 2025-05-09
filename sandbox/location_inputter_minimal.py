import tkinter as tk
from PIL import Image, ImageTk


class LocationInputter(tk.Canvas):
    CHECKBOX_POSITIONS = {'D1': (0.75, 0.375), 'D2': (0.7, 0.73), 'S1': (0.26, 0.36), }

    def __init__(self, master, image_path):
        super().__init__(master)

        # Load, scale, and display the image
        self.image = Image.open(image_path).resize((500, 500), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)
        self.create_image(0, 0, image=self.photo, anchor="nw")

        # Set canvas size to match image
        self.config(width=self.image.width, height=self.image.height)

        # Add all the checkbuttons
        for name, pos in self.CHECKBOX_POSITIONS.items():
            self.add_checkbutton(pos[0], pos[1])

    def add_checkbutton(self, relx, rely):
        """Add a checkbutton at the specified coordinates
        :param relx: The relative x position (0-1)
        :param rely: The relative y position (0-1)
        """
        cb = tk.Checkbutton(self, padx=0, pady=0, border=0)
        cb.place(relx=relx, rely=rely, anchor='nw')

image_path = "C:\\Users\\julia\\PycharmProjects\\EvokingSensation\\images\\foot_dermatomes.png"

root = tk.Tk()
root.overrideredirect(True)
canvas = tk.Canvas(root, width=500, height=500)
canvas.pack()
# Load Image
image = ImageTk.PhotoImage(Image.open(image_path).resize((500, 500)))
canvas.create_image(0, 0, anchor="nw", image=image)

# Create Checkbuttons
for name, pos in {'D1': (0.75, 0.375), 'D2': (0.7, 0.73), 'S1': (0.26, 0.36)}.items():
    cb = tk.Checkbutton(canvas, padx=0, pady=0, background='white')
    cb.place(relx=pos[0], rely=pos[1], anchor='nw')

root.mainloop()

