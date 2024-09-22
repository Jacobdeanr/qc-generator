import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
import sys
import webbrowser

def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.showtip)
        widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         wraplength=250)
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class QCFileGenerator:
    def __init__(self, master):
        self.master = master
        master.title("QC File Generator")

        # Variables
        self.surfaceprop_data = self.load_surfaceprop_yaml()
        self.game_list = self.get_game_list()
        self.surfaceprop = tk.StringVar()
        self.selected_games_vars = {}
        for game in self.game_list:
            self.selected_games_vars[game] = tk.BooleanVar(value=False)

        self.model_working_folder = tk.StringVar(value="props_dev/dev")
        self.model_name = tk.StringVar()
        self.cdmaterials = tk.StringVar()
        self.sequence = tk.StringVar()
        self.body_name = tk.StringVar(value="body")
        self.body_smd = tk.StringVar()
        self.scale = tk.DoubleVar(value=1.0)
        self.staticprop = tk.BooleanVar(value=False)
        self.casttextureshadows = tk.BooleanVar(value=False)
        self.mostlyopaque = tk.BooleanVar(value=False)
        self.collisionmodel = tk.StringVar()
        self.mass = tk.DoubleVar(value=35.0)
        self.concave = tk.BooleanVar()

        # LODs
        self.lod_entries = []

        self.create_widgets()

    def create_widgets(self):
        # Menu Bar
        menubar = tk.Menu(self.master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Load SMD", command=self.open_smd_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.open_about)
        menubar.add_cascade(label="Help", menu=helpmenu)
        self.master.config(menu=menubar)

        # Main Frame
        main_frame = tk.Frame(self.master)
        main_frame.pack(pady=10)

        # Model Name Entry
        tk.Label(main_frame, text="Model Name:").grid(row=0, column=0, sticky='e')
        self.model_name_entry = tk.Entry(main_frame, textvariable=self.model_name, width=50)
        self.model_name_entry.grid(row=0, column=1, padx=5, pady=5)
        Tooltip(self.model_name_entry, "Output name of the .mdl file.")

        # Model Working Folder
        tk.Label(main_frame, text="Working Folder:").grid(row=1, column=0, sticky='e')
        self.working_folder_entry = tk.Entry(main_frame, textvariable=self.model_working_folder, width=50)
        self.working_folder_entry.grid(row=1, column=1, padx=5, pady=5)
        Tooltip(self.working_folder_entry, "Where the .mdl will be compiled to, and where materials references will point relative to the game/materials/models folder.\n\nFor example a working folder of 'props_dev/dev' the model will compile to 'game/models/props_dev/dev/' and materials will need to be placed in 'game/materials/models/props_dev/dev/'")

        # Tabs
        tab_control = ttk.Notebook(self.master)
        tab_control.pack(expand=1, fill='both')

        # Collision Tab
        self.collision_tab = tk.Frame(tab_control)
        tab_control.add(self.collision_tab, text='Collision')
        self.create_collision_tab()

        # Surface Properties Tab
        self.surface_tab = tk.Frame(tab_control)
        tab_control.add(self.surface_tab, text='Surface Properties')
        self.create_surface_tab()

        # LOD Tab
        self.lod_tab = tk.Frame(tab_control)
        tab_control.add(self.lod_tab, text='LOD')
        self.create_lod_tab()

        # Advanced Settings Tab
        self.advanced_tab = tk.Frame(tab_control)
        tab_control.add(self.advanced_tab, text='Other Settings')
        self.create_other_tab()
        
        # Generate Button
        tk.Button(self.master, text="Generate QC File", command=self.generate_qc_file, bg='green', fg='white').pack(pady=10)

    def create_surface_tab(self):
        tk.Label(self.surface_tab, text="Surface Properties", font=('Arial', 12, 'bold')).pack(pady=10)

        form_frame = tk.Frame(self.surface_tab)
        form_frame.pack(pady=10)

        # Target Games
        tk.Label(form_frame, text="Target Games:").grid(row=0, column=0, sticky='ne')
        games_frame = tk.Frame(form_frame)
        games_frame.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        for idx, game in enumerate(self.game_list):
            chk = tk.Checkbutton(games_frame, text=game, variable=self.selected_games_vars[game], command=self.update_surfaceprop_options)
            chk.grid(row=idx//4, column=idx%4, sticky='w')

        # Surfaceprop
        tk.Label(form_frame, text="$surfaceprop:").grid(row=1, column=0, sticky='ne')
        self.surfaceprop_combobox = ttk.Combobox(form_frame, textvariable=self.surfaceprop, width=47, state='readonly')
        self.surfaceprop_combobox['values'] = []
        self.surfaceprop_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.surfaceprop_combobox.bind('<<ComboboxSelected>>', self.update_surfaceprop_details)

        # Description and Supported Games
        tk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky='ne')
        self.surfaceprop_description_text = tk.Text(form_frame, width=47, height=4, wrap='word')
        self.surfaceprop_description_text.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Supported Games:").grid(row=3, column=0, sticky='ne')
        self.surfaceprop_games_text = tk.Text(form_frame, width=47, height=2, wrap='word')
        self.surfaceprop_games_text.grid(row=3, column=1, padx=5, pady=5)

    def create_other_tab(self):
        tk.Label(self.advanced_tab, text="Other Settings", font=('Arial', 12, 'bold')).pack(pady=10)

        form_frame = tk.Frame(self.advanced_tab)
        form_frame.pack(pady=10)

        # Body Name Entry
        tk.Label(form_frame, text="Body Name:").grid(row=0, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.body_name, width=50).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Scale:").grid(row=1, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.scale, width=50).grid(row=1, column=1, padx=5, pady=5)

        self.staticprop_checkbutton = tk.Checkbutton(form_frame, text="Prop is static", variable=self.staticprop, command=self.update_casttextureshadows_state)
        self.staticprop_checkbutton.grid(row=2, column=0, columnspan=2, sticky='w')
        Tooltip(self.staticprop_checkbutton, "Tells the model compiler that this model is not intended to have any moving parts.")

        self.casttextureshadows_checkbutton = tk.Checkbutton(form_frame, text="Cast shadows from texture's alpha", variable=self.casttextureshadows)
        self.casttextureshadows_checkbutton.grid(row=3, column=0, columnspan=2, sticky='w')
        Tooltip(self.casttextureshadows_checkbutton, "Indicates the model should cast texture-based shadows from $alphatest and $translucent materials while compiling map in VRAD.")

        self.mostlyopaque_checkbutton = tk.Checkbutton(form_frame, text="Mostly Opaque", variable=self.mostlyopaque)
        self.mostlyopaque_checkbutton.grid(row=4, column=0, columnspan=2, sticky='w')
        Tooltip(self.mostlyopaque_checkbutton, "Causes the model to be rendered in two passes.Can be used to improve the visual quality of models such as foliage or underbrush, by improving the lighting on the translucent materials.")

        self.update_casttextureshadows_state()

    def update_casttextureshadows_state(self):
        if self.staticprop.get():
            self.casttextureshadows_checkbutton.config(state='normal')
        else:
            self.casttextureshadows_checkbutton.config(state='disabled')
            self.casttextureshadows.set(False)

    def create_collision_tab(self):
        tk.Label(self.collision_tab, text="Collision Settings", font=('Arial', 12, 'bold')).pack(pady=10)

        form_frame = tk.Frame(self.collision_tab)
        form_frame.pack(pady=10)

        # $collisionmodel with Browse Button
        tk.Label(form_frame, text="Collision Model:").grid(row=0, column=0, sticky='e')
        collision_frame = tk.Frame(form_frame)
        collision_frame.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        tk.Entry(collision_frame, textvariable=self.collisionmodel, width=40).pack(side=tk.LEFT)
        tk.Button(collision_frame, text="Browse", command=self.browse_collision_model).pack(side=tk.LEFT)

        # Mass Entry with validation
        tk.Label(form_frame, text="Mass:").grid(row=1, column=0, sticky='e')
        vcmd = (self.master.register(self.validate_float), '%P')
        mass_entry = tk.Entry(form_frame, textvariable=self.mass, width=50, validate='key', validatecommand=vcmd)
        mass_entry.grid(row=1, column=1, padx=5, pady=5)
        Tooltip(mass_entry, "By default, the Player can +USE pick up 35KG max. The gravgun can pick up 250KG max. The portal gun can pick up 85KG max.")

        self.concave_checkbutton = tk.Checkbutton(form_frame, text="Collision is Concave", variable=self.concave)
        self.concave_checkbutton.grid(row=3, column=0, columnspan=2, sticky='w')
        Tooltip(self.concave_checkbutton, "By default, studiomdl will generate a single convex hull by 'shrinkwrapping' any concavities. This option will use the concave hull provided in the collision model.")

    def create_lod_tab(self):
        tk.Label(self.lod_tab, text="Level of Detail (LOD) Settings", font=('Arial', 12, 'bold')).pack(pady=10)

        self.lod_frame = tk.Frame(self.lod_tab)
        self.lod_frame.pack(fill='both', expand=True)

        # Scrollable Canvas
        canvas = tk.Canvas(self.lod_frame)
        scrollbar = tk.Scrollbar(self.lod_frame, orient="vertical", command=canvas.yview)
        self.lod_items_frame = tk.Frame(canvas)

        self.lod_items_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.lod_items_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add LOD Button
        tk.Button(self.lod_tab, text="Add LOD", command=self.add_lod_entry).pack(pady=5)

    def add_lod_entry(self):
        idx = len(self.lod_entries)
        entry_frame = tk.Frame(self.lod_items_frame)
        entry_frame.pack(pady=5, fill='x')

        tk.Label(entry_frame, text="Screen Size:").grid(row=0, column=0, sticky='e')
        screen_size = tk.StringVar()
        tk.Entry(entry_frame, textvariable=screen_size, width=10).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(entry_frame, text="LOD Model:").grid(row=0, column=2, sticky='e')
        lod_model = tk.StringVar()
        tk.Entry(entry_frame, textvariable=lod_model, width=20).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(entry_frame, text="Browse", command=lambda: self.browse_lod_model(lod_model)).grid(row=0, column=4, padx=5)

        tk.Button(entry_frame, text="Remove", command=lambda: self.remove_lod_entry(entry_frame, idx)).grid(row=0, column=5, padx=5)

        self.lod_entries.append({
            'frame': entry_frame,
            'screen_size': screen_size,
            'lod_model': lod_model
        })

    def remove_lod_entry(self, frame, idx):
        frame.destroy()
        self.lod_entries.pop(idx)

    def validate_float(self, P):
        if P == '':
            return True
        try:
            float(P)
            return True
        except ValueError:
            return False

    def browse_collision_model(self):
        if not self.body_smd.get():
            messagebox.showerror("Error", "Please load an SMD file first. go to File > Load SMD")
            return
        smd_dir = os.path.dirname(self.body_smd.get())
        file_selected = filedialog.askopenfilename(initialdir=smd_dir, filetypes=[("SMD files", "*.smd")])
        if file_selected:
            # Get relative path to the main SMD file's directory
            rel_path = os.path.relpath(file_selected, smd_dir).replace("\\", "/")
            self.collisionmodel.set(rel_path)

    def browse_lod_model(self, lod_model_var):
        if not self.body_smd.get():
            messagebox.showerror("Error", "Please load an SMD file first. go to File > Load SMD")
            return
        smd_dir = os.path.dirname(self.body_smd.get())
        file_selected = filedialog.askopenfilename(initialdir=smd_dir, filetypes=[("SMD files", "*.smd")])
        if file_selected:
            # Get relative path to the main SMD file's directory
            rel_path = os.path.relpath(file_selected, smd_dir).replace("\\", "/")
            lod_model_var.set(rel_path)

    def open_smd_file(self):
        file_selected = filedialog.askopenfilename(filetypes=[("SMD files", "*.smd")])
        if file_selected:
            self.body_smd.set(file_selected)
            smd_base_name = os.path.basename(file_selected)
            smd_name_no_ext = os.path.splitext(smd_base_name)[0]
            self.sequence.set(smd_base_name)
            # Set Model Name to smd file name without extension
            self.model_name.set(f'{smd_name_no_ext}.mdl')
            # Infer cdmaterials if Model Working Folder is specified
            self.infer_cdmaterials()
    
    def open_about(self):
        webbrowser.open("https://github.com/Jacobdeanr/qc-generator")

    def infer_cdmaterials(self):
        working_folder = self.model_working_folder.get().strip()
        # Normalize working folder path
        working_folder = working_folder.strip("/\\").replace("\\", "/")
        if working_folder:
            # Set $cdmaterials
            cdmaterials_path = f"models/{working_folder}"
            self.cdmaterials.set(cdmaterials_path)
        else:
            # If working folder is empty, clear cdmaterials
            self.cdmaterials.set("")

    def update_surfaceprop_options(self):
        selected_games = [game for game, var in self.selected_games_vars.items() if var.get()]
        if not selected_games:
            self.surfaceprop_combobox['values'] = []
            self.surfaceprop.set('')  # Clear current selection
            self.surfaceprop_description_text.delete(1.0, tk.END)
            self.surfaceprop_games_text.delete(1.0, tk.END)
            return

        filtered_surfaceprops = []
        for key, details in self.surfaceprop_data.items():
            supported_games = details.get('supported_games', [])
            if 'ALL' in supported_games or any(game in supported_games for game in selected_games):
                filtered_surfaceprops.append(key)

        self.surfaceprop_combobox['values'] = filtered_surfaceprops
        self.surfaceprop.set('')
        self.surfaceprop_description_text.delete(1.0, tk.END)
        self.surfaceprop_games_text.delete(1.0, tk.END)

    def update_surfaceprop_details(self, event):
        selected_surfaceprop = self.surfaceprop.get()
        details = self.surfaceprop_data.get(selected_surfaceprop, {})
        description = details.get('description', 'No description available.')
        supported_games = ', '.join(details.get('supported_games', []))

        # Update the text widgets
        self.surfaceprop_description_text.delete(1.0, tk.END)
        self.surfaceprop_description_text.insert(tk.END, description)

        self.surfaceprop_games_text.delete(1.0, tk.END)
        self.surfaceprop_games_text.insert(tk.END, supported_games)


    def load_surfaceprop_yaml(self):
        yaml_file_path = resource_path('surfaceprop.yaml')

        if not os.path.isfile(yaml_file_path):
            messagebox.showerror("Error", f"surfaceprop.yaml file not found at {yaml_file_path}")
            return {}

        try:
            with open(yaml_file_path, 'r') as file:
                data = yaml.safe_load(file)

            surfaceprops = {}
            for type_category, subtypes in data.get('types', {}).items():
                for subtype, details in subtypes.items():
                    key = f"{type_category} - {subtype}"
                    supported_games = details.get('supported_games', '').split(', ')
                    surfaceprops[key] = {
                        'description': details.get('description', ''),
                        'supported_games': supported_games
                    }
            return surfaceprops
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load surfaceprop.yaml:\n{e}")
            return {}

    def get_game_list(self):
        games = set()
        for details in self.surfaceprop_data.values():
            games.update(details.get('supported_games', []))
        game_list = sorted(games)
        return game_list

    def generate_qc_file(self):
        if not self.body_smd.get():
            messagebox.showerror("Error", "Please open an SMD file first.")
            return

        if not self.model_working_folder.get() or not self.model_name.get():
            messagebox.showerror("Error", "Model Working Folder or Model Name not specified.")
            return

        # Normalize working folder path
        working_folder = self.model_working_folder.get().strip().strip("/\\").replace("\\", "/")
        model_name = self.model_name.get().strip()

        if not model_name.endswith(".mdl"):
            model_name += ".mdl"

        # Construct $modelname
        modelname_full = f"{working_folder}/{model_name}"

        # Update cdmaterials
        self.infer_cdmaterials()

        # Prepare QC file content
        qc_content = "//Made with QC File Generator by Jacob Robbins\n//https://github.com/Jacobdeanr/qc-generator\n"

        # Required fields
        qc_content += f'$modelname "{modelname_full}"\n'
        qc_content += f'$body "{self.body_name.get()}" "{os.path.basename(self.body_smd.get())}"\n'
        
        if not self.surfaceprop.get():
            qc_content += f'$surfaceprop "Default"\n'
        else:
            qc_content += f'$surfaceprop "{self.surfaceprop.get().split(" - ")[-1]}"\n'
        
        qc_content += f'$cdmaterials "{self.cdmaterials.get()}"\n'

        # Optional fields
        if self.scale.get():
            qc_content += f'$scale {self.scale.get()}\n'

        qc_content += f'$sequence "idle" "{os.path.basename(self.body_smd.get())}"\n'

        if self.staticprop.get():
            qc_content += '$staticprop\n'

        if self.casttextureshadows.get():
            qc_content += '$casttextureshadows\n'

        if self.mostlyopaque.get():
            qc_content += '$mostlyopaque\n'
        else:
            qc_content += '$opaque\n'

        # Collision settings
        if self.collisionmodel.get():
            qc_content += f'$collisionmodel "{self.collisionmodel.get()}"\n'
            qc_content += "{\n"
            if self.mass.get():
                qc_content += f'\t$mass {self.mass.get()}\n'
            if self.concave.get():
                qc_content += '\t$concave\n'
            qc_content += '}\n'

        # LOD settings
        base_model = os.path.basename(self.body_smd.get())
        for lod_entry in self.lod_entries:
            screen_size = lod_entry['screen_size'].get()
            lod_model = lod_entry['lod_model'].get()
            if screen_size and lod_model:
                qc_content += f'$lod {screen_size}\n'
                qc_content += '{\n'
                qc_content += f'\treplacemodel "{base_model}" "{lod_model}"\n'
                qc_content += '}\n'

        # Write to QC file in the same directory as the SMD file
        qc_file_path = os.path.splitext(self.body_smd.get())[0] + '.qc'
        try:
            with open(qc_file_path, 'w') as qc_file:
                qc_file.write(qc_content)
            messagebox.showinfo("Success", f"QC file generated at:\n{qc_file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write QC file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = QCFileGenerator(root)
    root.mainloop()
