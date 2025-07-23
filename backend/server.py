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

# Enhanced simulation engine
async def simulation_engine():
    """Enhanced background task with better event generation"""
    global auto_events_enabled
    while True:
        try:
            if auto_events_enabled:
                kingdom_data = await db.kingdoms.find_one()
                if kingdom_data and kingdom_data['cities']:
                    # Generate enhanced events 80% of the time
                    if random.random() < 0.8:
                        event_description = generate_enhanced_event(kingdom_data)
                        
                        event = Event(
                            description=event_description,
                            city_name=random.choice(kingdom_data['cities'])['name'],
                            kingdom_name=kingdom_data['name'],
                            event_type="auto",
                            priority=random.choices(["normal", "high"], weights=[80, 20])[0]
                        )
                        
                        await db.events.insert_one(event.dict())
                        await manager.broadcast({
                            "type": "new_event",
                            "event": event.dict()
                        })
                    
                    # Auto-generate registry content 20% of the time
                    else:
                        city = random.choice(kingdom_data['cities'])
                        registry_types = ["citizens", "livestock", "crimes", "soldiers"]
                        registry_type = random.choice(registry_types)
                        
                        try:
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
                            
                        except Exception as e:
                            logging.error(f"Auto-generation error for {registry_type}: {e}")
            
            await asyncio.sleep(random.randint(15, 45))  # 15-45 seconds between events
            
        except Exception as e:
            logging.error(f"Simulation error: {e}")
            await asyncio.sleep(30)

async def create_and_broadcast_event(description, city_name, kingdom_name, event_type, priority="normal"):
    """Helper function to create and broadcast events"""
    event = Event(
        description=description,
        city_name=city_name,
        kingdom_name=kingdom_name,
        event_type=event_type,
        priority=priority
    )
    
    await db.events.insert_one(event.dict())
    await manager.broadcast({
        "type": "new_event",
        "event": event.dict()
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
    result = await db.multi_kingdoms.delete_one({"id": kingdom_id})
    
    if result.deleted_count:
        return {"message": "Kingdom deleted successfully"}
    raise HTTPException(status_code=404, detail="Kingdom not found")

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

# Government Position Management
@api_router.get("/government-positions")
async def get_available_positions():
    return {"positions": GOVERNMENT_POSITIONS}

@api_router.post("/cities/{city_id}/government/appoint")
async def appoint_citizen_to_government(city_id: str, appointment: GovernmentAppointment):
    # Create government official record
    new_official = GovernmentOfficial(
        name="", # Will be filled from citizen data
        position=appointment.position,
        city_id=city_id,
        citizen_id=appointment.citizen_id
    )
    
    # Update citizen with government position
    result1 = await db.kingdoms.update_one(
        {"cities.id": city_id, "cities.citizens.id": appointment.citizen_id},
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
    
    # Get citizen name and add to government officials
    kingdom = await db.kingdoms.find_one()
    citizen_name = "Unknown"
    for city in kingdom['cities']:
        if city['id'] == city_id:
            for citizen in city['citizens']:
                if citizen['id'] == appointment.citizen_id:
                    citizen_name = citizen['name']
                    break
    
    new_official.name = citizen_name
    
    result2 = await db.kingdoms.update_one(
        {"cities.id": city_id},
        {"$push": {"cities.$.government_officials": new_official.dict()}}
    )
    
    if result1.modified_count and result2.modified_count:
        event_desc = f"🏛️ {citizen_name} appointed as {appointment.position} in {city['name']}!"
        await create_and_broadcast_event(event_desc, city['name'], kingdom['name'], "appointment", "high")
        return {"message": "Citizen appointed successfully"}
    
    raise HTTPException(status_code=404, detail="City or citizen not found")

@api_router.delete("/cities/{city_id}/government/{official_id}")
async def remove_government_official(city_id: str, official_id: str):
    # Remove from government officials
    result1 = await db.kingdoms.update_one(
        {"cities.id": city_id},
        {"$pull": {"cities.$.government_officials": {"id": official_id}}}
    )
    
    # Remove government position from citizen
    result2 = await db.kingdoms.update_one(
        {"cities.id": city_id},
        {
            "$unset": {
                "cities.$[city].citizens.$[].government_position": "",
                "cities.$[city].citizens.$[].appointed_date": ""
            }
        },
        array_filters=[{"city.id": city_id}]
    )
    
    if result1.modified_count:
        return {"message": "Government official removed successfully"}
    raise HTTPException(status_code=404, detail="Official not found")

# FIXED Auto-generation endpoints
@api_router.post("/auto-generate")
async def auto_generate_registry_items(request: AutoGenerateRequest):
    try:
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