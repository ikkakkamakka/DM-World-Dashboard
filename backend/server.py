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

# Import authentication router
from auth import auth_router

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

# Enhanced Harptos Calendar System for D&D fantasy setting
HARPTOS_MONTHS = [
    {"name": "Hammer", "alias": "Deepwinter", "days": 30},
    {"name": "Alturiak", "alias": "The Claw of Winter", "days": 30},
    {"name": "Ches", "alias": "The Claw of the Sunsets", "days": 30},
    {"name": "Tarsakh", "alias": "The Claw of the Storms", "days": 30},
    {"name": "Mirtul", "alias": "The Melting", "days": 30},
    {"name": "Kythorn", "alias": "The Time of Flowers", "days": 30},
    {"name": "Flamerule", "alias": "Summertide", "days": 30},
    {"name": "Eleasis", "alias": "Highsun", "days": 30},
    {"name": "Eleint", "alias": "The Fading", "days": 30},
    {"name": "Marpenoth", "alias": "Leaffall", "days": 30},
    {"name": "Uktar", "alias": "The Rotting", "days": 30},
    {"name": "Nightal", "alias": "The Drawing Down", "days": 30}
]

SPECIAL_DAYS = [
    {"name": "Midwinter", "after_month": 0, "description": "A festival day of reflection and celebration", "type": "holiday"},
    {"name": "Greengrass", "after_month": 3, "description": "Celebrates the arrival of spring", "type": "holiday"},
    {"name": "Midsummer", "after_month": 6, "description": "A day of celebration and festivity", "type": "holiday"},
    {"name": "Highharvestide", "after_month": 8, "description": "Marks the harvest time", "type": "holiday"},
    {"name": "The Feast of the Moon", "after_month": 10, "description": "Honors the dead and ancestors", "type": "holiday"}
]

# City-specific events templates
CITY_EVENT_TEMPLATES = [
    {"title": "Market Day", "type": "city", "description": "The monthly market brings traders from across the region"},
    {"title": "Harvest Festival", "type": "city", "description": "Citizens celebrate the season's harvest"},
    {"title": "Guard Patrol", "type": "city", "description": "City watch conducts extra patrols"},
    {"title": "Merchant Caravan Arrival", "type": "city", "description": "A trading caravan has arrived with exotic goods"},
    {"title": "Temple Festival", "type": "city", "description": "Local temple holds a religious celebration"},
    {"title": "Craftsmen's Fair", "type": "city", "description": "Artisans display their finest works"},
    {"title": "Bard's Performance", "type": "city", "description": "Traveling bards perform in the town square"},
    {"title": "Local Wedding", "type": "city", "description": "Citizens gather to celebrate a wedding"},
    {"title": "Seasonal Cleaning", "type": "city", "description": "Community effort to clean and maintain the city"},
    {"title": "Youth Tournament", "type": "city", "description": "Young citizens compete in friendly contests"}
]

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

# Enhanced notification templates
NOTIFICATION_TEMPLATES = {
    "citizen_birth": [
        "🍼 A child is born to the {family} family in {city}. The midwives declare the babe healthy and strong.",
        "🎉 {city} celebrates the birth of a new citizen to {family}. May the child grow wise and prosperous.",
        "👶 The {family} household welcomes a new member in {city}. The local cleric blesses the child."
    ],
    "citizen_death": [
        "⚰️ {name}, beloved {occupation} of {city}, has passed away at age {age}. The city mourns their loss.",
        "🕯️ {city} grieves as {name} joins their ancestors. Their work as {occupation} will be remembered.",
        "💀 Death has claimed {name} in {city}. The {occupation} lived {age} years and served the city well."
    ],
    "trade_caravan": [
        "🚚 A merchant caravan arrives in {city} bearing exotic goods from distant lands.",
        "💰 Traders from across the realm converge on {city}'s marketplace. Business is booming!",
        "🏪 New trading opportunities arise as merchants establish trade routes through {city}."
    ],
    "festival": [
        "🎪 A grand festival begins in {city}! Citizens feast, dance, and celebrate until dawn.",
        "🎭 The streets of {city} come alive with performers, musicians, and revelry.",
        "🍻 {city} hosts a harvest festival. Ale flows freely and spirits are high!"
    ],
    "weather": [
        "🌧️ Heavy rains bless the crops around {city}. Farmers expect a bountiful harvest.",
        "☀️ Glorious sunshine bathes {city}. Perfect weather for trade and travel.",
        "❄️ A harsh winter settles over {city}. Citizens huddle by their fires.",
        "🌪️ Wild storms rage near {city}. Ships seek shelter in the harbor."
    ],
    "magic": [
        "✨ Strange magical energies are reported near {city}. Wizards investigate the phenomenon.",
        "🔮 A new ley line is discovered running through {city}. Magic users sense the power.",
        "⚡ Arcane disturbances trouble the air around {city}. The Court Wizard takes precautions."
    ],
    "military": [
        "⚔️ The garrison of {city} conducts training exercises. The sound of clashing steel echoes.",
        "🛡️ New recruits join {city}'s military forces. The Captain inspects the fresh soldiers.",
        "🏹 Archery competitions are held in {city}. The best marksmen are rewarded."
    ],
    "economy": [
        "💎 A valuable ore deposit is discovered near {city}. Mining operations begin immediately.",
        "🌾 Record grain prices boost {city}'s economy. Merchants flock to the markets.",
        "🐄 Livestock auctions in {city} draw buyers from neighboring settlements."
    ]
}

def generate_enhanced_event(kingdom_data):
    """Generate immersive fantasy events with variety"""
    cities = kingdom_data.get('cities', [])
    if not cities:
        return "The kingdom rests in peaceful silence..."
    
    city = random.choice(cities)
    city_name = city['name']
    
    # Choose event category
    event_category = random.choice(list(NOTIFICATION_TEMPLATES.keys()))
    template = random.choice(NOTIFICATION_TEMPLATES[event_category])
    
    # Fill in template based on category
    if event_category == "citizen_birth":
        family_name = random.choice(FANTASY_LAST_NAMES)
        return template.format(family=family_name, city=city_name)
    
    elif event_category == "citizen_death" and city.get('citizens'):
        citizen = random.choice(city['citizens'])
        return template.format(
            name=citizen['name'],
            occupation=citizen['occupation'],
            age=citizen['age'],
            city=city_name
        )
    
    else:
        return template.format(city=city_name)

# Auto-generation functions (FIXED)
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

# FIXED Event generation for auto-generated content
def generate_registry_event(event_type, city_name, details):
    try:
        events_map = {
            "citizen": [
                f"🧑 {details.get('name', 'Unknown')} ({details.get('age', 0)} yrs, {details.get('occupation', 'Worker')}) joins {city_name}.",
                f"👤 New citizen {details.get('name', 'Unknown')} registers in {city_name} as a {details.get('occupation', 'Worker')}.",
                f"🏠 {details.get('name', 'Unknown')} arrives in {city_name} seeking work as a {details.get('occupation', 'Worker')}."
            ],
            "slave": [
                f"⛓️ New slave {details.get('name', 'Unknown')} acquired in {city_name} ({details.get('origin', 'Unknown origin')}).",
                f"👥 {details.get('name', 'Unknown')}, a {details.get('origin', 'slave')}, becomes enslaved in {city_name}.",
                f"🏭 Slave {details.get('name', 'Unknown')} assigned to {details.get('owner', 'City')} in {city_name}."
            ],
            "livestock": [
                f"🐄 New {details.get('type', 'animal').lower()} '{details.get('name', 'Unknown')}' added to {city_name} herds.",
                f"💰 {details.get('name', 'Unknown')} the {details.get('type', 'animal')} purchased for {details.get('value', 0)} GP in {city_name}.",
                f"📝 Livestock registry updated: {details.get('name', 'Unknown')} ({details.get('type', 'animal')}) in {city_name}."
            ],
            "soldier": [
                f"⚔️ {details.get('name', 'Unknown')} enlists as {details.get('rank', 'Recruit')} in {city_name} garrison.",
                f"🛡️ New recruit {details.get('name', 'Unknown')} joins {city_name}'s military forces.",
                f"👨‍✈️ {details.get('rank', 'Recruit')} {details.get('name', 'Unknown')} reports for duty in {city_name}."
            ],
            "crime": [
                f"🚨 {details.get('criminal_name', 'Unknown')} accused of {details.get('crime_type', 'unknown crime')} in {city_name}.",
                f"⚖️ Crime reported: {details.get('crime_type', 'unknown crime')} by {details.get('criminal_name', 'Unknown')} in {city_name}.",
                f"🕵️ {city_name} authorities investigate {details.get('criminal_name', 'Unknown')} for {details.get('crime_type', 'unknown crime')}."
            ],
            "tribute": [
                f"💎 {details.get('from_city', 'Unknown City')} owes {details.get('amount', 0)} GP tribute for {details.get('purpose', 'royal decree')}.",
                f"📜 Tribute demand: {details.get('from_city', 'Unknown City')} to pay {details.get('amount', 0)} GP to {details.get('to_city', 'Royal Treasury')}.",
                f"💰 {details.get('from_city', 'Unknown City')} tribute payment of {details.get('amount', 0)} GP is {details.get('status', 'pending').lower()}."
            ]
        }
        return random.choice(events_map.get(event_type, [f"📋 Registry updated in {city_name}."]))
    except Exception as e:
        logging.error(f"Error generating registry event: {e}")
        return f"📋 Registry updated in {city_name}."

class Citizen(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    occupation: str
    city_id: str
    health: str = "Healthy"
    notes: str = ""
    government_position: Optional[str] = None
    appointed_date: Optional[datetime] = None
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
    citizen_id: Optional[str] = None  # Link to citizen

class GovernmentAppointment(BaseModel):
    citizen_id: str
    position: str

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
    government_type: str = "Monarchy"
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
    priority: str = "normal"  # low, normal, high, critical

class EventCreate(BaseModel):
    description: str
    city_name: str
    event_type: str = "manual"
    priority: str = "normal"

class AutoGenerateRequest(BaseModel):
    registry_type: str  # "citizens", "slaves", "livestock", "garrison", "crimes", "tribute"
    city_id: str
    count: int = 1

# Enhanced Data Models for Multiple Kingdoms

class KingdomBoundary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kingdom_id: str
    boundary_points: List[dict] = []  # Array of {x: float, y: float} coordinates
    color: str = "#1e3a8a"  # Default blue
    created_at: datetime = Field(default_factory=datetime.utcnow)

class KingdomBoundaryCreate(BaseModel):
    kingdom_id: str
    boundary_points: List[dict]
    color: str = "#1e3a8a"

class MultiKingdom(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    ruler: str
    government_type: str = "Monarchy"
    color: str = "#1e3a8a"  # Kingdom's primary color
    total_population: int = 0
    royal_treasury: int = 5000
    cities: List[City] = []
    boundaries: List[KingdomBoundary] = []
    is_active: bool = True  # Whether this kingdom is currently being managed
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MultiKingdomCreate(BaseModel):
    name: str
    ruler: str
    government_type: str = "Monarchy"
    color: str = "#1e3a8a"

class MultiKingdomUpdate(BaseModel):
    name: Optional[str] = None
    ruler: Optional[str] = None
    government_type: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

# Enhanced simulation engine with real database impacts
async def simulation_engine():
    """Enhanced simulation engine that generates events with real database consequences for all active kingdoms"""
    await asyncio.sleep(5)  # Initial delay
    
    while True:
        try:
            # Get all kingdoms from multi_kingdoms collection
            kingdoms = await db.multi_kingdoms.find().to_list(None)
            
            if not kingdoms:
                await asyncio.sleep(30)
                continue
            
            for kingdom_data in kingdoms:
                if not kingdom_data.get('cities'):
                    continue
                
                # Life Events with Real Database Impact (new feature)
                if random.random() < 0.15:  # 15% chance for life events that actually change the kingdom
                    await generate_life_event_with_database_impact(kingdom_data)
                
                # Regular descriptive events (existing functionality)
                if random.random() < 0.3:  # 30% chance per cycle per kingdom
                    city = random.choice(kingdom_data['cities'])
                    
                    # Generate different types of events
                    event_types = [
                        lambda: f"🏰 A merchant caravan arrives in {city['name']}, bringing exotic goods and news from distant lands",
                        lambda: f"⚔️ The guards of {city['name']} successfully repel a group of bandits attempting to raid the city",
                        lambda: f"🎭 A traveling bard performs in {city['name']}'s town square, entertaining citizens with tales of heroic deeds",
                        lambda: f"🌾 The farmers near {city['name']} report an exceptionally good harvest this season",
                        lambda: f"🔥 A small fire breaks out in {city['name']} but is quickly contained by alert citizens",
                        lambda: f"👑 A noble from {city['name']} announces their engagement, causing much celebration",
                        lambda: f"⚡ A powerful storm passes over {city['name']}, but the city's defenses hold strong",
                        lambda: f"📜 New trade agreements are signed in {city['name']}, boosting the local economy",
                        lambda: f"🦅 Scouts from {city['name']} report unusual creature movements in the nearby wilderness",
                        lambda: f"💰 A hidden cache of ancient coins is discovered during construction work in {city['name']}"
                    ]
                    
                    event_description = random.choice(event_types)()
                    
                    # Create and broadcast kingdom-specific event
                    await create_and_broadcast_event(
                        event_description, 
                        city['name'], 
                        kingdom_data['name'], 
                        "auto",
                        kingdom_id=kingdom_data['id']
                    )
                
                # Auto-generate registry items occasionally for this kingdom
                if random.random() < 0.2:  # 20% chance per cycle per kingdom
                    city = random.choice(kingdom_data['cities'])
                    registry_types = ["citizens", "slaves", "livestock", "crimes", "soldiers", "tribute"]
                    registry_type = random.choice(registry_types)
                    
                    try:
                        if registry_type == "citizens":
                            new_citizen_data = generate_citizen(city['id'])
                            new_citizen = Citizen(**new_citizen_data)
                            
                            # Update the kingdom in multi_kingdoms collection
                            result = await db.multi_kingdoms.update_one(
                                {"id": kingdom_data['id'], "cities.id": city['id']},
                                {
                                    "$push": {"cities.$.citizens": new_citizen.dict()},
                                    "$inc": {"cities.$.population": 1, "total_population": 1}
                                }
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("citizen", city['name'], new_citizen_data)
                                await create_and_broadcast_event(
                                    event_desc, city['name'], kingdom_data['name'], "auto-registry",
                                    kingdom_id=kingdom_data['id']
                                )
                        
                        elif registry_type == "slaves":
                            new_slave_data = generate_slave(city['id'])
                            new_slave = Slave(**new_slave_data)
                            
                            result = await db.multi_kingdoms.update_one(
                                {"id": kingdom_data['id'], "cities.id": city['id']},
                                {"$push": {"cities.$.slaves": new_slave.dict()}}
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("slave", city['name'], new_slave_data)
                                await create_and_broadcast_event(
                                    event_desc, city['name'], kingdom_data['name'], "auto-registry",
                                    kingdom_id=kingdom_data['id']
                                )
                        
                        elif registry_type == "livestock":
                            new_livestock_data = generate_livestock(city['id'])
                            new_livestock = Livestock(**new_livestock_data)
                            
                            result = await db.multi_kingdoms.update_one(
                                {"id": kingdom_data['id'], "cities.id": city['id']},
                                {"$push": {"cities.$.livestock": new_livestock.dict()}}
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("livestock", city['name'], new_livestock_data)
                                await create_and_broadcast_event(
                                    event_desc, city['name'], kingdom_data['name'], "auto-registry",
                                    kingdom_id=kingdom_data['id']
                                )
                        
                        elif registry_type == "crimes":
                            new_crime_data = generate_crime(city['id'], city['name'])
                            new_crime = CrimeRecord(**new_crime_data)
                            
                            result = await db.multi_kingdoms.update_one(
                                {"id": kingdom_data['id'], "cities.id": city['id']},
                                {"$push": {"cities.$.crime_records": new_crime.dict()}}
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("crime", city['name'], new_crime_data)
                                await create_and_broadcast_event(
                                    event_desc, city['name'], kingdom_data['name'], "auto-registry",
                                    kingdom_id=kingdom_data['id']
                                )
                        
                        elif registry_type == "soldiers":
                            new_soldier_data = generate_soldier(city['id'])
                            new_soldier = Soldier(**new_soldier_data)
                            
                            result = await db.multi_kingdoms.update_one(
                                {"id": kingdom_data['id'], "cities.id": city['id']},
                                {"$push": {"cities.$.garrison": new_soldier.dict()}}
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("soldier", city['name'], new_soldier_data)
                                await create_and_broadcast_event(
                                    event_desc, city['name'], kingdom_data['name'], "auto-registry",
                                    kingdom_id=kingdom_data['id']
                                )
                        
                        elif registry_type == "tribute":
                            new_tribute_data = generate_tribute(city['name'])
                            new_tribute = TributeRecord(**new_tribute_data)
                            
                            result = await db.multi_kingdoms.update_one(
                                {"id": kingdom_data['id'], "cities.id": city['id']},
                                {"$push": {"cities.$.tribute_records": new_tribute.dict()}}
                            )
                            
                            if result.modified_count:
                                event_desc = generate_registry_event("tribute", city['name'], new_tribute_data)
                                await create_and_broadcast_event(
                                    event_desc, city['name'], kingdom_data['name'], "auto-registry",
                                    kingdom_id=kingdom_data['id']
                                )
                        
                    except Exception as e:
                        logging.error(f"Auto-generation error for {registry_type} in kingdom {kingdom_data['name']}: {e}")
            
            await asyncio.sleep(random.randint(15, 45))  # 15-45 seconds between cycles
            
        except Exception as e:
            logging.error(f"Simulation error: {e}")
            await asyncio.sleep(30)

async def generate_life_event_with_database_impact(kingdom_data):
    """Generate life events that actually modify the database and update dashboard counts"""
    try:
        city = random.choice(kingdom_data['cities'])
        
        # Types of life events that affect the database
        life_event_types = [
            'citizen_death',
            'citizen_birth', 
            'crime_resolution',
            'economic_boost',
            'disease_outbreak',
            'natural_disaster'
        ]
        
        event_type = random.choice(life_event_types)
        
        if event_type == 'citizen_death' and city.get('citizens') and len(city['citizens']) > 0:
            await handle_citizen_death_event(kingdom_data, city)
            
        elif event_type == 'citizen_birth':
            await handle_citizen_birth_event(kingdom_data, city)
            
        elif event_type == 'crime_resolution' and city.get('crime_records') and len(city['crime_records']) > 0:
            await handle_crime_resolution_event(kingdom_data, city)
            
        elif event_type == 'economic_boost':
            await handle_economic_boost_event(kingdom_data, city)
            
        elif event_type == 'disease_outbreak' and city.get('citizens') and len(city['citizens']) > 2:
            await handle_disease_outbreak_event(kingdom_data, city)
            
        elif event_type == 'natural_disaster':
            await handle_natural_disaster_event(kingdom_data, city)
    
    except Exception as e:
        logging.error(f"Life event generation error: {e}")

async def handle_citizen_death_event(kingdom_data, city):
    """Handle citizen death - actually remove from database and update counts"""
    if not city.get('citizens') or len(city['citizens']) == 0:
        return
        
    # Choose a random citizen to die
    citizen_to_remove = random.choice(city['citizens'])
    
    # Remove citizen from database
    result = await db.multi_kingdoms.update_one(
        {"id": kingdom_data['id'], "cities.id": city['id']},
        {
            "$pull": {"cities.$.citizens": {"id": citizen_to_remove['id']}},
            "$inc": {"cities.$.population": -1, "total_population": -1}
        }
    )
    
    if result.modified_count:
        # Create death event with actual impact
        death_causes = [
            "died peacefully in their sleep",
            "succumbed to a sudden illness", 
            "was killed in a farming accident",
            "died defending the city from bandits",
            "passed away from old age",
            "was struck by lightning during a storm",
            "fell from scaffolding during construction work"
        ]
        
        cause = random.choice(death_causes)
        event_desc = f"💀 {citizen_to_remove['name']}, beloved {citizen_to_remove['occupation']} of {city['name']}, has {cause}. Population decreased by 1."
        
        await create_and_broadcast_event(
            event_desc, city['name'], kingdom_data['name'], "life-event", 
            priority="high", kingdom_id=kingdom_data['id']
        )
        
        # Broadcast updated kingdom data for real-time dashboard updates
        await broadcast_kingdom_update(kingdom_data, "citizen_death")

async def handle_citizen_birth_event(kingdom_data, city):
    """Handle citizen birth - actually add to database and update counts"""
    # Generate new citizen
    new_citizen_data = generate_citizen(city['id'])
    new_citizen = Citizen(**new_citizen_data)
    
    # Add citizen to database
    result = await db.multi_kingdoms.update_one(
        {"id": kingdom_data['id'], "cities.id": city['id']},
        {
            "$push": {"cities.$.citizens": new_citizen.dict()},
            "$inc": {"cities.$.population": 1, "total_population": 1}
        }
    )
    
    if result.modified_count:
        family_names = ["Brightwater", "Goldleaf", "Stormwind", "Ironforge", "Moonwhisper"]
        family_name = random.choice(family_names)
        
        event_desc = f"👶 A child is born to the {family_name} family in {city['name']}! {new_citizen.name} will grow to become a {new_citizen.occupation}. Population increased by 1."
        
        await create_and_broadcast_event(
            event_desc, city['name'], kingdom_data['name'], "life-event",
            priority="normal", kingdom_id=kingdom_data['id']
        )
        
        # Broadcast updated kingdom data for real-time dashboard updates
        await broadcast_kingdom_update(kingdom_data, "citizen_birth")

async def handle_crime_resolution_event(kingdom_data, city):
    """Handle crime resolution - update crime status and possibly affect population"""
    if not city.get('crime_records') or len(city['crime_records']) == 0:
        return
        
    # Find unresolved crimes
    unresolved_crimes = [crime for crime in city['crime_records'] if crime.get('status') != 'Resolved']
    if not unresolved_crimes:
        return
        
    crime_to_resolve = random.choice(unresolved_crimes)
    
    # Resolve the crime
    result = await db.multi_kingdoms.update_one(
        {"id": kingdom_data['id'], "cities.id": city['id'], "cities.crime_records.id": crime_to_resolve['id']},
        {
            "$set": {
                "cities.$.crime_records.$[crime].status": "Resolved",
                "cities.$.crime_records.$[crime].date_resolved": datetime.utcnow()
            }
        },
        array_filters=[{"crime.id": crime_to_resolve['id']}]
    )
    
    if result.modified_count:
        # Severe crimes may result in execution (population decrease)
        if crime_to_resolve.get('crime_type') in ['Murder', 'Treason', 'Necromancy']:
            # Execute the criminal (reduce population)
            population_change = await db.multi_kingdoms.update_one(
                {"id": kingdom_data['id'], "cities.id": city['id']},
                {"$inc": {"cities.$.population": -1, "total_population": -1}}
            )
            
            if population_change.modified_count:
                event_desc = f"⚖️ {crime_to_resolve['criminal_name']} has been executed for {crime_to_resolve['crime_type']} in {city['name']}. Justice served, population decreased by 1."
                
                await broadcast_kingdom_update(kingdom_data, "execution")
            else:
                event_desc = f"⚖️ The case of {crime_to_resolve['criminal_name']} for {crime_to_resolve['crime_type']} has been resolved in {city['name']}."
        else:
            event_desc = f"⚖️ The case of {crime_to_resolve['criminal_name']} for {crime_to_resolve['crime_type']} has been resolved in {city['name']}."
        
        await create_and_broadcast_event(
            event_desc, city['name'], kingdom_data['name'], "life-event",
            priority="normal", kingdom_id=kingdom_data['id']
        )

async def handle_economic_boost_event(kingdom_data, city):
    """Handle economic events that boost city treasury"""
    boost_amount = random.randint(50, 300)
    
    result = await db.multi_kingdoms.update_one(
        {"id": kingdom_data['id'], "cities.id": city['id']},
        {"$inc": {"cities.$.treasury": boost_amount}}
    )
    
    if result.modified_count:
        boost_reasons = [
            "successful trade negotiations",
            "discovery of valuable minerals",
            "excellent harvest season",
            "tax collection efficiency improvements",
            "merchant guild donations",
            "tourism revenue increase"
        ]
        
        reason = random.choice(boost_reasons)
        event_desc = f"💰 {city['name']} receives {boost_amount} GP from {reason}. City treasury grows!"
        
        await create_and_broadcast_event(
            event_desc, city['name'], kingdom_data['name'], "life-event",
            priority="normal", kingdom_id=kingdom_data['id']
        )
        
        await broadcast_kingdom_update(kingdom_data, "economic_boost")

async def handle_disease_outbreak_event(kingdom_data, city):
    """Handle disease outbreak - may affect population"""
    if not city.get('citizens') or len(city['citizens']) < 3:
        return
        
    # Disease severity determines impact
    severity = random.choice(['mild', 'moderate', 'severe'])
    
    if severity == 'severe':
        # Severe outbreak - remove 1-2 citizens
        deaths = min(random.randint(1, 2), len(city['citizens']))
        
        for _ in range(deaths):
            if city['citizens']:
                victim = random.choice(city['citizens'])
                
                # Remove citizen from database
                await db.multi_kingdoms.update_one(
                    {"id": kingdom_data['id'], "cities.id": city['id']},
                    {
                        "$pull": {"cities.$.citizens": {"id": victim['id']}},
                        "$inc": {"cities.$.population": -1, "total_population": -1}
                    }
                )
        
        event_desc = f"🦠 A severe plague outbreak in {city['name']} claims {deaths} lives. The city mourns its losses. Population decreased by {deaths}."
        priority = "high"
        
        await broadcast_kingdom_update(kingdom_data, "disease_outbreak")
        
    elif severity == 'moderate':
        # Moderate outbreak - no deaths but affects health
        event_desc = f"🤒 A moderate disease outbreak affects several citizens in {city['name']}. Healers work tirelessly to treat the afflicted."
        priority = "normal"
        
    else:
        # Mild outbreak - minor impact
        event_desc = f"🤧 A mild illness spreads through {city['name']}, but most citizens recover quickly with proper care."
        priority = "low"
    
    await create_and_broadcast_event(
        event_desc, city['name'], kingdom_data['name'], "life-event",
        priority=priority, kingdom_id=kingdom_data['id']
    )

async def handle_natural_disaster_event(kingdom_data, city):
    """Handle natural disasters that may affect treasury and population"""
    disasters = [
        {'name': 'earthquake', 'treasury_loss': (100, 500), 'population_risk': 0.3},
        {'name': 'flood', 'treasury_loss': (50, 300), 'population_risk': 0.2},
        {'name': 'wildfire', 'treasury_loss': (75, 400), 'population_risk': 0.4},
        {'name': 'severe storm', 'treasury_loss': (25, 200), 'population_risk': 0.1}
    ]
    
    disaster = random.choice(disasters)
    treasury_loss = random.randint(disaster['treasury_loss'][0], disaster['treasury_loss'][1])
    
    # Update treasury (ensure it doesn't go below 0)
    result = await db.multi_kingdoms.update_one(
        {"id": kingdom_data['id'], "cities.id": city['id']},
        {"$inc": {"cities.$.treasury": -treasury_loss}}
    )
    
    # Ensure treasury doesn't go negative
    await db.multi_kingdoms.update_one(
        {"id": kingdom_data['id'], "cities.id": city['id'], "cities.treasury": {"$lt": 0}},
        {"$set": {"cities.$.treasury": 0}}
    )
    
    event_parts = [f"🌪️ A {disaster['name']} strikes {city['name']}, causing {treasury_loss} GP in damages."]
    
    # Check for population impact
    if random.random() < disaster['population_risk'] and city.get('citizens') and len(city['citizens']) > 0:
        casualty = random.choice(city['citizens'])
        
        # Remove casualty from database
        casualty_result = await db.multi_kingdoms.update_one(
            {"id": kingdom_data['id'], "cities.id": city['id']},
            {
                "$pull": {"cities.$.citizens": {"id": casualty['id']}},
                "$inc": {"cities.$.population": -1, "total_population": -1}
            }
        )
        
        if casualty_result.modified_count:
            event_parts.append(f" Tragically, {casualty['name']} was lost in the disaster. Population decreased by 1.")
            await broadcast_kingdom_update(kingdom_data, "natural_disaster")
    
    event_desc = "".join(event_parts)
    
    await create_and_broadcast_event(
        event_desc, city['name'], kingdom_data['name'], "life-event",
        priority="high", kingdom_id=kingdom_data['id']
    )

async def broadcast_kingdom_update(kingdom_data, event_type):
    """Broadcast updated kingdom data for real-time dashboard updates"""
    try:
        # Fetch updated kingdom data from database
        updated_kingdom = await db.multi_kingdoms.find_one({"id": kingdom_data['id']})
        
        if updated_kingdom:
            # Broadcast the updated kingdom data to all connected clients
            await manager.broadcast({
                "type": "kingdom_update",
                "kingdom_id": kingdom_data['id'],
                "kingdom_data": updated_kingdom,
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        logging.error(f"Error broadcasting kingdom update: {e}")

async def create_and_broadcast_event(description, city_name, kingdom_name, event_type, priority="normal", kingdom_id=None):
    """Helper function to create and broadcast kingdom-specific events"""
    event = Event(
        description=description,
        city_name=city_name,
        kingdom_name=kingdom_name,
        event_type=event_type,
        priority=priority
    )
    
    # Add kingdom_id to event data if provided
    event_data = event.dict()
    if kingdom_id:
        event_data['kingdom_id'] = kingdom_id
    
    await db.events.insert_one(event_data)
    await manager.broadcast({
        "type": "new_event",
        "event": event_data,
        "kingdom_id": kingdom_id  # Include kingdom_id in broadcast for frontend filtering
    })

# Initialize multi-kingdom data and migrate existing data
async def initialize_multi_kingdoms():
    """Migrate existing kingdom data to multi-kingdom format"""
    existing_multi_kingdoms = await db.multi_kingdoms.find().to_list(100)
    
    if not existing_multi_kingdoms:
        # Check if legacy kingdom exists
        legacy_kingdom = await db.kingdoms.find_one()
        
        if legacy_kingdom:
            # Convert legacy kingdom to multi-kingdom format
            migrated_kingdom = MultiKingdom(
                name=legacy_kingdom.get('name', 'Legacy Kingdom'),
                ruler=legacy_kingdom.get('ruler', 'Unknown Ruler'),
                government_type=legacy_kingdom.get('government_type', 'Monarchy'),
                color='#1e3a8a',
                total_population=legacy_kingdom.get('total_population', 0),
                royal_treasury=legacy_kingdom.get('royal_treasury', 5000),
                cities=legacy_kingdom.get('cities', []),
                boundaries=[],
                is_active=True
            )
            
            await db.multi_kingdoms.insert_one(migrated_kingdom.dict())
            logging.info("Legacy kingdom migrated to multi-kingdom format")
        
        else:
            # Create default kingdom if none exists
            await initialize_kingdom()
            
            # Now migrate the newly created kingdom
            legacy_kingdom = await db.kingdoms.find_one()
            if legacy_kingdom:
                migrated_kingdom = MultiKingdom(
                    name=legacy_kingdom.get('name', 'Faerûn Campaign'),
                    ruler=legacy_kingdom.get('ruler', 'Dungeon Master'),
                    government_type=legacy_kingdom.get('government_type', 'Campaign'),
                    color='#1e3a8a',
                    total_population=legacy_kingdom.get('total_population', 0),
                    royal_treasury=legacy_kingdom.get('royal_treasury', 5000),
                    cities=legacy_kingdom.get('cities', []),
                    boundaries=[],
                    is_active=True
                )
                
                await db.multi_kingdoms.insert_one(migrated_kingdom.dict())
                logging.info("Default kingdom created and migrated to multi-kingdom format")
async def initialize_kingdom():
    """Create sample kingdom data if none exists"""
    existing_kingdom = await db.kingdoms.find_one()
    if not existing_kingdom:
        # Create government officials for cities
        emberfalls_officials = [
            GovernmentOfficial(name="Captain Marcus Steel", position="Captain of the Guard", city_id="city1"),
            GovernmentOfficial(name="Elena Goldleaf", position="Master of Coin", city_id="city1"),
            GovernmentOfficial(name="Sage Thorin", position="High Scribe", city_id="city1"),
            GovernmentOfficial(name="Wizard Aldara", position="Court Wizard", city_id="city1"),
            GovernmentOfficial(name="Brother Felix", position="Head Cleric", city_id="city1"),
            GovernmentOfficial(name="Merchant Gareth", position="Trade Minister", city_id="city1"),
            GovernmentOfficial(name="Collector Bran", position="Tax Collector", city_id="city1"),
            GovernmentOfficial(name="Warden Kira", position="Market Warden", city_id="city1"),
        ]
        
        stormhaven_officials = [
            GovernmentOfficial(name="Commander Vera", position="Captain of the Guard", city_id="city2"),
            GovernmentOfficial(name="Treasurer Orin", position="Master of Coin", city_id="city2"),
            GovernmentOfficial(name="Scholar Lyra", position="High Scribe", city_id="city2"),
            GovernmentOfficial(name="Magistrate Quinn", position="City Magistrate", city_id="city2"),
            GovernmentOfficial(name="Admiral Thane", position="Harbor Master", city_id="city2"),
            GovernmentOfficial(name="Builder Magnus", position="Master Builder", city_id="city2"),
        ]
        
        # Create sample citizens
        citizens_emberfalls = [
            Citizen(name="Thorin Emberthane", age=45, occupation="Blacksmith", city_id="city1"),
            Citizen(name="Elena Brightwater", age=32, occupation="Healer", city_id="city1"),
            Citizen(name="Marcus Ironforge", age=28, occupation="Guard", city_id="city1"),
            Citizen(name="Lydia Moonwhisper", age=35, occupation="Scholar", city_id="city1"),
            Citizen(name="Brom Stormcaller", age=41, occupation="Merchant", city_id="city1"),
        ]
        
        citizens_stormhaven = [
            Citizen(name="Gareth Stormwind", age=52, occupation="Captain", city_id="city2"),
            Citizen(name="Aria Moonwhisper", age=29, occupation="Scholar", city_id="city2"),
            Citizen(name="Finn Goldleaf", age=38, occupation="Baker", city_id="city2"),
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
            government_type="Campaign",
            total_population=sum(city.population for city in cities),
            royal_treasury=5000,
            cities=cities
        )
        
        await db.kingdoms.insert_one(kingdom.dict())
        logging.info("Sample kingdom data initialized")

# Enhanced Harptos Calendar System and Date Management
class CampaignDate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dr_year: int = 1492  # Dale Reckoning year
    month: int = 0  # 0-11 for months
    day: int = 1  # 1-30 for days
    tenday: int = 1  # 1-3 for tendays within month
    season: str = "winter"  # winter, spring, summer, autumn
    is_leap_year: bool = False
    special_day: Optional[str] = None  # Current special day if any
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = "system"

class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    event_type: str  # "holiday", "city", "custom"
    city_name: Optional[str] = None  # For city-specific events
    kingdom_id: str
    event_date: dict  # {dr_year: int, month: int, day: int}
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # "yearly", "monthly", etc.
    created_by: str = "DM"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class CampaignDateUpdate(BaseModel):
    dr_year: int
    month: int
    day: int
    updated_by: str = "DM"

class EventCreate(BaseModel):
    title: str
    description: str
    event_type: str = "custom"  # "holiday", "city", "custom"
    city_name: Optional[str] = None
    event_date: dict
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None

def calculate_tenday_and_season(month: int, day: int) -> tuple:
    """Calculate tenday (1-3) and season based on month and day"""
    tenday = min(3, ((day - 1) // 10) + 1)
    
    # Seasons based on Faerûn calendar
    if month in [11, 0, 1]:  # Nightal, Hammer, Alturiak
        season = "winter"
    elif month in [2, 3, 4]:  # Ches, Tarsakh, Mirtul
        season = "spring"
    elif month in [5, 6, 7]:  # Kythorn, Flamerule, Eleasis
        season = "summer"
    else:  # Eleint, Marpenoth, Uktar
        season = "autumn"
        
    return tenday, season

def is_leap_year(dr_year: int) -> bool:
    """Check if a DR year is a leap year (Shieldmeet occurs)"""
    return dr_year % 4 == 0

def convert_real_time_to_harptos() -> dict:
    """Convert real world time to Harptos calendar with proper DR math"""
    now = datetime.utcnow()
    
    # Base conversion: 1492 DR = 2020 AD (fixed reference point)
    DR_BASE_YEAR = 1492
    AD_BASE_YEAR = 2020
    
    # Calculate current DR year
    dr_year = DR_BASE_YEAR + (now.year - AD_BASE_YEAR)
    
    # Get day of year (1-365/366)
    day_of_year = now.timetuple().tm_yday
    
    # Account for leap year differences between real world and Harptos
    # Harptos has Shieldmeet every 4 years after Midsummer
    is_harptos_leap = is_leap_year(dr_year)
    
    # Convert day of year to Harptos month and day
    remaining_days = day_of_year - 1  # 0-indexed
    current_month = 0
    current_day = 1
    special_day = None
    
    for month_idx, month_data in enumerate(HARPTOS_MONTHS):
        month_days = month_data["days"]
        
        # Check for special day after this month
        special_after = next((sd for sd in SPECIAL_DAYS if sd["after_month"] == month_idx), None)
        
        if remaining_days < month_days:
            current_month = month_idx
            current_day = remaining_days + 1
            break
        
        remaining_days -= month_days
        
        # Account for special day if it exists
        if special_after:
            if remaining_days == 0:
                special_day = special_after["name"]
                break
            elif remaining_days > 0:
                remaining_days -= 1
    
    # Check for Shieldmeet (occurs after Midsummer in leap years)
    if is_harptos_leap and current_month == 6 and current_day == 30:
        # Check if we should be on Shieldmeet instead
        if day_of_year > 182:  # After theoretical Midsummer + Shieldmeet
            special_day = "Shieldmeet"
    
    tenday, season = calculate_tenday_and_season(current_month, current_day)
    
    return {
        "dr_year": dr_year,
        "month": current_month,
        "day": current_day,
        "tenday": tenday,
        "season": season,
        "month_name": HARPTOS_MONTHS[current_month]["name"],
        "month_alias": HARPTOS_MONTHS[current_month]["alias"],
        "special_day": special_day,
        "is_leap_year": is_harptos_leap,
        "real_time": now
    }

def format_harptos_date(date_obj: dict) -> str:
    """Format Harptos date into readable string"""
    if date_obj.get("special_day"):
        return f"{date_obj['special_day']}, {date_obj['dr_year']} DR"
    return f"{date_obj['day']} {date_obj['month_name']}, {date_obj['dr_year']} DR"
    
class VotingSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kingdom_id: str
    city_id: Optional[str] = None  # If city-specific voting
    title: str
    description: str
    options: List[str]
    start_date: dict  # {year: int, month: int, day: int}
    end_date: dict
    status: str = "active"  # active, completed, cancelled
    created_by: str = "DM"
    votes: Dict[str, str] = {}  # citizen_id -> option
    results: Optional[Dict[str, int]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VotingSessionCreate(BaseModel):
    city_id: Optional[str] = None
    title: str
    description: str
    options: List[str]
    start_date: dict
    end_date: dict

class CastVote(BaseModel):
    citizen_id: str
    option: str
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_multi_kingdoms()
    task = asyncio.create_task(simulation_engine())
    yield
    # Shutdown
    task.cancel()

app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# Multiple Kingdoms Management
@api_router.get("/multi-kingdoms")
async def get_all_kingdoms():
    """Get all kingdoms for selection interface"""
    kingdoms = await db.multi_kingdoms.find().to_list(100)
    for kingdom in kingdoms:
        kingdom.pop('_id', None)
    return kingdoms

@api_router.post("/multi-kingdoms")
async def create_multi_kingdom(kingdom: MultiKingdomCreate):
    """Create a new kingdom"""
    new_kingdom = MultiKingdom(**kingdom.dict())
    
    result = await db.multi_kingdoms.insert_one(new_kingdom.dict())
    if result.inserted_id:
        return new_kingdom
    raise HTTPException(status_code=500, detail="Failed to create kingdom")

@api_router.get("/multi-kingdom/{kingdom_id}")
async def get_multi_kingdom(kingdom_id: str):
    """Get specific kingdom data"""
    kingdom = await db.multi_kingdoms.find_one({"id": kingdom_id})
    if kingdom:
        kingdom.pop('_id', None)
        return kingdom
    raise HTTPException(status_code=404, detail="Kingdom not found")

@api_router.put("/multi-kingdom/{kingdom_id}")
async def update_multi_kingdom(kingdom_id: str, updates: MultiKingdomUpdate):
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items()}
    
    result = await db.multi_kingdoms.update_one(
        {"id": kingdom_id},
        {"$set": update_data}
    )
    
    if result.modified_count:
        return {"message": "Kingdom updated successfully"}
    raise HTTPException(status_code=404, detail="Kingdom not found")

@api_router.delete("/multi-kingdom/{kingdom_id}")
async def delete_multi_kingdom(kingdom_id: str):
    """Delete a kingdom and all its cities, government hierarchy, and related data"""
    # Find the kingdom to get its data before deletion
    kingdom = await db.multi_kingdoms.find_one({"id": kingdom_id})
    if not kingdom:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    
    # Delete related data in cascade
    try:
        # Delete kingdom boundaries
        await db.kingdom_boundaries.delete_many({"kingdom_id": kingdom_id})
        
        # Delete campaign dates
        await db.campaign_dates.delete_many({"kingdom_id": kingdom_id})
        
        # Delete calendar events
        await db.calendar_events.delete_many({"kingdom_id": kingdom_id})
        
        # Delete the kingdom itself
        result = await db.multi_kingdoms.delete_one({"id": kingdom_id})
        
        if result.deleted_count:
            # Broadcast kingdom deletion
            await manager.broadcast({
                "type": "kingdom_deleted",
                "kingdom_id": kingdom_id,
                "kingdom_name": kingdom.get('name', 'Unknown Kingdom')
            })
            
            return {
                "message": f"Kingdom '{kingdom.get('name', 'Unknown Kingdom')}' and all related data deleted successfully",
                "deleted_cities": len(kingdom.get('cities', [])),
                "deleted_boundaries": True,
                "deleted_calendar_data": True
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete kingdom")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting kingdom: {str(e)}")

@api_router.post("/multi-kingdom/{kingdom_id}/set-active")
async def set_active_kingdom(kingdom_id: str):
    """Set a kingdom as the active one and deactivate others"""
    # Deactivate all kingdoms
    await db.multi_kingdoms.update_many({}, {"$set": {"is_active": False}})
    
    # Activate the selected kingdom
    result = await db.multi_kingdoms.update_one(
        {"id": kingdom_id},
        {"$set": {"is_active": True}}
    )
    
    if result.modified_count:
        return {"message": "Kingdom set as active"}
    raise HTTPException(status_code=404, detail="Kingdom not found")

@api_router.get("/active-kingdom")
async def get_active_kingdom():
    """Get the currently active kingdom"""
    kingdom = await db.multi_kingdoms.find_one({"is_active": True})
    if kingdom:
        kingdom.pop('_id', None)
        return kingdom
    # Fallback to legacy kingdom for backward compatibility
    return await get_kingdom()

# Kingdom Boundaries Management
@api_router.post("/kingdom-boundaries")
async def create_kingdom_boundary(boundary: KingdomBoundaryCreate):
    """Create a new kingdom boundary"""
    new_boundary = KingdomBoundary(**boundary.dict())
    
    result = await db.kingdom_boundaries.insert_one(new_boundary.dict())
    if result.inserted_id:
        # Update the kingdom with this boundary
        await db.multi_kingdoms.update_one(
            {"id": boundary.kingdom_id},
            {"$push": {"boundaries": new_boundary.dict()}}
        )
        return new_boundary
    raise HTTPException(status_code=500, detail="Failed to create boundary")

@api_router.get("/kingdom-boundaries/{kingdom_id}")
async def get_kingdom_boundaries(kingdom_id: str):
    """Get all boundaries for a specific kingdom"""
    boundaries = await db.kingdom_boundaries.find({"kingdom_id": kingdom_id}).to_list(100)
    for boundary in boundaries:
        boundary.pop('_id', None)
    return boundaries

@api_router.delete("/kingdom-boundaries/{boundary_id}")
async def delete_kingdom_boundary(boundary_id: str):
    boundary = await db.kingdom_boundaries.find_one({"id": boundary_id})
    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary not found")
    
    # Remove from both collections
    await db.kingdom_boundaries.delete_one({"id": boundary_id})
    await db.multi_kingdoms.update_one(
        {"id": boundary["kingdom_id"]},
        {"$pull": {"boundaries": {"id": boundary_id}}}
    )
    
    return {"message": "Boundary deleted successfully"}

@api_router.put("/kingdom-boundaries/{boundary_id}")
async def update_kingdom_boundary(boundary_id: str, boundary_update: dict):
    """Update existing kingdom boundary with new points"""
    boundary = await db.kingdom_boundaries.find_one({"id": boundary_id})
    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary not found")
    
    # Update boundary points
    updated_boundary = {**boundary, "boundary_points": boundary_update["boundary_points"]}
    
    # Update in both collections
    await db.kingdom_boundaries.update_one(
        {"id": boundary_id},
        {"$set": {"boundary_points": boundary_update["boundary_points"]}}
    )
    
    await db.multi_kingdoms.update_one(
        {"id": boundary["kingdom_id"], "boundaries.id": boundary_id},
        {"$set": {"boundaries.$.boundary_points": boundary_update["boundary_points"]}}
    )
    
    return {"message": "Boundary updated successfully"}

@api_router.delete("/kingdom-boundaries/clear/{kingdom_id}")
async def clear_all_kingdom_boundaries(kingdom_id: str):
    """Clear all boundaries for a specific kingdom"""
    # Delete all boundaries for this kingdom from boundaries collection
    result = await db.kingdom_boundaries.delete_many({"kingdom_id": kingdom_id})
    
    # Remove all boundaries from the kingdom document
    await db.multi_kingdoms.update_one(
        {"id": kingdom_id},
        {"$set": {"boundaries": []}}
    )
    
    return {"message": f"Cleared {result.deleted_count} boundaries for kingdom {kingdom_id}"}

# Enhanced Harptos Calendar Management System
@api_router.get("/campaign-date/{kingdom_id}")
async def get_campaign_date(kingdom_id: str):
    """Get the current campaign date for a kingdom"""
    campaign_date = await db.campaign_dates.find_one({"kingdom_id": kingdom_id})
    
    if not campaign_date:
        # Initialize with current Harptos time if not exists
        harptos_now = convert_real_time_to_harptos()
        new_date = CampaignDate(
            kingdom_id=kingdom_id,
            dr_year=harptos_now["dr_year"],
            month=harptos_now["month"],
            day=harptos_now["day"],
            tenday=harptos_now["tenday"],
            season=harptos_now["season"],
            is_leap_year=harptos_now["is_leap_year"],
            special_day=harptos_now.get("special_day")
        )
        await db.campaign_dates.insert_one(new_date.dict())
        campaign_date = new_date.dict()
    else:
        campaign_date.pop('_id', None)
    
    return campaign_date

@api_router.put("/campaign-date/{kingdom_id}")
async def update_campaign_date(kingdom_id: str, date_update: CampaignDateUpdate):
    """Update/advance campaign date manually (DM control)"""
    tenday, season = calculate_tenday_and_season(date_update.month, date_update.day)
    is_leap = is_leap_year(date_update.dr_year)
    
    # Check for special days
    special_day = None
    for special in SPECIAL_DAYS:
        if special["after_month"] == date_update.month and date_update.day == 30:
            special_day = special["name"]
            break
    
    update_data = {
        "dr_year": date_update.dr_year,
        "month": date_update.month,
        "day": date_update.day,
        "tenday": tenday,
        "season": season,
        "is_leap_year": is_leap,
        "special_day": special_day,
        "last_updated": datetime.utcnow(),
        "updated_by": date_update.updated_by
    }
    
    result = await db.campaign_dates.update_one(
        {"kingdom_id": kingdom_id},
        {"$set": update_data},
        upsert=True
    )
    
    if result.upserted_id or result.modified_count:
        # Broadcast time change event
        formatted_date = f"{date_update.day} {HARPTOS_MONTHS[date_update.month]['name']}, {date_update.dr_year} DR"
        await create_and_broadcast_event(
            f"📅 DM advanced campaign time to {formatted_date}", 
            "Kingdom", 
            "Time", 
            "time-advance"
        )
        return {"message": "Campaign date updated successfully", "date": update_data}
    
    raise HTTPException(status_code=500, detail="Failed to update campaign date")

@api_router.get("/calendar-events/{kingdom_id}")
async def get_calendar_events(kingdom_id: str):
    """Get all calendar events for a kingdom"""
    events = await db.calendar_events.find({"kingdom_id": kingdom_id}).to_list(100)
    for event in events:
        event.pop('_id', None)
    return events

@api_router.get("/calendar-events/{kingdom_id}/upcoming")
async def get_upcoming_events(kingdom_id: str, days: int = 10):
    """Get upcoming events for the next N days"""
    # Get current campaign date
    campaign_date = await db.campaign_dates.find_one({"kingdom_id": kingdom_id})
    if not campaign_date:
        harptos_now = convert_real_time_to_harptos()
        current_dr_year = harptos_now["dr_year"]
        current_month = harptos_now["month"]
        current_day = harptos_now["day"]
    else:
        current_dr_year = campaign_date["dr_year"]
        current_month = campaign_date["month"]
        current_day = campaign_date["day"]
    
    # Calculate date range for upcoming events
    upcoming_events = []
    
    # Add holidays within range
    for i in range(days):
        check_day = current_day + i
        check_month = current_month
        check_year = current_dr_year
        
        # Handle month/year overflow
        while check_day > 30:
            check_day -= 30
            check_month += 1
            if check_month > 11:
                check_month = 0
                check_year += 1
        
        # Check for special days/holidays
        for special in SPECIAL_DAYS:
            if special["after_month"] == check_month and check_day == 30:
                upcoming_events.append({
                    "title": special["name"],
                    "description": special["description"],
                    "event_type": "holiday",
                    "city_name": None,
                    "event_date": {"dr_year": check_year, "month": check_month, "day": check_day},
                    "days_from_now": i
                })
    
    # Get custom events within date range
    events_query = {
        "kingdom_id": kingdom_id,
        "$or": [
            {
                "event_date.dr_year": current_dr_year,
                "event_date.month": current_month,
                "event_date.day": {"$gte": current_day, "$lte": current_day + days}
            },
            {
                "event_date.dr_year": current_dr_year,
                "event_date.month": {"$gt": current_month}
            },
            {
                "event_date.dr_year": {"$gt": current_dr_year}
            }
        ]
    }
    
    custom_events = await db.calendar_events.find(events_query).to_list(100)
    for event in custom_events:
        event.pop('_id', None)
        # Calculate days from now
        event_dr_year = event["event_date"]["dr_year"]
        event_month = event["event_date"]["month"]
        event_day = event["event_date"]["day"]
        
        # Simple calculation (can be enhanced for accuracy)
        days_diff = (event_dr_year - current_dr_year) * 365 + (event_month - current_month) * 30 + (event_day - current_day)
        event["days_from_now"] = max(0, days_diff)
        
        if event["days_from_now"] <= days:
            upcoming_events.append(event)
    
    return sorted(upcoming_events, key=lambda x: x["days_from_now"])

@api_router.post("/calendar-events")
async def create_calendar_event(event: EventCreate, kingdom_id: str):
    """Create a new calendar event"""
    new_event = CalendarEvent(**event.dict(), kingdom_id=kingdom_id)
    
    result = await db.calendar_events.insert_one(new_event.dict())
    if result.inserted_id:
        # Create a kingdom event for this calendar event
        formatted_date = f"{new_event.event_date['day']} {HARPTOS_MONTHS[new_event.event_date['month']]['name']}, {new_event.event_date['dr_year']} DR"
        city_text = f" in {new_event.city_name}" if new_event.city_name else ""
        event_desc = f"📅 New {new_event.event_type} event: {new_event.title}{city_text} scheduled for {formatted_date}"
        await create_and_broadcast_event(event_desc, new_event.city_name or "Kingdom", "Calendar", "calendar-event")
        return new_event
    raise HTTPException(status_code=500, detail="Failed to create calendar event")

@api_router.put("/calendar-events/{event_id}")
async def update_calendar_event(event_id: str, event_update: EventCreate):
    """Update an existing calendar event"""
    update_data = event_update.dict()
    
    result = await db.calendar_events.update_one(
        {"id": event_id},
        {"$set": update_data}
    )
    
    if result.modified_count:
        return {"message": "Calendar event updated successfully"}
    raise HTTPException(status_code=404, detail="Calendar event not found")

@api_router.delete("/calendar-events/{event_id}")
async def delete_calendar_event(event_id: str):
    """Delete a calendar event"""
    result = await db.calendar_events.delete_one({"id": event_id})
    if result.deleted_count:
        return {"message": "Calendar event deleted successfully"}
    raise HTTPException(status_code=404, detail="Calendar event not found")

@api_router.post("/calendar-events/generate-city-events")
async def generate_random_city_events(kingdom_id: str, count: int = 5, date_range_days: int = 30):
    """Generate random city-specific events"""
    # Get kingdom's cities
    kingdom = await db.multi_kingdoms.find_one({"id": kingdom_id})
    if not kingdom:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    
    cities = kingdom.get("cities", [])
    if not cities:
        raise HTTPException(status_code=404, detail="No cities found in kingdom")
    
    # Get current campaign date
    campaign_date = await db.campaign_dates.find_one({"kingdom_id": kingdom_id})
    if not campaign_date:
        harptos_now = convert_real_time_to_harptos()
        base_dr_year = harptos_now["dr_year"]
        base_month = harptos_now["month"]
        base_day = harptos_now["day"]
    else:
        base_dr_year = campaign_date["dr_year"]
        base_month = campaign_date["month"]
        base_day = campaign_date["day"]
    
    generated_events = []
    
    for _ in range(count):
        # Select random city and event template
        city = random.choice(cities)
        event_template = random.choice(CITY_EVENT_TEMPLATES)
        
        # Generate random date within range
        random_days = random.randint(1, date_range_days)
        event_day = base_day + random_days
        event_month = base_month
        event_year = base_dr_year
        
        # Handle month/year overflow
        while event_day > 30:
            event_day -= 30
            event_month += 1
            if event_month > 11:
                event_month = 0
                event_year += 1
        
        new_event = CalendarEvent(
            title=event_template['title'],  # Remove city name from title
            description=event_template['description'],
            event_type=event_template['type'],
            city_name=city['name'],
            kingdom_id=kingdom_id,
            event_date={"dr_year": event_year, "month": event_month, "day": event_day},
            created_by="auto_generator"
        )
        
        # Insert into database
        result = await db.calendar_events.insert_one(new_event.dict())
        if result.inserted_id:
            generated_events.append(new_event.dict())
    
    # Broadcast notification
    await create_and_broadcast_event(
        f"🎲 Generated {len(generated_events)} new city events across the kingdom", 
        "Kingdom", 
        "Events", 
        "events-generated"
    )
    
    return {"message": f"Generated {len(generated_events)} city events", "events": generated_events}

# Voting System Management
@api_router.get("/voting-sessions/{kingdom_id}")
async def get_voting_sessions(kingdom_id: str):
    """Get all voting sessions for a kingdom"""
    sessions = await db.voting_sessions.find({"kingdom_id": kingdom_id}).to_list(100)
    for session in sessions:
        session.pop('_id', None)
    return sessions

@api_router.post("/voting-sessions")
async def create_voting_session(session: VotingSessionCreate, kingdom_id: str):
    """Create a new voting session"""
    new_session = VotingSession(**session.dict(), kingdom_id=kingdom_id)
    
    result = await db.voting_sessions.insert_one(new_session.dict())
    if result.inserted_id:
        # Create a kingdom event for this voting session
        location = "Kingdom-wide"
        if new_session.city_id:
            # Find city name
            kingdom = await db.multi_kingdoms.find_one({"id": kingdom_id})
            if kingdom and kingdom.get('cities'):
                city = next((c for c in kingdom['cities'] if c['id'] == new_session.city_id), None)
                location = city['name'] if city else "Unknown City"
        
        event_desc = f"🗳️ Voting session started: {new_session.title} ({location})"
        await create_and_broadcast_event(event_desc, location, "Voting", "voting-session")
        return new_session
    raise HTTPException(status_code=500, detail="Failed to create voting session")

@api_router.post("/voting-sessions/{session_id}/vote")
async def cast_vote(session_id: str, vote: CastVote):
    """Cast a vote in a voting session"""
    # Verify citizen exists and can vote
    kingdoms = await db.multi_kingdoms.find().to_list(None)
    citizen_found = False
    
    for kingdom in kingdoms:
        if kingdom.get('cities'):
            for city in kingdom['cities']:
                if city.get('citizens'):
                    for citizen in city['citizens']:
                        if citizen['id'] == vote.citizen_id:
                            citizen_found = True
                            break
    
    if not citizen_found:
        raise HTTPException(status_code=404, detail="Citizen not found")
    
    # Update the voting session
    result = await db.voting_sessions.update_one(
        {"id": session_id, "status": "active"},
        {"$set": {f"votes.{vote.citizen_id}": vote.option}}
    )
    
    if result.modified_count:
        return {"message": "Vote cast successfully"}
    else:
        # Check if session exists but is not active
        session = await db.voting_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Voting session not found")
        elif session.get('status') != 'active':
            raise HTTPException(status_code=400, detail="Voting session is not active")
        else:
            raise HTTPException(status_code=500, detail="Failed to cast vote")

@api_router.post("/voting-sessions/{session_id}/close")
async def close_voting_session(session_id: str):
    """Close a voting session and calculate results"""
    session = await db.voting_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Voting session not found")
    
    # Calculate results
    votes = session.get('votes', {})
    results = {}
    
    for option in session['options']:
        results[option] = 0
    
    for voted_option in votes.values():
        if voted_option in results:
            results[voted_option] += 1
    
    # Update session with results
    await db.voting_sessions.update_one(
        {"id": session_id},
        {
            "$set": {
                "status": "completed",
                "results": results
            }
        }
    )
    
    # Create event for voting results
    winning_option = max(results.items(), key=lambda x: x[1])
    event_desc = f"🏆 Voting completed: '{session['title']}' - Winner: {winning_option[0]} ({winning_option[1]} votes)"
    await create_and_broadcast_event(event_desc, "Kingdom", "Voting Results", "voting-results")
    
    return {"message": "Voting session closed", "results": results}

@api_router.get("/voting-sessions/{session_id}/results")
async def get_voting_results(session_id: str):
    """Get results of a voting session"""
    session = await db.voting_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Voting session not found")
    
    return {
        "session_id": session_id,
        "title": session['title'],
        "status": session['status'],
        "votes": session.get('votes', {}),
        "results": session.get('results', {}),
        "total_votes": len(session.get('votes', {}))
    }

# City assignment to kingdoms
@api_router.put("/cities/{city_id}/assign-kingdom/{kingdom_id}")
async def assign_city_to_kingdom(city_id: str, kingdom_id: str):
    """Assign a city to a specific kingdom"""
    # Get city data from legacy kingdom
    legacy_kingdom = await db.kingdoms.find_one()
    city_data = None
    
    if legacy_kingdom:
        for city in legacy_kingdom.get('cities', []):
            if city['id'] == city_id:
                city_data = city
                break
    
    if not city_data:
        raise HTTPException(status_code=404, detail="City not found")
    
    # Add city to new kingdom
    result = await db.multi_kingdoms.update_one(
        {"id": kingdom_id},
        {
            "$push": {"cities": city_data},
            "$inc": {"total_population": city_data.get('population', 0)}
        }
    )
    
    if result.modified_count:
        # Remove city from legacy kingdom
        await db.kingdoms.update_one(
            {},
            {
                "$pull": {"cities": {"id": city_id}},
                "$inc": {"total_population": -city_data.get('population', 0)}
            }
        )
        return {"message": "City assigned successfully"}
    
    raise HTTPException(status_code=404, detail="Kingdom not found")
@api_router.get("/kingdom")
async def get_kingdom():
    kingdom = await db.kingdoms.find_one()
    if kingdom:
        kingdom.pop('_id', None)
        return kingdom
    return {"error": "Kingdom not found"}

@api_router.put("/kingdom")
async def update_kingdom(updates: dict):
    update_data = {}
    if 'name' in updates:
        update_data['name'] = updates['name']
    if 'ruler' in updates:
        update_data['ruler'] = updates['ruler']
    if 'government_type' in updates:
        update_data['government_type'] = updates['government_type']
    
    result = await db.kingdoms.update_one(
        {},
        {"$set": update_data}
    )
    if result.modified_count:
        return {"message": "Kingdom updated successfully"}
    raise HTTPException(status_code=404, detail="Kingdom not found")

@api_router.post("/cities")
async def create_city(city: CityCreate):
    # Get the active kingdom
    active_kingdom = await db.multi_kingdoms.find_one({"is_active": True})
    if not active_kingdom:
        raise HTTPException(status_code=404, detail="No active kingdom found")
    
    new_city = City(**city.dict())
    
    # Add city to the active kingdom
    result = await db.multi_kingdoms.update_one(
        {"id": active_kingdom["id"]},
        {"$push": {"cities": new_city.dict()}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "city_created",
            "city": new_city.dict(),
            "kingdom_id": active_kingdom["id"]
        })
        return new_city
    raise HTTPException(status_code=404, detail="Failed to create city")

@api_router.get("/city/{city_id}")
async def get_city(city_id: str):
    # Search across all kingdoms for the city
    kingdoms = await db.multi_kingdoms.find().to_list(None)
    for kingdom in kingdoms:
        if kingdom.get('cities'):
            for city in kingdom['cities']:
                if city['id'] == city_id:
                    return city
    raise HTTPException(status_code=404, detail="City not found")

@api_router.put("/city/{city_id}")
async def update_city(city_id: str, updates: CityUpdate):
    # Find which kingdom contains this city and update it
    kingdoms = await db.multi_kingdoms.find().to_list(None)
    for kingdom in kingdoms:
        if kingdom.get('cities'):
            for i, city in enumerate(kingdom['cities']):
                if city['id'] == city_id:
                    # Update the city in this kingdom
                    update_data = {}
                    for k, v in updates.dict(exclude_unset=True).items():
                        update_data[f"cities.{i}.{k}"] = v
                    
                    result = await db.multi_kingdoms.update_one(
                        {"id": kingdom["id"]},
                        {"$set": update_data}
                    )
                    
                    if result.modified_count:
                        await manager.broadcast({
                            "type": "city_updated",
                            "city_id": city_id,
                            "updates": updates.dict(exclude_unset=True),
                            "kingdom_id": kingdom["id"]
                        })
                        return {"message": "City updated successfully"}
                    break
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/city/{city_id}")
async def delete_city(city_id: str):
    """Delete a city and its government hierarchy"""
    # Find which kingdom contains this city and remove it
    kingdoms = await db.multi_kingdoms.find().to_list(None)
    city_name = "Unknown City"
    kingdom_id = None
    
    for kingdom in kingdoms:
        if kingdom.get('cities'):
            for city in kingdom['cities']:
                if city['id'] == city_id:
                    city_name = city.get('name', 'Unknown City')
                    kingdom_id = kingdom["id"]
                    
                    # Remove city from kingdom
                    result = await db.multi_kingdoms.update_one(
                        {"id": kingdom["id"]},
                        {"$pull": {"cities": {"id": city_id}}}
                    )
                    
                    if result.modified_count:
                        # Delete related city data
                        try:
                            # Delete city-specific calendar events
                            await db.calendar_events.delete_many({
                                "kingdom_id": kingdom_id,
                                "city_name": city_name
                            })
                            
                            # Broadcast city deletion
                            await manager.broadcast({
                                "type": "city_deleted",
                                "city_id": city_id,
                                "city_name": city_name,
                                "kingdom_id": kingdom["id"]
                            })
                            
                            return {
                                "message": f"City '{city_name}' and its government hierarchy deleted successfully",
                                "deleted_government_positions": len(city.get('government_officials', [])),
                                "deleted_calendar_events": True
                            }
                        except Exception as e:
                            # City was removed from kingdom, but cleanup failed
                            return {
                                "message": f"City '{city_name}' deleted but some cleanup failed: {str(e)}",
                                "partial_success": True
                            }
                    break
    
    raise HTTPException(status_code=404, detail="City not found")

# Government Position Management
@api_router.get("/government-positions")
async def get_available_positions():
    return {"positions": GOVERNMENT_POSITIONS}

@api_router.get("/cities/{city_id}/government")
async def get_city_government(city_id: str):
    """Get all government positions for a city"""
    kingdoms = await db.multi_kingdoms.find().to_list(None)
    
    for kingdom in kingdoms:
        if kingdom.get('cities'):
            for city in kingdom['cities']:
                if city['id'] == city_id:
                    government_officials = city.get('government_officials', [])
                    
                    # Ensure officials have all required fields
                    for official in government_officials:
                        if 'id' not in official:
                            official['id'] = str(uuid.uuid4())
                    
                    return {
                        "city_id": city_id,
                        "city_name": city.get('name', 'Unknown City'),
                        "government_officials": government_officials
                    }
    
    raise HTTPException(status_code=404, detail="City not found")

@api_router.post("/cities/{city_id}/government/appoint")
async def appoint_citizen_to_government(city_id: str, appointment: GovernmentAppointment):
    """Appoint a citizen to a government position"""
    # Find the kingdom containing this city
    kingdoms = await db.multi_kingdoms.find().to_list(None)
    
    for kingdom in kingdoms:
        if kingdom.get('cities'):
            for city in kingdom['cities']:
                if city['id'] == city_id:
                    # Find the citizen
                    citizen_found = False
                    citizen_name = "Unknown"
                    
                    for citizen in city.get('citizens', []):
                        if citizen['id'] == appointment.citizen_id:
                            citizen_found = True
                            citizen_name = citizen['name']
                            break
                    
                    if not citizen_found:
                        raise HTTPException(status_code=404, detail="Citizen not found")
                    
                    # Check if position already exists
                    existing_officials = city.get('government_officials', [])
                    for official in existing_officials:
                        if official.get('position') == appointment.position:
                            raise HTTPException(
                                status_code=400, 
                                detail=f"Position '{appointment.position}' is already filled"
                            )
                    
                    # Create new government official
                    new_official = GovernmentOfficial(
                        name=citizen_name,
                        position=appointment.position,
                        city_id=city_id,
                        citizen_id=appointment.citizen_id
                    )
                    
                    # Update the citizen with government position
                    result1 = await db.multi_kingdoms.update_one(
                        {"id": kingdom["id"], "cities.id": city_id, "cities.citizens.id": appointment.citizen_id},
                        {
                            "$set": {
                                "cities.$[city].citizens.$[citizen].government_position": appointment.position,
                                "cities.$[city].citizens.$[citizen].appointed_date": datetime.utcnow()
                            }
                        },
                        array_filters=[
                            {"city.id": city_id},
                            {"citizen.id": appointment.citizen_id}
                        ]
                    )
                    
                    # Add to government officials
                    result2 = await db.multi_kingdoms.update_one(
                        {"id": kingdom["id"], "cities.id": city_id},
                        {"$push": {"cities.$.government_officials": new_official.dict()}}
                    )
                    
                    if result1.modified_count and result2.modified_count:
                        # Create event
                        event_desc = f"🏛️ {citizen_name} appointed as {appointment.position}!"
                        await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "appointment", "high")
                        
                        # Broadcast update
                        await manager.broadcast({
                            "type": "government_updated",
                            "city_id": city_id,
                            "action": "appointed",
                            "official": new_official.dict(),
                            "kingdom_id": kingdom["id"]
                        })
                        
                        return {
                            "message": "Citizen appointed successfully",
                            "official": new_official.dict()
                        }
                    
                    raise HTTPException(status_code=500, detail="Failed to appoint citizen")
    
    raise HTTPException(status_code=404, detail="City not found")

@api_router.put("/cities/{city_id}/government/{official_id}")
async def update_government_official(city_id: str, official_id: str, updates: dict):
    """Update a government official's information"""
    kingdoms = await db.multi_kingdoms.find().to_list(None)
    
    for kingdom in kingdoms:
        if kingdom.get('cities'):
            for city in kingdom['cities']:
                if city['id'] == city_id:
                    # Find the official
                    officials = city.get('government_officials', [])
                    official_found = False
                    
                    for i, official in enumerate(officials):
                        if official['id'] == official_id:
                            official_found = True
                            
                            # Update allowed fields
                            allowed_updates = ['position']
                            update_data = {}
                            
                            for key, value in updates.items():
                                if key in allowed_updates:
                                    update_data[f"cities.$.government_officials.{i}.{key}"] = value
                            
                            if update_data:
                                result = await db.multi_kingdoms.update_one(
                                    {"id": kingdom["id"], "cities.id": city_id},
                                    {"$set": update_data}
                                )
                                
                                if result.modified_count:
                                    await manager.broadcast({
                                        "type": "government_updated",
                                        "city_id": city_id,
                                        "action": "updated",
                                        "official_id": official_id,
                                        "updates": updates,
                                        "kingdom_id": kingdom["id"]
                                    })
                                    
                                    return {"message": "Government official updated successfully"}
                            
                            break
                    
                    if not official_found:
                        raise HTTPException(status_code=404, detail="Government official not found")
    
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/cities/{city_id}/government/{official_id}")
async def remove_government_official(city_id: str, official_id: str):
    """Remove a government official and clear their citizen's position"""
    kingdoms = await db.multi_kingdoms.find().to_list(None)
    
    for kingdom in kingdoms:
        if kingdom.get('cities'):
            for city in kingdom['cities']:
                if city['id'] == city_id:
                    # Find the official to get citizen_id
                    officials = city.get('government_officials', [])
                    citizen_id = None
                    official_name = "Unknown"
                    
                    for official in officials:
                        if official['id'] == official_id:
                            citizen_id = official.get('citizen_id')
                            official_name = official.get('name', 'Unknown')
                            break
                    
                    if not citizen_id:
                        raise HTTPException(status_code=404, detail="Government official not found")
                    
                    # Remove from government officials
                    result1 = await db.multi_kingdoms.update_one(
                        {"id": kingdom["id"], "cities.id": city_id},
                        {"$pull": {"cities.$.government_officials": {"id": official_id}}}
                    )
                    
                    # Remove government position from citizen
                    result2 = await db.multi_kingdoms.update_one(
                        {"id": kingdom["id"], "cities.id": city_id, "cities.citizens.id": citizen_id},
                        {
                            "$unset": {
                                "cities.$[city].citizens.$[citizen].government_position": "",
                                "cities.$[city].citizens.$[citizen].appointed_date": ""
                            }
                        },
                        array_filters=[
                            {"city.id": city_id},
                            {"citizen.id": citizen_id}
                        ]
                    )
                    
                    if result1.modified_count:
                        # Create event
                        event_desc = f"🏛️ {official_name} removed from government position!"
                        await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "removal", "medium")
                        
                        # Broadcast update
                        await manager.broadcast({
                            "type": "government_updated",
                            "city_id": city_id,
                            "action": "removed",
                            "official_id": official_id,
                            "kingdom_id": kingdom["id"]
                        })
                        
                        return {"message": "Government official removed successfully"}
                    
                    raise HTTPException(status_code=500, detail="Failed to remove government official")
    
    raise HTTPException(status_code=404, detail="City not found")
    raise HTTPException(status_code=404, detail="Official not found")

# FIXED Auto-generation endpoints
@api_router.post("/auto-generate")
async def auto_generate_registry_items(request: AutoGenerateRequest):
    """Fixed auto-generate functionality for multi-kingdom database structure"""
    try:
        # Find the kingdom that contains the specified city
        kingdom = None
        target_city = None
        
        # Search through all kingdoms in multi_kingdoms collection
        kingdoms = await db.multi_kingdoms.find().to_list(None)
        
        for k in kingdoms:
            for city in k.get('cities', []):
                if city['id'] == request.city_id:
                    kingdom = k
                    target_city = city
                    break
            if kingdom:
                break
        
        if not kingdom:
            raise HTTPException(status_code=404, detail="Kingdom containing the specified city not found")
        
        if not target_city:
            raise HTTPException(status_code=404, detail="City not found in any kingdom")
        
        generated_items = []
        
        for _ in range(request.count):
            if request.registry_type == "citizens":
                new_citizen_data = generate_citizen(request.city_id)
                new_citizen = Citizen(**new_citizen_data)
                
                result = await db.multi_kingdoms.update_one(
                    {"id": kingdom['id'], "cities.id": request.city_id},
                    {
                        "$push": {"cities.$.citizens": new_citizen.dict()},
                        "$inc": {"cities.$.population": 1, "total_population": 1}
                    }
                )
                
                if result.modified_count:
                    generated_items.append(new_citizen.dict())
                    event_desc = generate_registry_event("citizen", target_city['name'], new_citizen_data)
                    await create_and_broadcast_event(
                        event_desc, target_city['name'], kingdom['name'], "manual-generate",
                        kingdom_id=kingdom['id']
                    )
            
            elif request.registry_type == "slaves":
                new_slave_data = generate_slave(request.city_id)
                new_slave = Slave(**new_slave_data)
                
                result = await db.multi_kingdoms.update_one(
                    {"id": kingdom['id'], "cities.id": request.city_id},
                    {"$push": {"cities.$.slaves": new_slave.dict()}}
                )
                
                if result.modified_count:
                    generated_items.append(new_slave.dict())
                    event_desc = generate_registry_event("slave", target_city['name'], new_slave_data)
                    await create_and_broadcast_event(
                        event_desc, target_city['name'], kingdom['name'], "manual-generate",
                        kingdom_id=kingdom['id']
                    )
            
            elif request.registry_type == "livestock":
                new_livestock_data = generate_livestock(request.city_id)
                new_livestock = Livestock(**new_livestock_data)
                
                result = await db.multi_kingdoms.update_one(
                    {"id": kingdom['id'], "cities.id": request.city_id},
                    {"$push": {"cities.$.livestock": new_livestock.dict()}}
                )
                
                if result.modified_count:
                    generated_items.append(new_livestock.dict())
                    event_desc = generate_registry_event("livestock", target_city['name'], new_livestock_data)
                    await create_and_broadcast_event(
                        event_desc, target_city['name'], kingdom['name'], "manual-generate",
                        kingdom_id=kingdom['id']
                    )
            
            elif request.registry_type == "garrison":
                new_soldier_data = generate_soldier(request.city_id)
                new_soldier = Soldier(**new_soldier_data)
                
                result = await db.multi_kingdoms.update_one(
                    {"id": kingdom['id'], "cities.id": request.city_id},
                    {"$push": {"cities.$.garrison": new_soldier.dict()}}
                )
                
                if result.modified_count:
                    generated_items.append(new_soldier.dict())
                    event_desc = generate_registry_event("soldier", target_city['name'], new_soldier_data)
                    await create_and_broadcast_event(
                        event_desc, target_city['name'], kingdom['name'], "manual-generate",
                        kingdom_id=kingdom['id']
                    )
            
            elif request.registry_type == "crimes":
                new_crime_data = generate_crime(request.city_id, target_city['name'])
                new_crime = CrimeRecord(**new_crime_data)
                
                result = await db.multi_kingdoms.update_one(
                    {"id": kingdom['id'], "cities.id": request.city_id},
                    {"$push": {"cities.$.crime_records": new_crime.dict()}}
                )
                
                if result.modified_count:
                    generated_items.append(new_crime.dict())
                    event_desc = generate_registry_event("crime", target_city['name'], new_crime_data)
                    await create_and_broadcast_event(
                        event_desc, target_city['name'], kingdom['name'], "manual-generate",
                        kingdom_id=kingdom['id']
                    )
            
            elif request.registry_type == "tribute":
                new_tribute_data = generate_tribute(target_city['name'])
                new_tribute = TributeRecord(**new_tribute_data)
                
                result = await db.multi_kingdoms.update_one(
                    {"id": kingdom['id'], "cities.id": request.city_id},
                    {"$push": {"cities.$.tribute_records": new_tribute.dict()}}
                )
                
                if result.modified_count:
                    generated_items.append(new_tribute.dict())
                    event_desc = generate_registry_event("tribute", target_city['name'], new_tribute_data)
                    await create_and_broadcast_event(
                        event_desc, target_city['name'], kingdom['name'], "manual-generate",
                        kingdom_id=kingdom['id']
                    )
        
        return {"generated_items": generated_items, "count": len(generated_items)}
    
    except Exception as e:
        logging.error(f"Auto-generate error: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-generation failed: {str(e)}")

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
    
    result = await db.multi_kingdoms.update_one(
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
    result = await db.multi_kingdoms.update_one(
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
    
    result = await db.multi_kingdoms.update_one(
        {"cities.id": slave.city_id},
        {"$push": {"cities.$.slaves": new_slave.dict()}}
    )
    
    if result.modified_count:
        return new_slave
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/slaves/{slave_id}")
async def delete_slave(slave_id: str):
    result = await db.multi_kingdoms.update_one(
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
    
    result = await db.multi_kingdoms.update_one(
        {"cities.id": livestock.city_id},
        {"$push": {"cities.$.livestock": new_livestock.dict()}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "livestock_added",
            "livestock": new_livestock.dict()
        })
        return new_livestock
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/livestock/{livestock_id}")
async def delete_livestock(livestock_id: str):
    result = await db.multi_kingdoms.update_one(
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
    
    result = await db.multi_kingdoms.update_one(
        {"cities.id": soldier.city_id},
        {"$push": {"cities.$.garrison": new_soldier.dict()}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "soldier_added",
            "soldier": new_soldier.dict()
        })
        return new_soldier
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/soldiers/{soldier_id}")
async def delete_soldier(soldier_id: str):
    result = await db.multi_kingdoms.update_one(
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
    
    result = await db.multi_kingdoms.update_one(
        {"cities.name": tribute.from_city},
        {"$push": {"cities.$.tribute_records": new_tribute.dict()}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "tribute_added",
            "tribute": new_tribute.dict()
        })
        return new_tribute
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/tribute/{tribute_id}")
async def delete_tribute(tribute_id: str):
    result = await db.multi_kingdoms.update_one(
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
    
    result = await db.multi_kingdoms.update_one(
        {"cities.id": crime.city_id},
        {"$push": {"cities.$.crime_records": new_crime.dict()}}
    )
    
    if result.modified_count:
        await manager.broadcast({
            "type": "crime_added",
            "crime": new_crime.dict()
        })
        return new_crime
    raise HTTPException(status_code=404, detail="City not found")

@api_router.delete("/crimes/{crime_id}")
async def delete_crime(crime_id: str):
    result = await db.multi_kingdoms.update_one(
        {"cities.crime_records.id": crime_id},
        {"$pull": {"cities.$.crime_records": {"id": crime_id}}}
    )
    
    if result.modified_count:
        return {"message": "Crime record deleted successfully"}
    raise HTTPException(status_code=404, detail="Crime record not found")

# Events Management
@api_router.get("/events")
async def get_events():
    """Get all events (backward compatibility)"""
    events = await db.events.find().sort("timestamp", -1).limit(50).to_list(50)
    for event in events:
        event.pop('_id', None)
    return events

@api_router.get("/events/{kingdom_id}")
async def get_kingdom_events(kingdom_id: str):
    """Get events for a specific kingdom"""
    # Get events that match this kingdom (by kingdom_id or kingdom_name)
    kingdom = await db.multi_kingdoms.find_one({"id": kingdom_id})
    if not kingdom:
        raise HTTPException(status_code=404, detail="Kingdom not found")
    
    events = await db.events.find({
        "$or": [
            {"kingdom_id": kingdom_id},
            {"kingdom_name": kingdom["name"]}
        ]
    }).sort("timestamp", -1).limit(50).to_list(50)
    
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
        event_type="manual",
        priority=event.priority
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

# Include the main API router and auth router in the app
app.include_router(api_router)
app.include_router(auth_router)

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