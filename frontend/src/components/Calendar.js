import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

const Calendar = () => {
    const [eventName, setEventName] = useState("");
    const [selectedDates, setSelectedDates] = useState([null, null]); // Initialize properly for a range
    const navigate = useNavigate();

    const handleSubmit = async () => {
        if (!eventName.trim()) {
            alert("Event name is required.");
            return;
        }
        if (!selectedDates[0] || !selectedDates[1]) {
            alert("Please select a valid date range.");
            return;
        }

        try {
            const token = localStorage.getItem("token");
            const response = await fetch("http://localhost:8000/api/create-event/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Token ${token}`,
                },
                body: JSON.stringify({
                    event_name: eventName,
                    dates: selectedDates.map(date => date.toISOString().split('T')[0]),
                }),
            });

            if (response.ok) {
                navigate("/");
            } else {
                const errorData = await response.json();
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
                onChange={(dates) => setSelectedDates(dates || [null, null])} // Ensure dates is valid
                selectsRange
                startDate={selectedDates[0]}
                endDate={selectedDates[1]}
            />
            <button onClick={handleSubmit}>Create Event</button>
        </div>
    );
};

export default Calendar;