import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';
import pirateBg from './assets/1.jpg'; // Импорт изображения

function App() {
  return (
    <Router>
      <div className="container">
        <div 
          className="pirate-header"
          style={{ backgroundImage: `url(${pirateBg})` }}
        >
          <h1>Pirates of the Caribbean Sea</h1>
        </div>
        <Routes>
          <Route path="/" element={<CharacterList />} />
          <Route path="/add" element={<CharacterForm />} />
          <Route path="/edit/:id" element={<CharacterForm editMode={true} />} />
        </Routes>
      </div>
    </Router>
  );
}

function CharacterList() {
  const [characters, setCharacters] = useState([]);

  useEffect(() => {
    fetchCharacters();
  }, []);

  const fetchCharacters = async () => {
    try {
      const response = await axios.get('http://localhost:5000/characters');
      setCharacters(response.data);
    } catch (error) {
      console.error('Error fetching characters:', error);
    }
  };

  const deleteCharacter = async (id) => {
    try {
      await axios.delete(`http://localhost:5000/characters/${id}`);
      fetchCharacters();
    } catch (error) {
      console.error('Error deleting character:', error);
    }
  };

  return (
    <div>
      <Link to="/add">
        <button className="add">Add New Character</button>
      </Link>
      <table>
        <thead>
          <tr>
            <th>Character Name</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {characters.map((character) => (
            <tr key={character.id}>
              <td>{character.name}</td>
              <td>
                <Link to={`/edit/${character.id}`}>
                  <button className="edit">Edit</button>
                </Link>
                <button className="delete" onClick={() => deleteCharacter(character.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CharacterForm({ editMode }) {
  const [character, setCharacter] = useState({
    name: ''
  });

  useEffect(() => {
    if (editMode) {
      const fetchCharacter = async () => {
        const id = window.location.pathname.split('/')[2];
        try {
          const response = await axios.get(`http://localhost:5000/characters/${id}`);
          setCharacter(response.data);
        } catch (error) {
          console.error('Error fetching character:', error);
        }
      };
      fetchCharacter();
    }
  }, [editMode]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCharacter(prevState => ({
      ...prevState,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editMode) {
        const id = window.location.pathname.split('/')[2];
        await axios.put(`http://localhost:5000/characters/${id}`, character);
      } else {
        await axios.post('http://localhost:5000/characters', character);
      }
      window.location.href = '/';
    } catch (error) {
      console.error('Error saving character:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Character Name:</label>
        <input
          type="text"
          name="name"
          value={character.name}
          onChange={handleChange}
          required
        />
      </div>
      <div className="form-actions">
        <Link to="/">
          <button type="button">Cancel</button>
        </Link>
        <button type="submit" className={editMode ? 'edit' : 'add'}>
          {editMode ? 'Update Character' : 'Add Character'}
        </button>
      </div>
    </form>
  );
}

export default App;