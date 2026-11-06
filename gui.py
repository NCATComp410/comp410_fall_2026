"""
COMP410 Sprint 3 - PII Anonymizer GUI
A Tkinter front end for app.py that shows each stage of the pipeline:
model loading, entity detection (highlighted in the input), the redacted
output, and redaction metrics.

Run with:  python gui.py
"""

import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app import SUPPORTED_ENTITIES

SAMPLE_TEXT = (
    "Hi, I'm John. Email me at john.doe@example.com or call 919-555-1234.\n"
    "My SSN is 219-09-9999 and my card number is 4111 1111 1111 1111.\n"
    "The server lives at 192.168.1.10."
)

# One highlight color per supported entity
ENTITY_COLORS = {
    "PHONE_NUMBER": "#ffd8a8",
    "EMAIL_ADDRESS": "#a5d8ff",
    "CREDIT_CARD": "#ffc9c9",
    "US_SSN": "#d0bfff",
    "IP_ADDRESS": "#b2f2bb",
}


class AnonymizerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PII Anonymizer")
        self.root.geometry("1100x760")
        self.root.minsize(800, 600)

        self.pii_scan = None          # loaded lazily in a background thread
        self.events = queue.Queue()   # worker thread -> UI thread messages
        self.entity_vars = {}

        self._build_layout()
        self._poll_events()
        self._load_engine()

    # ------------------------------------------------------------------ layout
    def _build_layout(self):
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        # --- top controls -------------------------------------------------
        controls = ttk.Frame(outer)
        controls.pack(fill="x")

        ent_box = ttk.LabelFrame(controls, text="Entities to redact", padding=6)
        ent_box.pack(side="left", fill="x", expand=True)
        for ent in sorted(SUPPORTED_ENTITIES):
            var = tk.BooleanVar(value=True)
            self.entity_vars[ent] = var
            cb = tk.Checkbutton(ent_box, text=ent, variable=var,
                                bg=ENTITY_COLORS.get(ent), anchor="w",
                                activebackground=ENTITY_COLORS.get(ent))
            cb.pack(side="left", padx=3)

        buttons = ttk.Frame(controls)
        buttons.pack(side="right", padx=(10, 0))
        ttk.Button(buttons, text="Load sample", command=self._load_sample).pack(side="left", padx=2)
        ttk.Button(buttons, text="Open file…", command=self._open_file).pack(side="left", padx=2)
        ttk.Button(buttons, text="Clear", command=self._clear).pack(side="left", padx=2)
        self.run_btn = ttk.Button(buttons, text="Anonymize ▶", command=self._run, state="disabled")
        self.run_btn.pack(side="left", padx=2)

        # --- main panes ---------------------------------------------------
        panes = ttk.PanedWindow(outer, orient="vertical")
        panes.pack(fill="both", expand=True, pady=(10, 0))

        text_row = ttk.PanedWindow(panes, orient="horizontal")
        panes.add(text_row, weight=3)

        in_frame = ttk.LabelFrame(text_row, text="1. Input (detections highlighted)", padding=4)
        self.input_text = self._make_text(in_frame)
        text_row.add(in_frame, weight=1)

        out_frame = ttk.LabelFrame(text_row, text="3. Redacted output", padding=4)
        self.output_text = self._make_text(out_frame)
        self.output_text.configure(state="disabled", background="#f8f9fa")
        text_row.add(out_frame, weight=1)

        for ent, color in ENTITY_COLORS.items():
            self.input_text.tag_configure(ent, background=color)

        bottom_row = ttk.PanedWindow(panes, orient="horizontal")
        panes.add(bottom_row, weight=2)

        det_frame = ttk.LabelFrame(bottom_row, text="2. Detections", padding=4)
        cols = ("entity", "text", "span", "score", "recognizer")
        self.tree = ttk.Treeview(det_frame, columns=cols, show="headings", height=6)
        widths = {"entity": 120, "text": 200, "span": 80, "score": 60, "recognizer": 180}
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=widths[c], anchor="w")
        for ent, color in ENTITY_COLORS.items():
            self.tree.tag_configure(ent, background=color)
        tree_scroll = ttk.Scrollbar(det_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        bottom_row.add(det_frame, weight=3)

        side = ttk.Frame(bottom_row)
        bottom_row.add(side, weight=2)

        met_frame = ttk.LabelFrame(side, text="4. Metrics", padding=6)
        met_frame.pack(fill="x")
        self.metric_vars = {}
        for i, label in enumerate(["Entities found", "Input length", "Output length", "Time"]):
            ttk.Label(met_frame, text=label + ":").grid(row=i, column=0, sticky="w")
            var = tk.StringVar(value="–")
            self.metric_vars[label] = var
            ttk.Label(met_frame, textvariable=var, font=("Segoe UI", 9, "bold")).grid(
                row=i, column=1, sticky="w", padx=(8, 0))

        log_frame = ttk.LabelFrame(side, text="Activity log", padding=4)
        log_frame.pack(fill="both", expand=True, pady=(6, 0))
        self.log_text = tk.Text(log_frame, height=6, wrap="word", font=("Consolas", 9),
                                background="#212529", foreground="#e9ecef", state="disabled")
        self.log_text.pack(fill="both", expand=True)

        # --- status bar ---------------------------------------------------
        self.status = tk.StringVar(value="Starting…")
        status_bar = ttk.Frame(outer)
        status_bar.pack(fill="x", pady=(6, 0))
        self.progress = ttk.Progressbar(status_bar, mode="indeterminate", length=140)
        self.progress.pack(side="right")
        ttk.Label(status_bar, textvariable=self.status).pack(side="left")

    @staticmethod
    def _make_text(parent) -> tk.Text:
        txt = tk.Text(parent, wrap="word", font=("Consolas", 11), undo=True)
        scroll = ttk.Scrollbar(parent, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=scroll.set)
        txt.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return txt

    # ------------------------------------------------------------- helpers
    def log(self, msg: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _busy(self, on: bool, status: str):
        self.status.set(status)
        if on:
            self.progress.start(12)
            self.run_btn.configure(state="disabled")
        else:
            self.progress.stop()
            self.run_btn.configure(state="normal" if self.pii_scan else "disabled")

    def _set_output(self, text: str):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")

    def _clear_results(self):
        for ent in ENTITY_COLORS:
            self.input_text.tag_remove(ent, "1.0", "end")
        self.tree.delete(*self.tree.get_children())
        self._set_output("")
        for var in self.metric_vars.values():
            var.set("–")

    # ------------------------------------------------------------- actions
    def _load_sample(self):
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", SAMPLE_TEXT)
        self._clear_results()

    def _open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:  # pylint: disable=broad-except
            messagebox.showerror("Could not open file", str(e))
            return
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", content)
        self._clear_results()
        self.log(f"Loaded file {path} ({len(content)} chars)")

    def _clear(self):
        self.input_text.delete("1.0", "end")
        self._clear_results()

    def _load_engine(self):
        self._busy(True, "Loading spaCy model and Presidio engines (first run may take a while)…")
        self.log("Loading pii_scan (spaCy en_core_web_lg + Presidio)…")

        def work():
            start = time.perf_counter()
            try:
                import pii_scan  # pylint: disable=import-outside-toplevel
                self.events.put(("engine_ready", pii_scan, time.perf_counter() - start))
            except Exception as e:  # pylint: disable=broad-except
                self.events.put(("error", f"Failed to load engine: {e}"))

        threading.Thread(target=work, daemon=True).start()

    def _run(self):
        text = self.input_text.get("1.0", "end-1c")
        entities = [e for e, v in self.entity_vars.items() if v.get()]
        if not text.strip():
            messagebox.showinfo("No input", "Type or load some text first.")
            return
        if not entities:
            messagebox.showinfo("No entities", "Select at least one entity type.")
            return

        self._clear_results()
        self._busy(True, "Analyzing…")
        self.log(f"Analyzing {len(text)} chars for: {', '.join(sorted(entities))}")

        def work():
            start = time.perf_counter()
            try:
                results = self.pii_scan.analyze_text(text=text, entity_list=entities)
                self.events.put(("detected", results))
                redacted = self.pii_scan.anonymizer.anonymize(
                    text=text, analyzer_results=results).text
                self.events.put(("done", text, redacted, results, time.perf_counter() - start))
            except Exception as e:  # pylint: disable=broad-except
                self.events.put(("error", f"Anonymization failed: {e}"))

        threading.Thread(target=work, daemon=True).start()

    # -------------------------------------------------- worker -> UI events
    def _poll_events(self):
        try:
            while True:
                self._handle(self.events.get_nowait())
        except queue.Empty:
            pass
        self.root.after(50, self._poll_events)

    def _handle(self, event):
        kind = event[0]
        if kind == "engine_ready":
            _, self.pii_scan, secs = event
            self.log(f"Engine ready in {secs:.1f}s")
            self._busy(False, "Ready. Enter text and press Anonymize.")
        elif kind == "detected":
            results = sorted(event[1], key=lambda r: r.start)
            text = self.input_text.get("1.0", "end-1c")
            for r in results:
                self.input_text.tag_add(r.entity_type, f"1.0+{r.start}c", f"1.0+{r.end}c")
                recognizer = (r.recognition_metadata or {}).get("recognizer_name", "")
                self.tree.insert("", "end", tags=(r.entity_type,), values=(
                    r.entity_type, text[r.start:r.end], f"{r.start}–{r.end}",
                    f"{r.score:.2f}", recognizer))
            self.log(f"Detected {len(results)} entit{'y' if len(results) == 1 else 'ies'}")
            self.status.set("Anonymizing…")
        elif kind == "done":
            _, original, redacted, results, secs = event
            self._set_output(redacted)
            self.metric_vars["Entities found"].set(str(len(results)))
            self.metric_vars["Input length"].set(f"{len(original)} chars")
            self.metric_vars["Output length"].set(f"{len(redacted)} chars")
            self.metric_vars["Time"].set(f"{secs * 1000:.0f} ms")
            self.log(f"Redaction complete in {secs * 1000:.0f} ms")
            self._busy(False, "Done.")
        elif kind == "error":
            self.log(event[1])
            self._busy(False, event[1])
            messagebox.showerror("Error", event[1])


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("vista")
    except tk.TclError:
        pass
    app = AnonymizerGUI(root)
    app._load_sample()  # pylint: disable=protected-access
    root.mainloop()


if __name__ == "__main__":
    main()
