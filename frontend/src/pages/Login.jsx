// src/pages/Login.js
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
// eslint-disable-next-line no-unused-vars
import api  from '../api/axios';

export default function Login() {
  const [email, setEmail] = useState('test@kenya.com');
  const [password, setPassword] = useState('123456');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      // You'll add this route in backend later, or use this dummy token for now:
      const dummyToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI2NzA5ZmI3Y2QwZjRkNjAwM2QxZmI3Y2QiLCJlbWFpbCI6InRlc3RAa2VueWEuY29tIiwiaWF0IjoxNzI4ODM5OTk5fQ.dummy";
      
      login(dummyToken);
      navigate('/wardrobe');
    // eslint-disable-next-line no-unused-vars
    } catch (err) {
      alert('Login failed');
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '100px auto', padding: 20, fontFamily: 'Arial' }}>
      <h2>Login to Wardrobe AI Kenya</h2>
      <form onSubmit={handleLogin}>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: '100%', padding: 12, margin: '10px 0', fontSize: 16 }}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: '100%', padding: 12, margin: '10px 0', fontSize: 16 }}
          required
        />
        <button type="submit" style={{ width: '100%', padding: 14, background: '#1976d2', color: 'white', border: 'none', fontSize: 16 }}>
          Login
        </button>
      </form>
      <p style={{ marginTop: 20, color: '#555' }}>
        Use: <strong>test@kenya.com</strong> + <strong>123456</strong> (or just click Login)
      </p>
    </div>
  );
}