#!/usr/bin/env python3
import time
from gpiozero import DigitalInputDevice, DigitalOutputDevice

class HX711:
    def __init__(self, dout_pin, sck_pin, reference_unit=1, readings=1):
        """
        readings=1 -> Keine Mittelung, so hast du jeden einzelnen Messwert direkt.
        """
        # Auf dem Pi 5: kein interner Pull-up
        self.dout = DigitalInputDevice(dout_pin, pull_up=False)
        self.sck = DigitalOutputDevice(sck_pin, initial_value=False)
        self.reference_unit = reference_unit
        self.offset = 0
        self.readings = readings
        self.reset()
        
    def reset(self):
        """Setzt den HX711 zurück"""
        self.sck.on()
        time.sleep(0.0006)
        self.sck.off()
        time.sleep(0.0006)
        
    def read(self):
        """
        Liest einen Rohwert vom HX711, nachdem er Daten bereitstellt.
        Warte bis zu 0.5s, damit der HX711 sicher Zeit hatte, um die Daten zu aktualisieren.
        """
        # Warte, bis DOUT auf LOW geht (Data ready), max. 0.5s
        if not self.dout.wait_for_inactive(timeout=0.5):
            # Timeout -> keine neuen Daten
            return 0
        
        count = 0
        # 24 Bit einlesen
        for _ in range(24):
            self.sck.on()
            count <<= 1
            self.sck.off()
            if self.dout.value:
                count += 1
        
        # 25. Puls (Gain und Kanal bleiben hier auf Standard)
        self.sck.on()
        time.sleep(0.0001)
        self.sck.off()
        
        # 2er-Komplement
        if count & 0x800000:
            count -= 0x1000000
        return count
        
    def read_average(self, readings=None):
        """Mittelwert über 'readings'-Messungen."""
        if readings is None:
            readings = self.readings
        total = 0
        for _ in range(readings):
            total += self.read()
        return total / readings
        
    def get_value(self, readings=None):
        """Offset-korrigierter Wert."""
        return self.read_average(readings) - self.offset
        
    def get_weight(self, readings=None):
        """Berechnet das Gewicht in der kalibrierten Einheit."""
        value = self.get_value(readings)
        return value / self.reference_unit
        
    def tare(self, readings=None):
        """Tarierung (Nullsetzen) der Waage."""
        if readings is None:
            readings = self.readings
        self.offset = self.read_average(readings)
        
    def set_reference_unit(self, reference_unit):
        self.reference_unit = reference_unit


def main():
    try:
        dout_pin = 5
        sck_pin = 6
        hx = HX711(dout_pin, sck_pin, reference_unit=420.0, readings=1)
        
        print("Stelle sicher, dass keine Last aufliegt.")
        input("Drücke Enter, um zu tarieren...")
        hx.tare()
        print("Tarierung abgeschlossen.")
        
        print("Starte Messung bei ~3 Hz (alle 0,33s). Strg+C zum Beenden...")
        while True:
            # Lies 1 Messung vom HX711
            weight = hx.get_weight()
            print(f"Gewicht: {weight:.2f}")
            # Warte 0,33s => ~3 Hz
            time.sleep(0.33)
    except KeyboardInterrupt:
        print("\nMessung beendet.")

if __name__ == "__main__":
    main()