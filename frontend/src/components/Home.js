import React from "react";
import { useNavigate } from "react-router-dom";

const Home = ({ onLogout }) => {
    const navigate = useNavigate();

    const userName = localStorage.getItem("userName");

    const handleLogout = async () => {
        try {
            // Send request to backend logout endpoint
            const token = localStorage.getItem("token");
            const response = await fetch("http://localhost:8000/api/logout/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Token ${token}`, // Include token in Authorization header
                },
            });
    
            if (response.ok) {
                localStorage.removeItem("token"); // Remove token from local storage
                onLogout(); // Update frontend state
                navigate("/login"); // Redirect to login page
            } else {
                const errorData = await response.json();
                console.error("Logout failed:", errorData);
                alert("Logout failed. Please try again.");
            }
        } catch (error) {
            console.error("Error during logout:", error);
            alert("An error occurred during logout. Please try again.");
        }
    };

    return (
        <div>
            <h1>Home</h1>
            {userName && <h2>Welcome, {userName}!</h2>}
            <button onClick={handleLogout}>Logout</button>
        </div>
    );
};

export default Home;
