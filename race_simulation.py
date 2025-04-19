import random
import time
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List
from enum import Enum
import os
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
from kafka.structs import TopicPartition
def clear_console():
    os.system('clear')

class RaceStatus(Enum):
    GREEN = "Racing"
    YELLOW = "Yellow Flag"
    SC = "Safety Car"
    VSC = "Virtual Safety Car"
    RED = "Red Flag"

class Weather(Enum):
    DRY = "Dry"
    LIGHT_RAIN = "Light Rain"
    HEAVY_RAIN = "Heavy Rain"

class TireCompound:
    SOFT = {"name": "Soft (S)", "max_laps": 20, "pace_delta": -1.2, "wear_rate": 1.5, "color": "\033[31m"}
    MEDIUM = {"name": "Medium (M)", "max_laps": 22, "pace_delta": 0, "wear_rate": 1.0, "color": "\033[33m"}
    HARD = {"name": "Hard (H)", "max_laps": 30, "pace_delta": 0.8, "wear_rate": 0.7, "color": "\033[37m"}

class TeamPerformance:
    FACTORS = {
        "Red Bull": {"S1": 0.96, "S2": 0.96, "S3": 0.97, "base": 0.95},
        "Mercedes": {"S1": 0.98, "S2": 0.97, "S3": 0.98, "base": 0.96},
        "Ferrari": {"S1": 0.98, "S2": 0.95, "S3": 0.97, "base": 0.94},
        "McLaren": {"S1": 0.97, "S2": 0.98, "S3": 0.94, "base": 0.95},
        "Aston Martin": {"S1": 1.00, "S2": 1.00, "S3": 1.00, "base": 0.98},
        "Alpine": {"S1": 1.01, "S2": 1.01, "S3": 1.01, "base": 0.99},
        "Williams": {"S1": 1.02, "S2": 1.02, "S3": 1.02, "base": 1.00},
        "AlphaTauri": {"S1": 1.03, "S2": 1.03, "S3": 1.03, "base": 1.01},
        "Alfa Romeo": {"S1": 1.04, "S2": 1.04, "S3": 1.04, "base": 1.02},
        "Haas": {"S1": 1.05, "S2": 1.05, "S3": 1.05, "base": 1.03}
    }

@dataclass
class Driver:
    name: str
    number: int
    team: str
    skill: float
    wet_skill: float
    aggression: float
    tire_management: float

    def to_dict(self):
        return asdict(self)

@dataclass
class Car:
    driver: Driver
    position: int = 0
    gap_to_leader: float = 0.0
    current_tire: Dict = field(default_factory=lambda: TireCompound.SOFT)
    tire_age: int = 0
    sector1_time: float = 0.0
    sector2_time: float = 0.0
    sector3_time: float = 0.0
    last_lap: float = 0.0
    fastest_lap: float = float('inf')
    total_race_time: float = 0.0
    pit_phase: str = "none"
    pit_stops: int = 0
    dnf: bool = False
    dnf_reason: str = ""
    dnf_lap: int = 0
    race_status: str = "Running"

    def to_dict(self):
        car_dict = {
            'position': self.position,
            'gap_to_leader': self.gap_to_leader,
            'current_tire': self.current_tire['name'],
            'tire_age': self.tire_age,
            'sector1_time': self.sector1_time,
            'sector2_time': self.sector2_time,
            'sector3_time': self.sector3_time,
            'last_lap': self.last_lap,
            'fastest_lap': self.fastest_lap if self.fastest_lap != float('inf') else None,
            'total_race_time': self.total_race_time,
            'pit_phase': self.pit_phase,
            'pit_stops': self.pit_stops,
            'dnf': self.dnf,
            'dnf_reason': self.dnf_reason,
            'dnf_lap': self.dnf_lap,
            'race_status': self.race_status,
            'driver': self.driver.to_dict()
        }
        return car_dict

    def update_status(self) -> str:
        if self.dnf:
            return f"DNF ({self.dnf_reason})"
        if self.pit_phase != "none":
            return f"In Pit ({self.pit_phase})"
        return f"Running - {self.current_tire['color']}{self.current_tire['name']}\033[0m ({self.tire_age} laps)"

class F1Simulator:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        self.drivers = self.consume_grid_from_kafka()
        self.cars = [Car(driver) for driver in self.drivers]
        self.total_laps = 61
        self.current_lap = 0
        self.race_status = RaceStatus.GREEN
        self.safety_car = False
        self.safety_car_laps = 0
        self.weather = Weather.DRY
        self.dnf_count = 0
        self.max_dnf = 2
        self.drs_enabled = False
        self.fastest_lap = {"time": float('inf'), "driver": None}

        self.pit_times = {
            "entry": 13.5,
            "stop": 2.5,
            "exit": 15.0
        }

        self.team_pit_efficiency = {
            "Red Bull": 0.8,
            "Mercedes": 0.95,
            "Ferrari": 0.85,
            "McLaren": 0.9,
            "Aston Martin": 1.0,
            "Alpine": 1.1,
            "Williams": 1.05,
            "AlphaTauri": 0.95,
            "Alfa Romeo": 1.1,
            "Haas": 1.15
        }

        self.initialize_race()

    
    def consume_grid_from_kafka(self):
        drivers_pool = [
            Driver("Max Verstappen", 1, "Red Bull", 0.92, 0.91, 0.90, 0.92),
            Driver("Sergio Perez", 11, "Red Bull", 0.94, 0.90, 0.85, 0.90),
            Driver("Lewis Hamilton", 44, "Mercedes", 0.97, 0.96, 0.98, 0.96),
            Driver("George Russell", 63, "Mercedes", 0.95, 0.95, 0.95, 0.99),
            Driver("Charles Leclerc", 16, "Ferrari", 0.96, 0.93, 0.93, 0.91),
            Driver("Carlos Sainz", 55, "Ferrari", 0.98, 0.95, 0.96, 0.99),
            Driver("Lando Norris", 4, "McLaren", 0.93, 0.90, 0.90, 0.92),
            Driver("Oscar Piastri", 81, "McLaren", 0.91, 0.94, 0.93, 0.94),
            Driver("Fernando Alonso", 14, "Aston Martin", 0.95, 0.94, 0.90, 0.93),
            Driver("Lance Stroll", 18, "Aston Martin", 0.90, 0.87, 0.85, 0.86),
            Driver("Pierre Gasly", 10, "Alpine", 0.92, 0.89, 0.86, 0.88),
            Driver("Esteban Ocon", 31, "Alpine", 0.91, 0.88, 0.85, 0.87),
            Driver("Alex Albon", 23, "Williams", 0.90, 0.87, 0.84, 0.86),
            Driver("Logan Sargeant", 2, "Williams", 0.88, 0.85, 0.83, 0.84),
            Driver("Yuki Tsunoda", 22, "AlphaTauri", 0.89, 0.86, 0.85, 0.85),
            Driver("Daniel Ricciardo", 3, "AlphaTauri", 0.91, 0.88, 0.86, 0.88),
            Driver("Valtteri Bottas", 77, "Alfa Romeo", 0.90, 0.87, 0.84, 0.86),
            Driver("Zhou Guanyu", 24, "Alfa Romeo", 0.89, 0.86, 0.83, 0.85),
            Driver("Kevin Magnussen", 20, "Haas", 0.89, 0.86, 0.85, 0.84),
            Driver("Nico Hulkenberg", 27, "Haas", 0.90, 0.87, 0.84, 0.85)
        ]
        driver_map = {driver.number: driver for driver in drivers_pool}

        # Create consumer with specific settings for reading existing messages
        consumer = KafkaConsumer(
            'grid',
            bootstrap_servers='localhost:9092',
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest',  # Changed to earliest to read existing messages
            consumer_timeout_ms=5000,  # 5 second timeout
            group_id=f'race_sim_group_{int(time.time())}',  # Unique group ID
            enable_auto_commit=False,
            max_poll_records=1
        )

        # Wait for consumer to be ready
        while not consumer.assignment():
            consumer.poll(timeout_ms=100)
            time.sleep(0.1)

        # Get all partitions
        partitions = consumer.assignment()
        
        # Seek to end for each partition to get the latest offset
        consumer.seek_to_end()
        
        # Get the latest message
        latest_offsets = {tp: consumer.position(tp) for tp in partitions}
        
        messages = []
        for tp in partitions:
            if latest_offsets[tp] > 0:
                # Seek to the last message
                consumer.seek(tp, latest_offsets[tp] - 1)
                partition_messages = consumer.poll(timeout_ms=5000)
                for partition_record in partition_messages.values():
                    messages.extend(partition_record)

        if not messages:
            print("Debug: No messages found. Checking topic details...")
            print(f"Partitions: {partitions}")
            print(f"Latest offsets: {latest_offsets}")
            raise RuntimeError("No messages found in grid topic")

        # Get the latest message
        grid_data = messages[-1].value
        consumer.close()

        try:
            self.circuit_name = grid_data.get("circuit_name", "Unknown Circuit")
            self.base_laptime = grid_data.get("pole_time", 95.0)

            grid_order = [driver["number"] for driver in grid_data["grid_positions"]]
            ordered_drivers = []
            
            print("Debug: Grid data received:")
            print(f"Circuit: {self.circuit_name}")
            print(f"Grid order: {grid_order}")
            
            for number in grid_order:
                driver = driver_map.get(number)
                if driver:
                    ordered_drivers.append(driver)
                else:
                    print(f"Driver number {number} not found in drivers pool.")
            
            if not ordered_drivers:
                raise RuntimeError("No valid drivers found in grid message")
                
            return ordered_drivers
            
        except Exception as e:
            print(f"Debug: Error processing grid data: {str(e)}")
            print(f"Grid data content: {grid_data}")
            raise
    def send_race_update(self, sector_number=None):
        race_data = {
            'timestamp': datetime.now().isoformat(),
            'circuit_name': self.circuit_name,
            'current_lap': self.current_lap,
            'total_laps': self.total_laps,
            'race_status': self.race_status.value,
            'weather': self.weather.value,
            'safety_car': self.safety_car,
            'drs_enabled': self.drs_enabled,
            'sector': sector_number,
            'cars': [car.to_dict() for car in sorted(self.cars, key=lambda x: float('inf') if x.dnf else x.total_race_time)],
            'fastest_lap': {
                'time': self.fastest_lap['time'] if self.fastest_lap['time'] != float('inf') else None,
                'driver': self.fastest_lap['driver'].to_dict() if self.fastest_lap['driver'] else None
            }
        }
        
        self.producer.send('race', race_data)
        self.producer.flush()

    def get_team_cars(self, team: str) -> List[Car]:
        return [car for car in self.cars if car.driver.team == team]

    def initialize_race(self):
        teams_processed = set()
        for i, car in enumerate(self.cars):
            car.position = i + 1
            if car.driver.team not in teams_processed:
                car.current_tire = TireCompound.SOFT
                teams_processed.add(car.driver.team)
            else:
                car.current_tire = TireCompound.MEDIUM

    def should_pit(self, car: Car) -> bool:
        teammate = next((c for c in self.get_team_cars(car.driver.team) if c != car), None)
        tire_critical = car.tire_age >= (car.current_tire["max_laps"] - 1)
        teammate_in_pit = teammate and teammate.pit_phase != "none"
        return tire_critical and not teammate_in_pit

    def display_race_banner(self):
        print("\n" + "=" * 80)
        print(f"Lap {self.current_lap}/{self.total_laps} | {self.race_status.value} | {self.weather.value}")
        print(f"Circuit: {self.circuit_name} | Base Lap Time: {self.base_laptime:.3f}s")
        if self.safety_car:
            print("\U0001F6A8 Safety Car Period")
        if self.drs_enabled:
            print("\U0001F4A8 DRS Enabled")
        if self.fastest_lap["driver"]:
            print(f"\U0001F525 Fastest Lap: {self.fastest_lap['driver'].name} ({self.fastest_lap['time']:.3f})")
        print("=" * 80 + "\n")

    def calculate_sector_time(self, car: Car, sector: int) -> float:
        base_sector = self.base_laptime / 3
        team_factor = TeamPerformance.FACTORS[car.driver.team][f"S{sector}"]
        skill_factor = 1 - ((car.driver.skill - 0.8) * 0.5)
        tire_performance = (car.current_tire["pace_delta"] / 3) + ((car.tire_age / car.current_tire["max_laps"]) * 0.7)
        
        if car.pit_phase != "none":
            if car.pit_phase == "entry" and sector == 3:
                return base_sector + self.pit_times["entry"]
            elif car.pit_phase == "stop" and sector == 1:
                return base_sector + (self.pit_times["stop"] * self.team_pit_efficiency[car.driver.team])
            elif car.pit_phase == "exit" and sector == 1:
                return base_sector + self.pit_times["exit"]

        if self.safety_car:
            base_sector *= 1.4
            if car.position > 1:
                base_sector *= 0.98

        random_factor = random.uniform(-0.2, 0.2) * car.driver.skill
        return (base_sector * team_factor * skill_factor) + tire_performance + random_factor

    def handle_pit_stop(self, car: Car):
        if car.pit_phase == "none":
            car.pit_phase = "entry"
        elif car.pit_phase == "entry":
            car.pit_phase = "stop"
            teammate = next((c for c in self.get_team_cars(car.driver.team) if c != car), None)
            available_compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD]
            if teammate and teammate.current_tire in available_compounds:
                available_compounds.remove(teammate.current_tire)
            car.current_tire = random.choice(available_compounds)
            car.tire_age = 0
        elif car.pit_phase == "stop":
            car.pit_phase = "exit"
        else:
            car.pit_phase = "none"
            car.pit_stops += 1

    def check_incidents(self, car: Car) -> bool:
        # Skip incident check for Carlos Sainz (car #55)
        if car.driver.number == 55:
            return False

        if self.dnf_count >= self.max_dnf or car.dnf or random.random() > 0.001:
            return False
        car.dnf = True
        car.dnf_lap = self.current_lap
        car.dnf_reason = random.choice(["Engine", "Gearbox", "Collision", "Hydraulics"])
        self.dnf_count += 1

        if not self.safety_car and random.random() < 0.7:
            self.safety_car = True
            self.safety_car_laps = 5
            self.race_status = RaceStatus.SC
            print(f"\n\U0001F4A5 Incident: {car.driver.name} - {car.dnf_reason}")
            print("\U0001F6A8 Safety Car Deployed")
        return True

    def handle_overtakes(self, all_cars):
        for i in range(len(all_cars) - 1):
            car_ahead = all_cars[i]
            car_behind = all_cars[i + 1]

            if car_ahead.dnf or car_behind.dnf:
                continue

            gap = car_behind.total_race_time - car_ahead.total_race_time
            
            if self.safety_car and gap > 0.6:
                car_behind.total_race_time = car_ahead.total_race_time + random.uniform(0.1, 0.5)
                continue

            if gap <= 1.0:
                performance_diff = (car_behind.driver.skill * TeamPerformance.FACTORS[car_behind.driver.team]["base"]) - \
                                 (car_ahead.driver.skill * TeamPerformance.FACTORS[car_ahead.driver.team]["base"])
                
                tire_diff = (car_ahead.tire_age / car_ahead.current_tire["max_laps"]) - \
                           (car_behind.tire_age / car_behind.current_tire["max_laps"])
                
                overtake_probability = 0.3 + (performance_diff * 0.5) + (tire_diff * 0.2)
                
                if self.drs_enabled:
                    overtake_probability += 0.5

                if car_ahead.pit_phase != "none" and car_behind.pit_phase == "none":
                    overtake_probability = 0.8

                if random.random() < overtake_probability:
                    message = "\U0001F697 "
                    if car_ahead.pit_phase != "none":
                        message += "Pit lane overtake! "
                    elif self.drs_enabled:
                        message += "DRS assisted overtake! "
                    message += f"{car_behind.driver.name} passes {car_ahead.driver.name}"
                    print(message)

                    overtake_gap = random.uniform(0.69, 1.230)
                    car_behind.total_race_time = car_ahead.total_race_time - overtake_gap
                    car_behind.position, car_ahead.position = car_ahead.position, car_behind.position
                    all_cars[i], all_cars[i + 1] = all_cars[i + 1], all_cars[i]

    def update_fastest_lap(self, car: Car):
        current_lap_time = car.last_lap
        if not car.dnf and current_lap_time < car.fastest_lap:
            car.fastest_lap = current_lap_time
            
        if current_lap_time < self.fastest_lap["time"]:
            self.fastest_lap["time"] = current_lap_time
            self.fastest_lap["driver"] = car.driver
            print(f"\n\U0001F525 New Fastest Lap! {car.driver.name}: {current_lap_time:.3f}")

    def run_race(self):
        print(f"\nRace Start - {self.circuit_name}")
        self.send_race_update()  # Initial race state

        for lap in range(1, self.total_laps + 1):
            self.current_lap = lap
            clear_console()

            if self.current_lap > 2:
                self.drs_enabled = True

            self.display_race_banner()

            for sector in range(1, 4):
                print(f"\nSector {sector}:")

                for car in [c for c in self.cars if not c.dnf]:
                    if sector == 1:
                        car.tire_age += 1
                        if self.should_pit(car) and car.pit_phase == "none":
                            car.pit_phase = "entry"
                            print(f"\n🔧 {car.driver.name} is entering the pits")

                    sector_time = self.calculate_sector_time(car, sector)
                    setattr(car, f"sector{sector}_time", sector_time)
                    
                    if sector == 3:
                        car.last_lap = car.sector1_time + car.sector2_time + car.sector3_time
                        car.total_race_time += car.last_lap
                        self.update_fastest_lap(car)

                        if car.pit_phase != "none":
                            self.handle_pit_stop(car)

                    self.check_incidents(car)

                # Update positions and send race update after each sector
                all_cars = sorted(self.cars, key=lambda x: float('inf') if x.dnf else x.total_race_time)
                leader_time = next((c.total_race_time for c in all_cars if not c.dnf), 0)

                for pos, car in enumerate(all_cars, 1):
                    car.position = pos
                    if not car.dnf:
                        car.gap_to_leader = car.total_race_time - leader_time
                    
                    status = car.update_status()
                    tire_info = "" if car.dnf else f"| {car.current_tire['color']}{car.current_tire['name']}\033[0m ({car.tire_age} laps)"

                    if car.dnf:
                        print(f"{pos}. {car.driver.name:15} | {status}")
                    else:
                        gap = car.total_race_time - leader_time
                        gap_str = "LEADER" if gap == 0 else f"+{gap:.3f}s"
                        sector_time = getattr(car, f"sector{sector}_time", 0.0)
                        print(f"{pos}. {car.driver.name:15} | S{sector}: {sector_time:.3f} | Gap: {gap_str:10} | {status}")

                self.send_race_update(sector)

                if sector == 3 and not self.safety_car:
                    self.handle_overtakes(all_cars)

                time.sleep(1)

            if self.safety_car:
                self.safety_car_laps -= 1
                if self.safety_car_laps <= 0:
                    self.safety_car = False
                    self.race_status = RaceStatus.GREEN
                    print("\n\U0001F3C1 Safety Car In This Lap!")

            time.sleep(2)

        # Send final race update
        self.send_race_update()
        
        print("\n" + "=" * 80)
        print(f"RACE FINISHED - {self.circuit_name}")
        print("=" * 80)

        points_system = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
        all_cars = sorted(self.cars, key=lambda x: float('inf') if x.dnf else x.total_race_time)
        leader_time = next((c.total_race_time for c in all_cars if not c.dnf), 0)

        print("\nFinal Classification:")
        for pos, car in enumerate(all_cars, 1):
            points = points_system.get(pos, 0)
            if car.driver == self.fastest_lap["driver"] and pos <= 10:
                points += 1
                fastest_lap_indicator = " \U0001F525 FASTEST LAP"
            else:
                fastest_lap_indicator = ""
                
            if car.dnf:
                print(f"{pos}. {car.driver.name:15} | DNF (Lap {car.dnf_lap} - {car.dnf_reason})")
            else:
                gap = car.total_race_time - leader_time
                gap_str = "WINNER!" if gap == 0 else f"+{gap:.3f}s"
                print(f"{pos}. {car.driver.name:15} | {gap_str:10} | Stops: {car.pit_stops} | Points: {points}{fastest_lap_indicator}")

        print("\nFastest Lap Award:")
        print(f"{self.fastest_lap['driver'].name}: {self.fastest_lap['time']:.3f}")
        
        # Close Kafka producer
        self.producer.close()

if __name__ == "__main__":
    sim = F1Simulator()
    sim.run_race()