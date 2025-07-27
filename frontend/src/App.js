import React, { useState, useEffect } from "react";
import "./App.css";
import { AuthProvider, useAuth, AuthScreen, UserProfile } from './Auth';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

// Enhanced Harptos Calendar System for D&D
const HARPTOS_MONTHS = [
  { name: 'Hammer', alias: 'Deepwinter', days: 30 },
  { name: 'Alturiak', alias: 'The Claw of Winter', days: 30 },
  { name: 'Ches', alias: 'The Claw of the Sunsets', days: 30 },
  { name: 'Tarsakh', alias: 'The Claw of the Storms', days: 30 },
  { name: 'Mirtul', alias: 'The Melting', days: 30 },
  { name: 'Kythorn', alias: 'The Time of Flowers', days: 30 },
  { name: 'Flamerule', alias: 'Summertide', days: 30 },
  { name: 'Eleasis', alias: 'Highsun', days: 30 },
  { name: 'Eleint', alias: 'The Fading', days: 30 },
  { name: 'Marpenoth', alias: 'Leaffall', days: 30 },
  { name: 'Uktar', alias: 'The Rotting', days: 30 },
  { name: 'Nightal', alias: 'The Drawing Down', days: 30 }
];

const SPECIAL_DAYS = [
  { name: 'Midwinter', after_month: 0, description: 'A festival day of reflection and celebration', type: 'holiday' },
  { name: 'Greengrass', after_month: 3, description: 'Celebrates the arrival of spring', type: 'holiday' },
  { name: 'Midsummer', after_month: 6, description: 'A day of celebration and festivity', type: 'holiday' },
  { name: 'Highharvestide', after_month: 8, description: 'Marks the harvest time', type: 'holiday' },
  { name: 'The Feast of the Moon', after_month: 10, description: 'Honors the dead and ancestors', type: 'holiday' }
];

// Fixed DR to real world time conversion
const convertRealTimeToHarptos = () => {
  const now = new Date();
  
  // Base conversion: 1492 DR = 2020 AD (fixed reference point)
  const DR_BASE_YEAR = 1492;
  const AD_BASE_YEAR = 2020;
  
  // Calculate current DR year
  const drYear = DR_BASE_YEAR + (now.getFullYear() - AD_BASE_YEAR);
  
  // Get day of year (1-365/366)
  const dayOfYear = now.getDate() + Math.floor((now - new Date(now.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
  
  // Convert day of year to Harptos month and day
  let remainingDays = dayOfYear - 1; // 0-indexed
  let currentMonth = 0;
  let currentDay = 1;
  let specialDay = null;
  
  for (let month = 0; month < HARPTOS_MONTHS.length; month++) {
    // Check for special day after this month
    const specialBefore = SPECIAL_DAYS.find(sd => sd.after_month === month);
    if (specialBefore && remainingDays === 0) {
      specialDay = specialBefore.name;
      break;
    } else if (specialBefore && remainingDays > 0) {
      remainingDays--; // Account for special day
    }
    
    if (remainingDays < HARPTOS_MONTHS[month].days) {
      currentMonth = month;
      currentDay = remainingDays + 1;
      break;
    }
    
    remainingDays -= HARPTOS_MONTHS[month].days;
  }
  
  // Calculate tenday and season
  const tenday = Math.min(3, Math.floor((currentDay - 1) / 10) + 1);
  
  let season;
  if ([11, 0, 1].includes(currentMonth)) season = 'winter';
  else if ([2, 3, 4].includes(currentMonth)) season = 'spring';
  else if ([5, 6, 7].includes(currentMonth)) season = 'summer';
  else season = 'autumn';
  
  // Check for Shieldmeet (leap year every 4 years)
  const isShieldmeetYear = drYear % 4 === 0;
  if (isShieldmeetYear && dayOfYear > 180 && dayOfYear < 182) { // Around midsummer
    specialDay = 'Shieldmeet';
  }
  
  return {
    drYear,
    month: currentMonth,
    day: currentDay,
    tenday,
    season,
    monthName: HARPTOS_MONTHS[currentMonth]?.name || 'Unknown',
    monthAlias: HARPTOS_MONTHS[currentMonth]?.alias || '',
    specialDay,
    isShieldmeetYear,
    realTime: now
  };
};

const getSeasonalEvents = (harptos) => {
  const events = [];
  const { month, day, monthName, specialDay } = harptos;
  
  // Special day events
  if (specialDay) {
    events.push({
      type: 'special_day',
      title: specialDay.name,
      description: specialDay.description,
      isToday: true
    });
  }
  
  // Monthly seasonal events
  switch (month) {
    case 0: // Hammer
      events.push({ type: 'season', title: 'Deep Winter', description: 'The coldest time of year, when travel is treacherous' });
      break;
    case 1: // Alturiak
      events.push({ type: 'season', title: 'Winter\'s Grip', description: 'The harshest winter storms rage across the land' });
      break;
    case 2: // Ches
      events.push({ type: 'season', title: 'Late Winter', description: 'The first hints of spring begin to appear' });
      break;
    case 3: // Tarsakh
      events.push({ type: 'season', title: 'Storm Season', description: 'Violent storms herald the changing season' });
      break;
    case 4: // Mirtul
      events.push({ type: 'season', title: 'Spring Thaw', description: 'Ice melts and the land awakens from winter slumber' });
      break;
    case 5: // Kythorn
      events.push({ type: 'season', title: 'Flowering', description: 'Flowers bloom and life returns to the world' });
      break;
    case 6: // Flamerule
      events.push({ type: 'season', title: 'High Summer', description: 'The height of summer warmth and growth' });
      break;
    case 7: // Eleasis
      events.push({ type: 'season', title: 'Late Summer', description: 'The peak of the year\'s heat and abundance' });
      break;
    case 8: // Eleint
      events.push({ type: 'season', title: 'Early Autumn', description: 'Leaves begin to change and harvests are gathered' });
      break;
    case 9: // Marpenoth
      events.push({ type: 'season', title: 'Autumn Harvest', description: 'The time of great harvests and preparation for winter' });
      break;
    case 10: // Uktar
      events.push({ type: 'season', title: 'Late Autumn', description: 'Decay and preparation for the coming cold' });
      break;
    case 11: // Nightal
      events.push({ type: 'season', title: 'Early Winter', description: 'The year draws to a close as winter approaches' });
      break;
  }
  
  return events;
};

// Enhanced Harptos Calendar Component with Full Event Management
const HarptosCalendar = ({ kingdom, isVisible }) => {
  const [campaignDate, setCampaignDate] = useState(null);
  const [events, setEvents] = useState([]);
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [calendarMode, setCalendarMode] = useState('auto'); // 'auto' or 'manual'
  const [viewMode, setViewMode] = useState('calendar'); // 'calendar', 'events', 'upcoming'
  const [showEventForm, setShowEventForm] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  
  // Event form state
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    event_type: 'custom',
    city_name: '',
    event_date: { dr_year: 1492, month: 0, day: 1 },
    is_recurring: false
  });

  // Manual date control
  const [manualDate, setManualDate] = useState({ dr_year: 1492, month: 0, day: 1 });
  
  // Year names cache
  const [drYearNames, setDrYearNames] = useState(null);
  const [isLoadingYearNames, setIsLoadingYearNames] = useState(false);

  // Load DR year names from JSON file (cached)
  const loadDrYearNames = async () => {
    if (drYearNames || isLoadingYearNames) return; // Already loaded or loading
    
    setIsLoadingYearNames(true);
    try {
      const response = await fetch('/dr_year_names.json');
      if (response.ok) {
        const yearNames = await response.json();
        setDrYearNames(yearNames);
      } else {
        console.warn('Failed to load DR year names, using numeric fallback');
        setDrYearNames({});
      }
    } catch (error) {
      console.warn('Error loading DR year names:', error);
      setDrYearNames({});
    } finally {
      setIsLoadingYearNames(false);
    }
  };

  useEffect(() => {
    if (isVisible && kingdom) {
      loadDrYearNames(); // Load year names on first render
      fetchCampaignDate();
      fetchCalendarEvents();
      fetchUpcomingEvents();
      
      // Update every minute if in auto mode
      const interval = setInterval(() => {
        if (calendarMode === 'auto') {
          fetchCampaignDate();
        }
      }, 60000);
      
      return () => clearInterval(interval);
    }
  }, [isVisible, kingdom, calendarMode]);

  const fetchCampaignDate = async () => {
    if (!kingdom) return;
    try {
      const response = await fetch(`${API}/campaign-date/${kingdom.id}`);
      if (response.ok) {
        const date = await response.json();
        setCampaignDate(date);
        if (calendarMode === 'manual') {
          setManualDate({
            dr_year: date.dr_year,
            month: date.month,
            day: date.day
          });
        }
      }
    } catch (error) {
      console.error('Error fetching campaign date:', error);
    }
  };

  const fetchCalendarEvents = async () => {
    if (!kingdom) return;
    try {
      const response = await fetch(`${API}/calendar-events/${kingdom.id}`);
      if (response.ok) {
        const events = await response.json();
        setEvents(events);
      }
    } catch (error) {
      console.error('Error fetching calendar events:', error);
    }
  };

  const fetchUpcomingEvents = async () => {
    if (!kingdom) return;
    try {
      const response = await fetch(`${API}/calendar-events/${kingdom.id}/upcoming?days=10`);
      if (response.ok) {
        const upcomingEvents = await response.json();
        setUpcomingEvents(upcomingEvents);
      }
    } catch (error) {
      console.error('Error fetching upcoming events:', error);
    }
  };

  const handleManualDateUpdate = async () => {
    if (!kingdom) return;
    try {
      const response = await fetch(`${API}/campaign-date/${kingdom.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(manualDate)
      });
      
      if (response.ok) {
        fetchCampaignDate();
        fetchUpcomingEvents();
      }
    } catch (error) {
      console.error('Error updating campaign date:', error);
    }
  };

  const handleCreateEvent = async () => {
    if (!kingdom) return;
    try {
      const eventData = { ...eventForm };
      const url = editingEvent 
        ? `${API}/calendar-events/${editingEvent.id}`
        : `${API}/calendar-events?kingdom_id=${kingdom.id}`;
      
      const method = editingEvent ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventData)
      });
      
      if (response.ok) {
        setShowEventForm(false);
        setEditingEvent(null);
        resetEventForm();
        fetchCalendarEvents();
        fetchUpcomingEvents();
      }
    } catch (error) {
      console.error('Error creating/updating event:', error);
    }
  };

  const handleDeleteEvent = async (eventId) => {
    try {
      const response = await fetch(`${API}/calendar-events/${eventId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        fetchCalendarEvents();
        fetchUpcomingEvents();
      }
    } catch (error) {
      console.error('Error deleting event:', error);
    }
  };

  const generateCityEvents = async () => {
    if (!kingdom) return;
    try {
      const response = await fetch(`${API}/calendar-events/generate-city-events?kingdom_id=${kingdom.id}&count=5&date_range_days=30`, {
        method: 'POST'
      });
      
      if (response.ok) {
        fetchCalendarEvents();
        fetchUpcomingEvents();
      }
    } catch (error) {
      console.error('Error generating city events:', error);
    }
  };

  const resetEventForm = () => {
    setEventForm({
      title: '',
      description: '',
      event_type: 'custom',
      city_name: '',
      event_date: campaignDate ? 
        { dr_year: campaignDate.dr_year, month: campaignDate.month, day: campaignDate.day } :
        { dr_year: 1492, month: 0, day: 1 },
      is_recurring: false
    });
  };

  const openEditEvent = (event) => {
    setEditingEvent(event);
    setEventForm({
      title: event.title,
      description: event.description,
      event_type: event.event_type,
      city_name: event.city_name || '',
      event_date: event.event_date,
      is_recurring: event.is_recurring
    });
    setShowEventForm(true);
  };

  const getEventsForDate = (dr_year, month, day) => {
    return events.filter(event => 
      event.event_date.dr_year === dr_year && 
      event.event_date.month === month && 
      event.event_date.day === day
    );
  };

  const getHolidaysForDate = (month, day) => {
    return SPECIAL_DAYS.filter(special => 
      special.after_month === month && day === 30
    );
  };

  const formatHarptosDate = (dateObj) => {
    const yearString = (dateObj.dr_year || dateObj.drYear || 1492).toString();
    const yearName = drYearNames?.[yearString];
    
    // Create base date string
    let baseDate;
    if (dateObj.special_day) {
      baseDate = `${dateObj.special_day}, ${yearString} DR`;
    } else {
      baseDate = `${dateObj.day} ${HARPTOS_MONTHS[dateObj.month]?.name || 'Unknown'}, ${yearString} DR`;
    }
    
    // Add year name if available
    if (yearName) {
      return `${baseDate} – ${yearName}`;
    }
    
    return baseDate;
  };

  const formatEventDate = (eventDate) => {
    const yearString = eventDate.dr_year.toString();
    const yearName = drYearNames?.[yearString];
    
    // Create base date string
    const baseDate = `${eventDate.day} ${HARPTOS_MONTHS[eventDate.month]?.name}, ${yearString} DR`;
    
    // Add year name if available
    if (yearName) {
      return `${baseDate} – ${yearName}`;
    }
    
    return baseDate;
  };

  const formatCalendarDayTooltip = (day, month, year) => {
    // Handle undefined year parameter
    if (year === undefined || year === null) {
      return `${day} ${HARPTOS_MONTHS[month]?.name || 'Unknown'}`;
    }
    
    const yearString = year.toString();
    const yearName = drYearNames?.[yearString];
    
    // Create base date string
    const baseDate = `${day} ${HARPTOS_MONTHS[month]?.name}, ${yearString} DR`;
    
    // Add year name if available
    if (yearName) {
      return `${baseDate} – ${yearName}`;
    }
    
    return baseDate;
  };

  const getEventIcon = (eventType) => {
    switch(eventType) {
      case 'holiday': return '🎉';
      case 'city': return '🏘️';
      case 'custom': return '📝';
      default: return '📅';
    }
  };

  const getEventTypeColor = (eventType) => {
    switch(eventType) {
      case 'holiday': return '#d4af37';
      case 'city': return '#4ade80';
      case 'custom': return '#8b5cf6';
      default: return '#6b7280';
    }
  };

  if (!isVisible || !kingdom) return null;

  const displayDate = campaignDate || convertRealTimeToHarptos();

  return (
    <div className="harptos-calendar">
      <div className="calendar-header">
        <h2>🗓️ Harptos Calendar</h2>
        <div className="calendar-controls">
          <div className="calendar-mode-selector">
            <button 
              className={`mode-btn ${calendarMode === 'auto' ? 'active' : ''}`}
              onClick={() => setCalendarMode('auto')}
            >
              Auto Time
            </button>
            <button 
              className={`mode-btn ${calendarMode === 'manual' ? 'active' : ''}`}
              onClick={() => setCalendarMode('manual')}
            >
              Manual Control
            </button>
          </div>
          <div className="view-mode-selector">
            <button 
              className={`mode-btn ${viewMode === 'calendar' ? 'active' : ''}`}
              onClick={() => setViewMode('calendar')}
            >
              Calendar
            </button>
            <button 
              className={`mode-btn ${viewMode === 'upcoming' ? 'active' : ''}`}
              onClick={() => setViewMode('upcoming')}
            >
              Upcoming
            </button>
            <button 
              className={`mode-btn ${viewMode === 'events' ? 'active' : ''}`}
              onClick={() => setViewMode('events')}
            >
              All Events
            </button>
          </div>
        </div>
      </div>

      <div className="current-date-display">
        <h3>{formatHarptosDate(displayDate)}</h3>
        <p className="season-info">
          {displayDate.season && (
            <span className={`season-${displayDate.season}`}>
              {displayDate.season.charAt(0).toUpperCase() + displayDate.season.slice(1)} - Tenday {displayDate.tenday || 1}
            </span>
          )}
        </p>
        {displayDate.special_day && (
          <div className="special-day-notice">
            🎉 Today is {displayDate.special_day}!
          </div>
        )}
      </div>

      {calendarMode === 'manual' && (
        <div className="manual-date-controls">
          <h4>DM Date Control</h4>
          <div className="date-inputs">
            <input
              type="number"
              placeholder="Year"
              value={manualDate.dr_year}
              onChange={(e) => setManualDate(prev => ({...prev, dr_year: parseInt(e.target.value) || 1492}))}
            />
            <select 
              value={manualDate.month}
              onChange={(e) => setManualDate(prev => ({...prev, month: parseInt(e.target.value)}))}
            >
              {HARPTOS_MONTHS.map((month, index) => (
                <option key={index} value={index}>
                  {month.name} ({month.alias})
                </option>
              ))}
            </select>
            <input
              type="number"
              placeholder="Day"
              min="1"
              max="30"
              value={manualDate.day}
              onChange={(e) => setManualDate(prev => ({...prev, day: parseInt(e.target.value) || 1}))}
            />
            <button className="btn-primary" onClick={handleManualDateUpdate}>
              Update Campaign Date
            </button>
          </div>
        </div>
      )}

      <div className="calendar-actions">
        <button className="btn-primary" onClick={() => {
          resetEventForm();
          setShowEventForm(true);
        }}>
          Add Custom Event
        </button>
        <button className="btn-secondary" onClick={generateCityEvents}>
          Generate City Events
        </button>
      </div>

      {viewMode === 'calendar' && (
        <div className="calendar-grid">
          <h4>Month of {HARPTOS_MONTHS[displayDate.month]?.name || 'Unknown'}</h4>
          <div className="days-grid">
            {Array.from({ length: 30 }, (_, i) => {
              const day = i + 1;
              const dayEvents = getEventsForDate(displayDate.dr_year || displayDate.drYear, displayDate.month, day);
              const holidays = getHolidaysForDate(displayDate.month, day);
              const isToday = displayDate.day === day;
              const hasEvents = dayEvents.length > 0 || holidays.length > 0;
              
              return (
                <div 
                  key={day} 
                  className={`calendar-day ${isToday ? 'today' : ''} ${hasEvents ? 'has-events' : ''}`}
                  onClick={() => setSelectedDate({ dr_year: displayDate.dr_year || displayDate.drYear, month: displayDate.month, day })}
                  title={
                    hasEvents 
                      ? `${holidays.map(h => `🎉 ${h.name}`).join(', ')} ${dayEvents.map(e => `${getEventIcon(e.event_type)} ${e.city_name ? `${e.title} – ${e.city_name}` : e.title}`).join(', ')}`
                      : formatCalendarDayTooltip(day, displayDate.month, displayDate.dr_year || displayDate.drYear)
                  }
                >
                  <span className="day-number">{day}</span>
                  {hasEvents && (
                    <div className="event-indicators">
                      {holidays.map((holiday, idx) => (
                        <span key={idx} className="holiday-indicator">🎉</span>
                      ))}
                      {dayEvents.map((event, idx) => (
                        <span 
                          key={idx} 
                          className="event-indicator"
                          style={{ color: getEventTypeColor(event.event_type) }}
                        >
                          {getEventIcon(event.event_type)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {viewMode === 'upcoming' && (
        <div className="upcoming-events">
          <h4>Next 10 Days</h4>
          {upcomingEvents.length === 0 ? (
            <p>No upcoming events scheduled.</p>
          ) : (
            <div className="upcoming-list">
              {upcomingEvents.map((event, index) => (
                <div key={event.id || index} className="upcoming-event">
                  <div className="event-date">
                    {event.days_from_now === 0 ? 'Today' : `In ${event.days_from_now} day${event.days_from_now > 1 ? 's' : ''}`}
                  </div>
                  <div className="event-details">
                    <span className="event-icon" style={{ color: getEventTypeColor(event.event_type) }}>
                      {getEventIcon(event.event_type)}
                    </span>
                    <div>
                      <div className="event-title">
                        {event.city_name ? `${event.title} – ${event.city_name}` : event.title}
                      </div>
                      <div className="event-description">{event.description}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {viewMode === 'events' && (
        <div className="all-events">
          <h4>All Scheduled Events</h4>
          <div className="events-list">
            {events.map(event => (
              <div key={event.id} className="event-card">
                <div className="event-header">
                  <div className="event-header-left">
                    <span className="event-type-icon" style={{ color: getEventTypeColor(event.event_type) }}>
                      {getEventIcon(event.event_type)}
                    </span>
                    <div className="event-title-section">
                      <div className="event-title">{event.city_name ? `${event.title} – ${event.city_name}` : event.title}</div>
                    </div>
                  </div>
                  <div className="event-actions">
                    <button onClick={() => openEditEvent(event)}>✏️ Edit</button>
                    <button onClick={() => handleDeleteEvent(event.id)}>🗑️ Delete</button>
                  </div>
                </div>
                <div className="event-info">
                  <div>Date: {formatEventDate(event.event_date)}</div>
                  {event.city_name && <div>City: {event.city_name}</div>}
                  <div>Type: {event.event_type.charAt(0).toUpperCase() + event.event_type.slice(1)}</div>
                  <div>Created by: {event.created_by}</div>
                </div>
                <div className="event-description">{event.description}</div>
              </div>
            ))}
            {events.length === 0 && (
              <div style={{ textAlign: 'center', color: '#c4b5a0', fontStyle: 'italic', padding: '2rem' }}>
                No events scheduled yet. Create your first event!
              </div>
            )}
          </div>
        </div>
      )}

      {/* Event Form Modal */}
      <Modal isOpen={showEventForm} onClose={() => {
        setShowEventForm(false);
        setEditingEvent(null);
        resetEventForm();
      }} title={editingEvent ? 'Edit Event' : 'Create New Event'}>
        <div className="event-form">
          <input
            type="text"
            placeholder="Event Title"
            value={eventForm.title}
            onChange={(e) => setEventForm(prev => ({...prev, title: e.target.value}))}
          />
          <textarea
            placeholder="Event Description"
            value={eventForm.description}
            onChange={(e) => setEventForm(prev => ({...prev, description: e.target.value}))}
          />
          <select 
            value={eventForm.event_type}
            onChange={(e) => setEventForm(prev => ({...prev, event_type: e.target.value}))}
          >
            <option value="custom">Custom Event</option>
            <option value="holiday">Holiday/Festival</option>
            <option value="city">City Event</option>
          </select>
          <input
            type="text"
            placeholder="City Name (optional)"
            value={eventForm.city_name}
            onChange={(e) => setEventForm(prev => ({...prev, city_name: e.target.value}))}
          />
          <div className="date-inputs">
            <input
              type="number"
              placeholder="Year"
              value={eventForm.event_date.dr_year}
              onChange={(e) => setEventForm(prev => ({
                ...prev, 
                event_date: {...prev.event_date, dr_year: parseInt(e.target.value) || 1492}
              }))}
            />
            <select 
              value={eventForm.event_date.month}
              onChange={(e) => setEventForm(prev => ({
                ...prev, 
                event_date: {...prev.event_date, month: parseInt(e.target.value)}
              }))}
            >
              {HARPTOS_MONTHS.map((month, index) => (
                <option key={index} value={index}>{month.name}</option>
              ))}
            </select>
            <input
              type="number"
              placeholder="Day"
              min="1"
              max="30"
              value={eventForm.event_date.day}
              onChange={(e) => setEventForm(prev => ({
                ...prev, 
                event_date: {...prev.event_date, day: parseInt(e.target.value) || 1}
              }))}
            />
          </div>
          <div className="form-actions">
            <button className="btn-primary" onClick={handleCreateEvent}>
              {editingEvent ? 'Update Event' : 'Create Event'}
            </button>
            <button className="btn-secondary" onClick={() => {
              setShowEventForm(false);
              setEditingEvent(null);
              resetEventForm();
            }}>
              Cancel
            </button>
          </div>
        </div>
      </Modal>

      {/* Special Days Info */}
      <div className="special-days-info">
        <h4>Faerûnian Holidays</h4>
        <div className="special-days-list">
          {SPECIAL_DAYS.map((specialDay, index) => (
            <div key={index} className="special-day-item">
              <span className="special-day-name">🎉 {specialDay.name}</span>
              <span className="special-day-desc">{specialDay.description}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
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

// Navigation Component with Multi-Kingdom Support
const Navigation = ({ currentView, onViewChange, kingdom, onBackToSelector }) => {
  return (
    <div className="navigation">
      <button 
        className="nav-button back-to-selector"
        onClick={onBackToSelector}
        title="Switch Kingdom"
      >
        🏛️ Switch Kingdom
      </button>
      
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
      <button 
        className={`nav-button ${currentView === 'calendar' ? 'active' : ''}`}
        onClick={() => onViewChange('calendar')}
        title="Harptos Calendar System"
      >
        📅 Calendar
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

// Kingdom Dashboard Component with Totals and Kingdom Editing
const KingdomDashboard = ({ kingdom, events, autoEventsEnabled, onToggleAutoEvents }) => {
  const [showKingdomEditForm, setShowKingdomEditForm] = useState(false);
  const [kingdomEditData, setKingdomEditData] = useState({
    name: kingdom?.name || '',
    ruler: kingdom?.ruler || '',
    government_type: kingdom?.government_type || 'Monarchy'
  });

  const governmentTypes = [
    'Monarchy', 'Republic', 'Empire', 'Council', 'Federation', 
    'Theocracy', 'Magocracy', 'Oligarchy', 'Democracy', 'Confederation'
  ];

  if (!kingdom) return <div className="loading">Loading kingdom...</div>;

  const handleKingdomEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/kingdom`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(kingdomEditData)
      });
      if (response.ok) {
        setShowKingdomEditForm(false);
        window.location.reload();
      }
    } catch (error) {
      console.error('Error updating kingdom:', error);
    }
  };

  const totalTreasury = kingdom.royal_treasury + (kingdom.cities?.reduce((sum, city) => sum + city.treasury, 0) || 0);
  const totalSlaves = kingdom.cities?.reduce((sum, city) => sum + (city.slaves?.length || 0), 0) || 0;
  const totalLivestock = kingdom.cities?.reduce((sum, city) => sum + (city.livestock?.length || 0), 0) || 0;
  const totalSoldiers = kingdom.cities?.reduce((sum, city) => sum + (city.garrison?.length || 0), 0) || 0;
  const totalCrimes = kingdom.cities?.reduce((sum, city) => sum + (city.crime_records?.length || 0), 0) || 0;

  return (
    <div className="kingdom-dashboard">
      <div className="kingdom-header">
        <div className="kingdom-header-content">
          <h1 className="kingdom-title">{kingdom.name}</h1>
          <p className="kingdom-ruler">Campaign managed by {kingdom.ruler}</p>
          <p className="kingdom-government">Government Type: {kingdom.government_type || 'Monarchy'}</p>
          <button 
            className="edit-kingdom-btn"
            onClick={() => setShowKingdomEditForm(true)}
            title="Edit kingdom details"
          >
            ✏️ Edit Kingdom
          </button>
        </div>
      </div>

      {/* Kingdom Edit Modal */}
      <Modal isOpen={showKingdomEditForm} onClose={() => setShowKingdomEditForm(false)} title="Edit Kingdom Details">
        <form onSubmit={handleKingdomEditSubmit}>
          <div className="form-group">
            <label>Kingdom Name:</label>
            <input
              type="text"
              value={kingdomEditData.name}
              onChange={(e) => setKingdomEditData({...kingdomEditData, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Ruler/Campaign Manager:</label>
            <input
              type="text"
              value={kingdomEditData.ruler}
              onChange={(e) => setKingdomEditData({...kingdomEditData, ruler: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Government Type:</label>
            <select
              value={kingdomEditData.government_type}
              onChange={(e) => setKingdomEditData({...kingdomEditData, government_type: e.target.value})}
            >
              {governmentTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Update Kingdom</button>
            <button type="button" onClick={() => setShowKingdomEditForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

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

// Kingdom Selection Component for Multi-Kingdom Management
const KingdomSelector = ({ kingdoms, activeKingdom, onKingdomChange, onCreateNew }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [kingdomToDelete, setKingdomToDelete] = useState(null);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [newKingdomData, setNewKingdomData] = useState({
    name: '',
    ruler: '',
    government_type: 'Monarchy',
    color: '#1e3a8a'
  });

  const governmentTypes = [
    'Monarchy', 'Republic', 'Empire', 'Council', 'Federation', 
    'Theocracy', 'Magocracy', 'Oligarchy', 'Democracy', 'Confederation'
  ];

  const kingdomColors = [
    '#1e3a8a', '#7c2d12', '#166534', '#7c3aed', '#dc2626', 
    '#ea580c', '#0891b2', '#4338ca', '#059669', '#be123c'
  ];

  const handleCreateKingdom = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/multi-kingdoms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newKingdomData)
      });
      
      if (response.ok) {
        const newKingdom = await response.json();
        setShowCreateForm(false);
        setNewKingdomData({ name: '', ruler: '', government_type: 'Monarchy', color: '#1e3a8a' });
        onCreateNew(newKingdom);
      }
    } catch (error) {
      console.error('Error creating kingdom:', error);
    }
  };

  const handleDeleteClick = (e, kingdom) => {
    e.stopPropagation(); // Prevent kingdom selection
    setKingdomToDelete(kingdom);
    setDeleteConfirmText('');
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (deleteConfirmText !== 'DELETE') {
      return;
    }

    try {
      const response = await fetch(`${API}/multi-kingdom/${kingdomToDelete.id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setShowDeleteModal(false);
        setKingdomToDelete(null);
        setDeleteConfirmText('');
        // Refresh kingdoms list
        window.location.reload();
      } else {
        console.error('Failed to delete kingdom');
      }
    } catch (error) {
      console.error('Error deleting kingdom:', error);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
    setKingdomToDelete(null);
    setDeleteConfirmText('');
  };

  return (
    <div className="kingdom-selector">
      <div className="selector-header">
        <h3>Select Kingdom</h3>
        <button 
          className="btn-primary create-kingdom-btn"
          onClick={() => setShowCreateForm(true)}
        >
          + Create New Kingdom
        </button>
      </div>
      
      <div className="kingdoms-grid">
        {kingdoms?.map(kingdom => (
          <div 
            key={kingdom.id}
            className={`kingdom-card ${activeKingdom?.id === kingdom.id ? 'active' : ''}`}
            onClick={() => onKingdomChange(kingdom)}
            style={{ borderColor: kingdom.color }}
          >
            <button 
              className="kingdom-delete-btn"
              onClick={(e) => handleDeleteClick(e, kingdom)}
              title="Delete Kingdom"
            >
              ✕
            </button>
            <div className="kingdom-color-indicator" style={{ backgroundColor: kingdom.color }}></div>
            <div className="kingdom-info">
              <h4>{kingdom.name}</h4>
              <p>Ruled by {kingdom.ruler}</p>
              <p className="government-type">{kingdom.government_type}</p>
              <div className="kingdom-stats">
                <span>{kingdom.cities?.length || 0} cities</span>
                <span>{kingdom.total_population || 0} population</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Modal isOpen={showCreateForm} onClose={() => setShowCreateForm(false)} title="Create New Kingdom">
        <form onSubmit={handleCreateKingdom}>
          <div className="form-group">
            <label>Kingdom Name:</label>
            <input
              type="text"
              value={newKingdomData.name}
              onChange={(e) => setNewKingdomData({...newKingdomData, name: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Ruler:</label>
            <input
              type="text"
              value={newKingdomData.ruler}
              onChange={(e) => setNewKingdomData({...newKingdomData, ruler: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Government Type:</label>
            <select
              value={newKingdomData.government_type}
              onChange={(e) => setNewKingdomData({...newKingdomData, government_type: e.target.value})}
            >
              {governmentTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Kingdom Color:</label>
            <div className="color-picker">
              {kingdomColors.map(color => (
                <div
                  key={color}
                  className={`color-option ${newKingdomData.color === color ? 'selected' : ''}`}
                  style={{ backgroundColor: color }}
                  onClick={() => setNewKingdomData({...newKingdomData, color})}
                />
              ))}
            </div>
          </div>
          <div className="form-actions">
            <button type="submit" className="btn-primary">Create Kingdom</button>
            <button type="button" onClick={() => setShowCreateForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showDeleteModal} onClose={handleDeleteCancel} title="Delete Kingdom">
        <div className="delete-confirmation">
          <div className="warning-message">
            <div className="warning-icon">⚠️</div>
            <p>Are you sure you want to delete <strong>{kingdomToDelete?.name}</strong>?</p>
            <p className="warning-text">This will also delete all its cities and government hierarchy.</p>
          </div>
          
          <div className="form-group">
            <label>Type <strong>DELETE</strong> to confirm:</label>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="Type DELETE here"
              className="delete-confirm-input"
            />
          </div>
          
          <div className="form-actions">
            <button 
              onClick={handleDeleteConfirm}
              className="btn-danger"
              disabled={deleteConfirmText !== 'DELETE'}
            >
              Delete Kingdom
            </button>
            <button onClick={handleDeleteCancel} className="btn-secondary">Cancel</button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

// Enhanced Map Component with Smart Boundary System
const EnhancedFaerunMap = ({ kingdoms, activeKingdom, cities, onCitySelect, onMapClick }) => {
  const [showAddCityForm, setShowAddCityForm] = useState(false);
  const [newCityCoords, setNewCityCoords] = useState({ x: 0, y: 0 });
  const [draggedCity, setDraggedCity] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [boundaryMode, setBoundaryMode] = useState('off'); // 'off', 'draw', 'paint', 'erase'
  const [currentBoundary, setCurrentBoundary] = useState([]);
  const [paintBrushSize, setPaintBrushSize] = useState(20);
  const [mapDimensions, setMapDimensions] = useState({ width: 0, height: 0 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [allBoundaries, setAllBoundaries] = useState([]);

  useEffect(() => {
    // Get map dimensions for proper coordinate calculation
    const mapElement = document.querySelector('.map-placeholder');
    if (mapElement) {
      const rect = mapElement.getBoundingClientRect();
      setMapDimensions({ width: rect.width, height: rect.height });
    }
  }, []);

  // Fetch all boundaries from all kingdoms
  useEffect(() => {
    const fetchAllBoundaries = async () => {
      try {
        if (kingdoms && kingdoms.length > 0) {
          let boundaries = [];
          for (const kingdom of kingdoms) {
            if (kingdom.boundaries && kingdom.boundaries.length > 0) {
              boundaries = [...boundaries, ...kingdom.boundaries.map(b => ({...b, kingdomColor: kingdom.color, kingdomName: kingdom.name}))];
            }
          }
          setAllBoundaries(boundaries);
        }
      } catch (error) {
        console.error('Error fetching boundaries:', error);
      }
    };
    
    fetchAllBoundaries();
  }, [kingdoms]);

  const handleMapClick = (e) => {
    if (isDragging || isPanning) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left - pan.x) / (rect.width * zoom)) * 100;
    const y = ((e.clientY - rect.top - pan.y) / (rect.height * zoom)) * 100;
    
    if (boundaryMode === 'draw') {
      // Smart boundary detection - snap to nearby edges or geographical features
      const snappedPoint = snapToFeatures(x, y, rect);
      setCurrentBoundary([...currentBoundary, snappedPoint]);
      
    } else if (boundaryMode === 'paint') {
      // Paint mode - add circular area to boundary
      paintBoundaryArea(x, y);
      
    } else if (boundaryMode === 'erase') {
      // Enhanced erase mode - remove boundary area from existing boundaries
      eraseBoundaryArea(x, y);
    }
    // Removed single-click city creation - now requires double-click
  };

  const handleMapDoubleClick = (e) => {
    if (isDragging || isPanning || boundaryMode !== 'off') return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left - pan.x) / (rect.width * zoom)) * 100;
    const y = ((e.clientY - rect.top - pan.y) / (rect.height * zoom)) * 100;
    
    // Double-click to add new city
    setNewCityCoords({ x, y });
    setShowAddCityForm(true);
  };

  const snapToFeatures = (x, y, rect) => {
    // Smart snapping to geographical features
    // This would analyze the map image for rivers, coastlines, etc.
    // For now, implementing basic edge snapping
    
    const snapDistance = 2; // 2% of map size
    const snappedPoint = { x, y };
    
    // Snap to map edges
    if (x < snapDistance) snappedPoint.x = 0;
    if (x > 100 - snapDistance) snappedPoint.x = 100;
    if (y < snapDistance) snappedPoint.y = 0;
    if (y > 100 - snapDistance) snappedPoint.y = 100;
    
    // Future: Add river/coastline detection using image analysis
    // const features = detectGeographicalFeatures(x, y);
    // if (features.length > 0) return features[0];
    
    return snappedPoint;
  };

  const paintBoundaryArea = (centerX, centerY) => {
    // Create circular boundary points around the clicked area
    const brushRadius = paintBrushSize / 10; // Convert to percentage
    const newPoints = [];
    
    for (let angle = 0; angle < 360; angle += 15) {
      const radian = (angle * Math.PI) / 180;
      const pointX = centerX + Math.cos(radian) * brushRadius;
      const pointY = centerY + Math.sin(radian) * brushRadius;
      
      if (pointX >= 0 && pointX <= 100 && pointY >= 0 && pointY <= 100) {
        newPoints.push({ x: pointX, y: pointY });
      }
    }
    
    setCurrentBoundary([...currentBoundary, ...newPoints]);
  };

  const eraseBoundaryArea = async (centerX, centerY) => {
    // Enhanced erase mode - works on both current boundary and existing boundaries
    const eraseRadius = paintBrushSize / 10;
    
    // Remove points from current boundary being drawn
    setCurrentBoundary(currentBoundary.filter(point => {
      const distance = Math.sqrt(
        Math.pow(point.x - centerX, 2) + Math.pow(point.y - centerY, 2)
      );
      return distance > eraseRadius;
    }));
    
    // Find and modify existing boundaries that intersect with erase area
    let hasModifications = false;
    
    for (const boundary of allBoundaries) {
      // Check if any boundary points are within the erase radius
      const pointsInEraseArea = boundary.boundary_points.filter(point => {
        const distance = Math.sqrt(
          Math.pow(point.x - centerX, 2) + Math.pow(point.y - centerY, 2)
        );
        return distance <= eraseRadius;
      });
      
      if (pointsInEraseArea.length > 0) {
        // Calculate remaining points after erasing
        const remainingPoints = boundary.boundary_points.filter(point => {
          const distance = Math.sqrt(
            Math.pow(point.x - centerX, 2) + Math.pow(point.y - centerY, 2)
          );
          return distance > eraseRadius;
        });
        
        hasModifications = true;
        
        if (remainingPoints.length < 3) {
          // Delete entire boundary if too few points remain
          console.log(`Deleting boundary ${boundary.id} - insufficient points remaining`);
          await deleteBoundary(boundary.id);
        } else {
          // Update boundary with remaining points
          console.log(`Updating boundary ${boundary.id} - removing ${pointsInEraseArea.length} points`);
          await updateBoundary(boundary.id, remainingPoints);
        }
      }
    }
    
    if (hasModifications) {
      // Refresh the page to show updated boundaries
      setTimeout(() => window.location.reload(), 500);
    }
  };

  const deleteBoundary = async (boundaryId) => {
    try {
      const response = await fetch(`${API}/kingdom-boundaries/${boundaryId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        // Refresh boundaries
        window.location.reload();
      }
    } catch (error) {
      console.error('Error deleting boundary:', error);
    }
  };

  const updateBoundary = async (boundaryId, newPoints) => {
    try {
      const response = await fetch(`${API}/kingdom-boundaries/${boundaryId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          boundary_points: newPoints
        })
      });
      
      if (response.ok) {
        // Refresh boundaries
        window.location.reload();
      }
    } catch (error) {
      console.error('Error updating boundary:', error);
    }
  };

  const completeBoundary = async () => {
    if (currentBoundary.length < 3) {
      alert('A boundary must have at least 3 points');
      return;
    }

    // Create a closed polygon by connecting first and last points
    let boundaryPoints = [...currentBoundary];
    if (boundaryMode === 'draw') {
      // For drawing mode, close the polygon
      boundaryPoints.push(currentBoundary[0]);
    } else {
      // For paint mode, create a convex hull
      boundaryPoints = createConvexHull(currentBoundary);
    }

    try {
      const response = await fetch(`${API}/kingdom-boundaries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          kingdom_id: activeKingdom.id,
          boundary_points: boundaryPoints,
          color: activeKingdom.color
        })
      });
      
      if (response.ok) {
        setCurrentBoundary([]);
        setBoundaryMode('off');
        window.location.reload();
      }
    } catch (error) {
      console.error('Error creating boundary:', error);
    }
  };

  const createConvexHull = (points) => {
    // Simple convex hull algorithm for paint mode
    if (points.length < 3) return points;
    
    // Sort points by x coordinate
    const sortedPoints = [...points].sort((a, b) => a.x - b.x);
    
    // Build upper hull
    const upper = [];
    for (let i = 0; i < sortedPoints.length; i++) {
      while (upper.length >= 2 && cross(upper[upper.length-2], upper[upper.length-1], sortedPoints[i]) <= 0) {
        upper.pop();
      }
      upper.push(sortedPoints[i]);
    }
    
    // Build lower hull
    const lower = [];
    for (let i = sortedPoints.length - 1; i >= 0; i--) {
      while (lower.length >= 2 && cross(lower[lower.length-2], lower[lower.length-1], sortedPoints[i]) <= 0) {
        lower.pop();
      }
      lower.push(sortedPoints[i]);
    }
    
    return [...upper.slice(0, -1), ...lower.slice(0, -1)];
  };

  const cross = (o, a, b) => {
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
  };

  // Zoom and Pan handlers
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [isHoveringMap, setIsHoveringMap] = useState(false);
  
  const handleWheel = (e) => {
    if (!isHoveringMap) return; // Only zoom when hovering over map
    e.preventDefault();
    e.stopPropagation();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    const newZoom = Math.max(0.5, Math.min(3, zoom + delta));
    setZoom(newZoom);
  };

  const handleMouseEnter = () => {
    setIsHoveringMap(true);
  };

  const handleMouseLeave = () => {
    setIsHoveringMap(false);
    setIsPanning(false);
  };

  const handlePanStart = (e) => {
    if (boundaryMode !== 'off') return;
    setIsPanning(true);
    setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handlePanMove = (e) => {
    if (!isPanning) return;
    setPan({
      x: e.clientX - panStart.x,
      y: e.clientY - panStart.y
    });
  };

  const handlePanEnd = () => {
    setIsPanning(false);
  };

  const clearBoundary = () => {
    setCurrentBoundary([]);
    setBoundaryMode('off');
  };

  const clearAllBoundaries = async () => {
    if (!activeKingdom) {
      alert('No active kingdom selected');
      return;
    }
    
    if (window.confirm(`Are you sure you want to clear ALL boundaries for ${activeKingdom.name}? This action cannot be undone.`)) {
      try {
        console.log(`Clearing boundaries for kingdom: ${activeKingdom.id}`);
        
        const response = await fetch(`${API}/kingdom-boundaries/clear/${activeKingdom.id}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const result = await response.json();
          console.log('Clear boundaries result:', result);
          
          // Update UI immediately by filtering out boundaries for this kingdom
          setAllBoundaries(prevBoundaries => 
            prevBoundaries.filter(boundary => boundary.kingdom_id !== activeKingdom.id)
          );
          
          alert(`Successfully cleared all boundaries for ${activeKingdom.name}: ${result.message}`);
          
          // Force a complete reload after user acknowledges
          setTimeout(() => window.location.reload(), 500);
        } else {
          const errorText = await response.text();
          console.error('Clear boundaries failed:', response.status, errorText);
          throw new Error(`Failed to clear boundaries: ${response.status}`);
        }
        
      } catch (error) {
        console.error('Error clearing all boundaries:', error);
        alert(`Failed to clear boundaries: ${error.message}. Please try again.`);
      }
    }
  };

  const analyzeMapImageForBoundaries = async (canvasElement, cities) => {
    // This function analyzes the map image to detect color boundaries for geographical features
    const ctx = canvasElement.getContext('2d');
    const imageData = ctx.getImageData(0, 0, canvasElement.width, canvasElement.height);
    const data = imageData.data;
    
    // Helper function to get pixel color at specific coordinates
    const getPixelColor = (x, y) => {
      const index = (y * canvasElement.width + x) * 4;
      return [data[index], data[index + 1], data[index + 2]]; // RGB
    };
    
    // Helper function to calculate color difference (Euclidean distance)
    const colorDistance = (color1, color2) => {
      return Math.sqrt(
        Math.pow(color1[0] - color2[0], 2) + 
        Math.pow(color1[1] - color2[1], 2) + 
        Math.pow(color1[2] - color2[2], 2)
      );
    };
    
    // Define minimum contrast threshold for edge detection
    const contrastThreshold = 40; // Adjust this value to control sensitivity
    
    // Get city positions as reference points
    const cityPositions = cities.map(city => ({
      x: Math.floor((city.x_coordinate / 100) * canvasElement.width),
      y: Math.floor((city.y_coordinate / 100) * canvasElement.height)
    }));
    
    // Find the bounding box around all cities with padding
    const padding = Math.min(canvasElement.width, canvasElement.height) * 0.15; // 15% of smaller dimension
    let minX = Math.min(...cityPositions.map(p => p.x)) - padding;
    let maxX = Math.max(...cityPositions.map(p => p.x)) + padding;
    let minY = Math.min(...cityPositions.map(p => p.y)) - padding;
    let maxY = Math.max(...cityPositions.map(p => p.y)) + padding;
    
    // Clamp to canvas boundaries
    minX = Math.max(0, minX);
    maxX = Math.min(canvasElement.width - 1, maxX);
    minY = Math.max(0, minY);
    maxY = Math.min(canvasElement.height - 1, maxY);
    
    // Edge detection around the perimeter of the bounding box
    const boundaryPoints = [];
    const sampleStep = 5; // Sample every 5 pixels for performance
    
    // Top edge - scan for color contrasts
    for (let x = minX; x <= maxX; x += sampleStep) {
      for (let y = minY; y <= maxY; y += sampleStep) {
        const currentColor = getPixelColor(x, y);
        
        // Check neighbors for color contrast
        const neighbors = [
          {dx: -1, dy: 0}, {dx: 1, dy: 0}, // left, right
          {dx: 0, dy: -1}, {dx: 0, dy: 1}, // up, down
          {dx: -1, dy: -1}, {dx: 1, dy: 1}, // diagonals
          {dx: -1, dy: 1}, {dx: 1, dy: -1}
        ];
        
        let hasContrast = false;
        for (const neighbor of neighbors) {
          const nx = x + neighbor.dx * sampleStep;
          const ny = y + neighbor.dy * sampleStep;
          
          if (nx >= 0 && nx < canvasElement.width && ny >= 0 && ny < canvasElement.height) {
            const neighborColor = getPixelColor(nx, ny);
            if (colorDistance(currentColor, neighborColor) > contrastThreshold) {
              hasContrast = true;
              break;
            }
          }
        }
        
        if (hasContrast) {
          boundaryPoints.push({
            x: (x / canvasElement.width) * 100, // Convert back to percentage
            y: (y / canvasElement.height) * 100
          });
        }
      }
    }
    
    // If no contrasts found, fall back to city-based boundary
    if (boundaryPoints.length < 3) {
      console.log('No sufficient color contrasts found, falling back to city-based boundary');
      return generateCityBasedBoundary(cities);
    }
    
    // Create a simplified boundary from the detected points
    return createSimplifiedBoundary(boundaryPoints);
  };
  
  const generateCityBasedBoundary = (cities) => {
    // Fallback: Generate boundary around cities with padding
    const cityPoints = cities.map(city => ({
      x: city.x_coordinate,
      y: city.y_coordinate
    }));
    
    // Add padding around each city
    const paddedPoints = [];
    cityPoints.forEach(city => {
      const radius = 8; // Radius around each city
      for (let angle = 0; angle < 360; angle += 45) {
        const radian = (angle * Math.PI) / 180;
        const x = Math.max(0, Math.min(100, city.x + Math.cos(radian) * radius));
        const y = Math.max(0, Math.min(100, city.y + Math.sin(radian) * radius));
        paddedPoints.push({ x, y });
      }
    });
    
    return createConvexHull(paddedPoints);
  };
  
  const createSimplifiedBoundary = (points) => {
    // Simplify the boundary points to create a cleaner polygon
    if (points.length < 3) return points;
    
    // Use Douglas-Peucker algorithm for line simplification
    const simplifyTolerance = 2.0; // Adjust for desired simplification level
    const simplified = douglasPeucker(points, simplifyTolerance);
    
    // Ensure we have a valid boundary
    if (simplified.length < 3) {
      return createConvexHull(points);
    }
    
    return simplified;
  };
  
  const douglasPeucker = (points, tolerance) => {
    if (points.length <= 2) return points;
    
    // Find the point with maximum distance from line between first and last points
    let maxDistance = 0;
    let maxIndex = 0;
    
    const firstPoint = points[0];
    const lastPoint = points[points.length - 1];
    
    for (let i = 1; i < points.length - 1; i++) {
      const distance = perpendicularDistance(points[i], firstPoint, lastPoint);
      if (distance > maxDistance) {
        maxDistance = distance;
        maxIndex = i;
      }
    }
    
    // If max distance is greater than tolerance, recursively simplify
    if (maxDistance > tolerance) {
      const leftPart = douglasPeucker(points.slice(0, maxIndex + 1), tolerance);
      const rightPart = douglasPeucker(points.slice(maxIndex), tolerance);
      
      // Combine results (remove duplicate point at junction)
      return leftPart.slice(0, -1).concat(rightPart);
    } else {
      // All points are within tolerance, return simplified line
      return [firstPoint, lastPoint];
    }
  };
  
  const perpendicularDistance = (point, lineStart, lineEnd) => {
    const A = lineEnd.x - lineStart.x;
    const B = lineEnd.y - lineStart.y;
    const C = point.x - lineStart.x;
    const D = point.y - lineStart.y;
    
    const dot = C * A + D * B;
    const lenSq = A * A + B * B;
    
    if (lenSq === 0) return Math.sqrt(C * C + D * D);
    
    const param = dot / lenSq;
    
    let xx, yy;
    if (param < 0) {
      xx = lineStart.x;
      yy = lineStart.y;
    } else if (param > 1) {
      xx = lineEnd.x;
      yy = lineEnd.y;
    } else {
      xx = lineStart.x + param * A;
      yy = lineStart.y + param * B;
    }
    
    const dx = point.x - xx;
    const dy = point.y - yy;
    return Math.sqrt(dx * dx + dy * dy);
  };

  const generateAutomaticBorders = async () => {
    if (!activeKingdom || !activeKingdom.cities || activeKingdom.cities.length === 0) {
      alert('No cities found to generate borders around');
      return;
    }
    
    try {
      console.log(`Generating automatic borders for ${activeKingdom.name} using color detection...`);
      
      // Create a canvas to analyze the map image
      const mapImage = document.querySelector('.map-image');
      if (!mapImage) {
        throw new Error('Map image not found');
      }
      
      // Wait for image to load if needed
      if (!mapImage.complete) {
        await new Promise((resolve) => {
          mapImage.onload = resolve;
        });
      }
      
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      // Set canvas size to match image display size
      const rect = mapImage.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      
      // Draw the image to canvas for analysis
      ctx.drawImage(mapImage, 0, 0, canvas.width, canvas.height);
      
      // Analyze the image for color-based boundaries
      const boundaryPoints = await analyzeMapImageForBoundaries(canvas, activeKingdom.cities);
      
      if (boundaryPoints.length >= 3) {
        const response = await fetch(`${API}/kingdom-boundaries`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            kingdom_id: activeKingdom.id,
            boundary_points: boundaryPoints,
            color: activeKingdom.color
          })
        });
        
        if (response.ok) {
          console.log(`Generated automatic border with ${boundaryPoints.length} points using color detection`);
          alert(`Successfully generated border with ${boundaryPoints.length} points based on map features!`);
          setTimeout(() => window.location.reload(), 1000);
        } else {
          throw new Error('Failed to save boundary to server');
        }
      } else {
        throw new Error('Insufficient boundary points detected');
      }
      
    } catch (error) {
      console.error('Error generating automatic borders:', error);
      alert(`Failed to generate automatic borders: ${error.message}. Falling back to city-based generation.`);
      
      // Fallback to the original city-based method
      try {
        const kingdomCities = activeKingdom.cities.map(city => ({
          x: city.x_coordinate,
          y: city.y_coordinate
        }));
        
        const hullPoints = generateCityBasedBoundary(kingdomCities);
        
        if (hullPoints.length >= 3) {
          const response = await fetch(`${API}/kingdom-boundaries`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              kingdom_id: activeKingdom.id,
              boundary_points: hullPoints,
              color: activeKingdom.color
            })
          });
          
          if (response.ok) {
            console.log(`Generated fallback border with ${hullPoints.length} points around cities`);
            setTimeout(() => window.location.reload(), 1000);
          }
        }
      } catch (fallbackError) {
        console.error('Fallback border generation also failed:', fallbackError);
        alert('Failed to generate borders using both methods. Please try manual drawing.');
      }
    }
  };

  // ... (keeping existing city drag/drop functionality)
  const handleCityMouseDown = (e, city) => {
    if (boundaryMode !== 'off') return; // Disable city interaction in boundary mode
    e.stopPropagation();
    setDraggedCity(city);
    setIsDragging(true);
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !draggedCity) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    const cityMarker = document.querySelector(`[data-city-id="${draggedCity.id}"]`);
    if (cityMarker) {
      cityMarker.style.left = `${x}%`;
      cityMarker.style.top = `${y}%`;
    }
  };

  const handleMouseUp = async (e) => {
    if (!isDragging || !draggedCity) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    try {
      const response = await fetch(`${API}/city/${draggedCity.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x_coordinate: x, y_coordinate: y })
      });
      
      if (response.ok) {
        setTimeout(() => window.location.reload(), 100);
      }
    } catch (error) {
      console.error('Error updating city position:', error);
    }
    
    setDraggedCity(null);
    setIsDragging(false);
  };

  const handleDeleteCity = async (e, city) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete ${city.name}?`)) {
      try {
        const response = await fetch(`${API}/city/${city.id}`, { method: 'DELETE' });
        if (response.ok) window.location.reload();
      } catch (error) {
        console.error('Error deleting city:', error);
      }
    }
  };

  const handleCreateCity = async (cityData) => {
    try {
      const response = await fetch(`${API}/cities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ...cityData, 
          x_coordinate: newCityCoords.x, 
          y_coordinate: newCityCoords.y,
          kingdom_id: activeKingdom?.id 
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('City created successfully:', result);
        setShowAddCityForm(false);
        // Refresh data after a short delay
        setTimeout(() => window.location.reload(), 1000);
      } else {
        const errorText = await response.text();
        console.error('Failed to create city:', response.status, errorText);
        alert('Failed to create city. Please try again.');
      }
    } catch (error) {
      console.error('Error creating city:', error);
      alert('Error creating city. Please try again.');
    }
  };

  const getBoundaryModeInstructions = () => {
    switch (boundaryMode) {
      case 'draw':
        return `Click points to draw ${activeKingdom?.name || 'Kingdom'} boundary. Lines will snap to geographical features.`;
      case 'paint':
        return `Paint to expand ${activeKingdom?.name || 'Kingdom'} territory. Brush size: ${paintBrushSize}px`;
      case 'erase':
        return `Erase to reduce ${activeKingdom?.name || 'Kingdom'} territory. Brush size: ${paintBrushSize}px`;
      default:
        return 'Click anywhere to add a new city • Drag cities to move them • Right-click cities to delete';
    }
  };

  return (
    <div className="enhanced-map-container">
      <div className="boundary-tools">
        <div className="boundary-mode-controls">
          <button 
            className={`tool-btn ${boundaryMode === 'draw' ? 'active' : ''}`}
            onClick={() => setBoundaryMode(boundaryMode === 'draw' ? 'off' : 'draw')}
          >
            ✏️ Draw Boundary
          </button>
          
          <button 
            className={`tool-btn ${boundaryMode === 'paint' ? 'active' : ''}`}
            onClick={() => setBoundaryMode(boundaryMode === 'paint' ? 'off' : 'paint')}
          >
            🖌️ Paint Territory
          </button>
          
          <button 
            className={`tool-btn ${boundaryMode === 'erase' ? 'active' : ''}`}
            onClick={() => setBoundaryMode(boundaryMode === 'erase' ? 'off' : 'erase')}
          >
            🧽 Erase Territory
          </button>
          
          <button 
            className="tool-btn auto-generate"
            onClick={generateAutomaticBorders}
            title="Automatically generate borders around cities"
          >
            🤖 Auto Generate Borders
          </button>
          
          <button 
            className="tool-btn clear-all"
            onClick={clearAllBoundaries}
            title="Clear all boundaries for this kingdom"
          >
            🗑️ Clear All Boundaries
          </button>
        </div>

        {(boundaryMode === 'paint' || boundaryMode === 'erase') && (
          <div className="brush-controls">
            <label>Brush Size: {paintBrushSize}px</label>
            <input
              type="range"
              min="10"
              max="50"
              value={paintBrushSize}
              onChange={(e) => setPaintBrushSize(parseInt(e.target.value))}
              className="brush-slider"
            />
          </div>
        )}

        {boundaryMode !== 'off' && (
          <div className="boundary-actions">
            {currentBoundary.length > 2 && (
              <button className="btn-primary" onClick={completeBoundary}>
                Complete Boundary ({currentBoundary.length} points)
              </button>
            )}
            <button className="btn-secondary" onClick={clearBoundary}>
              Clear & Exit
            </button>
          </div>
        )}
      </div>

      <div className="map-instructions">
        Double-click to add a new city • Drag cities to move them • Right-click cities to delete • Use boundary tools to manage territories
      </div>
      
      <div className="map-controls">
        <button 
          className="btn-secondary" 
          onClick={() => setZoom(Math.min(3, zoom + 0.2))}
          disabled={zoom >= 3}
        >
          🔍+ Zoom In
        </button>
        <span className="zoom-indicator">{Math.round(zoom * 100)}%</span>
        <button 
          className="btn-secondary" 
          onClick={() => setZoom(Math.max(0.5, zoom - 0.2))}
          disabled={zoom <= 0.5}
        >
          🔍- Zoom Out
        </button>
        <button 
          className="btn-secondary" 
          onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
        >
          🎯 Reset View
        </button>
      </div>
      
      <div className="map-container-locked">
        <div 
          className="map-placeholder" 
          onClick={handleMapClick}
          onDoubleClick={handleMapDoubleClick}
          onMouseMove={(e) => {
            handleMouseMove(e);
            handlePanMove(e);
          }}
          onMouseUp={(e) => {
            handleMouseUp(e);
            handlePanEnd();
          }}
          onMouseDown={handlePanStart}
          onWheel={handleWheel}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          style={{ 
            cursor: boundaryMode === 'draw' ? 'crosshair' : 
                    boundaryMode === 'paint' ? 'copy' :
                    boundaryMode === 'erase' ? 'not-allowed' :
                    isPanning ? 'grabbing' :
                    (isDragging ? 'grabbing' : (boundaryMode === 'off' ? 'grab' : 'default'))
          }}
        >
          <div 
            className="map-content"
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transformOrigin: 'center center'
            }}
          >
        <img 
          src="https://images.unsplash.com/photo-1677295922463-147d7f2f718c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxmYW50YXN5JTIwbWFwfGVufDB8fHx8MTc1MzI0Mzk3OXww&ixlib=rb-4.1.0&q=85"
          alt="Faerûn Map"
          className="map-image"
          draggable={false}
        />
        
        {/* Render ALL Kingdom Boundaries from all kingdoms */}
        <svg className="boundary-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
          {allBoundaries.map((boundary, index) => (
            <g key={`${boundary.id || index}`}>
              {/* Filled area */}
              <polygon
                points={boundary.boundary_points.map(p => `${p.x},${p.y}`).join(' ')}
                fill={`${boundary.kingdomColor || boundary.color}40`}
                stroke={boundary.kingdomColor || boundary.color}
                strokeWidth="0.3"
                opacity="0.8"
              />
              {/* Border highlight */}
              <polygon
                points={boundary.boundary_points.map(p => `${p.x},${p.y}`).join(' ')}
                fill="none"
                stroke={boundary.kingdomColor || boundary.color}
                strokeWidth="0.5"
                opacity="1"
                strokeDasharray="1,0.5"
              />
              {/* Kingdom label */}
              {boundary.boundary_points.length > 0 && (
                <text
                  x={boundary.boundary_points.reduce((sum, p) => sum + p.x, 0) / boundary.boundary_points.length}
                  y={boundary.boundary_points.reduce((sum, p) => sum + p.y, 0) / boundary.boundary_points.length}
                  fill={boundary.kingdomColor || boundary.color}
                  fontSize="2"
                  textAnchor="middle"
                  fontWeight="bold"
                  opacity="0.8"
                >
                  {boundary.kingdomName}
                </text>
              )}
            </g>
          ))}
        </svg>
        
        {/* Current boundary being drawn/painted */}
        {boundaryMode !== 'off' && currentBoundary.length > 0 && (
          <svg className="boundary-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
            {boundaryMode === 'draw' && currentBoundary.length > 2 && (
              <>
                {/* Preview filled area */}
                <polygon
                  points={[...currentBoundary, currentBoundary[0]].map(p => `${p.x},${p.y}`).join(' ')}
                  fill={`${activeKingdom?.color || '#1e3a8a'}30`}
                  stroke={activeKingdom?.color || '#1e3a8a'}
                  strokeWidth="0.3"
                  opacity="0.6"
                />
              </>
            )}
            
            {boundaryMode === 'paint' && currentBoundary.length > 2 && (
              <>
                {/* Preview painted area */}
                <polygon
                  points={createConvexHull(currentBoundary).map(p => `${p.x},${p.y}`).join(' ')}
                  fill={`${activeKingdom?.color || '#1e3a8a'}40`}
                  stroke={activeKingdom?.color || '#1e3a8a'}
                  strokeWidth="0.3"
                  opacity="0.7"
                />
              </>
            )}
            
            {/* Draw current boundary points */}
            <polyline
              points={currentBoundary.map(p => `${p.x},${p.y}`).join(' ')}
              fill="none"
              stroke={activeKingdom?.color || '#1e3a8a'}
              strokeWidth="0.4"
              strokeDasharray="1,0.5"
            />
            
            {/* Draw individual points */}
            {currentBoundary.map((point, index) => (
              <circle
                key={index}
                cx={point.x}
                cy={point.y}
                r="0.5"
                fill={activeKingdom?.color || '#1e3a8a'}
                opacity="0.8"
              />
            ))}
          </svg>
        )}
        
        {/* Render Cities (disabled during boundary mode) */}
        {cities?.map(city => (
          <div
            key={city.id}
            data-city-id={city.id}
            className={`city-marker ${isDragging && draggedCity?.id === city.id ? 'dragging' : ''} ${boundaryMode !== 'off' ? 'disabled' : ''}`}
            style={{
              left: `${city.x_coordinate}%`,
              top: `${city.y_coordinate}%`,
              cursor: boundaryMode !== 'off' ? 'not-allowed' : (isDragging ? 'grabbing' : 'grab'),
              opacity: boundaryMode !== 'off' ? 0.6 : 1
            }}
            onMouseDown={(e) => handleCityMouseDown(e, city)}
            onClick={(e) => {
              e.stopPropagation();
              if (!isDragging && boundaryMode === 'off') {
                onCitySelect(city.id);
              }
            }}
            onContextMenu={(e) => {
              e.preventDefault();
              if (boundaryMode === 'off') {
                handleDeleteCity(e, city);
              }
            }}
            title={boundaryMode !== 'off' ? 'Exit boundary mode to interact with cities' : `${city.name} - Right-click to delete, drag to move`}
          >
            <span className="city-icon" style={{ filter: `drop-shadow(0 0 3px ${city.kingdomColor || '#1e3a8a'})` }}>🏰</span>
            <span className="city-name">{city.name}</span>
            {boundaryMode === 'off' && (
              <button 
                className="city-delete-btn" 
                onClick={(e) => handleDeleteCity(e, city)}
                title="Delete city"
              >
                ✖
              </button>
            )}
          </div>
        ))}
          </div>
        </div>
      </div>

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
const FaerunMap = ({ cities, onCitySelect, onMapClick }) => {
  const [showAddCityForm, setShowAddCityForm] = useState(false);
  const [newCityCoords, setNewCityCoords] = useState({ x: 0, y: 0 });
  const [draggedCity, setDraggedCity] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleMapClick = (e) => {
    if (isDragging) return; // Don't create city if we're dragging
    
    const rect = e.target.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setNewCityCoords({ x, y });
    setShowAddCityForm(true);
  };

  const handleCityMouseDown = (e, city) => {
    e.stopPropagation();
    setDraggedCity(city);
    setIsDragging(true);
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !draggedCity) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    // Update city position in real-time during drag
    const cityMarker = document.querySelector(`[data-city-id="${draggedCity.id}"]`);
    if (cityMarker) {
      cityMarker.style.left = `${x}%`;
      cityMarker.style.top = `${y}%`;
    }
  };

  const handleMouseUp = async (e) => {
    if (!isDragging || !draggedCity) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    try {
      // Update city position in backend
      const response = await fetch(`${API}/city/${draggedCity.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x_coordinate: x, y_coordinate: y })
      });
      
      if (response.ok) {
        console.log(`City ${draggedCity.name} moved to (${x.toFixed(1)}, ${y.toFixed(1)})`);
        
        // Update the visual position immediately
        const cityMarker = document.querySelector(`[data-city-id="${draggedCity.id}"]`);
        if (cityMarker) {
          cityMarker.style.left = `${x}%`;
          cityMarker.style.top = `${y}%`;
        }
        
        // Refresh data after a short delay to ensure consistency
        setTimeout(() => window.location.reload(), 1000);
      } else {
        const errorText = await response.text();
        console.error('Failed to update city position:', response.status, errorText);
        alert('Failed to move city. Please try again.');
      }
    } catch (error) {
      console.error('Error updating city position:', error);
      alert('Error moving city. Please try again.');
    }
    
    setDraggedCity(null);
    setIsDragging(false);
  };

  const handleDeleteCity = async (e, city) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete ${city.name}? This action cannot be undone.`)) {
      try {
        const response = await fetch(`${API}/city/${city.id}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          console.log(`City ${city.name} deleted successfully`);
          // Remove the city from the DOM immediately
          const cityMarker = document.querySelector(`[data-city-id="${city.id}"]`);
          if (cityMarker) {
            cityMarker.style.display = 'none';
          }
          // Refresh data after a short delay
          setTimeout(() => window.location.reload(), 1000);
        } else {
          const errorText = await response.text();
          console.error('Failed to delete city:', response.status, errorText);
          alert('Failed to delete city. Please try again.');
        }
      } catch (error) {
        console.error('Error deleting city:', error);
        alert('Error deleting city. Please try again.');
      }
    }
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
      <div className="map-instructions">
        Click anywhere to add a new city • Drag cities to move them • Right-click cities to delete
      </div>
      <div 
        className="map-placeholder" 
        onClick={handleMapClick}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'default' }}
      >
        <img 
          src="https://images.unsplash.com/photo-1677295922463-147d7f2f718c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxmYW50YXN5JTIwbWFwfGVufDB8fHx8MTc1MzI0Mzk3OXww&ixlib=rb-4.1.0&q=85"
          alt="Faerûn Map"
          className="map-image"
          draggable={false}
        />
        {cities?.map(city => (
          <div
            key={city.id}
            data-city-id={city.id}
            className={`city-marker ${isDragging && draggedCity?.id === city.id ? 'dragging' : ''}`}
            style={{
              left: `${city.x_coordinate}%`,
              top: `${city.y_coordinate}%`,
              cursor: isDragging ? 'grabbing' : 'grab'
            }}
            onMouseDown={(e) => handleCityMouseDown(e, city)}
            onClick={(e) => {
              e.stopPropagation();
              if (!isDragging) {
                onCitySelect(city.id);
              }
            }}
            onContextMenu={(e) => {
              e.preventDefault();
              handleDeleteCity(e, city);
            }}
            title={`${city.name} - Right-click to delete, drag to move`}
          >
            <span className="city-icon">🏰</span>
            <span className="city-name">{city.name}</span>
            <button 
              className="city-delete-btn" 
              onClick={(e) => handleDeleteCity(e, city)}
              title="Delete city"
            >
              ✖
            </button>
          </div>
        ))}
      </div>

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

// Government Management Component
const GovernmentManagement = ({ city, onClose }) => {
  const [availablePositions] = useState([
    'Captain of the Guard', 'Master of Coin', 'High Scribe', 'Court Wizard', 'Head Cleric',
    'Trade Minister', 'City Magistrate', 'Harbor Master', 'Master Builder', 'Tax Collector', 'Market Warden'
  ]);
  const [selectedCitizen, setSelectedCitizen] = useState('');
  const [selectedPosition, setSelectedPosition] = useState('');

  const handleAppointment = async () => {
    if (!selectedCitizen || !selectedPosition) {
      alert('Please select both a citizen and a position');
      return;
    }

    try {
      const response = await fetch(`${API}/cities/${city.id}/government/appoint`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          citizen_id: selectedCitizen,
          position: selectedPosition
        })
      });
      
      if (response.ok) {
        onClose();
        window.location.reload();
      }
    } catch (error) {
      console.error('Error appointing citizen:', error);
    }
  };

  // Get citizens who don't already have government positions
  const availableCitizens = city.citizens?.filter(citizen => !citizen.government_position) || [];

  return (
    <div className="government-management">
      <div className="form-group">
        <label>Select Citizen:</label>
        <select 
          value={selectedCitizen} 
          onChange={(e) => setSelectedCitizen(e.target.value)}
        >
          <option value="">-- Choose Citizen --</option>
          {availableCitizens.map(citizen => (
            <option key={citizen.id} value={citizen.id}>
              {citizen.name} ({citizen.occupation})
            </option>
          ))}
        </select>
      </div>
      
      <div className="form-group">
        <label>Select Position:</label>
        <select 
          value={selectedPosition} 
          onChange={(e) => setSelectedPosition(e.target.value)}
        >
          <option value="">-- Choose Position --</option>
          {availablePositions.map(position => (
            <option key={position} value={position}>{position}</option>
          ))}
        </select>
      </div>
      
      <div className="form-actions">
        <button onClick={handleAppointment} className="btn-primary">
          Appoint to Position
        </button>
        <button onClick={onClose} className="btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  );
};

// City Dashboard Component with editing and government hierarchy
const CityDashboard = ({ city, activeTab, setActiveTab }) => {
  const [showEditForm, setShowEditForm] = useState(false);
  const [showGovtManagement, setShowGovtManagement] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [editFormData, setEditFormData] = useState({
    name: city?.name || '',
    governor: city?.governor || ''
  });

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest('.city-actions-dropdown')) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showDropdown]);

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

  const handleDeleteClick = () => {
    setShowDropdown(false);
    setDeleteConfirmText('');
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (deleteConfirmText !== 'DELETE') {
      return;
    }

    try {
      const response = await fetch(`${API}/city/${city.id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        // Redirect back to kingdom dashboard
        window.location.href = '/';
      } else {
        console.error('Failed to delete city');
      }
    } catch (error) {
      console.error('Error deleting city:', error);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
    setDeleteConfirmText('');
  };

  const handleRemoveOfficial = async (official) => {
    const confirmMessage = `Remove ${official.position}: ${official.name}?`;
    if (window.confirm(confirmMessage)) {
      try {
        const response = await fetch(`${API}/cities/${city.id}/government/${official.id}`, {
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
          <div className="city-title-row">
            <h1 className="city-title">{city.name}</h1>
            <div className="city-actions-dropdown">
              <button 
                className="edit-city-btn dropdown-toggle"
                onClick={() => setShowDropdown(!showDropdown)}
                title="City actions"
              >
                ⚙️ Actions ▼
              </button>
              {showDropdown && (
                <div className="dropdown-menu">
                  <button 
                    className="dropdown-item edit-item"
                    onClick={() => {
                      setShowDropdown(false);
                      setShowEditForm(true);
                    }}
                  >
                    ✏️ Edit City Details
                  </button>
                  <button 
                    className="dropdown-item manage-item"
                    onClick={() => {
                      setShowDropdown(false);
                      setShowGovtManagement(true);
                    }}
                  >
                    👥 Manage Positions
                  </button>
                  <button 
                    className="dropdown-item delete-item"
                    onClick={handleDeleteClick}
                  >
                    🗑️ Delete City
                  </button>
                </div>
              )}
            </div>
          </div>
          <p className="city-governor">Governor: {city.governor}</p>
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
                    onClick={() => handleRemoveOfficial(official)}
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
                    onClick={() => handleRemoveOfficial(official)}
                    title="Remove from position"
                  >
                    ✖
                  </button>
                </div>
              ))}
            </div>
          </div>
          
          {/* Minor Officials - Fourth Tier - Only show if there are administrative staff */}
          {(() => {
            const adminStaff = city.government_officials?.filter(official => 
              !['Captain of the Guard', 'Master of Coin', 'High Scribe', 'Court Wizard', 'Head Cleric',
                'Trade Minister', 'City Magistrate', 'Harbor Master', 'Master Builder', 'Tax Collector', 'Market Warden'].includes(official.position)
            ) || [];
            
            if (adminStaff.length === 0) return null;
            
            return (
              <div className="hierarchy-level minor-officials">
                <h4 className="tier-title">Administrative Staff</h4>
                <div className="officials-tier">
                  {adminStaff.map(official => (
                    <div key={official.id} className="government-official minor-card">
                      <div className="official-rank">{official.position}</div>
                      <div className="official-name">{official.name}</div>
                      <button 
                        className="remove-official-btn"
                        onClick={() => handleRemoveOfficial(official)}
                        title="Remove from position"
                      >
                        ✖
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
          
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

      <Modal isOpen={showDeleteModal} onClose={handleDeleteCancel} title="Delete City">
        <div className="delete-confirmation">
          <div className="warning-message">
            <div className="warning-icon">⚠️</div>
            <p>Are you sure you want to delete <strong>{city.name}</strong>?</p>
            <p className="warning-text">This will remove its local government hierarchy and all linked data.</p>
          </div>
          
          <div className="form-group">
            <label>Type <strong>DELETE</strong> to confirm:</label>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="Type DELETE here"
              className="delete-confirm-input"
            />
          </div>
          
          <div className="form-actions">
            <button 
              onClick={handleDeleteConfirm}
              className="btn-danger"
              disabled={deleteConfirmText !== 'DELETE'}
            >
              Delete City
            </button>
            <button onClick={handleDeleteCancel} className="btn-secondary">Cancel</button>
          </div>
        </div>
      </Modal>

      <RegistryTabs 
        city={city} 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
      />
    </div>
  );
};

// Main App Component with Multi-Kingdom Support and Authentication
function AuthenticatedApp() {
  const { token, logout } = useAuth(); // Get authentication token and logout function
  const [kingdom, setKingdom] = useState(null);
  const [multiKingdoms, setMultiKingdoms] = useState([]);
  const [activeKingdom, setActiveKingdom] = useState(null);
  const [currentView, setCurrentView] = useState('kingdom-selector'); // Start with kingdom selector
  const [activeTab, setActiveTab] = useState('Citizens');
  const [events, setEvents] = useState([]);
  const [autoEventsEnabled, setAutoEventsEnabled] = useState(true);
  const [wsConnection, setWsConnection] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Helper function to create authenticated headers
  const getAuthHeaders = () => {
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    return headers;
  };

  // Enhanced authenticated fetch helper with better error handling
  const authenticatedFetch = async (url, options = {}) => {
    const config = {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...options.headers
      }
    };
    
    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        console.error('Authentication failed - invalid or expired token');
        setErrorMessage('Your session has expired. Please log in again.');
        setShowErrorModal(true);
        setTimeout(() => {
          logout(); // Trigger logout after showing error
        }, 2000);
        return null;
      } else if (response.status === 403) {
        console.error('Access denied for:', url);
        setErrorMessage('Access denied. You do not have permission to perform this action.');
        setShowErrorModal(true);
        return null;
      }
      
      return response;
    } catch (error) {
      console.error('Network error for:', url, error);
      setErrorMessage('Network error. Please check your connection and try again.');
      setShowErrorModal(true);
      return null;
    }
  };

  // Fetch initial data when token is available
  useEffect(() => {
    if (token) {
      fetchMultiKingdoms();
      fetchActiveKingdom();
      fetchEvents();
      fetchAutoEventsStatus();
      connectWebSocket();
    }

    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [token]); // Depend on token

  const fetchMultiKingdoms = async () => {
    try {
      const response = await authenticatedFetch(`${API}/multi-kingdoms`);
      
      if (response && response.ok) {
        const data = await response.json();
        setMultiKingdoms(Array.isArray(data) ? data : []);
      } else {
        setMultiKingdoms([]);
      }
    } catch (error) {
      console.error('Error fetching multi kingdoms:', error);
      setMultiKingdoms([]);
    }
  };

  const fetchActiveKingdom = async () => {
    try {
      const response = await fetch(`${API}/active-kingdom`);
      const data = await response.json();
      setActiveKingdom(data);
      setKingdom(data); // For backward compatibility
    } catch (error) {
      console.error('Error fetching active kingdom:', error);
    }
  };

  const handleKingdomChange = async (selectedKingdom) => {
    try {
      const response = await fetch(`${API}/multi-kingdom/${selectedKingdom.id}/set-active`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setActiveKingdom(selectedKingdom);
        setKingdom(selectedKingdom);
        setCurrentView('kingdom');
      }
    } catch (error) {
      console.error('Error setting active kingdom:', error);
    }
  };

  const handleCreateNewKingdom = (newKingdom) => {
    setMultiKingdoms([...multiKingdoms, newKingdom]);
    handleKingdomChange(newKingdom);
  };

  // Fetch events for the active kingdom
  const fetchEvents = async () => {
    if (!activeKingdom) return;
    
    try {
      const response = await authenticatedFetch(`${API}/events/${activeKingdom.id}`);
      if (response && response.ok) {
        const kingdomEvents = await response.json();
        setEvents(kingdomEvents);
      } else {
        setEvents([]);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
      setEvents([]);
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
          // Only add events for the active kingdom
          if (activeKingdom && 
              (data.kingdom_id === activeKingdom.id || 
               data.event.kingdom_name === activeKingdom.name ||
               (!data.kingdom_id && data.event.kingdom_name === activeKingdom.name))) {
            setEvents(prevEvents => [data.event, ...prevEvents]);
            fetchActiveKingdom(); // Refresh kingdom data
          }
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

  const getCurrentCity = () => {
    if (currentView === 'kingdom' || currentView === 'map' || currentView === 'kingdom-selector') return null;
    return (activeKingdom || kingdom)?.cities?.find(city => city.id === currentView);
  };

  const currentCity = getCurrentCity();

  return (
    <div className="App">
      {/* App Header with User Profile */}
      <header className="app-header">
        <div className="header-content">
          <h1 className="app-title">⚔️ Faerûn Campaign Manager</h1>
          <UserProfile />
        </div>
      </header>

      <div className="status-bar">
        <span className="status-text">{connectionStatus}</span>
        {activeKingdom && (
          <span className="active-kingdom">Managing: {activeKingdom.name}</span>
        )}
      </div>
      
      {currentView === 'kingdom-selector' && (
        <KingdomSelector 
          kingdoms={multiKingdoms}
          activeKingdom={activeKingdom}
          onKingdomChange={handleKingdomChange}
          onCreateNew={handleCreateNewKingdom}
        />
      )}

      {activeKingdom && currentView !== 'kingdom-selector' && (
        <>
          <Navigation 
            currentView={currentView} 
            onViewChange={handleViewChange}
            kingdom={activeKingdom}
            onBackToSelector={() => setCurrentView('kingdom-selector')}
          />

          {currentView === 'kingdom' && (
            <KingdomDashboard 
              kingdom={activeKingdom} 
              events={events}
              autoEventsEnabled={autoEventsEnabled}
              onToggleAutoEvents={handleToggleAutoEvents}
            />
          )}

          {currentView === 'calendar' && (
            <HarptosCalendar 
              kingdom={activeKingdom}
              isVisible={true}
            />
          )}

          {currentView === 'map' && (
            <EnhancedFaerunMap 
              kingdoms={multiKingdoms}
              activeKingdom={activeKingdom}
              cities={multiKingdoms.flatMap(kingdom => 
                kingdom.cities?.map(city => ({
                  ...city, 
                  kingdomColor: kingdom.color,
                  kingdomName: kingdom.name
                })) || []
              )} 
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
        </>
      )}

      {/* Error Modal */}
      <Modal 
        isOpen={showErrorModal} 
        onClose={() => setShowErrorModal(false)} 
        title="Error"
      >
        <div className="error-modal-content">
          <div className="error-icon">⚠️</div>
          <p>{errorMessage}</p>
          <div className="error-actions">
            <button 
              className="btn-primary" 
              onClick={() => setShowErrorModal(false)}
            >
              OK
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// Main App with Authentication Wrapper
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

// App Content with Authentication Check
function AppContent() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <h2>⚔️ Faerûn Campaign Manager</h2>
          <div className="loading-spinner"></div>
          <p>Loading your campaign...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return <AuthenticatedApp />;
}

export default App;