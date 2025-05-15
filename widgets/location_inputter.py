import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
from enum import Enum


class LocationType(Enum):
    FOOT = "foot"
    LEG = "leg"

    @property
    def image_name(self) -> str:
        if self == LocationType.FOOT:
            return "foot_dermatomes.png"
        return "lower_leg_pictogram.png"


class LocationInputter(tk.Canvas):
    FOOT_CHECKBOXES = {
        "D1": {"x_rel": 0.786, "y_rel": 0.357, 'background': '#F1EF99'},
        "D2": {"x_rel": 0.725, "y_rel": 0.710, 'background': '#EF5440'},
        "D3": {"x_rel": 0.832, "y_rel": 0.035, 'background': '#FFFFFF'},
        "D4": {"x_rel": 0.950, "y_rel": 0.632, 'background': '#FFFFFF'},
        "S1": {"x_rel": 0.281, "y_rel": 0.340, 'background': '#BBA052'},
        "S2": {"x_rel": 0.136, "y_rel": 0.398, 'background': '#8BAADB'},
        "S3": {"x_rel": 0.444, "y_rel": 0.629, 'background': '#FFFFFF'},
        "S4": {"x_rel": 0.045, "y_rel": 0.763, 'background': '#FFFFFF'},
        "S5": {"x_rel": 0.259, "y_rel": 0.789, 'background': '#64A98B'}
    }
    LEG_CHECKBOXES = {
        "Calf": {"x_rel": 0.20, "y_rel": 0.6, 'background': '#FFFFFF'},
        "Shin": {"x_rel": 0.60, "y_rel": 0.6, 'background': '#FFFFFF'}
    }
    IMAGES_DIR = Path(__file__).parent.parent / 'images'

    def __init__(self, master, location_type: LocationType, location_vars: dict[str, tk.BooleanVar],
                 scaling: float = 1.0):
        super().__init__(master,
                         highlightbackground='green', highlightthickness=2,
                         )
        self.location_vars = location_vars
        self.style = ttk.Style()
        # self.style.theme_use('clam')

        # Select correct values based on type of inputter
        checkbox_params = self.FOOT_CHECKBOXES if location_type == LocationType.FOOT else self.LEG_CHECKBOXES
        image_path = self.IMAGES_DIR / location_type.image_name

        # Load, scale, and display the image
        self.image = Image.open(image_path)
        scaled_width, scaled_height = int(self.image.width * scaling), int(self.image.height * scaling)
        self.image = self.image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

        self.photo = ImageTk.PhotoImage(self.image)
        self.create_image(0, 0, image=self.photo, anchor="nw")

        # Set canvas size to match the image
        self.config(width=self.image.width, height=self.image.height)

        # Add all the Checkbuttons
        for name, params in checkbox_params.items():
            self.add_checkbutton(name, _(name), params['x_rel'], params['y_rel'], params['background'])

    def add_checkbutton(self, id, display_name, relx: float, rely: float, color: str):
        """Add a checkbutton at the specified coordinates
        :param relx: The relative x position (0-1)
        :param rely: The relative y position (0-1)
        :param id: The English name of the location (e.g. "Calf")
        :param display_name: The text that the checkbutton shows (e.g. "Calf" or "Schienbein")
        """
        assert 0 <= relx <= 1
        assert 0 <= rely <= 1

        style_name = f'Custom.{id}.TCheckbutton'
        self.style.configure(style_name, background=color, font=30,
                             indicatorbackground=color,  # make the box itself adjust to the background color
                             )
        cb = ttk.Checkbutton(self, variable=self.location_vars[id], text=display_name, style=style_name)
        cb.place(relx=relx, rely=rely, anchor='center')

    def get_states(self):
        """Get the state all Checkbuttons"""
        return {name: var.get() for name, var in self.location_vars.items()}


# Example usage
if __name__ == "__main__":
    root = tk.Tk()

    location_vars = {loc: tk.BooleanVar(value=False) for loc in
                     ["D1", "D2", "D3", "D4", "S1", "S2", "S3", "S4", "S5", "Calf", "Shin", ]}
    LocationInputter(root, LocationType.FOOT, location_vars, scaling=0.3).pack(side='left', padx=10, pady=10)
    LocationInputter(root, LocationType.LEG, location_vars, scaling=0.3).pack(padx=10, pady=10)


    def check_states():
        for name, var in location_vars.items():
            print(f'{name}: {var.get()}')
        print()


    tk.Button(root, text="Check States", command=check_states).pack()
    root.mainloop()
