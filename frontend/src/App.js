import React, { useState, useEffect } from "react";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// Kingdom Dashboard Component
const KingdomDashboard = ({ kingdom, onCitySelect, events }) => {
  if (!kingdom) return <div className="loading">Loading kingdom...</div>;

  const totalTreasury = kingdom.royal_treasury + (kingdom.cities?.reduce((sum, city) => sum + city.treasury, 0) || 0);

  return (
    <div className="kingdom-dashboard">
      <div className="kingdom-header">
        <h1 className="kingdom-title">{kingdom.name}</h1>
        <p className="kingdom-ruler">Ruled by {kingdom.ruler}</p>
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
      </div>

      <div className="cities-section">
        <h2>Cities of the Realm</h2>
        <div className="cities-grid">
          {kingdom.cities?.map(city => (
            <div key={city.id} className="city-card" onClick={() => onCitySelect(city)}>
              <h3>{city.name}</h3>
              <p className="governor">Governor: {city.governor}</p>
              <div className="city-stats">
                <span>{city.population} citizens</span>
                <span>{city.treasury} GP</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="events-section">
        <h2>Recent Kingdom Events</h2>
        <div className="events-feed">
          {events.slice(0, 10).map(event => (
            <div key={event.id} className="event-item">
              <div className="event-time">
                {new Date(event.timestamp).toLocaleTimeString()}
              </div>
              <div className="event-description">{event.description}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// City Dashboard Component  
const CityDashboard = ({ city, onBack, events }) => {
  if (!city) return <div className="loading">Loading city...</div>;

  const cityEvents = events.filter(event => event.city_name === city.name);

  return (
    <div className="city-dashboard">
      <div className="city-header">
        <button className="back-button" onClick={onBack}>← Back to Kingdom</button>
        <h1 className="city-title">{city.name}</h1>
        <p className="city-governor">Governor: {city.governor}</p>
      </div>

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
          <div className="stat-number">{city.citizens?.length || 0}</div>
          <div className="stat-label">Registered Citizens</div>
        </div>
      </div>

      <div className="citizens-section">
        <h2>Citizens Registry</h2>
        <div className="citizens-grid">
          {city.citizens?.map(citizen => (
            <div key={citizen.id} className="citizen-card">
              <h3>{citizen.name}</h3>
              <p className="occupation">{citizen.occupation}</p>
              <p className="age">Age: {citizen.age}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="events-section">
        <h2>Local Events</h2>
        <div className="events-feed">
          {cityEvents.slice(0, 10).map(event => (
            <div key={event.id} className="event-item">
              <div className="event-time">
                {new Date(event.timestamp).toLocaleTimeString()}
              </div>
              <div className="event-description">{event.description}</div>
            </div>
          ))}
          {cityEvents.length === 0 && (
            <div className="no-events">No recent events in this city</div>
          )}
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [kingdom, setKingdom] = useState(null);
  const [selectedCity, setSelectedCity] = useState(null);
  const [events, setEvents] = useState([]);
  const [wsConnection, setWsConnection] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  // Fetch initial data
  useEffect(() => {
    fetchKingdom();
    fetchEvents();
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

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(`${WS_URL}/api/ws`);
      
      ws.onopen = () => {
        setConnectionStatus('Connected - Live updates enabled');
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_event') {
          setEvents(prevEvents => [data.event, ...prevEvents]);
          // Refresh kingdom data to get updated stats
          fetchKingdom();
        }
      };

      ws.onclose = () => {
        setConnectionStatus('Disconnected - Retrying...');
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('Connection error');
      };

      setWsConnection(ws);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setConnectionStatus('Connection failed');
    }
  };

  const handleCitySelect = (city) => {
    setSelectedCity(city);
  };

  const handleBackToKingdom = () => {
    setSelectedCity(null);
  };

  return (
    <div className="App">
      <div className="status-bar">
        <span className="status-text">{connectionStatus}</span>
      </div>
      
      {selectedCity ? (
        <CityDashboard 
          city={selectedCity} 
          onBack={handleBackToKingdom}
          events={events}
        />
      ) : (
        <KingdomDashboard 
          kingdom={kingdom} 
          onCitySelect={handleCitySelect}
          events={events}
        />
      )}
    </div>
  );
}

export default App;