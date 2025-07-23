from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import asyncio
import logging
import json
import random
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# Auto-events toggle
auto_events_enabled = True

# Enhanced data for realism
FANTASY_FIRST_NAMES = [
    "Aelindra", "Brak", "Caelynn", "Darius", "Eryndor", "Faelyn", "Gareth", 
    "Hilda", "Ivara", "Jareth", "Kira", "Lyra", "Magnus", "Nora", "Orin",
    "Petra", "Quentin", "Raven", "Senna", "Thane", "Ulric", "Vera", "Willem", 
    "Xara", "Yorick", "Zara", "Aldric", "Brenna", "Cedric", "Delia", "Eamon", 
    "Faye", "Gideon", "Hera", "Ian", "Jora", "Kael", "Lara", "Mira", "Nash"
]

FANTASY_LAST_NAMES = [
    "Stormwind", "Ironforge", "Goldleaf", "Shadowmere", "Brightblade", "Darkwood", 
    "Silvermoon", "Redstone", "Blackwater", "Whitehawk", "Greycloak", "Bluethorn",
    "Emberthane", "Frostborn", "Sunblade", "Moonwhisper", "Starweaver", "Flamekeeper",
    "Stormcaller", "Earthshaker", "Windrider", "Lightbringer", "Shadowbane", "Dragonheart"
]

OCCUPATIONS = [
    "Blacksmith", "Baker", "Merchant", "Guard", "Scholar", "Healer", "Farmer", 
    "Carpenter", "Mason", "Innkeeper", "Scribe", "Mage", "Archer", "Knight",
    "Tailor", "Fletcher", "Alchemist", "Jeweler", "Fisherman", "Hunter", "Bard"
]

GOVERNMENT_POSITIONS = [
    # High Council Positions
    "Captain of the Guard", "Master of Coin", "High Scribe", "Court Wizard", "Head Cleric",
    
    # Administrative Positions  
    "Tax Collector", "Market Warden", "Harbor Master", "Gate Keeper", "Master of Arms",
    
    # Trade & Commerce
    "Trade Minister", "Guild Representative", "Merchant Overseer", "Customs Officer",
    
    # Law & Order
    "City Magistrate", "Prison Warden", "Court Bailiff", "Sheriff Deputy",
    
    # Infrastructure
    "Master Builder", "Road Warden", "Bridge Keeper", "City Engineer",
    
    # Cultural & Religious
    "Festival Coordinator", "Temple Overseer", "Library Keeper", "Academy Dean"
]

LIVESTOCK_TYPES = [
    "Cattle", "Horse", "Goat", "Sheep", "Chicken", "Pig", "Ox", "Mule", "Donkey"
]

MILITARY_RANKS = [
    "Recruit", "Private", "Corporal", "Sergeant", "Lieutenant", "Captain", "Major", "Commander"
]

# Expanded crime system
CRIME_TYPES_DETAILED = {
    # Petty Crimes
    "Petty Theft": {"severity": "minor", "fine": (1, 10), "punishment": ["Public humiliation", "1-3 days stocks", "Community service"]},
    "Pickpocketing": {"severity": "minor", "fine": (2, 15), "punishment": ["Cut off finger", "2-5 days stocks", "Branded hand"]},
    "Vandalism": {"severity": "minor", "fine": (5, 25), "punishment": ["Repair damages", "Public work", "1 week jail"]},
    "Public Drunkenness": {"severity": "minor", "fine": (1, 5), "punishment": ["Night in jail", "Public apology", "Banned from taverns"]},
    "Disturbing Peace": {"severity": "minor", "fine": (2, 8), "punishment": ["Warning", "Small fine", "Night in jail"]},
    
    # Moderate Crimes
    "Burglary": {"severity": "moderate", "fine": (20, 100), "punishment": ["30 days jail", "Flogging", "Banishment"]},
    "Assault": {"severity": "moderate", "fine": (25, 150), "punishment": ["Public flogging", "1-6 months jail", "Compensation to victim"]},
    "Fraud": {"severity": "moderate", "fine": (50, 200), "punishment": ["Brand on forehead", "6 months jail", "Triple compensation"]},
    "Tax Evasion": {"severity": "moderate", "fine": (100, 500), "punishment": ["Double tax owed", "Seizure of property", "Public shame"]},
    "Smuggling": {"severity": "moderate", "fine": (75, 300), "punishment": ["Confiscation of goods", "6 months jail", "Banishment"]},
    "Bribery": {"severity": "moderate", "fine": (50, 250), "punishment": ["Public disgrace", "Loss of position", "Fine and jail"]},
    
    # Serious Crimes
    "Armed Robbery": {"severity": "serious", "fine": (200, 1000), "punishment": ["1-5 years prison", "Hand cut off", "Death"]},
    "Arson": {"severity": "serious", "fine": (500, 2000), "punishment": ["Death by fire", "Life imprisonment", "Banishment"]},
    "Kidnapping": {"severity": "serious", "fine": (300, 1500), "punishment": ["Death", "Life slavery", "Torture then death"]},
    "Rape": {"severity": "serious", "fine": (0, 0), "punishment": ["Castration", "Death", "Life imprisonment"]},
    "Murder": {"severity": "serious", "fine": (0, 0), "punishment": ["Death by hanging", "Death by beheading", "Drawn and quartered"]},
    "Treason": {"severity": "serious", "fine": (0, 0), "punishment": ["Death by torture", "Family execution", "Public execution"]},
    
    # Magical Crimes
    "Illegal Magic Use": {"severity": "moderate", "fine": (100, 400), "punishment": ["Magic binding", "6 months jail", "Magical probation"]},
    "Necromancy": {"severity": "serious", "fine": (0, 0), "punishment": ["Death by fire", "Banishment to shadowlands", "Life imprisonment"]},
    "Demon Summoning": {"severity": "serious", "fine": (0, 0), "punishment": ["Death by holy fire", "Exorcism then death", "Sealed in holy prison"]},
    
    # Economic Crimes
    "Counterfeiting": {"severity": "moderate", "fine": (100, 300), "punishment": ["Brand on hand", "Loss of hands", "Public flogging"]},
    "Market Manipulation": {"severity": "moderate", "fine": (200, 800), "punishment": ["Trade ban", "Seizure of assets", "Public humiliation"]},
    "Guild Violations": {"severity": "minor", "fine": (10, 50), "punishment": ["Guild suspension", "Fine to guild", "Public apology"]}
}

def generate_fantasy_name():
    return f"{random.choice(FANTASY_FIRST_NAMES)} {random.choice(FANTASY_LAST_NAMES)}"

def get_crime_punishment(crime_type):
    """Generate appropriate punishment for crime type"""
    if crime_type in CRIME_TYPES_DETAILED:
        crime_data = CRIME_TYPES_DETAILED[crime_type]
        punishment = random.choice(crime_data["punishment"])
        fine_range = crime_data["fine"]
        fine = random.randint(fine_range[0], fine_range[1]) if fine_range[0] > 0 else 0
        return punishment, fine
    return "Fine and jail time", random.randint(5, 50)

# Auto-generation functions
def generate_citizen(city_id):
    return {
        "name": generate_fantasy_name(),
        "age": random.randint(16, 70),
        "occupation": random.choice(OCCUPATIONS),
        "city_id": city_id,
        "health": random.choices(["Healthy", "Injured", "Sick"], weights=[85, 10, 5])[0],
        "notes": random.choice(["", f"Notable for {random.choice(['bravery', 'skill', 'wisdom', 'kindness'])}", 
                               f"Family member of local {random.choice(['merchant', 'noble', 'artisan'])}"]),
    }

def generate_slave(city_id):
    origins = ["Captured Orc", "War Prisoner", "Debt Slave", "Born Slave", "Criminal Sentence", "Captured Bandit"]
    return {
        "name": generate_fantasy_name(),
        "age": random.randint(14, 50),
        "origin": random.choice(origins),
        "occupation": random.choice(["Laborer", "Servant", "Cook", "Cleaner", "Builder", "Farm Worker"]),
        "owner": random.choice(["City", "Noble House", "Merchant Guild", "Private Owner"]),
        "purchase_price": random.randint(20, 200),
        "city_id": city_id,
        "health": random.choices(["Healthy", "Injured", "Sick"], weights=[70, 20, 10])[0],
        "status": "Enslaved",
        "notes": ""
    }

def generate_livestock(city_id):
    animal_type = random.choice(LIVESTOCK_TYPES)
    base_weights = {"Cattle": 800, "Horse": 1000, "Goat": 60, "Sheep": 80, 
                   "Chicken": 5, "Pig": 200, "Ox": 1200, "Mule": 400, "Donkey": 300}
    base_values = {"Cattle": 150, "Horse": 300, "Goat": 25, "Sheep": 35,
                  "Chicken": 2, "Pig": 40, "Ox": 200, "Mule": 100, "Donkey": 80}
    
    weight = base_weights.get(animal_type, 100) + random.randint(-50, 100)
    value = base_values.get(animal_type, 50) + random.randint(-20, 50)
    
    return {
        "name": random.choice(["Thunder", "Lightning", "Storm", "Mighty", "Swift", "Strong", "Gentle", "Brave"]),
        "type": animal_type,
        "age": random.randint(1, 8),
        "health": random.choices(["Healthy", "Injured", "Sick"], weights=[80, 15, 5])[0],
        "weight": max(weight, 1),
        "value": max(value, 1),
        "city_id": city_id,
        "owner": random.choice(["City", "Private Owner", "Noble", "Merchant"]),
        "notes": ""
    }

def generate_soldier(city_id):
    return {
        "name": generate_fantasy_name(),
        "rank": random.choice(MILITARY_RANKS),
        "age": random.randint(18, 45),
        "years_of_service": random.randint(0, 20),
        "equipment": random.sample(["Sword", "Shield", "Spear", "Bow", "Crossbow", "Chain Mail", 
                                  "Leather Armor", "Helmet", "Boots", "Dagger"], 
                                 random.randint(2, 5)),
        "status": random.choices(["Active", "Injured", "Deserter"], weights=[85, 10, 5])[0],
        "city_id": city_id,
        "notes": ""
    }

def generate_crime(city_id, city_name):
    crime_type = random.choice(list(CRIME_TYPES_DETAILED.keys()))
    punishment, fine = get_crime_punishment(crime_type)
    
    return {
        "criminal_name": generate_fantasy_name(),
        "crime_type": crime_type,
        "description": f"Accused of {crime_type.lower()} in {city_name}",
        "city_id": city_id,
        "punishment": punishment,
        "status": random.choices(["Reported", "Investigated", "Resolved"], weights=[40, 35, 25])[0],
        "fine_amount": fine,
        "date_occurred": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        "notes": ""
    }

def generate_tribute(from_city, to_city="Royal Treasury"):
    purposes = ["Annual Tribute", "Trade Tax", "Military Support", "Road Maintenance", 
               "Defense Fund", "Royal Decree", "Emergency Tax", "Harvest Tax"]
    return {
        "from_city": from_city,
        "to_city": to_city,
        "amount": random.randint(50, 500),
        "type": random.choice(["Gold", "Goods", "Services"]),
        "purpose": random.choice(purposes),
        "status": random.choices(["Pending", "Paid", "Overdue"], weights=[50, 40, 10])[0],
        "due_date": datetime.utcnow() + timedelta(days=random.randint(1, 90)),
        "notes": ""
    }

# Event generation for auto-generated content
def generate_registry_event(event_type, city_name, details):
    events = {
        "citizen": [
            f"{details['name']} ({details['age']} yrs, {details['occupation']}) joins {city_name}.",
            f"New citizen {details['name']} registers in {city_name} as a {details['occupation']}.",
            f"{details['name']} arrives in {city_name} seeking work as a {details['occupation']}."
        ],
        "slave": [
            f"New slave {details['name']} acquired in {city_name} ({details.get('origin', 'Unknown origin')}).",
            f"{details['name']}, a {details.get('origin', 'slave')}, becomes enslaved in {city_name}.",
            f"Slave {details['name']} assigned to {details.get('owner', 'City')} in {city_name}."
        ],
        "livestock": [
            f"New {details['type'].lower()} '{details['name']}' added to {city_name} herds.",
            f"{details['name']} the {details['type']} purchased for {details['value']} GP in {city_name}.",
            f"Livestock registry updated: {details['name']} ({details['type']}) in {city_name}."
        ],
        "soldier": [
            f"{details['name']} enlists as {details['rank']} in {city_name} garrison.",
            f"New recruit {details['name']} joins {city_name}'s military forces.",
            f"{details['rank']} {details['name']} reports for duty in {city_name}."
        ],
        "crime": [
            f"{details['criminal_name']} accused of {details['crime_type']} in {city_name}.",
            f"Crime reported: {details['crime_type']} by {details['criminal_name']} in {city_name}.",
            f"{city_name} authorities investigate {details['criminal_name']} for {details['crime_type']}."
        ],
        "tribute": [
            f"{details['from_city']} owes {details['amount']} GP tribute for {details.get('purpose', 'royal decree')}.",
            f"Tribute demand: {details['from_city']} to pay {details['amount']} GP to {details.get('to_city', 'Royal Treasury')}.",
            f"{details['from_city']} tribute payment of {details['amount']} GP is {details.get('status', 'pending').lower()}."
        ]
    }
    return random.choice(events.get(event_type, [f"Registry updated in {city_name}."]))

# Enhanced Data Models
class Citizen(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    occupation: str
    city_id: str
    health: str = "Healthy"
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CitizenCreate(BaseModel):
    name: str
    age: int
    occupation: str
    city_id: str
    health: str = "Healthy"
    notes: str = ""

class CitizenUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    occupation: Optional[str] = None
    health: Optional[str] = None
    notes: Optional[str] = None

class GovernmentOfficial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    position: str
    appointed_date: datetime = Field(default_factory=datetime.utcnow)
    city_id: str

class Slave(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    origin: str
    occupation: str
    owner: str
    purchase_price: int
    city_id: str
    health: str = "Healthy"
    status: str = "Enslaved"
    manumission_date: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SlaveCreate(BaseModel):
    name: str
    age: int
    origin: str
    occupation: str
    owner: str
    purchase_price: int
    city_id: str
    health: str = "Healthy"
    notes: str = ""

class Livestock(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str
    age: int
    health: str = "Healthy"
    weight: int
    value: int
    city_id: str
    owner: str = "City"
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LivestockCreate(BaseModel):
    name: str
    type: str
    age: int
    health: str = "Healthy"
    weight: int
    value: int
    city_id: str
    owner: str = "City"
    notes: str = ""

class Soldier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    rank: str
    age: int
    years_of_service: int
    equipment: List[str] = []
    status: str = "Active"
    city_id: str
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SoldierCreate(BaseModel):
    name: str
    rank: str
    age: int
    years_of_service: int = 0
    equipment: List[str] = []
    status: str = "Active"
    city_id: str
    notes: str = ""

class TributeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_city: str
    to_city: str
    amount: int
    type: str = "Gold"
    purpose: str
    status: str = "Pending"
    due_date: datetime
    paid_date: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TributeCreate(BaseModel):
    from_city: str
    to_city: str
    amount: int
    type: str = "Gold"
    purpose: str
    due_date: datetime
    notes: str = ""

class CrimeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    criminal_name: str
    crime_type: str
    description: str
    city_id: str
    punishment: str = ""
    status: str = "Reported"
    fine_amount: int = 0
    date_occurred: datetime
    date_resolved: Optional[datetime] = None
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CrimeCreate(BaseModel):
    criminal_name: str
    crime_type: str
    description: str
    city_id: str
    punishment: str = ""
    fine_amount: int = 0
    date_occurred: datetime
    notes: str = ""

class City(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    governor: str
    government_officials: List[GovernmentOfficial] = []
    population: int = 0
    treasury: int = 1000
    x_coordinate: float = 0.0
    y_coordinate: float = 0.0
    citizens: List[Citizen] = []
    slaves: List[Slave] = []
    livestock: List[Livestock] = []
    garrison: List[Soldier] = []
    tribute_records: List[TributeRecord] = []
    crime_records: List[CrimeRecord] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CityCreate(BaseModel):
    name: str
    governor: str
    x_coordinate: float = 0.0
    y_coordinate: float = 0.0

class CityUpdate(BaseModel):
    name: Optional[str] = None
    governor: Optional[str] = None
    treasury: Optional[int] = None
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None

class Kingdom(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    ruler: str
    total_population: int = 0
    royal_treasury: int = 5000
    cities: List[City] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    city_name: str
    kingdom_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = "general"

class EventCreate(BaseModel):
    description: str
    city_name: str
    event_type: str = "manual"

class AutoGenerateRequest(BaseModel):
    registry_type: str  # "citizens", "slaves", "livestock", "garrison", "crimes", "tribute"
    city_id: str
    count: int = 1

# Enhanced simulation engine with auto-generation
async def simulation_engine():
    """Background task that generates kingdom events and auto-generates registry content"""
    global auto_events_enabled
    while True:
        try:
            if auto_events_enabled:
                kingdom_data = await db.kingdoms.find_one()
                if kingdom_data and kingdom_data['cities']:
                    # Regular fantasy events
                    if random.random() < 0.7:  # 70% chance for regular events
                        city = random.choice(kingdom_data['cities'])
                        event_templates = [
                            f"A traveling merchant arrives in {city['name']} with exotic goods.",
                            f"The harvest looks promising around {city['name']} this season.",
                            f"A festival celebrating the harvest begins in {city['name']}.",
                            f"Weather has been favorable for trade in {city['name']}.",
                            f"Local artisans in {city['name']} display their finest work.",
                            f"A wandering bard performs tales of old in {city['name']}'s square."
                        ]
                        
                        event = Event(
                            description=random.choice(event_templates),
                            city_name=city['name'],
                            kingdom_name=kingdom_data['name'],
                            event_type="auto"
                        )
                        
                        await db.events.insert_one(event.dict())
                        await manager.broadcast({
                            "type": "new_event",
                            "event": event.dict()
                        })
                    
                    # Auto-generate registry content
                    else:  # 30% chance for registry auto-generation
                        city = random.choice(kingdom_data['cities'])
                        registry_types = ["citizens", "livestock", "crimes", "soldiers"]
                        registry_type = random.choice(registry_types)
                        
                        if registry_type == "citizens":
                            new_citizen_data = generate_citizen(city['id'])
                            new_citizen = Citizen(**new_citizen_data)
                            
                            result = await db.kingdoms.update_one(
                                {"cities.id": city['id']},
                                {
                                    "$push": {"cities.$.citizens": new_citizen.dict()},
                                    "$inc": {"cities.$.population": 1, "total_population": 1}
                                }
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("citizen", city['name'], new_citizen_data)
                                await create_and_broadcast_event(event_desc, city['name'], kingdom_data['name'], "auto-registry")
                        
                        elif registry_type == "livestock":
                            new_livestock_data = generate_livestock(city['id'])
                            new_livestock = Livestock(**new_livestock_data)
                            
                            result = await db.kingdoms.update_one(
                                {"cities.id": city['id']},
                                {"$push": {"cities.$.livestock": new_livestock.dict()}}
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("livestock", city['name'], new_livestock_data)
                                await create_and_broadcast_event(event_desc, city['name'], kingdom_data['name'], "auto-registry")
                        
                        elif registry_type == "crimes":
                            new_crime_data = generate_crime(city['id'], city['name'])
                            new_crime = CrimeRecord(**new_crime_data)
                            
                            result = await db.kingdoms.update_one(
                                {"cities.id": city['id']},
                                {"$push": {"cities.$.crime_records": new_crime.dict()}}
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("crime", city['name'], new_crime_data)
                                await create_and_broadcast_event(event_desc, city['name'], kingdom_data['name'], "auto-registry")
                        
                        elif registry_type == "soldiers":
                            new_soldier_data = generate_soldier(city['id'])
                            new_soldier = Soldier(**new_soldier_data)
                            
                            result = await db.kingdoms.update_one(
                                {"cities.id": city['id']},
                                {"$push": {"cities.$.garrison": new_soldier.dict()}}
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("soldier", city['name'], new_soldier_data)
                                await create_and_broadcast_event(event_desc, city['name'], kingdom_data['name'], "auto-registry")
            
            await asyncio.sleep(random.randint(20, 60))  # 20-60 seconds between events
            
        except Exception as e:
            logging.error(f"Simulation error: {e}")
            await asyncio.sleep(30)

async def create_and_broadcast_event(description, city_name, kingdom_name, event_type):
    """Helper function to create and broadcast events"""
    event = Event(
        description=description,
        city_name=city_name,
        kingdom_name=kingdom_name,
        event_type=event_type
    )
    
    await db.events.insert_one(event.dict())
    await manager.broadcast({
        "type": "new_event",
        "event": event.dict()
    })

# Initialize kingdom data with government officials
async def initialize_kingdom():
    """Create sample kingdom data if none exists"""
    existing_kingdom = await db.kingdoms.find_one()
    if not existing_kingdom:
        # Create government officials for cities
        emberfalls_officials = [
            GovernmentOfficial(name="Captain Marcus Steel", position="Captain of the Guard", city_id="city1"),
            GovernmentOfficial(name="Elena Goldleaf", position="Master of Coin", city_id="city1"),
            GovernmentOfficial(name="Sage Thorin", position="High Scribe", city_id="city1"),
        ]
        
        stormhaven_officials = [
            GovernmentOfficial(name="Commander Vera", position="Captain of the Guard", city_id="city2"),
            GovernmentOfficial(name="Merchant Gareth", position="Trade Minister", city_id="city2"),
        ]
        
        # Create sample citizens
        citizens_emberfalls = [
            Citizen(name="Thorin Emberthane", age=45, occupation="Blacksmith", city_id="city1"),
            Citizen(name="Elena Brightwater", age=32, occupation="Healer", city_id="city1"),
            Citizen(name="Marcus Ironforge", age=28, occupation="Guard", city_id="city1"),
        ]
        
        citizens_stormhaven = [
            Citizen(name="Gareth Stormwind", age=52, occupation="Captain", city_id="city2"),
            Citizen(name="Aria Moonwhisper", age=29, occupation="Scholar", city_id="city2"),
        ]
        
        # Create sample slaves and livestock
        slaves_emberfalls = [
            Slave(name="Keth", age=25, origin="Captured Orc", occupation="Laborer", 
                  owner="City", purchase_price=50, city_id="city1"),
        ]
        
        livestock_emberfalls = [
            Livestock(name="Thunder", type="Horse", age=5, weight=1200, value=300, city_id="city1"),
            Livestock(name="Bessie", type="Cattle", age=3, weight=800, value=150, city_id="city1"),
        ]
        
        garrison_emberfalls = [
            Soldier(name="Captain Steel", rank="Captain", age=35, years_of_service=10, 
                   equipment=["Sword", "Shield", "Chain Mail"], city_id="city1"),
            Soldier(name="Corporal Brown", rank="Corporal", age=28, years_of_service=5,
                   equipment=["Crossbow", "Leather Armor"], city_id="city1"),
        ]
        
        cities = [
            City(
                id="city1",
                name="Emberfalls",
                governor="Lord Aldric Emberthane",
                government_officials=emberfalls_officials,
                population=len(citizens_emberfalls),
                treasury=2500,
                x_coordinate=45.2,
                y_coordinate=67.8,
                citizens=citizens_emberfalls,
                slaves=slaves_emberfalls,
                livestock=livestock_emberfalls,
                garrison=garrison_emberfalls
            ),
            City(
                id="city2", 
                name="Stormhaven",
                governor="Lady Vera Stormwind",
                government_officials=stormhaven_officials,
                population=len(citizens_stormhaven),
                treasury=1800,
                x_coordinate=72.1,
                y_coordinate=34.5,
                citizens=citizens_stormhaven,
                slaves=[],
                livestock=[],
                garrison=[]
            )
        ]
        
        kingdom = Kingdom(
            name="Faerûn Campaign",
            ruler="Dungeon Master",
            total_population=sum(city.population for city in cities),
            royal_treasury=5000,
            cities=cities
        )
        
        await db.kingdoms.insert_one(kingdom.dict())
        logging.info("Sample kingdom data initialized")

# Create the main app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_kingdom()
    task = asyncio.create_task(simulation_engine())
    yield
    # Shutdown
    task.cancel()

app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# Kingdom & City Management
@api_router.get("/kingdom")
async def get_kingdom():
    kingdom = await db.kingdoms.find_one()
    if kingdom:
        kingdom.pop('_id', None)
        return kingdom
    return {"error": "Kingdom not found"}

@api_router.put("/kingdom")
async def update_kingdom(name: str, ruler: str):
    result = await db.kingdoms.update_one(
        {},
        {"$set": {"name": name, "ruler": ruler}}
    )
    if result.modified_count:
        return {"message": "Kingdom updated successfully"}
    raise HTTPException(status_code=404, detail="Kingdom not found")

@api_router.post("/cities")
async def create_city(city: CityCreate):
    new_city = City(**city.dict())
    
    result = await db.kingdoms.update_one(
        {},
        {"$push": {"cities": new_city.dict()}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "city_created",
            "city": new_city.dict()
        })
        return new_city
    raise HTTPException(status_code=404, detail="Kingdom not found")

@api_router.get("/city/{city_id}")
async def get_city(city_id: str):
    kingdom = await db.kingdoms.find_one()
    if kingdom:
        for city in kingdom['cities']:
            if city['id'] == city_id:
                return city
    raise HTTPException(status_code=404, detail="City not found")

@api_router.put("/city/{city_id}")
async def update_city(city_id: str, updates: CityUpdate):
    update_data = {f"cities.$.{k}": v for k, v in updates.dict(exclude_unset=True).items()}
    
    result = await db.kingdoms.update_one(
        {"cities.id": city_id},
        {"$set": update_data}
    )
    
    if result.modified_count:
        return {"message": "City updated successfully"}
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/city/{city_id}")
async def delete_city(city_id: str):
    result = await db.kingdoms.update_one(
        {},
        {"$pull": {"cities": {"id": city_id}}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "city_deleted",
            "city_id": city_id
        })
        return {"message": "City deleted successfully"}
    raise HTTPException(status_code=404, detail="City not found")

# Auto-generation endpoints
@api_router.post("/auto-generate")
async def auto_generate_registry_items(request: AutoGenerateRequest):
    kingdom = await db.kingdoms.find_one()
    if not kingdom:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    
    city = None
    for c in kingdom['cities']:
        if c['id'] == request.city_id:
            city = c
            break
    
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    
    generated_items = []
    
    for _ in range(request.count):
        if request.registry_type == "citizens":
            new_citizen_data = generate_citizen(request.city_id)
            new_citizen = Citizen(**new_citizen_data)
            
            result = await db.kingdoms.update_one(
                {"cities.id": request.city_id},
                {
                    "$push": {"cities.$.citizens": new_citizen.dict()},
                    "$inc": {"cities.$.population": 1, "total_population": 1}
                }
            )
            
            if result.modified_count:
                generated_items.append(new_citizen.dict())
                event_desc = generate_registry_event("citizen", city['name'], new_citizen_data)
                await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "manual-generate")
        
        elif request.registry_type == "slaves":
            new_slave_data = generate_slave(request.city_id)
            new_slave = Slave(**new_slave_data)
            
            result = await db.kingdoms.update_one(
                {"cities.id": request.city_id},
                {"$push": {"cities.$.slaves": new_slave.dict()}}
            )
            
            if result.modified_count:
                generated_items.append(new_slave.dict())
                event_desc = generate_registry_event("slave", city['name'], new_slave_data)
                await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "manual-generate")
        
        elif request.registry_type == "livestock":
            new_livestock_data = generate_livestock(request.city_id)
            new_livestock = Livestock(**new_livestock_data)
            
            result = await db.kingdoms.update_one(
                {"cities.id": request.city_id},
                {"$push": {"cities.$.livestock": new_livestock.dict()}}
            )
            
            if result.modified_count:
                generated_items.append(new_livestock.dict())
                event_desc = generate_registry_event("livestock", city['name'], new_livestock_data)
                await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "manual-generate")
        
        elif request.registry_type == "garrison":
            new_soldier_data = generate_soldier(request.city_id)
            new_soldier = Soldier(**new_soldier_data)
            
            result = await db.kingdoms.update_one(
                {"cities.id": request.city_id},
                {"$push": {"cities.$.garrison": new_soldier.dict()}}
            )
            
            if result.modified_count:
                generated_items.append(new_soldier.dict())
                event_desc = generate_registry_event("soldier", city['name'], new_soldier_data)
                await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "manual-generate")
        
        elif request.registry_type == "crimes":
            new_crime_data = generate_crime(request.city_id, city['name'])
            new_crime = CrimeRecord(**new_crime_data)
            
            result = await db.kingdoms.update_one(
                {"cities.id": request.city_id},
                {"$push": {"cities.$.crime_records": new_crime.dict()}}
            )
            
            if result.modified_count:
                generated_items.append(new_crime.dict())
                event_desc = generate_registry_event("crime", city['name'], new_crime_data)
                await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "manual-generate")
        
        elif request.registry_type == "tribute":
            new_tribute_data = generate_tribute(city['name'])
            new_tribute = TributeRecord(**new_tribute_data)
            
            result = await db.kingdoms.update_one(
                {"cities.id": request.city_id},
                {"$push": {"cities.$.tribute_records": new_tribute.dict()}}
            )
            
            if result.modified_count:
                generated_items.append(new_tribute.dict())
                event_desc = generate_registry_event("tribute", city['name'], new_tribute_data)
                await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "manual-generate")
    
    return {"generated_items": generated_items, "count": len(generated_items)}

# Get crime types and punishments
@api_router.get("/crime-types")
async def get_crime_types():
    return {
        "crime_types": list(CRIME_TYPES_DETAILED.keys()),
        "crime_details": CRIME_TYPES_DETAILED
    }

# Citizens Management
@api_router.post("/citizens")
async def create_citizen(citizen: CitizenCreate):
    new_citizen = Citizen(**citizen.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": citizen.city_id},
        {
            "$push": {"cities.$.citizens": new_citizen.dict()},
            "$inc": {"cities.$.population": 1, "total_population": 1}
        }
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "citizen_added",
            "citizen": new_citizen.dict()
        })
        return new_citizen
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/citizens/{citizen_id}")
async def delete_citizen(citizen_id: str):
    result = await db.kingdoms.update_one(
        {"cities.citizens.id": citizen_id},
        {
            "$pull": {"cities.$.citizens": {"id": citizen_id}},
            "$inc": {"cities.$.population": -1, "total_population": -1}
        }
    )
    
    if result.modified_count:
        return {"message": "Citizen deleted successfully"}
    raise HTTPException(status_code=404, detail="Citizen not found")

# Slaves Management
@api_router.post("/slaves")
async def create_slave(slave: SlaveCreate):
    new_slave = Slave(**slave.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": slave.city_id},
        {"$push": {"cities.$.slaves": new_slave.dict()}}
    )
    
    if result.modified_count:
        return new_slave
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/slaves/{slave_id}")
async def delete_slave(slave_id: str):
    result = await db.kingdoms.update_one(
        {"cities.slaves.id": slave_id},
        {"$pull": {"cities.$.slaves": {"id": slave_id}}}
    )
    
    if result.modified_count:
        return {"message": "Slave deleted successfully"}
    raise HTTPException(status_code=404, detail="Slave not found")

# Livestock Management
@api_router.post("/livestock")
async def create_livestock(livestock: LivestockCreate):
    new_livestock = Livestock(**livestock.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": livestock.city_id},
        {"$push": {"cities.$.livestock": new_livestock.dict()}}
    )
    
    if result.modified_count:
        return new_livestock
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/livestock/{livestock_id}")
async def delete_livestock(livestock_id: str):
    result = await db.kingdoms.update_one(
        {"cities.livestock.id": livestock_id},
        {"$pull": {"cities.$.livestock": {"id": livestock_id}}}
    )
    
    if result.modified_count:
        return {"message": "Livestock deleted successfully"}
    raise HTTPException(status_code=404, detail="Livestock not found")

# Military/Garrison Management
@api_router.post("/soldiers")
async def create_soldier(soldier: SoldierCreate):
    new_soldier = Soldier(**soldier.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": soldier.city_id},
        {"$push": {"cities.$.garrison": new_soldier.dict()}}
    )
    
    if result.modified_count:
        return new_soldier
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/soldiers/{soldier_id}")
async def delete_soldier(soldier_id: str):
    result = await db.kingdoms.update_one(
        {"cities.garrison.id": soldier_id},
        {"$pull": {"cities.$.garrison": {"id": soldier_id}}}
    )
    
    if result.modified_count:
        return {"message": "Soldier deleted successfully"}
    raise HTTPException(status_code=404, detail="Soldier not found")

# Tribute Management
@api_router.post("/tribute")
async def create_tribute(tribute: TributeCreate):
    new_tribute = TributeRecord(**tribute.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.name": tribute.from_city},
        {"$push": {"cities.$.tribute_records": new_tribute.dict()}}
    )
    
    if result.modified_count:
        return new_tribute
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/tribute/{tribute_id}")
async def delete_tribute(tribute_id: str):
    result = await db.kingdoms.update_one(
        {"cities.tribute_records.id": tribute_id},
        {"$pull": {"cities.$.tribute_records": {"id": tribute_id}}}
    )
    
    if result.modified_count:
        return {"message": "Tribute record deleted successfully"}
    raise HTTPException(status_code=404, detail="Tribute record not found")

# Crime Management
@api_router.post("/crimes")
async def create_crime(crime: CrimeCreate):
    new_crime = CrimeRecord(**crime.dict())
    
    result = await db.kingdoms.update_one(
        {"cities.id": crime.city_id},
        {"$push": {"cities.$.crime_records": new_crime.dict()}}
    )
    
    if result.modified_count:
        return new_crime
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/crimes/{crime_id}")
async def delete_crime(crime_id: str):
    result = await db.kingdoms.update_one(
        {"cities.crime_records.id": crime_id},
        {"$pull": {"cities.$.crime_records": {"id": crime_id}}}
    )
    
    if result.modified_count:
        return {"message": "Crime record deleted successfully"}
    raise HTTPException(status_code=404, detail="Crime record not found")

# Events Management
@api_router.get("/events")
async def get_recent_events(limit: int = 20):
    events = await db.events.find().sort("timestamp", -1).limit(limit).to_list(limit)
    for event in events:
        event.pop('_id', None)
    return events

@api_router.post("/events")
async def create_manual_event(event: EventCreate):
    kingdom = await db.kingdoms.find_one()
    kingdom_name = kingdom['name'] if kingdom else "Unknown Kingdom"
    
    new_event = Event(
        description=event.description,
        city_name=event.city_name,
        kingdom_name=kingdom_name,
        event_type="manual"
    )
    
    await db.events.insert_one(new_event.dict())
    
    await manager.broadcast({
        "type": "new_event",
        "event": new_event.dict()
    })
    
    return new_event

@api_router.post("/toggle-auto-events")
async def toggle_auto_events():
    global auto_events_enabled
    auto_events_enabled = not auto_events_enabled
    return {"auto_events_enabled": auto_events_enabled}

@api_router.get("/auto-events-status")
async def get_auto_events_status():
    return {"auto_events_enabled": auto_events_enabled}

@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()