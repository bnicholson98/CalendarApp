import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const Register = ({ onRegister }) => { 
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("http://127.0.0.1:8000/api/auth/register/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        alert("User registered successfully!");
        localStorage.setItem("token", "mockToken"); // Simulate token from API
        onRegister(); // Update parent state
        navigate("/home"); // Navigate to home page
      } else {
        alert("Error during registration");
      }
    } catch (error) {
      console.error("Registration error:", error);
    }
  };

  return (
    <div>
      <h1>Register</h1>
      <form onSubmit={handleRegister}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Register</button>
        <button type="button" onClick={() => navigate("/login")}>
          Back to Login
        </button>
      </form>
    </div>
  );
};

export default Register;
