import random
import time
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List
from enum import Enum
import os
from kafka import KafkaProducer
from datetime import datetime

def clear_console():
    os.system('clear')

PURPLE = '\033[95m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

class Weather(Enum):
    DRY = "Dry"
    LIGHT_RAIN = "Light Rain"
    HEAVY_RAIN = "Heavy Rain"

class TireCompound:
    SOFT = {"name": "Soft", "pace": +0.180, "color": "\033[31m"}
    MEDIUM = {"name": "Medium", "pace": +0.200, "color": "\033[33m"}
    HARD = {"name": "Hard", "pace": +0.361, "color": "\033[37m"}

@dataclass
class Driver:
    name: str
    number: int
    team: str
    skill: float
    sector1: float = 0.0
    sector2: float = 0.0
    sector3: float = 0.0
    lap_time: float = float('inf')
    personal_best_s1: float = float('inf')
    personal_best_s2: float = float('inf')
    personal_best_s3: float = float('inf')
    personal_best_lap: float = float('inf')
    current_tire: Dict = field(default_factory=lambda: TireCompound.HARD)
    status: str = "In Garage"
    has_run: bool = False

@dataclass
class QualifyingMessage:
    session_name: str
    circuit_name: str
    weather: str
    timestamp: str
    drivers: List[Dict]

@dataclass
class GridPositionMessage:
    circuit_name: str
    timestamp: str
    grid_positions: List[Dict]
    pole_time: float

def format_sector_time(seconds: float) -> str:
    if seconds == 0.0 or seconds == float('inf'):
        return "No Time"
    return f"{seconds:.3f}"

def format_laptime(seconds: float) -> str:
    if seconds == float('inf'):
        return "No Time"
    minutes = int(seconds // 60)
    seconds_part = seconds % 60
    return f"{minutes}:{seconds_part:06.3f}"

class F1Simulator:
    def __init__(self):
        self.circuit_name = "Marina Bay Street Circuit"
        self.weather = Weather.DRY
        self.base_time = 100.015
        self.current_session = "Q1"
        self.reset_session_bests()
        
        self.producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        self.team_performance = {
            "Red Bull": 0.95,
            "Ferrari": 0.95,
            "Mercedes": 0.95,
            "McLaren": 0.95,
            "Aston Martin": 1.00,
            "Alpine": 1.09,
            "Williams": 1.00,
            "AlphaTauri": 1.00,
            "Alfa Romeo": 1.00,
            "Haas": 0.99
        }
        
        self.drivers = [
            Driver("Max Verstappen", 1, "Red Bull", 0.955),
            Driver("Sergio Perez", 11, "Red Bull", 0.99),
            Driver("Charles Leclerc", 16, "Ferrari", 0.88),
            Driver("Carlos Sainz", 55, "Ferrari", 0.85),
            Driver("Lewis Hamilton", 44, "Mercedes", 0.87),
            Driver("George Russell", 63, "Mercedes", 0.96),
            Driver("Lando Norris", 4, "McLaren", 0.93),
            Driver("Oscar Piastri", 81, "McLaren", 0.96),
            Driver("Fernando Alonso", 14, "Aston Martin", 0.98),
            Driver("Lance Stroll", 18, "Aston Martin", 0.96),
            Driver("Pierre Gasly", 10, "Alpine", 0.91),
            Driver("Esteban Ocon", 31, "Alpine", 0.94),
            Driver("Alex Albon", 23, "Williams", 0.96),
            Driver("Logan Sargeant", 2, "Williams", 0.94),
            Driver("Yuki Tsunoda", 22, "AlphaTauri", 0.92),
            Driver("Daniel Ricciardo", 3, "AlphaTauri", 0.93),
            Driver("Valtteri Bottas", 77, "Alfa Romeo", 0.93),
            Driver("Zhou Guanyu", 24, "Alfa Romeo", 0.92),
            Driver("Kevin Magnussen", 20, "Haas", 0.98),
            Driver("Nico Hulkenberg", 27, "Haas", 0.93)
        ]

    def send_to_kafka(self, drivers: List[Driver]):
        message = QualifyingMessage(
            session_name=self.current_session,
            circuit_name=self.circuit_name,
            weather=self.weather.value,
            timestamp=datetime.now().isoformat(),
            drivers=[{
                'name': d.name,
                'team': d.team,
                'number': d.number,
                'sector1': d.sector1,
                'sector2': d.sector2,
                'sector3': d.sector3,
                'lap_time': d.lap_time,
                'status': d.status,
                'tire': d.current_tire['name']
            } for d in drivers]
        )
        
        self.producer.send('quali', asdict(message))
        self.producer.flush()

    def send_grid_positions(self, drivers: List[Driver]):
        message = GridPositionMessage(
            circuit_name=self.circuit_name,
            timestamp=datetime.now().isoformat(),
            grid_positions=[{
                'position': idx + 1,
                'name': driver.name,
                'team': driver.team,
                'number': driver.number,
                'lap_time': format_laptime(driver.lap_time),
                'gap_to_pole': f"+{(driver.lap_time - drivers[0].lap_time):.3f}" if idx > 0 else "POLE"
            } for idx, driver in enumerate(drivers)],
            pole_time=drivers[0].lap_time
        )
        
        self.producer.send('grid', asdict(message))
        self.producer.flush()

    def reset_session_bests(self):
        self.session_best = {
            'S1': float('inf'),
            'S2': float('inf'),
            'S3': float('inf'),
            'lap': float('inf')
        }

    def format_time(self, time: float, personal_best: float, session_best: float) -> str:
        if time == 0.0 or time == float('inf'):
            return "No Time"
        
        time_str = format_sector_time(time)
        if abs(time - session_best) < 0.001:
            return f"{PURPLE}{time_str}{RESET}"
        if abs(time - personal_best) < 0.001:
            return f"{GREEN}{time_str}{RESET}"
        return f"{YELLOW}{time_str}{RESET}"

    def simulate_sector(self, driver: Driver, sector: int) -> float:
        base = self.base_time / 3
        team_factor = self.team_performance[driver.team]
        skill_factor = driver.skill
        tire_factor = 1 + driver.current_tire['pace']
        random_factor = random.uniform(-0.2, 0.2)
        
        time = base * team_factor * skill_factor * tire_factor + random_factor
        
        if time < getattr(driver, f'personal_best_s{sector}'):
            setattr(driver, f'personal_best_s{sector}', time)
        
        if time < self.session_best[f'S{sector}']:
            self.session_best[f'S{sector}'] = time
            
        return time

    def display_timing(self, drivers: List[Driver]):
        clear_console()
        print(f"\nQualifying - {self.circuit_name}")
        print(f"Weather: {self.weather.value}")
        print(f"Session: {self.current_session}\n")
        print("Pos  Driver          S1      S2      S3      Time     Tire    Status")
        print("-" * 80)
        
        sorted_drivers = sorted(drivers, key=lambda x: x.lap_time)
        
        for pos, driver in enumerate(sorted_drivers, 1):
            s1 = self.format_time(driver.sector1, driver.personal_best_s1, self.session_best['S1'])
            s2 = self.format_time(driver.sector2, driver.personal_best_s2, self.session_best['S2'])
            s3 = self.format_time(driver.sector3, driver.personal_best_s3, self.session_best['S3'])
            
            if driver.has_run:
                time_str = format_laptime(driver.lap_time)
            else:
                time_str = "No Time"
                
            tire_str = f"{driver.current_tire['color']}{driver.current_tire['name']}{RESET}"
            print(f"{pos:2d}.  {driver.name:<14} {s1:>7} {s2:>7} {s3:>7} {time_str:>10} {tire_str:>8} {driver.status:>8}")

    def run_session(self, name: str, drivers: List[Driver], cutoff: int) -> List[Driver]:
        self.current_session = name
        print(f"\n{name} Session Start")
        
        for driver in drivers:
            driver.status = "Out Lap"
            driver.sector1 = 0.0
            driver.sector2 = 0.0
            driver.sector3 = 0.0
            driver.lap_time = float('inf')
            self.display_timing(drivers)
            self.send_to_kafka(drivers)
            time.sleep(1)
            
            driver.status = "Flying Lap"
            
            driver.sector1 = self.simulate_sector(driver, 1)
            self.display_timing(drivers)
            self.send_to_kafka(drivers)
            time.sleep(1)
            
            driver.sector2 = self.simulate_sector(driver, 2)
            self.display_timing(drivers)
            self.send_to_kafka(drivers)
            time.sleep(1)
            
            driver.sector3 = self.simulate_sector(driver, 3)
            driver.lap_time = driver.sector1 + driver.sector2 + driver.sector3
            
            if driver.lap_time < driver.personal_best_lap:
                driver.personal_best_lap = driver.lap_time
            
            if driver.lap_time < self.session_best['lap']:
                self.session_best['lap'] = driver.lap_time
            
            driver.has_run = True
            driver.status = "In Garage"
            self.display_timing(drivers)
            self.send_to_kafka(drivers)
            time.sleep(1)
        
        drivers.sort(key=lambda x: x.lap_time)
        eliminated = drivers[cutoff:]
        if eliminated:
            print(f"\nEliminated from {name}:")
            for pos, driver in enumerate(eliminated, cutoff + 1):
                print(f"{pos}. {driver.name:<15} {format_laptime(driver.lap_time)}")
        return drivers[:cutoff]

    def display_final_classification(self):
        print("\nFinal Qualifying Classification:")
        print("-" * 80)
        
        all_drivers = self.drivers
        all_drivers.sort(key=lambda x: x.lap_time)
        
        for pos, driver in enumerate(all_drivers, 1):
            gap = f"+{(driver.lap_time - all_drivers[0].lap_time):.3f}" if pos > 1 else "POLE"
            print(f"{pos:2d}. {driver.name:<15} {format_laptime(driver.lap_time)} {gap:>8}")
        
        # Send final grid positions to 'grid' topic
        self.send_grid_positions(all_drivers)

    def run_qualifying(self):
        print(f"\nQualifying Session - {self.circuit_name}")
        
        print("\nQ1 Session - Hard Tires")
        for driver in self.drivers:
            driver.current_tire = TireCompound.HARD
        q2_drivers = self.run_session("Q1", self.drivers.copy(), 15)
        self.reset_session_bests()
        time.sleep(2)
        
        print("\nQ2 Session - Medium Tires")
        for driver in q2_drivers:
            driver.current_tire = TireCompound.MEDIUM
        q3_drivers = self.run_session("Q2", q2_drivers, 10)
        self.reset_session_bests()
        time.sleep(2)
        
        print("\nQ3 Session - Soft Tires")
        for driver in q3_drivers:
            driver.current_tire = TireCompound.SOFT
        final_order = self.run_session("Q3", q3_drivers, 10)
        
        self.display_final_classification()

    def __del__(self):
        """Cleanup Kafka producer on deletion"""
        if hasattr(self, 'producer'):
            self.producer.close()

if __name__ == "__main__":
    sim = F1Simulator()
    sim.run_qualifying()