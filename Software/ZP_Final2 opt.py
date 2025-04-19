import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import sys
import threading
import time
import os
from HX711 import HX711
from gpiozero import PWMOutputDevice, DigitalOutputDevice


class ZugpruefmaschineGUI:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.title("Zugprüfmaschine Touch-Steuerung")

        # ------------------------------------------
        # 1) Initialisierung HX711
        # ------------------------------------------
        self.hx = HX711(dout_pin=5, sck_pin=6, reference_unit=420.0, readings=1)
        self.hx.tare()

        # Kraftanzeige-Variablen
        self.current_force = 0.0
        self.force_value_var = tk.StringVar(value="Kraft: 0.00 N")
        self.max_force_value = 0.0
        self.max_force_var = tk.StringVar(value="Max: 0.00 N")

        # Für den Filter:
        self.last_valid_force = None
        self.candidate_count = 0
        self.candidate_sum = 0.0

        # ------------------------------------------
        # 2) Initialisierung Schrittmotor
        # ------------------------------------------
        self.step_pin = 18
        self.dir_pin = 19
        self.enable_pin = 26
        self.step = DigitalOutputDevice(self.step_pin, active_high=True, initial_value=False)
        self.dir = DigitalOutputDevice(self.dir_pin, active_high=True, initial_value=False)
        self.enable = DigitalOutputDevice(self.enable_pin, active_high=True, initial_value=False)

        self.steps_per_rev = 1600
        self.rotation_distance = 3.125  # mm pro Umdrehung
        self.position = 0.0             # Aktuelle Position in mm

        # ------------------------------------------
        # 3) Variablen für Kraftabfall, Zuglänge, Vorschub, Logfile
        # ------------------------------------------
        self.kraft_abfall_grenze = 0
        self.zuglaenge = 5
        self.feed_rate = 5

        # Logbase-Name (wird über das GUI-Entry gesetzt)
        self.log_base_var = tk.StringVar(value="zugversuch_log")

        # Prozess-Flags
        self.is_testing = False
        self.process_stop_event = threading.Event()
        self.process_thread = None

        # GUI aufbauen
        self.build_layout()

        # ------------------------------------------
        # 4) Sensor-Thread: Liest den HX711 alle 0.1 s (10 Hz)
        # ------------------------------------------
        self.stop_event = threading.Event()
        self.sensor_thread = threading.Thread(target=self.update_force_loop, daemon=True)
        self.sensor_thread.start()

    # Neue Methode: Ausfallsicheres Auslesen mittels Timeout, das auf das Signal des HX711 wartet
    def read_value_with_timeout(self, timeout_ms=15):
        start_time = time.perf_counter()  # Startzeit in Sekunden
        timeout_sec = timeout_ms / 1000.0  # Timeout in Sekunden
        # Warte darauf, dass der DOUT-Pin signalisiert, dass ein neuer Wert vorliegt (also LOW)
        while self.hx.dout.value:
            if (time.perf_counter() - start_time) > timeout_sec:
                return None
        return self.hx.get_value()

    # Filterfunktion: Verarbeitet einen neuen Kraftwert anhand des zuletzt akzeptierten Wertes.
    # Bei einem plötzlichen Sprung über den Schwellenwert (15 N) wird der neue Wert als Kandidat registriert.
    # Liegen zwei aufeinanderfolgende Kandidaten innerhalb einer Toleranz von 2 N, wird der Übergang akzeptiert.
    def filter_force(self, new_val, threshold=15.0, tolerance=2.0):
        if self.last_valid_force is None:
            self.last_valid_force = new_val
            self.candidate_count = 0
            self.candidate_sum = 0.0
            return new_val
        # Wenn die Differenz zum letzten gültigen Wert innerhalb des Schwellenwerts liegt, sofort übernehmen.
        if abs(new_val - self.last_valid_force) <= threshold:
            self.candidate_count = 0
            self.candidate_sum = 0.0
            self.last_valid_force = new_val
            return new_val
        else:
            # Neuer Messwert unterscheidet sich deutlich vom letzten gültigen.
            if self.candidate_count == 0:
                # Ersten Kandidaten speichern und alten Wert anzeigen.
                self.candidate_count = 1
                self.candidate_sum = new_val
                return self.last_valid_force
            elif self.candidate_count == 1:
                # Zweiter Kandidat: Prüfen, ob beide Kandidaten innerhalb der Toleranz liegen.
                if abs(new_val - self.candidate_sum) <= tolerance:
                    # Übergang akzeptieren: Mittelwert der Kandidaten berechnen.
                    filtered = (self.candidate_sum + new_val) / 2.0
                    self.last_valid_force = filtered
                    self.candidate_count = 0
                    self.candidate_sum = 0.0
                    return filtered
                else:
                    # Kandidaten nicht konsistent: Ausreißer verwerfen, alten Wert beibehalten.
                    self.candidate_count = 0
                    self.candidate_sum = 0.0
                    return self.last_valid_force

    # ------------------------------------------
    # GUI Layout
    # ------------------------------------------
    def build_layout(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill='both', expand=True)

        # Oberer Bereich: Position, Kraft, Max-Kraft
        display_frame = ttk.Frame(frame)
        display_frame.pack(fill='x', pady=10)

        self.pos_display = ttk.Label(display_frame, text="Position: 0.00 mm", font=("Helvetica", 24))
        self.pos_display.pack(side='left', padx=40)

        self.force_value = ttk.Label(display_frame, textvariable=self.force_value_var, font=("Helvetica", 24))
        self.force_value.pack(side='left', padx=40)

        self.max_force_label = ttk.Label(display_frame, textvariable=self.max_force_var, font=("Helvetica", 24))
        self.max_force_label.pack(side='left', padx=40)

        # Mittlerer Bereich: Position steuern und Zuglänge einstellen
        control_row = ttk.Frame(frame)
        control_row.pack(fill='x', pady=10)

        # Position steuern Frame
        pos_frame = ttk.LabelFrame(control_row, text="Position steuern", padding=20)
        pos_frame.pack(side='left', fill='both', expand=True, padx=10)

        pos_btn_frame = ttk.Frame(pos_frame)
        pos_btn_frame.pack()

        for step in [-10, -1, -0.5, 0.5, 1, 10]:
            style = PRIMARY
            label = f"{step:+}".replace(".0", "") + " mm"
            ttk.Button(pos_btn_frame, text=label, bootstyle=style, width=10,
                       command=lambda s=step: self.move_by(s)).pack(side='left', padx=5)

        # Zuglänge einstellen Frame
        zug_frame = ttk.LabelFrame(control_row, text="Zuglänge", padding=20)
        zug_frame.pack(side='left', fill='both', expand=True, padx=10)

        self.zuglaenge_label = ttk.Label(zug_frame, text=f"{self.zuglaenge} mm", font=("Helvetica", 24))
        self.zuglaenge_label.pack(pady=10)

        zug_btn_frame = ttk.Frame(zug_frame)
        zug_btn_frame.pack()

        ttk.Button(zug_btn_frame, text="-1 mm", bootstyle=PRIMARY, width=7,
                   command=lambda: self.adjust_zuglaenge(-1)).pack(side='left', padx=5)
        ttk.Button(zug_btn_frame, text="+1 mm", bootstyle=PRIMARY, width=7,
                   command=lambda: self.adjust_zuglaenge(1)).pack(side='left', padx=5)

        # Vorschub- und Kraftabfall-Bereiche
        feed_kraft_frame = ttk.Frame(frame)
        feed_kraft_frame.pack(fill='x', pady=10)

        # Vorschubsteuerung
        feed_frame = ttk.LabelFrame(feed_kraft_frame, text="Vorschub verstellen", padding=20)
        feed_frame.pack(side='left', fill='x', expand=True, padx=10)

        self.feed_display = ttk.Label(feed_frame, text=f"Vorschub: {self.feed_rate} mm/min", font=("Helvetica", 24))
        self.feed_display.pack(pady=10)

        feed_btn_frame = ttk.Frame(feed_frame)
        feed_btn_frame.pack()

        for step in [-10, -1, 1, 10]:
            style = PRIMARY
            label = f"{step:+}".replace(".0", "") + " mm/min"
            ttk.Button(feed_btn_frame, text=label, bootstyle=style, width=12,
                       command=lambda s=step: self.adjust_feed(s)).pack(side='left', padx=5)

        # Kraftabfall-Grenze
        kraft_frame = ttk.LabelFrame(feed_kraft_frame, text="Kraftabfall-Grenze", padding=20)
        kraft_frame.pack(side='left', fill='x', expand=True, padx=10)

        self.kraft_display = ttk.Label(kraft_frame, text=f"Grenze: {self.kraft_abfall_grenze} N", font=("Helvetica", 24))
        self.kraft_display.pack(pady=10)

        kraft_btn_frame = ttk.Frame(kraft_frame)
        kraft_btn_frame.pack()

        for delta in [-5, 5]:
            label = f"{delta:+} N"
            ttk.Button(kraft_btn_frame, text=label, bootstyle=PRIMARY, width=10,
                       command=lambda d=delta: self.adjust_kraft_grenze(d)).pack(side='left', padx=10)

        # Unterer Bereich: Tarieren und Log-Base Eingabe
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', pady=15)

        ttk.Button(control_frame, text="Tarieren", bootstyle=WARNING, width=10,
                   command=self.tare).pack(side='left', padx=10)

        log_base_frame = ttk.Frame(control_frame)
        log_base_frame.pack(side='right', padx=10)
        ttk.Label(log_base_frame, text="Log-Base:", font=("Helvetica", 14)).pack(side='left', padx=5)
        self.log_base_entry = ttk.Entry(log_base_frame, textvariable=self.log_base_var, width=20)
        self.log_base_entry.pack(side='left', padx=5)

        # Prozessbereich
        process_frame = ttk.Frame(frame)
        process_frame.pack(fill='x', pady=20)

        self.start_button = ttk.Button(process_frame, text="Prozess starten", bootstyle=SUCCESS, width=20,
                                        command=self.toggle_process)
        self.start_button.pack(side='left', padx=10)

        ttk.Button(process_frame, text="Pos. Nullsetzen", bootstyle=PRIMARY, width=16,
                   command=self.reset_position).pack(side='left', padx=10)

        ttk.Button(process_frame, text="Zurück zu 0 Position", bootstyle=WARNING, width=18,
                   command=self.return_to_zero).pack(side='left', padx=10)

        self.logfile_label = ttk.Label(process_frame, text="", font=("Helvetica", 14))
        self.logfile_label.pack(side='left', padx=20)

        ttk.Button(process_frame, text="Beenden", bootstyle=DANGER, width=12,
                   command=self.exit_app).pack(side='right', padx=20)

    # ------------------------------------------
    # Sensor-Thread: Liest den HX711 alle 0.1 s (10 Hz) und wendet den Filter an
    # ------------------------------------------
    def update_force_loop(self):
        sample_interval = 0.0125  # in Sekunden (10 Hz)
        while not self.stop_event.is_set():
            loop_start = time.perf_counter()
            raw_value = self.read_value_with_timeout(timeout_ms=15)
            if raw_value is not None:
                force = raw_value * -0.0003024406
                # Filterung: neuer Wert wird durch den Filter verarbeitet.
                filtered_force = self.filter_force(force)
                self.current_force = filtered_force
                self.force_value_var.set(f"Kraft: {filtered_force:.2f} N")
                if filtered_force > self.max_force_value:
                    self.max_force_value = filtered_force
                    self.max_force_var.set(f"Max: {self.max_force_value:.2f} N")
            elapsed = time.perf_counter() - loop_start
            if elapsed < sample_interval:
                time.sleep(sample_interval - elapsed)

    # ------------------------------------------
    # Motorsteuerung, Position usw.
    # ------------------------------------------
    def move_by(self, mm):
        mm_per_step = self.rotation_distance / self.steps_per_rev
        steps = int(mm / mm_per_step)
        if steps >= 0:
            self.dir.on()
            x = 1
        else:
            self.dir.off()
            x = -1

        mm_to_move = abs(mm)
        mm_moved = 0
        
        while mm_moved < mm_to_move:
            frequency = 853
            self.step.value = 1
            step_time = 1 / frequency
            time.sleep(step_time)
            self.step.value = 0
            self.position += mm_per_step * x
            self.pos_display.configure(text=f"Position: {self.position:.2f} mm")
            self.pos_display.update_idletasks()
            
            mm_moved += mm_per_step


    def exit_app(self):
        self.stop_event.set()
        self.root.destroy()
        sys.exit()

    def adjust_feed(self, delta):
        self.feed_rate = max(1, self.feed_rate + delta)
        self.feed_display.configure(text=f"Vorschub: {self.feed_rate} mm/min")

    def adjust_kraft_grenze(self, delta):
        self.kraft_abfall_grenze = max(0, self.kraft_abfall_grenze + delta)
        self.kraft_display.configure(text=f"Grenze: {self.kraft_abfall_grenze} N")

    def adjust_zuglaenge(self, delta):
        self.zuglaenge = max(1, self.zuglaenge + delta)
        self.zuglaenge_label.configure(text=f"{self.zuglaenge} mm")

    def tare(self):
        self.hx.tare()

    def reset_position(self):
        self.position = 0.0
        self.pos_display.configure(text=f"Position: {self.position:.2f} mm")

    def return_to_zero(self):
        self.move_by(-self.position)

    # ------------------------------------------
    # Erzeugt einen unique Log-Filename
    # ------------------------------------------
    def get_log_filename(self):
        log_dir = "./logs"
        os.makedirs(log_dir, exist_ok=True)
        base_name = self.log_base_var.get().strip() or "zugversuch_log"
        index = 1
        filename = f"{log_dir}/{base_name}_{index}.csv"
        while os.path.exists(filename):
            index += 1
            filename = f"{log_dir}/{base_name}_{index}.csv"
        return filename

    # ------------------------------------------
    # Prozess-Thread: Führt den Zugversuch aus und loggt Messwerte
    # ------------------------------------------
    def toggle_process(self):
        if self.is_testing:
            return
        self.max_force_value = 0.0
        self.max_force_var.set("Max: 0.00 N")
        self.position = 0.0
        self.pos_display.configure(text="Position: 0.00 mm")
        self.is_testing = True
        self.process_stop_event.clear()
        self.process_thread = threading.Thread(target=self.run_test_process, daemon=True)
        self.process_thread.start()

    def run_test_process(self):
        feed = self.feed_rate  # mm/min
        mm_per_step = self.rotation_distance / self.steps_per_rev
        steps_per_sec = feed / 60 / mm_per_step
        self.logfile_name = self.get_log_filename()
        self.logfile_label.configure(text=os.path.basename(self.logfile_name))
        stop_event = self.process_stop_event
        try:
            with open(self.logfile_name, "w") as logfile:
                logfile.write("Position;Force\n")
                def log_task():
                    previous_force = None
                    while not stop_event.is_set():
                        force = self.current_force
                        logfile.write(f"{self.position:.2f};{force:.2f}\n")
                        logfile.flush()
                        if previous_force is not None and self.kraft_abfall_grenze > 0:
                            if (previous_force - force) >= self.kraft_abfall_grenze:
                                stop_event.set()
                                break
                        previous_force = force
                        time.sleep(0.15)
                log_thread = threading.Thread(target=log_task, daemon=True)
                log_thread.start()
                mm_to_move = self.zuglaenge
                mm_moved = 0
                while mm_moved < mm_to_move and not stop_event.is_set():
                    self.dir.on()
                    #frequency = steps_per_sec
                    self.step.value = 1
                    step_time = 1 / steps_per_sec
                    time.sleep(step_time)
                    self.step.value = 0
                    self.position += mm_per_step
                    self.pos_display.configure(text=f"Position: {self.position:.2f} mm")
                    mm_moved += mm_per_step
                stop_event.set()
                log_thread.join()
        finally:
            self.is_testing = False


if __name__ == '__main__':
    root = ttk.Window(themename="darkly")
    app = ZugpruefmaschineGUI(root)
    root.mainloop()
