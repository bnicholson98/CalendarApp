import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from './components/Login';
import Register from './components/Register';
import Home from './components/Home';

function App() {
	const [authenticated, setAuthenticated] = useState(false);

	useEffect(() => {
		if (localStorage.getItem('token')) {
		setAuthenticated(true);  // Check if token exists
		}
	}, []);

	const handleRegister = () => setAuthenticated(true);
	const handleLogin = () => setAuthenticated(true);
	const handleLogout = () => {
		localStorage.removeItem('token');
		setAuthenticated(false);
	};

	return (
		<Router>
		  	<Routes>
				<Route
			  		path="/login"
			  		element={
						authenticated ? (
				  			<Navigate to="/home" />
						) : (
				  			<Login onLogin={handleLogin} />
						)
					}
				/>
				<Route
					path="/register"
					element={
						authenticated ? (
							<Navigate to="/home" />
						) : (
							<Register onRegister={handleRegister} />
						)
					}
				/>
				<Route
					path="/home"
					element={
						authenticated ? (
							<Home onLogout={handleLogout} />
						) : (
							<Navigate to="/login" />
						)
					}
				/>
				<Route path="/" element={<Navigate to="/login" />} />
			</Routes>
		</Router>
	);
}

export default App;
