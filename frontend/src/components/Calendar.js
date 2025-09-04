import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import api from "../services/api";

const Calendar = () => {
    const [eventName, setEventName] = useState("");
    const [selectedDates, setSelectedDates] = useState([]);
    const navigate = useNavigate();

    const handleSubmit = async () => {
        if (!eventName.trim()) {
            alert("Event name is required.");
            return;
        }
        if (selectedDates.length === 0) {
            alert("Please select at least one date.");
            return;
        }

        try {
            const token = localStorage.getItem("token");
            const response = await api.post("/events/create/", {
                event_name: eventName,
                dates: selectedDates.map(date => date.toISOString().split('T')[0]),
            }, {
                headers: {
                    Authorization: `Token ${token}`,
                },
            });

            if (response.status === 201) {
                navigate("/");
            } else {
                const errorData = response.data;
                console.error("Event creation failed:", errorData);
                alert("Event creation failed. Please try again.");
            }
        } catch (error) {
            console.error("Error during event creation:", error);
            alert("An error occurred during event creation. Please try again.");
        }
    };

    return (
        <div>
            <h1>Create Event</h1>
            <input
                type="text"
                value={eventName}
                onChange={(e) => setEventName(e.target.value)}
                placeholder="Event Name"
            />
            <DatePicker
                onChange={(dates) => setSelectedDates(dates || [])}
                selectsMultiple
                inline
            />
            <button onClick={handleSubmit}>Create Event</button>
        </div>
    );
};

export default Calendar;
