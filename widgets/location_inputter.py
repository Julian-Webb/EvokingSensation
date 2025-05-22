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
        elif self == LocationType.LEG:
            return "lower_leg_pictogram.png"
        else:
            raise ValueError(f"Invalid location type: {self}")


class LocationInputter(tk.Canvas):
    FOOT_CHECKBOXES = {
        "D1": {"x_rel": 0.760, "y_rel": 0.357, 'background': '#F2EF8D'},
        "D2": {"x_rel": 0.705, "y_rel": 0.710, 'background': '#FF4444'},
        "D3": {"x_rel": 0.823, "y_rel": 0.035, 'background': '#DCDCDC'},
        "D4": {"x_rel": 0.940, "y_rel": 0.632, 'background': '#DCDCDC'},
        "S1": {"x_rel": 0.281, "y_rel": 0.340, 'background': '#C19F43'},
        "S2": {"x_rel": 0.155, "y_rel": 0.398, 'background': '#83ABE0'},
        "S3": {"x_rel": 0.444, "y_rel": 0.629, 'background': '#DCDCDC'},
        "S4": {"x_rel": 0.060, "y_rel": 0.763, 'background': '#DCDCDC'},
        "S5": {"x_rel": 0.259, "y_rel": 0.789, 'background': '#4AAB89'}
    }
    LEG_CHECKBOXES = {
        "Calf": {"x_rel": 0.32, "y_rel": 0.6, 'background': '#DCDCDC'},
        "Shin": {"x_rel": 0.67, "y_rel": 0.6, 'background': '#DCDCDC'}
    }
    IMAGES_DIR = Path(__file__).parent.parent / 'images'

    def __init__(self, master, location_type: LocationType, location_vars: dict[str, tk.BooleanVar],
                 image_width: int = 600):
        super().__init__(master,
                         # borderwidth=1, relief='solid'
                         )
        self.location_vars = location_vars
        self.style = ttk.Style()

        # Select correct values based on the type of inputter
        checkbox_params = self.FOOT_CHECKBOXES if location_type == LocationType.FOOT else self.LEG_CHECKBOXES
        image_path = self.IMAGES_DIR / location_type.image_name

        # Load, scale, and display the image
        image = Image.open(image_path)
        scaling = image_width / image.width
        scaled_height = round(scaling * image.height)
        image = image.resize((image_width, scaled_height), Image.Resampling.LANCZOS)

        self.photo = ImageTk.PhotoImage(image)
        self.create_image(0, 0, image=self.photo, anchor="nw")

        # Set canvas size to match the image
        self.config(width=image.width, height=image.height)

        # Add all the Checkbuttons
        for name, params in checkbox_params.items():
            self.add_checkbutton(name, _(name), params['x_rel'], params['y_rel'], params['background'])

    def add_checkbutton(self, button_id, display_name, relx: float, rely: float, color: str):
        """Add a checkbutton at the specified coordinates
        :param button_id: The English name of the location (e.g. "Calf")
        :param display_name: The text that the checkbutton shows (e.g. "Calf" or "Schienbein")
        :param relx: The relative x position (0-1)
        :param rely: The relative y position (0-1)
        :param color: The background color of the checkbutton
        """
        assert 0 <= relx <= 1
        assert 0 <= rely <= 1

        style_name = f'Custom.{button_id}.TCheckbutton'
        self.style.configure(style_name, background=color, font=30,
                             indicatorbackground=color,  # make the box itself adjust to the background color
                             )
        cb = ttk.Checkbutton(self, variable=self.location_vars[button_id], text=display_name, style=style_name)
        cb.place(relx=relx, rely=rely, anchor='center')

    def get_states(self):
        """Get the state all Checkbuttons"""
        return {name: var.get() for name, var in self.location_vars.items()}


# Example usage
if __name__ == "__main__":
    root = tk.Tk()

    _ = lambda string: string # for gettext

    location_vars = {loc: tk.BooleanVar(value=False) for loc in
                     ["D1", "D2", "D3", "D4", "S1", "S2", "S3", "S4", "S5", "Calf", "Shin", ]}
    LocationInputter(root, LocationType.FOOT, location_vars, image_width=400).pack(side='left', padx=10, pady=10)
    LocationInputter(root, LocationType.LEG, location_vars, image_width=400).pack(padx=10, pady=10)


    def check_states():
        for name, var in location_vars.items():
            print(f'{name}: {var.get()}')
        print()


    tk.Button(root, text="Check States", command=check_states).pack()
    root.mainloop()
