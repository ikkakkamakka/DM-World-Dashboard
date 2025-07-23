import React, { useState, useEffect } from "react";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// Modal Component for Forms
const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = ({ currentView, onViewChange, kingdom }) => {
  return (
    <div className="navigation">
      <button 
        className={`nav-button ${currentView === 'kingdom' ? 'active' : ''}`}
        onClick={() => onViewChange('kingdom')}
      >
        Kingdom Dashboard
      </button>
      <button 
        className={`nav-button ${currentView === 'map' ? 'active' : ''}`}
        onClick={() => onViewChange('map')}
      >
        Faerûn Map
      </button>
      {kingdom?.cities?.map(city => (
        <button
          key={city.id}
          className={`nav-button city-nav ${currentView === city.id ? 'active' : ''}`}
          onClick={() => onViewChange(city.id)}
        >
          {city.name}
        </button>
      ))}
    </div>
  );
};

// Kingdom Dashboard Component with Totals
const KingdomDashboard = ({ kingdom, events, autoEventsEnabled, onToggleAutoEvents }) => {
  if (!kingdom) return <div className="loading">Loading kingdom...</div>;

  const totalTreasury = kingdom.royal_treasury + (kingdom.cities?.reduce((sum, city) => sum + city.treasury, 0) || 0);
  const totalSlaves = kingdom.cities?.reduce((sum, city) => sum + (city.slaves?.length || 0), 0) || 0;
  const totalLivestock = kingdom.cities?.reduce((sum, city) => sum + (city.livestock?.length || 0), 0) || 0;
  const totalSoldiers = kingdom.cities?.reduce((sum, city) => sum + (city.garrison?.length || 0), 0) || 0;
  const totalCrimes = kingdom.cities?.reduce((sum, city) => sum + (city.crime_records?.length || 0), 0) || 0;

  return (
    <div className="kingdom-dashboard">
      <div className="kingdom-header">
        <h1 className="kingdom-title">{kingdom.name}</h1>
        <p className="kingdom-ruler">Campaign managed by {kingdom.ruler}</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{kingdom.total_population}</div>
          <div className="stat-label">Total Population</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{totalTreasury}</div>
          <div className="stat-label">Total Treasury (GP)</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{kingdom.cities?.length || 0}</div>
          <div className="stat-label">Cities</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{totalSlaves}</div>
          <div className="stat-label">Total Slaves</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{totalLivestock}</div>
          <div className="stat-label">Total Livestock</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{totalSoldiers}</div>
          <div className="stat-label">Total Soldiers</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{totalCrimes}</div>
          <div className="stat-label">Total Crimes</div>
        </div>
      </div>

      <div className="cities-section">
        <h2>Cities Overview</h2>
        <div className="cities-grid">
          {kingdom.cities?.map(city => (
            <div key={city.id} className="city-overview-card">
              <h3>{city.name}</h3>
              <p className="governor">Governor: {city.governor}</p>
              <div className="city-details">
                <div className="detail-row">
                  <span>Population: {city.population}</span>
                  <span>Treasury: {city.treasury} GP</span>
                </div>
                <div className="detail-row">
                  <span>Slaves: {city.slaves?.length || 0}</span>
                  <span>Livestock: {city.livestock?.length || 0}</span>
                </div>
                <div className="detail-row">
                  <span>Garrison: {city.garrison?.length || 0}</span>
                  <span>Crimes: {city.crime_records?.length || 0}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="events-section">
        <div className="events-header">
          <h2>Kingdom Events</h2>
          <div className="events-controls">
            <button 
              className={`toggle-button ${autoEventsEnabled ? 'enabled' : 'disabled'}`}
              onClick={onToggleAutoEvents}
            >
              Auto Events: {autoEventsEnabled ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>
        <div className="events-feed">
          {events.slice(0, 15).map(event => (
            <div key={event.id} className="event-item">
              <div className="event-header">
                <div className="event-time">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
                <div className={`event-type ${event.event_type}`}>
                  {event.event_type === 'auto' ? '🤖' : '✍️'}
                </div>
              </div>
              <div className="event-description">{event.description}</div>
              <div className="event-city">📍 {event.city_name}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Faerûn Map Component
const FaerunMap = ({ cities, onCitySelect, onMapClick }) => {
  const [showAddCityForm, setShowAddCityForm] = useState(false);
  const [newCityCoords, setNewCityCoords] = useState({ x: 0, y: 0 });

  const handleMapClick = (e) => {
    const rect = e.target.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setNewCityCoords({ x, y });
    setShowAddCityForm(true);
  };

  const handleCreateCity = async (cityData) => {
    try {
      const response = await fetch(`${API}/cities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...cityData, x_coordinate: newCityCoords.x, y_coordinate: newCityCoords.y })
      });
      
      if (response.ok) {
        setShowAddCityForm(false);
        window.location.reload();
      }
    } catch (error) {
      console.error('Error creating city:', error);
    }
  };

  return (
    <div className="map-container">
      <h2>Faerûn Map</h2>
      <div className="map-placeholder" onClick={handleMapClick}>
        <img 
          src="https://images.unsplash.com/photo-1677295922463-147d7f2f718c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxmYW50YXN5JTIwbWFwfGVufDB8fHx8MTc1MzI0Mzk3OXww&ixlib=rb-4.1.0&q=85"
          alt="Faerûn Map"
          className="map-image"
        />
        {cities?.map(city => (
          <div
            key={city.id}
            className="city-marker"
            style={{
              left: `${city.x_coordinate}%`,
              top: `${city.y_coordinate}%`
            }}
            onClick={(e) => {
              e.stopPropagation();
              onCitySelect(city.id);
            }}
            title={city.name}
          >
            🏰
          </div>
        ))}
      </div>
      <p className="map-instructions">
        Click anywhere on the map to place a new city, or click existing markers to manage cities
      </p>

      <Modal 
        isOpen={showAddCityForm} 
        onClose={() => setShowAddCityForm(false)} 
        title="Create New City"
      >
        <AddCityForm
          onSubmit={handleCreateCity}
          onCancel={() => setShowAddCityForm(false)}
        />
      </Modal>
    </div>
  );
};

// Add City Form
const AddCityForm = ({ onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [governor, setGovernor] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name && governor) {
      onSubmit({ name, governor });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="city-form">
      <div className="form-group">
        <label>City Name:</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter city name"
          required
        />
      </div>
      <div className="form-group">
        <label>Governor:</label>
        <input
          type="text"
          value={governor}
          onChange={(e) => setGovernor(e.target.value)}
          placeholder="Enter governor name"
          required
        />
      </div>
      <div className="form-actions">
        <button type="submit" className="btn-primary">Create City</button>
        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
      </div>
    </form>
  );
};

// Registry Tabs Component
const RegistryTabs = ({ city, activeTab, setActiveTab }) => {
  const tabs = ['Citizens', 'Slaves', 'Livestock', 'Garrison', 'Tribute', 'Crime'];

  return (
    <div className="registry-tabs">
      <div className="tab-buttons">
        {tabs.map(tab => (
          <button
            key={tab}
            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab} ({getTabCount(city, tab)})
          </button>
        ))}
      </div>
      
      <div className="tab-content">
        {activeTab === 'Citizens' && <CitizensRegistry city={city} />}
        {activeTab === 'Slaves' && <SlavesRegistry city={city} />}
        {activeTab === 'Livestock' && <LivestockRegistry city={city} />}
        {activeTab === 'Garrison' && <GarrisonRegistry city={city} />}
        {activeTab === 'Tribute' && <TributeRegistry city={city} />}
        {activeTab === 'Crime' && <CrimeRegistry city={city} />}
      </div>
    </div>
  );
};

const getTabCount = (city, tab) => {
  switch (tab) {
    case 'Citizens': return city.citizens?.length || 0;
    case 'Slaves': return city.slaves?.length || 0;
    case 'Livestock': return city.livestock?.length || 0;
    case 'Garrison': return city.garrison?.length || 0;
    case 'Tribute': return city.tribute_records?.length || 0;
    case 'Crime': return city.crime_records?.length || 0;
    default: return 0;
  }
};

// Citizens Registry
const CitizensRegistry = ({ city }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '', age: '', occupation: '', health: 'Healthy', notes: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/citizens`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, city_id: city.id, age: parseInt(formData.age) })
      });
      if (response.ok) {
        setShowAddForm(false);
        setFormData({ name: '', age: '', occupation: '', health: 'Healthy', notes: '' });
        window.location.reload();
      }
    } catch (error) {
      console.error('Error adding citizen:', error);
    }
  };

  const handleDelete = async (citizenId) => {
    if (window.confirm('Are you sure you want to delete this citizen?')) {
      try {
        const response = await fetch(`${API}/citizens/${citizenId}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          window.location.reload();
        }
      } catch (error) {
        console.error('Error deleting citizen:', error);
      }
    }
  };

  const handleAutoGenerate = async () => {
    try {
      const response = await fetch(`${API}/auto-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registry_type: 'citizens',
          city_id: city.id,
          count: Math.floor(Math.random() * 5) + 2 // 2-6 citizens
        })
      });
      if (response.ok) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Error auto-generating citizens:', error);
    }
  };

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Citizens Registry</h3>
        <div className="registry-actions">
          <button className="btn-secondary" onClick={handleAutoGenerate}>
            Auto Generate
          </button>
          <button className="btn-primary" onClick={() => setShowAddForm(true)}>
            Add Citizen
          </button>
        </div>
      </div>

      <Modal isOpen={showAddForm} onClose={() => setShowAddForm(false)} title="Add New Citizen">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Age:</label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({...formData, age: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Occupation:</label>
            <input
              type="text"
              value={formData.occupation}
              onChange={(e) => setFormData({...formData, occupation: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Health Status:</label>
            <select
              value={formData.health}
              onChange={(e) => setFormData({...formData, health: e.target.value})}
            >
              <option value="Healthy">Healthy</option>
              <option value="Injured">Injured</option>
              <option value="Sick">Sick</option>
              <option value="Dead">Dead</option>
            </select>
          </div>
          <div className="form-group">
            <label>Notes:</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows="3"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Add Citizen</button>
            <button type="button" onClick={() => setShowAddForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

      <div className="registry-grid">
        {city.citizens?.map(citizen => (
          <div key={citizen.id} className="registry-card">
            <div className="card-header">
              <h4>{citizen.name}</h4>
              <button 
                className="delete-btn"
                onClick={() => handleDelete(citizen.id)}
                title="Delete citizen"
              >
                🗑️
              </button>
            </div>
            <div className="card-details">
              <p><strong>Age:</strong> {citizen.age}</p>
              <p><strong>Occupation:</strong> {citizen.occupation}</p>
              <p><strong>Health:</strong> <span className={`health-${citizen.health?.toLowerCase() || 'healthy'}`}>{citizen.health}</span></p>
              {citizen.notes && <p><strong>Notes:</strong> {citizen.notes}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Slaves Registry
const SlavesRegistry = ({ city }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '', age: '', origin: '', occupation: '', owner: '', purchase_price: '', notes: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/slaves`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ...formData, 
          city_id: city.id,
          age: parseInt(formData.age),
          purchase_price: parseInt(formData.purchase_price)
        })
      });
      if (response.ok) {
        setShowAddForm(false);
        setFormData({ name: '', age: '', origin: '', occupation: '', owner: '', purchase_price: '', notes: '' });
        window.location.reload();
      }
    } catch (error) {
      console.error('Error adding slave:', error);
    }
  };

  const handleDelete = async (slaveId) => {
    if (window.confirm('Are you sure you want to delete this slave record?')) {
      try {
        const response = await fetch(`${API}/slaves/${slaveId}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          window.location.reload();
        }
      } catch (error) {
        console.error('Error deleting slave:', error);
      }
    }
  };

  const handleAutoGenerate = async () => {
    try {
      const response = await fetch(`${API}/auto-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registry_type: 'slaves',
          city_id: city.id,
          count: Math.floor(Math.random() * 3) + 1 // 1-3 slaves
        })
      });
      if (response.ok) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Error auto-generating slaves:', error);
    }
  };

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Slave Registry</h3>
        <div className="registry-actions">
          <button className="btn-secondary" onClick={handleAutoGenerate}>
            Auto Generate
          </button>
          <button className="btn-primary" onClick={() => setShowAddForm(true)}>
            Add Slave
          </button>
        </div>
      </div>

      <Modal isOpen={showAddForm} onClose={() => setShowAddForm(false)} title="Add New Slave">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Age:</label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({...formData, age: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Origin:</label>
            <input
              type="text"
              value={formData.origin}
              onChange={(e) => setFormData({...formData, origin: e.target.value})}
              placeholder="Where they came from"
              required
            />
          </div>
          <div className="form-group">
            <label>Occupation:</label>
            <input
              type="text"
              value={formData.occupation}
              onChange={(e) => setFormData({...formData, occupation: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Owner:</label>
            <input
              type="text"
              value={formData.owner}
              onChange={(e) => setFormData({...formData, owner: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Purchase Price (GP):</label>
            <input
              type="number"
              value={formData.purchase_price}
              onChange={(e) => setFormData({...formData, purchase_price: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Notes:</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows="3"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Add Slave</button>
            <button type="button" onClick={() => setShowAddForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

      <div className="registry-grid">
        {city.slaves?.map(slave => (
          <div key={slave.id} className="registry-card">
            <div className="card-header">
              <h4>{slave.name}</h4>
              <button 
                className="delete-btn"
                onClick={() => handleDelete(slave.id)}
                title="Delete slave record"
              >
                🗑️
              </button>
            </div>
            <div className="card-details">
              <p><strong>Age:</strong> {slave.age}</p>
              <p><strong>Origin:</strong> {slave.origin}</p>
              <p><strong>Occupation:</strong> {slave.occupation}</p>
              <p><strong>Owner:</strong> {slave.owner}</p>
              <p><strong>Purchase Price:</strong> {slave.purchase_price} GP</p>
              <p><strong>Status:</strong> <span className={`status-${slave.status?.toLowerCase() || 'enslaved'}`}>{slave.status}</span></p>
              {slave.notes && <p><strong>Notes:</strong> {slave.notes}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Livestock Registry  
const LivestockRegistry = ({ city }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '', type: 'Cattle', age: '', weight: '', value: '', owner: 'City', notes: ''
  });

  const livestockTypes = ['Cattle', 'Horse', 'Goat', 'Sheep', 'Chicken', 'Pig', 'Ox', 'Mule', 'Donkey'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/livestock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ...formData, 
          city_id: city.id,
          age: parseInt(formData.age),
          weight: parseInt(formData.weight),
          value: parseInt(formData.value)
        })
      });
      if (response.ok) {
        setShowAddForm(false);
        setFormData({ name: '', type: 'Cattle', age: '', weight: '', value: '', owner: 'City', notes: '' });
        window.location.reload();
      }
    } catch (error) {
      console.error('Error adding livestock:', error);
    }
  };

  const handleDelete = async (livestockId) => {
    if (window.confirm('Are you sure you want to delete this livestock?')) {
      try {
        const response = await fetch(`${API}/livestock/${livestockId}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          window.location.reload();
        }
      } catch (error) {
        console.error('Error deleting livestock:', error);
      }
    }
  };

  const handleAutoGenerate = async () => {
    try {
      const response = await fetch(`${API}/auto-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registry_type: 'livestock',
          city_id: city.id,
          count: Math.floor(Math.random() * 4) + 2 // 2-5 livestock
        })
      });
      if (response.ok) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Error auto-generating livestock:', error);
    }
  };

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Livestock Registry</h3>
        <div className="registry-actions">
          <button className="btn-secondary" onClick={handleAutoGenerate}>
            Auto Generate
          </button>
          <button className="btn-primary" onClick={() => setShowAddForm(true)}>
            Add Livestock
          </button>
        </div>
      </div>

      <Modal isOpen={showAddForm} onClose={() => setShowAddForm(false)} title="Add New Livestock">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Type:</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
            >
              {livestockTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Age (years):</label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({...formData, age: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Weight (lbs):</label>
            <input
              type="number"
              value={formData.weight}
              onChange={(e) => setFormData({...formData, weight: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Value (GP):</label>
            <input
              type="number"
              value={formData.value}
              onChange={(e) => setFormData({...formData, value: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Owner:</label>
            <input
              type="text"
              value={formData.owner}
              onChange={(e) => setFormData({...formData, owner: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Notes:</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows="3"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Add Livestock</button>
            <button type="button" onClick={() => setShowAddForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

      <div className="registry-grid">
        {city.livestock?.map(animal => (
          <div key={animal.id} className="registry-card">
            <div className="card-header">
              <h4>{animal.name}</h4>
              <button 
                className="delete-btn"
                onClick={() => handleDelete(animal.id)}
                title="Delete livestock"
              >
                🗑️
              </button>
            </div>
            <div className="card-details">
              <p><strong>Type:</strong> {animal.type}</p>
              <p><strong>Age:</strong> {animal.age} years</p>
              <p><strong>Weight:</strong> {animal.weight} lbs</p>
              <p><strong>Value:</strong> {animal.value} GP</p>
              <p><strong>Owner:</strong> {animal.owner}</p>
              <p><strong>Health:</strong> <span className={`health-${animal.health?.toLowerCase() || 'healthy'}`}>{animal.health}</span></p>
              {animal.notes && <p><strong>Notes:</strong> {animal.notes}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Garrison Registry
const GarrisonRegistry = ({ city }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '', rank: 'Recruit', age: '', years_of_service: '0', equipment: '', status: 'Active', notes: ''
  });

  const ranks = ['Recruit', 'Private', 'Corporal', 'Sergeant', 'Lieutenant', 'Captain', 'Major', 'Commander'];

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const equipmentArray = formData.equipment.split(',').map(item => item.trim()).filter(item => item);
      const response = await fetch(`${API}/soldiers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ...formData, 
          city_id: city.id,
          age: parseInt(formData.age),
          years_of_service: parseInt(formData.years_of_service),
          equipment: equipmentArray
        })
      });
      if (response.ok) {
        setShowAddForm(false);
        setFormData({ name: '', rank: 'Recruit', age: '', years_of_service: '0', equipment: '', status: 'Active', notes: '' });
        window.location.reload();
      }
    } catch (error) {
      console.error('Error adding soldier:', error);
    }
  };

  const handleDelete = async (soldierId) => {
    if (window.confirm('Are you sure you want to delete this soldier?')) {
      try {
        const response = await fetch(`${API}/soldiers/${soldierId}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          window.location.reload();
        }
      } catch (error) {
        console.error('Error deleting soldier:', error);
      }
    }
  };

  const handleAutoGenerate = async () => {
    try {
      const response = await fetch(`${API}/auto-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registry_type: 'garrison',
          city_id: city.id,
          count: Math.floor(Math.random() * 3) + 2 // 2-4 soldiers
        })
      });
      if (response.ok) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Error auto-generating soldiers:', error);
    }
  };

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Garrison Registry</h3>
        <div className="registry-actions">
          <button className="btn-secondary" onClick={handleAutoGenerate}>
            Auto Generate
          </button>
          <button className="btn-primary" onClick={() => setShowAddForm(true)}>
            Add Soldier
          </button>
        </div>
      </div>

      <Modal isOpen={showAddForm} onClose={() => setShowAddForm(false)} title="Add New Soldier">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Rank:</label>
            <select
              value={formData.rank}
              onChange={(e) => setFormData({...formData, rank: e.target.value})}
            >
              {ranks.map(rank => (
                <option key={rank} value={rank}>{rank}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Age:</label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({...formData, age: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Years of Service:</label>
            <input
              type="number"
              value={formData.years_of_service}
              onChange={(e) => setFormData({...formData, years_of_service: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Equipment (comma-separated):</label>
            <input
              type="text"
              value={formData.equipment}
              onChange={(e) => setFormData({...formData, equipment: e.target.value})}
              placeholder="Sword, Shield, Chain Mail"
            />
          </div>
          <div className="form-group">
            <label>Status:</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({...formData, status: e.target.value})}
            >
              <option value="Active">Active</option>
              <option value="Injured">Injured</option>
              <option value="Deserter">Deserter</option>
              <option value="Dead">Dead</option>
            </select>
          </div>
          <div className="form-group">
            <label>Notes:</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows="3"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Add Soldier</button>
            <button type="button" onClick={() => setShowAddForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

      <div className="registry-grid">
        {city.garrison?.map(soldier => (
          <div key={soldier.id} className="registry-card">
            <div className="card-header">
              <h4>{soldier.name}</h4>
              <button 
                className="delete-btn"
                onClick={() => handleDelete(soldier.id)}
                title="Delete soldier"
              >
                🗑️
              </button>
            </div>
            <div className="card-details">
              <p><strong>Rank:</strong> {soldier.rank}</p>
              <p><strong>Age:</strong> {soldier.age}</p>
              <p><strong>Service:</strong> {soldier.years_of_service} years</p>
              <p><strong>Status:</strong> <span className={`status-${soldier.status?.toLowerCase() || 'active'}`}>{soldier.status}</span></p>
              {soldier.equipment?.length > 0 && (
                <p><strong>Equipment:</strong> {soldier.equipment.join(', ')}</p>
              )}
              {soldier.notes && <p><strong>Notes:</strong> {soldier.notes}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Tribute Registry
const TributeRegistry = ({ city }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    to_city: '', amount: '', type: 'Gold', purpose: '', due_date: '', notes: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/tribute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ...formData, 
          from_city: city.name,
          amount: parseInt(formData.amount),
          due_date: new Date(formData.due_date).toISOString()
        })
      });
      if (response.ok) {
        setShowAddForm(false);
        setFormData({ to_city: '', amount: '', type: 'Gold', purpose: '', due_date: '', notes: '' });
        window.location.reload();
      }
    } catch (error) {
      console.error('Error adding tribute:', error);
    }
  };

  const handleDelete = async (tributeId) => {
    if (window.confirm('Are you sure you want to delete this tribute record?')) {
      try {
        const response = await fetch(`${API}/tribute/${tributeId}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          window.location.reload();
        }
      } catch (error) {
        console.error('Error deleting tribute:', error);
      }
    }
  };

  const handleAutoGenerate = async () => {
    try {
      const response = await fetch(`${API}/auto-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registry_type: 'tribute',
          city_id: city.id,
          count: Math.floor(Math.random() * 2) + 1 // 1-2 tribute records
        })
      });
      if (response.ok) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Error auto-generating tribute:', error);
    }
  };

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Tribute Ledger</h3>
        <div className="registry-actions">
          <button className="btn-secondary" onClick={handleAutoGenerate}>
            Auto Generate
          </button>
          <button className="btn-primary" onClick={() => setShowAddForm(true)}>
            Add Tribute
          </button>
        </div>
      </div>

      <Modal isOpen={showAddForm} onClose={() => setShowAddForm(false)} title="Add New Tribute">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>To City:</label>
            <input
              type="text"
              value={formData.to_city}
              onChange={(e) => setFormData({...formData, to_city: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Amount:</label>
            <input
              type="number"
              value={formData.amount}
              onChange={(e) => setFormData({...formData, amount: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Type:</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
            >
              <option value="Gold">Gold</option>
              <option value="Goods">Goods</option>
              <option value="Services">Services</option>
            </select>
          </div>
          <div className="form-group">
            <label>Purpose:</label>
            <input
              type="text"
              value={formData.purpose}
              onChange={(e) => setFormData({...formData, purpose: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Due Date:</label>
            <input
              type="date"
              value={formData.due_date}
              onChange={(e) => setFormData({...formData, due_date: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Notes:</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows="3"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Add Tribute</button>
            <button type="button" onClick={() => setShowAddForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

      <div className="registry-grid">
        {city.tribute_records?.map(tribute => (
          <div key={tribute.id} className="registry-card">
            <div className="card-header">
              <h4>To: {tribute.to_city}</h4>
              <button 
                className="delete-btn"
                onClick={() => handleDelete(tribute.id)}
                title="Delete tribute"
              >
                🗑️
              </button>
            </div>
            <div className="card-details">
              <p><strong>Amount:</strong> {tribute.amount} {tribute.type}</p>
              <p><strong>Purpose:</strong> {tribute.purpose}</p>
              <p><strong>Due:</strong> {new Date(tribute.due_date).toLocaleDateString()}</p>
              <p><strong>Status:</strong> <span className={`status-${tribute.status?.toLowerCase() || 'pending'}`}>{tribute.status}</span></p>
              {tribute.notes && <p><strong>Notes:</strong> {tribute.notes}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Crime Registry
const CrimeRegistry = ({ city }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [crimeTypes, setCrimeTypes] = useState([]);
  const [formData, setFormData] = useState({
    criminal_name: '', crime_type: 'Petty Theft', description: '', punishment: '', fine_amount: '0', date_occurred: '', notes: ''
  });

  useEffect(() => {
    fetchCrimeTypes();
  }, []);

  const fetchCrimeTypes = async () => {
    try {
      const response = await fetch(`${API}/crime-types`);
      const data = await response.json();
      setCrimeTypes(data.crime_types || []);
    } catch (error) {
      console.error('Error fetching crime types:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/crimes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ...formData, 
          city_id: city.id,
          fine_amount: parseInt(formData.fine_amount),
          date_occurred: new Date(formData.date_occurred).toISOString()
        })
      });
      if (response.ok) {
        setShowAddForm(false);
        setFormData({ criminal_name: '', crime_type: 'Petty Theft', description: '', punishment: '', fine_amount: '0', date_occurred: '', notes: '' });
        window.location.reload();
      }
    } catch (error) {
      console.error('Error adding crime:', error);
    }
  };

  const handleDelete = async (crimeId) => {
    if (window.confirm('Are you sure you want to delete this crime record?')) {
      try {
        const response = await fetch(`${API}/crimes/${crimeId}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          window.location.reload();
        }
      } catch (error) {
        console.error('Error deleting crime:', error);
      }
    }
  };

  const handleAutoGenerate = async () => {
    try {
      const response = await fetch(`${API}/auto-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registry_type: 'crimes',
          city_id: city.id,
          count: Math.floor(Math.random() * 3) + 1 // 1-3 crimes
        })
      });
      if (response.ok) {
        window.location.reload();
      }
    } catch (error) {
      console.error('Error auto-generating crimes:', error);
    }
  };

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Crime Records</h3>
        <div className="registry-actions">
          <button className="btn-secondary" onClick={handleAutoGenerate}>
            Auto Generate
          </button>
          <button className="btn-primary" onClick={() => setShowAddForm(true)}>
            Add Crime
          </button>
        </div>
      </div>

      <Modal isOpen={showAddForm} onClose={() => setShowAddForm(false)} title="Add New Crime">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Criminal Name:</label>
            <input
              type="text"
              value={formData.criminal_name}
              onChange={(e) => setFormData({...formData, criminal_name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Crime Type:</label>
            <select
              value={formData.crime_type}
              onChange={(e) => setFormData({...formData, crime_type: e.target.value})}
            >
              {crimeTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Description:</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              rows="3"
              required
            />
          </div>
          <div className="form-group">
            <label>Punishment:</label>
            <input
              type="text"
              value={formData.punishment}
              onChange={(e) => setFormData({...formData, punishment: e.target.value})}
              placeholder="e.g., 30 days in jail"
            />
          </div>
          <div className="form-group">
            <label>Fine Amount (GP):</label>
            <input
              type="number"
              value={formData.fine_amount}
              onChange={(e) => setFormData({...formData, fine_amount: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label>Date Occurred:</label>
            <input
              type="date"
              value={formData.date_occurred}
              onChange={(e) => setFormData({...formData, date_occurred: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Notes:</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              rows="3"
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Add Crime</button>
            <button type="button" onClick={() => setShowAddForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

      <div className="registry-grid">
        {city.crime_records?.map(crime => (
          <div key={crime.id} className="registry-card">
            <div className="card-header">
              <h4>{crime.criminal_name}</h4>
              <button 
                className="delete-btn"
                onClick={() => handleDelete(crime.id)}
                title="Delete crime record"
              >
                🗑️
              </button>
            </div>
            <div className="card-details">
              <p><strong>Crime:</strong> {crime.crime_type}</p>
              <p><strong>Description:</strong> {crime.description}</p>
              <p><strong>Date:</strong> {new Date(crime.date_occurred).toLocaleDateString()}</p>
              <p><strong>Status:</strong> <span className={`status-${crime.status?.toLowerCase() || 'reported'}`}>{crime.status}</span></p>
              {crime.punishment && <p><strong>Punishment:</strong> {crime.punishment}</p>}
              {crime.fine_amount > 0 && <p><strong>Fine:</strong> {crime.fine_amount} GP</p>}
              {crime.notes && <p><strong>Notes:</strong> {crime.notes}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// City Dashboard Component with editing and government hierarchy
const CityDashboard = ({ city, activeTab, setActiveTab }) => {
  const [showEditForm, setShowEditForm] = useState(false);
  const [showGovtManagement, setShowGovtManagement] = useState(false);
  const [editFormData, setEditFormData] = useState({
    name: city?.name || '',
    governor: city?.governor || ''
  });

  if (!city) return <div className="loading">Loading city...</div>;

  const totalLivestockValue = city.livestock?.reduce((sum, animal) => sum + animal.value, 0) || 0;
  const totalSlaveValue = city.slaves?.reduce((sum, slave) => sum + slave.purchase_price, 0) || 0;

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/city/${city.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editFormData)
      });
      if (response.ok) {
        setShowEditForm(false);
        window.location.reload();
      }
    } catch (error) {
      console.error('Error updating city:', error);
    }
  };

  const handleRemoveOfficial = async (officialId) => {
    if (window.confirm('Are you sure you want to remove this official from their position?')) {
      try {
        const response = await fetch(`${API}/cities/${city.id}/government/${officialId}`, {
          method: 'DELETE'
        });
        if (response.ok) {
          window.location.reload();
        }
      } catch (error) {
        console.error('Error removing official:', error);
      }
    }
  };

  return (
    <div className="city-dashboard">
      <div className="city-header">
        <div className="city-header-content">
          <h1 className="city-title">{city.name}</h1>
          <p className="city-governor">Governor: {city.governor}</p>
          <button 
            className="edit-city-btn"
            onClick={() => setShowEditForm(true)}
            title="Edit city details"
          >
            ✏️ Edit
          </button>
        </div>
      </div>

      {/* Government Hierarchy Section */}
      <div className="government-section">
        <div className="government-header">
          <h2>Local Government Hierarchy</h2>
          <button 
            className="btn-primary manage-govt-btn" 
            onClick={() => setShowGovtManagement(true)}
          >
            Manage Positions
          </button>
        </div>
        <div className="government-hierarchy">
          {/* Governor at the top */}
          <div className="hierarchy-level governor-level">
            <div className="government-official governor-card">
              <div className="official-rank">Governor</div>
              <div className="official-name">{city.governor}</div>
            </div>
          </div>
          
          {/* High Council - Second Tier */}
          <div className="hierarchy-level high-council">
            <h4 className="tier-title">High Council</h4>
            <div className="officials-tier">
              {city.government_officials?.filter(official => 
                ['Captain of the Guard', 'Master of Coin', 'High Scribe', 'Court Wizard', 'Head Cleric'].includes(official.position)
              ).map(official => (
                <div key={official.id} className="government-official high-council-card">
                  <div className="official-rank">{official.position}</div>
                  <div className="official-name">{official.name}</div>
                  <button 
                    className="remove-official-btn"
                    onClick={() => handleRemoveOfficial(official.id)}
                    title="Remove from position"
                  >
                    ✖
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* Department Heads - Third Tier */}
          <div className="hierarchy-level department-heads">
            <h4 className="tier-title">Department Heads</h4>
            <div className="officials-tier">
              {city.government_officials?.filter(official => 
                ['Trade Minister', 'City Magistrate', 'Harbor Master', 'Master Builder', 'Tax Collector', 'Market Warden'].includes(official.position)
              ).map(official => (
                <div key={official.id} className="government-official department-card">
                  <div className="official-rank">{official.position}</div>
                  <div className="official-name">{official.name}</div>
                  <button 
                    className="remove-official-btn"
                    onClick={() => handleRemoveOfficial(official.id)}
                    title="Remove from position"
                  >
                    ✖
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* Minor Officials - Fourth Tier */}
          <div className="hierarchy-level minor-officials">
            <h4 className="tier-title">Administrative Staff</h4>
            <div className="officials-tier">
              {city.government_officials?.filter(official => 
                !['Captain of the Guard', 'Master of Coin', 'High Scribe', 'Court Wizard', 'Head Cleric',
                  'Trade Minister', 'City Magistrate', 'Harbor Master', 'Master Builder', 'Tax Collector', 'Market Warden'].includes(official.position)
              ).map(official => (
                <div key={official.id} className="government-official minor-card">
                  <div className="official-rank">{official.position}</div>
                  <div className="official-name">{official.name}</div>
                  <button 
                    className="remove-official-btn"
                    onClick={() => handleRemoveOfficial(official.id)}
                    title="Remove from position"
                  >
                    ✖
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* Show message if no officials */}
          {(!city.government_officials || city.government_officials.length === 0) && (
            <div className="no-officials">No government officials appointed</div>
          )}
        </div>
      </div>

      {/* Government Management Modal */}
      <Modal isOpen={showGovtManagement} onClose={() => setShowGovtManagement(false)} title="Manage Government Positions">
        <GovernmentManagement city={city} onClose={() => setShowGovtManagement(false)} />
      </Modal>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{city.population}</div>
          <div className="stat-label">Population</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{city.treasury}</div>
          <div className="stat-label">City Treasury (GP)</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{city.slaves?.length || 0}</div>
          <div className="stat-label">Slaves</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{totalLivestockValue}</div>
          <div className="stat-label">Livestock Value (GP)</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{city.garrison?.length || 0}</div>
          <div className="stat-label">Garrison Size</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{city.crime_records?.length || 0}</div>
          <div className="stat-label">Crime Records</div>
        </div>
      </div>

      <Modal isOpen={showEditForm} onClose={() => setShowEditForm(false)} title="Edit City Details">
        <form onSubmit={handleEditSubmit}>
          <div className="form-group">
            <label>City Name:</label>
            <input
              type="text"
              value={editFormData.name}
              onChange={(e) => setEditFormData({...editFormData, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Governor:</label>
            <input
              type="text"
              value={editFormData.governor}
              onChange={(e) => setEditFormData({...editFormData, governor: e.target.value})}
              required
            />
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Update City</button>
            <button type="button" onClick={() => setShowEditForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

      <RegistryTabs 
        city={city} 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
      />
    </div>
  );
};

// Main App Component
function App() {
  const [kingdom, setKingdom] = useState(null);
  const [currentView, setCurrentView] = useState('kingdom');
  const [activeTab, setActiveTab] = useState('Citizens');
  const [events, setEvents] = useState([]);
  const [autoEventsEnabled, setAutoEventsEnabled] = useState(true);
  const [wsConnection, setWsConnection] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  // Fetch initial data
  useEffect(() => {
    fetchKingdom();
    fetchEvents();
    fetchAutoEventsStatus();
    connectWebSocket();

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, []);

  const fetchKingdom = async () => {
    try {
      const response = await fetch(`${API}/kingdom`);
      const data = await response.json();
      setKingdom(data);
    } catch (error) {
      console.error('Error fetching kingdom:', error);
    }
  };

  const fetchEvents = async () => {
    try {
      const response = await fetch(`${API}/events`);
      const data = await response.json();
      setEvents(data);
    } catch (error) {
      console.error('Error fetching events:', error);
    }
  };

  const fetchAutoEventsStatus = async () => {
    try {
      const response = await fetch(`${API}/auto-events-status`);
      const data = await response.json();
      setAutoEventsEnabled(data.auto_events_enabled);
    } catch (error) {
      console.error('Error fetching auto events status:', error);
    }
  };

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(`${WS_URL}/api/ws`);
      
      ws.onopen = () => {
        setConnectionStatus('Connected - Live updates enabled');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_event') {
          setEvents(prevEvents => [data.event, ...prevEvents]);
          fetchKingdom();
        }
      };

      ws.onclose = () => {
        setConnectionStatus('Disconnected - Retrying...');
        setTimeout(connectWebSocket, 3000);
      };

      setWsConnection(ws);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setConnectionStatus('Connection failed');
    }
  };

  const handleToggleAutoEvents = async () => {
    try {
      const response = await fetch(`${API}/toggle-auto-events`, {
        method: 'POST'
      });
      const data = await response.json();
      setAutoEventsEnabled(data.auto_events_enabled);
    } catch (error) {
      console.error('Error toggling auto events:', error);
    }
  };

  const handleViewChange = (view) => {
    setCurrentView(view);
    setActiveTab('Citizens'); // Reset tab when changing views
  };

  if (!kingdom) return <div className="loading">Loading Faerûn...</div>;

  const getCurrentCity = () => {
    if (currentView === 'kingdom' || currentView === 'map') return null;
    return kingdom.cities?.find(city => city.id === currentView);
  };

  const currentCity = getCurrentCity();

  return (
    <div className="App">
      <div className="status-bar">
        <span className="status-text">{connectionStatus}</span>
      </div>
      
      <Navigation 
        currentView={currentView} 
        onViewChange={handleViewChange}
        kingdom={kingdom}
      />

      {currentView === 'kingdom' && (
        <KingdomDashboard 
          kingdom={kingdom} 
          events={events}
          autoEventsEnabled={autoEventsEnabled}
          onToggleAutoEvents={handleToggleAutoEvents}
        />
      )}

      {currentView === 'map' && (
        <FaerunMap 
          cities={kingdom.cities} 
          onCitySelect={handleViewChange}
        />
      )}

      {currentCity && (
        <CityDashboard 
          city={currentCity}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />
      )}
    </div>
  );
}

export default App;