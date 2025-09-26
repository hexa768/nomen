
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NPC & Place-name Generator - GUI (Tkinter)
- Select data directory and types
- Configure counts and seed
- Generate village + residents
- Export as JSON/CSV or copy to clipboard
"""
import json
import os
import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# -----------------------------
# Core (embedded from CLI version, lightly adapted)
# -----------------------------
class PlaceData:
    def __init__(self, place_roots):
        self.place_roots = place_roots

    @staticmethod
    def from_json(obj, kind):
        roots = obj.get(kind, {}).get("place_roots")
        if not isinstance(roots, list) or not roots:
            raise ValueError(f"place_roots for type '{kind}' must be a non-empty list")
        return PlaceData(place_roots=roots)


class NameData:
    def __init__(self, male, female):
        self.male = male
        self.female = female

    @staticmethod
    def from_json(obj, kind):
        node = obj.get(kind, {})
        male = node.get("male")
        female = node.get("female")
        if not isinstance(male, list) or not isinstance(female, list):
            raise ValueError(f"male/female for type '{kind}' must be lists")
        if not male or not female:
            raise ValueError(f"male/female lists for type '{kind}' must be non-empty")
        return NameData(male, female)


class NPCPlaceGenerator:
    def __init__(self, data_dir, place_type="default", name_type="default",
                 num_male=5, num_female=5, min_roots=2, max_roots=3, seed=None):
        self.data_dir = data_dir
        self.place_type = place_type
        self.name_type = name_type
        self.num_male = num_male
        self.num_female = num_female
        self.min_roots = min_roots
        self.max_roots = max_roots
        self.seed = seed

        if seed is not None:
            random.seed(seed)

        self.place_data = self._load_place_data()
        self.name_data = self._load_name_data()

    def _load_json(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_place_data(self):
        path = os.path.join(self.data_dir, f"plname_{self.place_type}.json")
        return PlaceData.from_json(self._load_json(path), self.place_type)

    def _load_name_data(self):
        path = os.path.join(self.data_dir, f"name_{self.name_type}.json")
        return NameData.from_json(self._load_json(path), self.name_type)

    @staticmethod
    def _tidy_place_name(raw):
        if not raw:
            return raw
        out = raw
        # Collapse triples
        for ch in "abcdefghijklmnopqrstuvwxyz":
            out = out.replace(ch*3, ch*2)
        # Smooth selected doubles
        for seq in ["tt", "ll", "ss", "ff", "rr", "mm", "nn"]:
            out = out.replace(seq, seq[0])
        return out[0].upper() + out[1:]

    def generate_place_name(self):
        k = random.randint(self.min_roots, self.max_roots)
        roots = random.sample(self.place_data.place_roots, k)
        return self._tidy_place_name("".join(roots))

    @staticmethod
    def _pick_unique(src, n):
        if n <= len(src):
            import random as _r
            return _r.sample(src, n)
        # sample with replacement but cycle to increase variety
        res, pool = [], list(src)
        import random as _r
        while len(res) < n and src:
            if not pool:
                pool = list(src)
            choice = _r.choice(pool)
            pool.remove(choice)
            res.append(choice)
        return res

    def generate(self):
        village = self.generate_place_name()
        males = self._pick_unique(self.name_data.male, self.num_male)
        females = self._pick_unique(self.name_data.female, self.num_female)
        out = {
            "village": village,
            "residents": {
                "male": [f"{m} of {village}" for m in males],
                "female": [f"{f} of {village}" for f in females],
            }
        }
        return out

# -----------------------------
# GUI
# -----------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NPC & Place-name Generator")
        self.geometry("760x620")
        self.minsize(720, 580)

        self.var_data_dir = tk.StringVar(value=os.getcwd())
        self.var_place_type = tk.StringVar(value="default")
        self.var_name_type = tk.StringVar(value="default")
        self.var_num_male = tk.IntVar(value=5)
        self.var_num_female = tk.IntVar(value=5)
        self.var_min_roots = tk.IntVar(value=2)
        self.var_max_roots = tk.IntVar(value=3)
        self.var_seed = tk.StringVar(value="")

        self._build_ui()

        self.generated = None

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        # Data dir row
        frame_top = ttk.LabelFrame(self, text="Data")
        frame_top.pack(fill="x", **pad)
        ttk.Label(frame_top, text="Data directory").grid(row=0, column=0, sticky="w", **pad)
        ent = ttk.Entry(frame_top, textvariable=self.var_data_dir, width=60)
        ent.grid(row=0, column=1, sticky="we", **pad)
        ttk.Button(frame_top, text="Browse...", command=self._choose_dir).grid(row=0, column=2, **pad)
        frame_top.columnconfigure(1, weight=1)

        # Types and counts
        frame_cfg = ttk.LabelFrame(self, text="Configuration")
        frame_cfg.pack(fill="x", **pad)

        ttk.Label(frame_cfg, text="Place type").grid(row=0, column=0, sticky="w", **pad)
        ttk.Combobox(frame_cfg, textvariable=self.var_place_type, values=["default","normal","basic","korean","chinese","nordic","slavic"], width=12, state="readonly").grid(row=0, column=1, **pad)

        ttk.Label(frame_cfg, text="Name type").grid(row=0, column=2, sticky="w", **pad)
        ttk.Combobox(frame_cfg, textvariable=self.var_name_type, values=["default","normal","basic","korean","chinese","nordic","slavic"], width=12, state="readonly").grid(row=0, column=3, **pad)

        ttk.Label(frame_cfg, text="Male #").grid(row=1, column=0, sticky="w", **pad)
        ttk.Spinbox(frame_cfg, from_=0, to=200, textvariable=self.var_num_male, width=8).grid(row=1, column=1, **pad)

        ttk.Label(frame_cfg, text="Female #").grid(row=1, column=2, sticky="w", **pad)
        ttk.Spinbox(frame_cfg, from_=0, to=200, textvariable=self.var_num_female, width=8).grid(row=1, column=3, **pad)

        ttk.Label(frame_cfg, text="Roots (min/max)").grid(row=2, column=0, sticky="w", **pad)
        ttk.Spinbox(frame_cfg, from_=1, to=5, textvariable=self.var_min_roots, width=8).grid(row=2, column=1, **pad)
        ttk.Spinbox(frame_cfg, from_=1, to=5, textvariable=self.var_max_roots, width=8).grid(row=2, column=2, **pad)

        ttk.Label(frame_cfg, text="Seed (optional)").grid(row=2, column=3, sticky="w", **pad)
        ttk.Entry(frame_cfg, textvariable=self.var_seed, width=12).grid(row=2, column=4, **pad)

        ttk.Button(frame_cfg, text="Generate", command=self._on_generate).grid(row=0, column=5, rowspan=3, sticky="ns", **pad)

        for c in range(5):
            frame_cfg.columnconfigure(c, weight=1)

        # Output
        frame_out = ttk.LabelFrame(self, text="Output")
        frame_out.pack(fill="both", expand=True, **pad)

        self.txt = tk.Text(frame_out, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=8, pady=8)

        # Actions
        frame_actions = ttk.Frame(self)
        frame_actions.pack(fill="x", **pad)

        ttk.Button(frame_actions, text="Copy Text", command=self._copy_text).pack(side="left", padx=4)
        ttk.Button(frame_actions, text="Export JSON", command=lambda: self._export("json")).pack(side="left", padx=4)
        ttk.Button(frame_actions, text="Export CSV", command=lambda: self._export("csv")).pack(side="left", padx=4)

    def _choose_dir(self):
        path = filedialog.askdirectory(initialdir=self.var_data_dir.get() or os.getcwd())
        if path:
            self.var_data_dir.set(path)

    def _on_generate(self):
        try:
            seed_val = self.var_seed.get().strip()
            seed = int(seed_val) if seed_val else None
            gen = NPCPlaceGenerator(
                data_dir=self.var_data_dir.get(),
                place_type=self.var_place_type.get(),
                name_type=self.var_name_type.get(),
                num_male=int(self.var_num_male.get()),
                num_female=int(self.var_num_female.get()),
                min_roots=int(self.var_min_roots.get()),
                max_roots=int(self.var_max_roots.get()),
                seed=seed,
            )
            self.generated = gen.generate()
            self._render_output()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _render_output(self):
        if not self.generated:
            return
        bundle = self.generated
        village = bundle["village"]
        lines = [f"Village: {village}", "Residents:"]
        for m in bundle["residents"]["male"]:
            lines.append(f"  - {m}")
        for f in bundle["residents"]["female"]:
            lines.append(f"  - {f}")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(lines))

    def _copy_text(self):
        txt = self.txt.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(txt)
        messagebox.showinfo("Copied", "Output copied to clipboard!")

    def _export(self, fmt):
        if not self.generated:
            messagebox.showwarning("No data", "Please generate first.")
            return
        if fmt == "json":
            fp = filedialog.asksaveasfilename(defaultextension=".json",
                                              filetypes=[("JSON files", "*.json")])
            if not fp: 
                return
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(self.generated, f, ensure_ascii=False, indent=2)
        elif fmt == "csv":
            import csv
            fp = filedialog.asksaveasfilename(defaultextension=".csv",
                                              filetypes=[("CSV files", "*.csv")])
            if not fp:
                return
            with open(fp, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["gender", "name"])
                for m in self.generated["residents"]["male"]:
                    w.writerow(["male", m])
                for x in self.generated["residents"]["female"]:
                    w.writerow(["female", x])
        messagebox.showinfo("Saved", f"Exported as {fmt.upper()}")

if __name__ == "__main__":
    App().mainloop()
