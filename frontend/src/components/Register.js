import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const Register = ({ onRegister }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post("/auth/register/", {
        username,
        password,
      });
      if (response.status === 201) {
        alert("User registered successfully!");
        const loginResponse = await api.post("/auth/login/", {
          username,
          password,
        });
        if (loginResponse.status === 200) {
          localStorage.setItem("token", loginResponse.data.token);
          localStorage.setItem("userId", loginResponse.data.userId);
          localStorage.setItem("userName", loginResponse.data.userName);
          onRegister(); // Update parent state
          navigate("/home"); // Navigate to home page
        } else {
          alert("Login failed after registration.");
        }
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
