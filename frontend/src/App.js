import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from './components/Login';
import Register from './components/Register';
import Home from './components/Home';
import CreateEvent from "./components/CreateEvent";
import EventDetails from "./components/EventDetails";

function App() {
	// Read the token synchronously so the first render already knows the auth
	// state; otherwise protected routes redirect to /login before it's checked.
	// An invalid token is caught by the 401 interceptor in services/api.js.
	const [authenticated, setAuthenticated] = useState(() => !!localStorage.getItem('token'));

	const handleRegister = () => setAuthenticated(true);
	const handleLogin = () => setAuthenticated(true);
	const handleLogout = () => {
		localStorage.removeItem('token');
		setAuthenticated(false);
	};

	return (
		<Router>
		  	<Routes>
				<Route path="/login" element={authenticated ? (<Navigate to="/home" />) : (<Login onLogin={handleLogin} />)}/>
				<Route path="/register" element={authenticated ? (<Navigate to="/home" />) : (<Register onRegister={handleRegister} />)}/>
				<Route path="/home" element={authenticated ? (<Home onLogout={handleLogout} />) : (<Navigate to="/login" />)}/>
				<Route path="/" element={<Navigate to="/login" />} />
				<Route path="/create-event" element={authenticated ? (<CreateEvent />) : (<Navigate to="/login" />)} />
				<Route path="/event-details/:eventId" element={authenticated ? (<EventDetails />) : (<Navigate to="/login" />)} />
			</Routes>
		</Router>
	);
}

export default App;
