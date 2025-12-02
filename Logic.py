from __future__ import annotations

from PyQt6.QtCore import QObject
from Earth_Project import Ui_mainWindow


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp value into [min_value, max_value]."""
    return max(min_value, min(value, max_value))


class EarthSimulation(QObject):
    """
    Holds the state of the system and runs one simulation step
    every time the user presses the Enter button.
    """

    def __init__(self, ui: Ui_mainWindow):
        super().__init__()
        self.ui = ui
        self.step_count = 0

        # --- read initial state from the GUI so you can tweak it there ---
        self.air_temp_c = self._parse_temp_label(self.ui.AirTemp_Number.text())
        self.water_temp_c = self._parse_temp_label(self.ui.WaterTemp_Number.text())
        self.surface_temp_c = self._parse_temp_label(self.ui.SurfaceTemp_Number.text())
        self.soil_moisture = self._parse_percentage_label(self.ui.SoilMoisture_Number.text())

        self.cloud_coverage = 0.0  # fraction 0–1, computed from evaporation

        # Biosphere populations are stored as 0–1 internally
        self.plant_pop = self.ui.plant_progressBar.value() / 100.0
        self.prey_pop = self.ui.Prey_progressBar.value() / 100.0
        self.predator_pop = self.ui.Predator_progressBar.value() / 100.0

        # connect button → one simulation step
        self.ui.User_input_Button.clicked.connect(self.step_simulation)

    # ---------- small parsing helpers ----------

    @staticmethod
    def _parse_temp_label(text: str) -> float:
        """
        'X' -> X.X
        """
        try:
            parts = text.split()
            return float(parts[0])
        except Exception:
            return 0.0

    @staticmethod
    def _parse_percentage_label(text: str) -> float:
        """
        'X%' -> 0.X (fraction 0–1)
        """
        try:
            t = text.strip().replace('%', '')
            return float(t) / 100.0
        except Exception:
            return 0.0

    # ---------- core physics / ecology helper functions ----------

    def update_temperatures(self, avg_temp_c: float) -> None:
        """
        Update air, water, and surface temperature using simple
        'move toward the average' formulas.
        """
        # Air and water: classic "moving toward the average" equation
        self.air_temp_c = self.air_temp_c + 0.8 * (avg_temp_c - self.air_temp_c)
        self.water_temp_c = self.water_temp_c + 0.2 * (avg_temp_c - self.water_temp_c)

        # Surface temp based on water & average
        self.surface_temp_c = self.water_temp_c + 0.5 * (avg_temp_c - self.water_temp_c)

    def calc_air_pressure(self) -> float:
        """
        Ideal gas law scaling with temperature (in Kelvin):
        P(Tk) = 1013 * (Tk / 298.15)
        """
        tk = self.air_temp_c + 273.15
        return 1013.0 * (tk / 298.15)

    def calc_evaporation_rate(self, pressure_hpa: float) -> float:
        """
        Evaporation rate (mm/day):
          Eb = 5 mm/day (baseline)
          Water temp effect = max(0, (Twater - 5) / 20)
          Pressure factor = 1 + 0.3 * ((1013 - P) / 1013)
        """
        Eb = 5.0
        temp_effect = (self.water_temp_c - 5.0) / 20.0
        temp_effect = max(0.0, temp_effect)

        pressure_factor = 1.0 + 0.3 * ((1013.0 - pressure_hpa) / 1013.0)
        pressure_factor = max(0.0, pressure_factor)

        evaporation = Eb * pressure_factor * temp_effect
        return max(0.0, evaporation)

    def calc_cloud_coverage(self, evaporation_mm: float, pressure_hpa: float) -> float:
        """
        Cloud coverage is first normalized from evaporation, then modified
        depending on pressure zone.
        """
        cc = evaporation_mm / 5.0  # 0 at 0 mm/day, 1 at 5 mm/day baseline

        # Apply pressure zone rule
        if pressure_hpa > 1020.0:  # High pressure → clouds disperse
            cc = cc * 0.8
        elif 1005.0 <= pressure_hpa <= 1020.0:  # Normal
            cc = cc + 0.02 * evaporation_mm
        else:  # Low pressure → clouds form
            cc = cc + 0.05 + 0.05 * evaporation_mm

        return clamp(cc, 0.0, 1.0)

    @staticmethod
    def cloud_to_oktas(cc: float) -> int:
        """
        Convert cloud coverage fraction (0–1) to oktas.
        """
        if 0.00 <= cc < 0.10:
            return 0
        elif 0.10 <= cc < 0.25:
            return 1
        elif 0.25 <= cc < 0.38:
            return 2
        elif 0.38 <= cc < 0.50:
            return 3
        elif 0.50 <= cc < 0.63:
            return 4
        elif 0.63 <= cc < 0.75:
            return 5
        elif 0.75 <= cc < 0.88:
            return 6
        elif 0.88 <= cc < 1.00:
            return 7
        else:
            return 8

    def calc_storm_chance(self, evaporation_mm: float, cloud_coverage: float,
                          pressure_hpa: float) -> tuple[float, float, str]:
        """
        Returns (storm_index 0–1, probability %, category string).
        (Pf) = clamp( (1013 - P) / 40 )
        (Ef) = clamp( E / 5 )
        (Cf) = cloud coverage (0–1)
        Storm = Cf * (0.5 + 0.5Pf) * (0.3 + 0.7Ef)
        """
        Pf = clamp((1013.0 - pressure_hpa) / 40.0, 0.0, 1.0)
        Ef = clamp(evaporation_mm / 5.0, 0.0, 1.0)
        Cf = cloud_coverage

        storm_index = Cf * (0.5 + 0.5 * Pf) * (0.3 + 0.7 * Ef)
        storm_index = clamp(storm_index, 0.0, 1.0)
        probability = storm_index * 100.0

        if probability == 0:
            category = "None"
        elif probability <= 20:
            category = "Low"
        elif probability <= 50:
            category = "Moderate"
        elif probability <= 80:
            category = "High"
        else:
            category = "Very High"

        return storm_index, probability, category

    def calc_precip_type(self) -> str:
        """
        Treat air temperatures at or below 1°C as snow.
        """
        if self.air_temp_c <= 1.0:
            return "Snow"
        else:
            return "Rain"

    def update_soil_moisture(self, storm_category: str) -> None:
        """
        Adjust soil moisture (0–1) using storm-driven moisture input and
        heat-driven moisture loss.
        """
        # Storm input
        add_lookup = {
            "None": 0.00,
            "Low": 0.10,
            "Moderate": 0.20,
            "High": 0.30,
            "Very High": 0.35,
        }
        Ma = add_lookup.get(storm_category, 0.0)

        # Temperature-driven loss
        T = self.surface_temp_c
        if T < 10.0:
            Ms = 0.05
        elif 10.0 <= T <= 25.0:
            Ms = 0.15
        else:  # T > 25
            Ms = 0.30

        temp_moisture = self.soil_moisture + Ma
        temp_moisture = temp_moisture - Ms * temp_moisture

        self.soil_moisture = clamp(temp_moisture, 0.0, 1.0)

    def calc_vegetation_health(self) -> tuple[float, str]:
        """
        Vegetation health index and status using temperature and soil moisture.
        Sf = 1 - |T - 25| / 15
        Mf = 1 - |M - 0.5| / 0.4
        Veg = Sf * Mf
        """
        T = self.surface_temp_c
        M = self.soil_moisture

        Sf = 1.0 - abs(T - 25.0) / 15.0
        Mf = 1.0 - abs(M - 0.5) / 0.4

        Sf = clamp(Sf, 0.0, 1.0)
        Mf = clamp(Mf, 0.0, 1.0)

        veg_index = Sf * Mf
        status = self._veg_status_from_index(veg_index)
        return veg_index, status

    @staticmethod
    def _veg_status_from_index(val: float) -> str:
        if 0.0 <= val < 0.2:
            return "Decay"
        elif 0.2 <= val < 0.4:
            return "Stressed"
        elif 0.4 <= val < 0.6:
            return "Stable"
        elif 0.6 <= val < 0.8:
            return "Healthy"
        else:
            return "Flourishing"

    def calc_flood_drought_status(self, evaporation_mm: float) -> str:
        """
        Flood / drought risk based on soil moisture (as %) and evaporation.
        """
        M_pct = self.soil_moisture * 100.0
        E = evaporation_mm

        if M_pct > 85 and E < 1.5:
            return "Flood likely"
        if M_pct > 70 and E < 3.0:
            return "Flood risk"
        if M_pct < 15 and E > 5.0:
            return "Drought likely"
        if M_pct < 30 and E > 4.0:
            return "Drought risk"
        return "Normal"

    @staticmethod
    def _plant_base_growth_from_status(status: str) -> float:
        """
        Base plant growth factor from vegetation status.
        This is used as a coefficient in the logistic plant equation.
        """
        lookup = {
            "Decay": -0.07,
            "Stressed": -0.00,
            "Stable": 0.07,
            "Healthy": 0.15,
            "Flourishing": 0.25,
        }
        return lookup.get(status, 0.0)

    def calc_plant_growth(self, veg_status: str,
                          flood_status: str,
                          precip_type: str) -> float:
        """
        Base growth factor from vegetation health, then modifiers based on
        flood/drought and snow. This returns a 'growth factor' that
        will then be used in the logistic feedback equation.
        """
        growth = self._plant_base_growth_from_status(veg_status)

        # Flood / drought multipliers
        if flood_status in ("Flood risk", "Drought risk"):
            growth *= 0.5
        elif flood_status in ("Flood likely", "Drought likely"):
            growth *= 0.0

        # Snow stops growth
        if precip_type == "Snow":
            growth *= 0.0

        return growth

    def calc_prey_growth(self) -> float:
        """
        Prey growth factor depends on plant population (0–1).
        """
        v = self.plant_pop
        if 0.0 <= v < 0.2:
            return -0.15
        elif 0.2 <= v < 0.4:
            return -0.05
        elif 0.4 <= v < 0.6:
            return 0.05
        elif 0.6 <= v < 0.8:
            return 0.10
        else:
            return 0.15

    def calc_predator_growth(self) -> float:
        """
        Predator growth factor depends on prey population (0–1).
        """
        v = self.prey_pop
        if 0.0 <= v < 0.2:
            return -0.10
        elif 0.2 <= v < 0.4:
            return -0.05
        elif 0.4 <= v < 0.6:
            return 0.03
        elif 0.6 <= v < 0.8:
            return 0.07
        else:
            return 0.10

    def _update_biosphere(self, plant_growth_factor: float,
                          prey_growth_factor: float,
                          predator_growth_factor: float) -> tuple[float, float, float]:
        """
        Apply a logistic-style feedback loop so populations don't explode.
        Then apply:
        - extra "crash" rules if prey overshoot plants or predators overshoot prey
          by more than 10%.
        - extra "boost" rules if plants are more than double prey, or prey more
          than double predators (5% bonus).
        Finally, apply a fail-safe floor so no population truly dies out.
        """
        p = self.plant_pop
        prey = self.prey_pop
        pred = self.predator_pop

        # Logistic self-limiting term: pop * (1 - pop)
        base_plant = plant_growth_factor * p * (1.0 - p)
        base_prey = prey_growth_factor * prey * (1.0 - prey)
        base_pred = predator_growth_factor * pred * (1.0 - pred)

        # Interaction terms (simple predator–prey–plant loop)
        eaten_plants = 0.10 * prey * p          # gentler grazing
        prey_food_gain = 0.20 * p * prey        # more plants → more prey food
        prey_eaten = 0.25 * pred * prey         # more predators → more prey eaten
        pred_food_gain = 0.20 * prey * pred     # more prey → more predator growth
        natural_pred_death = 0.05 * pred        # predators slowly die off

        delta_plant = base_plant - eaten_plants
        delta_prey = base_prey + prey_food_gain - prey_eaten
        delta_pred = base_pred + pred_food_gain - natural_pred_death

        # --- DAMPING: slow down normal changes to make the system more resilient ---
        damping = 0.10  # smaller = more stable / slower changes
        delta_plant *= damping
        delta_prey *= damping
        delta_pred *= damping

        # --- EXTRA CRASH CONDITIONS (soft) ---
        # If prey are more than 10% above plants, some prey die back
        if prey > p * 1.10 and prey > 0:
            delta_prey -= 0.05 * prey  # ~5% reduction

        # If predators are more than 10% above prey, some predators die back
        if pred > prey * 1.10 and pred > 0:
            delta_pred -= 0.05 * pred  # ~5% reduction

        #  EXTRA BOOST CONDITIONS
        # If plants are more than double prey, give prey a 5% boost
        if p > 2.0 * prey and prey > 0:
            delta_prey += 0.05 * prey   # +5% of current prey population

        # If prey are more than double predators, give predators a 5% boost
        if prey > 2.0 * pred and pred > 0:
            delta_pred += 0.05 * pred   # +5% of current predator population

        # Apply deltas
        new_p = p + delta_plant
        new_prey = prey + delta_prey
        new_pred = pred + delta_pred

        # Clamp to [0, 1]
        new_p = clamp(new_p, 0.0, 1.0)
        new_prey = clamp(new_prey, 0.0, 1.0)
        new_pred = clamp(new_pred, 0.0, 1.0)

        # --- FAIL-SAFE: nothing truly dies out ---
        MIN_POP = 0.01  # 1% minimum population
        if new_p < MIN_POP:
            new_p = MIN_POP
        if new_prey < MIN_POP:
            new_prey = MIN_POP
        if new_pred < MIN_POP:
            new_pred = MIN_POP

        # Commit back to state
        self.plant_pop = new_p
        self.prey_pop = new_prey
        self.predator_pop = new_pred

        # Return actual changes so we can show them in the status window
        return new_p - p, new_prey - prey, new_pred - pred

    # ---------- one full simulation step ----------

    def step_simulation(self) -> None:
        """
        Called when the user presses the Enter button.
        Uses the current average monthly temp from the spinbox,
        advances the model by one step, and updates the GUI.
        """
        # 0. Reset the status window every time we run a new step
        self.ui.Output_Text.clear()

        avg_temp_c = float(self.ui.Temp_box.value())
        self.step_count += 1

        # 1. Temperatures
        self.update_temperatures(avg_temp_c)

        # 2. Pressure
        pressure_hpa = self.calc_air_pressure()

        # 3. Evaporation
        evaporation_mm = self.calc_evaporation_rate(pressure_hpa)

        # 4. Clouds
        self.cloud_coverage = self.calc_cloud_coverage(evaporation_mm, pressure_hpa)
        oktas = self.cloud_to_oktas(self.cloud_coverage)

        # 5. Storm chance
        storm_index, storm_prob, storm_category = self.calc_storm_chance(
            evaporation_mm,
            self.cloud_coverage,
            pressure_hpa,
        )

        # 6. Precipitation type
        precip_type = self.calc_precip_type()

        # 7. Soil moisture
        self.update_soil_moisture(storm_category)

        # 8. Vegetation
        veg_index, veg_status = self.calc_vegetation_health()

        # 9. Flood / drought
        flood_status = self.calc_flood_drought_status(evaporation_mm)

        # 10. Biosphere (plants → prey → predators) with feedback loop
        plant_growth_factor = self.calc_plant_growth(veg_status, flood_status, precip_type)
        prey_growth_factor = self.calc_prey_growth()
        predator_growth_factor = self.calc_predator_growth()
        delta_plant, delta_prey, delta_pred = self._update_biosphere(
            plant_growth_factor,
            prey_growth_factor,
            predator_growth_factor,
        )

        # 11. Push everything back into the GUI
        self._update_gui(
            pressure_hpa=pressure_hpa,
            evaporation_mm=evaporation_mm,
            oktas=oktas,
            storm_prob=storm_prob,
            storm_category=storm_category,
            precip_type=precip_type,
            veg_index=veg_index,
            veg_status=veg_status,
            flood_status=flood_status,
        )

        # 12. Append a multi-line log entry to the text box
        self._append_log_entry(
            pressure_hpa=pressure_hpa,
            evaporation_mm=evaporation_mm,
            storm_prob=storm_prob,
            storm_category=storm_category,
            veg_status=veg_status,
            flood_status=flood_status,
            delta_plant=delta_plant,
            delta_prey=delta_prey,
            delta_predator=delta_pred,
        )

    # ---------- GUI update helpers ----------

    def _update_gui(self,
                    pressure_hpa: float,
                    evaporation_mm: float,
                    oktas: int,
                    storm_prob: float,
                    storm_category: str,
                    precip_type: str,
                    veg_index: float,
                    veg_status: str,
                    flood_status: str) -> None:
        # Atmosphere
        self.ui.AirTemp_Number.setText(f"{self.air_temp_c:.1f} C")
        self.ui.AirPressure_Number.setText(f"{pressure_hpa:.0f} hPa")
        self.ui.CloudCoverage_Number.setText(f"{oktas} oktas")
        self.ui.ChanceOfStorms_Number.setText(f"{storm_category} ({storm_prob:.0f}%)")
        self.ui.PrecipitationTypes_Number.setText(precip_type)

        # Hydrosphere
        self.ui.WaterTemp_Number.setText(f"{self.water_temp_c:.1f} C")
        self.ui.EvaporationRate_Number.setText(f"{evaporation_mm:.2f} mm/day")
        self.ui.FloodOrDrought_Status.setText(flood_status)

        # Geosphere
        self.ui.SurfaceTemp_Number.setText(f"{self.surface_temp_c:.1f} C")
        self.ui.SoilMoisture_Number.setText(f"{self.soil_moisture * 100:.0f}%")
        self.ui.VegetationHealth_Status.setText(veg_status)

        # Biosphere progress bars expect 0–100 integers
        self.ui.plant_progressBar.setValue(int(self.plant_pop * 100))
        self.ui.Prey_progressBar.setValue(int(self.prey_pop * 100))
        self.ui.Predator_progressBar.setValue(int(self.predator_pop * 100))

    def _append_log_entry(self,
                          pressure_hpa: float,
                          evaporation_mm: float,
                          storm_prob: float,
                          storm_category: str,
                          veg_status: str,
                          flood_status: str,
                          delta_plant: float,
                          delta_prey: float,
                          delta_predator: float) -> None:
        """
        Write a multi-line summary into the QTextBrowser at the bottom
        """
        self.ui.Output_Text.append(f"Day {self.step_count}")
        self.ui.Output_Text.append(
            f"  Atmosphere: Air {self.air_temp_c:.1f}°C, "
            f"P={pressure_hpa:.0f} hPa, clouds ≈ {self.cloud_coverage * 100:.0f}%"
        )
        self.ui.Output_Text.append(
            f"  Hydrosphere: Water {self.water_temp_c:.1f}°C, "
            f"E={evaporation_mm:.2f} mm/day, Flood/Drought: {flood_status}"
        )
        self.ui.Output_Text.append(
            f"  Geosphere: Surface {self.surface_temp_c:.1f}°C, "
            f"Soil moisture={self.soil_moisture * 100:.0f}%, Vegetation={veg_status}"
        )
        self.ui.Output_Text.append(
            f"  Biosphere: Plant={delta_plant:+.3f}, "
            f"Prey={delta_prey:+.3f}, Pred={delta_predator:+.3f}"
        )



