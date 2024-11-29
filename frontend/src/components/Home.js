import React from "react";
import { useNavigate } from "react-router-dom";

const Home = ({ onLogout }) => {
    const navigate = useNavigate();

    const handleLogout = () => {
        onLogout();
        navigate("/login");
    };

    return (
        <div>
            <h1>Welcome to the Home Page</h1>
            <button onClick={handleLogout}>Logout</button>
        </div>
    );
};

export default Home;
