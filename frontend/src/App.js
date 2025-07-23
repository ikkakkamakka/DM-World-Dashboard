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

// Faerûn Map Component
const FaerunMap = ({ cities, onCitySelect, onMapClick }) => {
  const handleMapClick = (e) => {
    const rect = e.target.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    onMapClick(x, y);
  };

  return (
    <div className="map-container">
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
              onCitySelect(city);
            }}
            title={city.name}
          >
            📍
          </div>
        ))}
      </div>
      <p className="map-instructions">
        Click anywhere on the map to place a new city, or click existing markers to manage cities
      </p>
    </div>
  );
};

// Add City Form
const AddCityForm = ({ x, y, onSubmit, onCancel }) => {
  const [name, setName] = useState('');
  const [governor, setGovernor] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name && governor) {
      onSubmit({ name, governor, x_coordinate: x, y_coordinate: y });
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
  const tabs = ['Citizens', 'Livestock', 'Garrison', 'Tribute', 'Crime'];

  return (
    <div className="registry-tabs">
      <div className="tab-buttons">
        {tabs.map(tab => (
          <button
            key={tab}
            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab} ({city[tab.toLowerCase()]?.length || 0})
          </button>
        ))}
      </div>
      
      <div className="tab-content">
        {activeTab === 'Citizens' && <CitizensRegistry city={city} />}
        {activeTab === 'Livestock' && <LivestockRegistry city={city} />}
        {activeTab === 'Garrison' && <GarrisonRegistry city={city} />}
        {activeTab === 'Tribute' && <TributeRegistry city={city} />}
        {activeTab === 'Crime' && <CrimeRegistry city={city} />}
      </div>
    </div>
  );
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
        window.location.reload(); // Refresh to show new data
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

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Citizens Registry</h3>
        <button className="btn-primary" onClick={() => setShowAddForm(true)}>
          Add Citizen
        </button>
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
              <p><strong>Health:</strong> <span className={`health-${citizen.health.toLowerCase()}`}>{citizen.health}</span></p>
              {citizen.notes && <p><strong>Notes:</strong> {citizen.notes}</p>}
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

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Livestock Registry</h3>
        <button className="btn-primary" onClick={() => setShowAddForm(true)}>
          Add Livestock
        </button>
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
              <p><strong>Health:</strong> <span className={`health-${animal.health.toLowerCase()}`}>{animal.health}</span></p>
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

  return (
    <div className="registry-section">
      <div className="registry-header">
        <h3>Garrison Registry</h3>
        <button className="btn-primary" onClick={() => setShowAddForm(true)}>
          Add Soldier
        </button>
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
              <p><strong>Status:</strong> <span className={`status-${soldier.status.toLowerCase()}`}>{soldier.status}</span></p>
              {soldier.equipment.length > 0 && (
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

// Placeholder for other registries
const TributeRegistry = ({ city }) => (
  <div className="registry-section">
    <h3>Tribute Ledger</h3>
    <p>Tribute tracking coming soon...</p>
  </div>
);

const CrimeRegistry = ({ city }) => (
  <div className="registry-section">
    <h3>Crime Records</h3>
    <p>Crime tracking coming soon...</p>
  </div>
);

// Main App Component
function App() {
  const [kingdom, setKingdom] = useState(null);
  const [selectedCity, setSelectedCity] = useState(null);
  const [showAddCityForm, setShowAddCityForm] = useState(false);
  const [newCityCoords, setNewCityCoords] = useState({ x: 0, y: 0 });
  const [activeTab, setActiveTab] = useState('Citizens');
  const [wsConnection, setWsConnection] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  // Fetch initial data
  useEffect(() => {
    fetchKingdom();
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

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(`${WS_URL}/api/ws`);
      
      ws.onopen = () => {
        setConnectionStatus('Connected - Live updates enabled');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // Handle real-time updates
        fetchKingdom();
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

  const handleMapClick = (x, y) => {
    setNewCityCoords({ x, y });
    setShowAddCityForm(true);
  };

  const handleCreateCity = async (cityData) => {
    try {
      const response = await fetch(`${API}/cities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cityData)
      });
      
      if (response.ok) {
        setShowAddCityForm(false);
        fetchKingdom();
      }
    } catch (error) {
      console.error('Error creating city:', error);
    }
  };

  const handleCitySelect = (city) => {
    setSelectedCity(city);
  };

  const handleBackToMap = () => {
    setSelectedCity(null);
  };

  if (!kingdom) return <div className="loading">Loading Faerûn...</div>;

  return (
    <div className="App">
      <div className="status-bar">
        <span className="status-text">{connectionStatus}</span>
      </div>
      
      <div className="kingdom-header">
        <h1 className="kingdom-title">{kingdom.name}</h1>
        <p className="kingdom-ruler">Campaign managed by {kingdom.ruler}</p>
      </div>

      {selectedCity ? (
        <div className="city-management">
          <div className="city-header">
            <button className="back-button" onClick={handleBackToMap}>← Back to Map</button>
            <h2>{selectedCity.name}</h2>
            <p>Governor: {selectedCity.governor}</p>
          </div>
          
          <div className="city-stats">
            <div className="stat-card">
              <div className="stat-number">{selectedCity.population}</div>
              <div className="stat-label">Population</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{selectedCity.treasury}</div>
              <div className="stat-label">Treasury (GP)</div>
            </div>
          </div>

          <RegistryTabs 
            city={selectedCity} 
            activeTab={activeTab} 
            setActiveTab={setActiveTab} 
          />
        </div>
      ) : (
        <>
          <div className="kingdom-overview">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-number">{kingdom.total_population}</div>
                <div className="stat-label">Total Population</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{kingdom.cities?.length || 0}</div>
                <div className="stat-label">Cities</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{kingdom.royal_treasury}</div>
                <div className="stat-label">Royal Treasury (GP)</div>
              </div>
            </div>
          </div>

          <FaerunMap 
            cities={kingdom.cities} 
            onCitySelect={handleCitySelect}
            onMapClick={handleMapClick}
          />

          <Modal 
            isOpen={showAddCityForm} 
            onClose={() => setShowAddCityForm(false)} 
            title="Create New City"
          >
            <AddCityForm
              x={newCityCoords.x}
              y={newCityCoords.y}
              onSubmit={handleCreateCity}
              onCancel={() => setShowAddCityForm(false)}
            />
          </Modal>
        </>
      )}
    </div>
  );
}

export default App;