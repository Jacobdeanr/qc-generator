import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
import pprint

class QCFileGenerator:
    def __init__(self, master):
        self.master = master
        master.title("QC File Generator")

        # Variables
        self.output_dir = tk.StringVar()

        # Required fields
        self.modelname = tk.StringVar()
        self.surfaceprop = tk.StringVar()
        self.cdmaterials = tk.StringVar()
        self.sequence = tk.StringVar()

        # Body Group fields
        self.body_name = tk.StringVar()
        self.body_smd = tk.StringVar()

        # Texture Group fields
        self.texturegroup_name = tk.StringVar()
        self.texturegroup_materials_vars = []

        # Advanced fields
        self.scale = tk.StringVar()
        self.lod = tk.StringVar()
        self.staticprop = tk.BooleanVar()
        self.casttextureshadows = tk.BooleanVar()
        self.collisionmodel = tk.StringVar()

        # Load surfaceprop options from YAML
        self.surfaceprop_options = self.load_surfaceprop_yaml()

        # Create GUI
        self.create_widgets()

    def create_widgets(self):
        # Output Directory at the top
        output_frame = tk.Frame(self.master)
        output_frame.pack(pady=10)

        tk.Label(output_frame, text="Output Directory:").pack(side=tk.LEFT)
        tk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(output_frame, text="Browse", command=self.browse_directory).pack(side=tk.LEFT)

        # Create Tabs
        tab_control = ttk.Notebook(self.master)
        tab_control.pack(expand=1, fill='both')

        # Tab Frames
        self.model_tab = tk.Frame(tab_control)
        self.body_tab = tk.Frame(tab_control)
        self.texture_tab = tk.Frame(tab_control)
        self.advanced_tab = tk.Frame(tab_control)

        tab_control.add(self.model_tab, text='Model Information')
        tab_control.add(self.body_tab, text='Body Groups')
        tab_control.add(self.texture_tab, text='Textures')
        tab_control.add(self.advanced_tab, text='Advanced Settings')

        self.create_model_tab()
        self.create_body_tab()
        self.create_texture_tab()
        self.create_advanced_tab()

        # Generate Button
        tk.Button(self.master, text="Generate QC File", command=self.generate_qc_file, bg='green', fg='white').pack(pady=20)

    def create_model_tab(self):
        tk.Label(self.model_tab, text="Model Information", font=('Arial', 12, 'bold')).pack(pady=10)

        form_frame = tk.Frame(self.model_tab)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="$modelname:").grid(row=0, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.modelname, width=50).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="$surfaceprop:").grid(row=1, column=0, sticky='e')

        # Use Combobox for surfaceprop selection
        self.surfaceprop_combobox = ttk.Combobox(form_frame, textvariable=self.surfaceprop, width=47)
        self.surfaceprop_combobox['values'] = self.surfaceprop_options
        self.surfaceprop_combobox.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="$cdmaterials:").grid(row=2, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.cdmaterials, width=50).grid(row=2, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="$sequence:").grid(row=3, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.sequence, width=50).grid(row=3, column=1, padx=5, pady=5)

    def create_body_tab(self):
        tk.Label(self.body_tab, text="Body Groups", font=('Arial', 12, 'bold')).pack(pady=10)

        form_frame = tk.Frame(self.body_tab)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="$body Name:").grid(row=0, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.body_name, width=50).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="$body SMD:").grid(row=1, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.body_smd, width=50).grid(row=1, column=1, padx=5, pady=5)

    def create_texture_tab(self):
        tk.Label(self.texture_tab, text="Texture Groups", font=('Arial', 12, 'bold')).pack(pady=10)

        form_frame = tk.Frame(self.texture_tab)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="$texturegroup Name:").grid(row=0, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.texturegroup_name, width=50).grid(row=0, column=1, padx=5, pady=5)

        materials_label = tk.Label(form_frame, text="$texturegroup Materials:")
        materials_label.grid(row=1, column=0, sticky='ne')

        self.texturegroup_frame = tk.Frame(form_frame)
        self.texturegroup_frame.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        self.add_texturegroup_material()

        buttons_frame = tk.Frame(form_frame)
        buttons_frame.grid(row=2, column=1, sticky='w')

        tk.Button(buttons_frame, text="Add Material", command=self.add_texturegroup_material).pack(side=tk.LEFT)
        tk.Button(buttons_frame, text="Remove Material", command=self.remove_texturegroup_material).pack(side=tk.LEFT, padx=5)

    def create_advanced_tab(self):
        tk.Label(self.advanced_tab, text="Advanced Settings", font=('Arial', 12, 'bold')).pack(pady=10)

        form_frame = tk.Frame(self.advanced_tab)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="$scale:").grid(row=0, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.scale, width=50).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="$lod:").grid(row=1, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.lod, width=50).grid(row=1, column=1, padx=5, pady=5)

        tk.Checkbutton(form_frame, text="$staticprop", variable=self.staticprop).grid(row=2, column=0, columnspan=2, sticky='w')
        tk.Checkbutton(form_frame, text="$casttextureshadows", variable=self.casttextureshadows).grid(row=3, column=0, columnspan=2, sticky='w')

        tk.Label(form_frame, text="$collisionmodel:").grid(row=4, column=0, sticky='e')
        tk.Entry(form_frame, textvariable=self.collisionmodel, width=50).grid(row=4, column=1, padx=5, pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def add_texturegroup_material(self):
        var = tk.StringVar()
        self.texturegroup_materials_vars.append(var)
        index = len(self.texturegroup_materials_vars) - 1
        tk.Entry(self.texturegroup_frame, textvariable=var, width=50).grid(row=index, column=0, pady=2)

    def remove_texturegroup_material(self):
        if self.texturegroup_materials_vars:
            var = self.texturegroup_materials_vars.pop()
            widgets = self.texturegroup_frame.grid_slaves(row=len(self.texturegroup_materials_vars))
            for widget in widgets:
                widget.destroy()

    def load_surfaceprop_yaml(self):
        # Path to the surfaceprop.yaml file
        yaml_file_path = 'surfaceprop.yaml'

        # Check if the file exists
        if not os.path.isfile(yaml_file_path):
            messagebox.showerror("Error", f"surfaceprop.yaml file not found at {yaml_file_path}")
            return []

        try:
            with open(yaml_file_path, 'r') as file:
                data = yaml.safe_load(file)

            # Debug: Print out the loaded data
            pprint.pprint(data)

            # Check if data is None
            if data is None:
                messagebox.showerror("Error", "surfaceprop.yaml is empty or invalid.")
                return []

            # Extract the surfaceprop types and subtypes
            surfaceprops = []
            for type_category, subtypes in data.get('types', {}).items():
                if subtypes is None:
                    continue  # Handle cases where subtypes are None
                for subtype in subtypes.keys():
                    surfaceprops.append(subtype)

            return sorted(surfaceprops)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load surfaceprop.yaml:\n{e}")
            return []

    def generate_qc_file(self):
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output directory.")
            return

        # Prepare QC file content
        qc_content = ""

        # Required fields
        qc_content += f'$modelname "{self.modelname.get()}"\n'
        qc_content += f'$body "{self.body_name.get()}" "{self.body_smd.get()}"\n'
        qc_content += f'$surfaceprop "{self.surfaceprop.get()}"\n'
        qc_content += f'$cdmaterials "{self.cdmaterials.get()}"\n'
        qc_content += f'$sequence "{self.sequence.get()}"\n'

        # Optional fields
        if self.scale.get():
            qc_content += f'$scale {self.scale.get()}\n'

        # $texturegroup
        if self.texturegroup_name.get() and self.texturegroup_materials_vars:
            qc_content += f'$texturegroup "{self.texturegroup_name.get()}"\n'
            qc_content += "{\n"
            for var in self.texturegroup_materials_vars:
                material = var.get()
                if material:
                    qc_content += f'    {{ "{material}" }}\n'
            qc_content += "}\n"

        if self.lod.get():
            qc_content += f'$lod {self.lod.get()}\n'
        if self.staticprop.get():
            qc_content += '$staticprop\n'
        if self.casttextureshadows.get():
            qc_content += '$casttextureshadows\n'
        if self.collisionmodel.get():
            qc_content += f'$collisionmodel "{self.collisionmodel.get()}"\n'

        # Write to file
        output_path = os.path.join(self.output_dir.get(), "model.qc")
        try:
            with open(output_path, 'w') as qc_file:
                qc_file.write(qc_content)
            messagebox.showinfo("Success", f"QC file generated at:\n{output_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write QC file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = QCFileGenerator(root)
    root.mainloop()
