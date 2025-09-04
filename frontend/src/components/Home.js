import React from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

const Home = ({ onLogout }) => {
    const navigate = useNavigate();

    const userName = localStorage.getItem("userName");

    const handleLogout = async () => {
        try {
            // Send request to backend logout endpoint
            const token = localStorage.getItem("token");
    
            // If there’s no token, just clean up; no need to call the server.
            if (!token) {
                localStorage.removeItem("token");
                onLogout?.();
                navigate("/login");
                return;
            }

            const response = await api.post("/auth/logout/", {}, {
                headers: {
                    Authorization: `Token ${token}`,
                },
            });

            if (response.status === 204) {
                localStorage.removeItem("token");
                onLogout?.(); // Update frontend state
                navigate("/login"); // Redirect to login page
            } else {
                const errorData = response.data;
                console.error("Logout failed:", errorData);
                alert("Logout failed. Please try again.");
            }
        } catch (error) {
            console.error("Error during logout:", error);
            alert("An error occurred during logout. Please try again.");
        }
    };

    const handleCreateEvent = () => {
        navigate("/create-event");
    };

    return (
        <div>
            <h1>Home</h1>
            {userName && <h2>Welcome, {userName}!</h2>}
            <button style={{ backgroundColor: 'blue', color: 'white' }} onClick={handleCreateEvent}>Create Event</button>
            <button onClick={handleLogout}>Logout</button>
        </div>
    );
};

export default Home;
