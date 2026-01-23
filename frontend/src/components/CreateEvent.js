import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { createEvent } from "../services/api";

const CreateEvent = () => {
    const [eventName, setEventName] = useState("");
    const [selectedDates, setSelectedDates] = useState([]);
    const [inviteesInput, setInviteesInput] = useState("");
    const navigate = useNavigate();

    const handleDateChange = (date) => {
        if (!date) return;

        // Check if date is already selected
        const dateExists = selectedDates.some(
            (d) => d.toDateString() === date.toDateString()
        );

        if (dateExists) {
            // Remove date if already selected
            setSelectedDates(selectedDates.filter(
                (d) => d.toDateString() !== date.toDateString()
            ));
        } else {
            // Add date if not selected
            setSelectedDates([...selectedDates, date].sort((a, b) => a - b));
        }
    };

    const removeDate = (dateToRemove) => {
        setSelectedDates(selectedDates.filter(
            (d) => d.toDateString() !== dateToRemove.toDateString()
        ));
    };

    const parseInvitees = () => {
        if (!inviteesInput.trim()) return [];

        const ids = inviteesInput
            .split(",")
            .map((id) => id.trim())
            .filter((id) => id !== "")
            .map((id) => parseInt(id, 10))
            .filter((id) => !isNaN(id));

        return [...new Set(ids)]; // Remove duplicates
    };

    const handleSubmit = async () => {
        if (!eventName.trim()) {
            alert("Event name is required.");
            return;
        }
        if (selectedDates.length === 0) {
            alert("Please select at least one date.");
            return;
        }

        const invitees = parseInvitees();

        try {
            // Format dates as 'YYYY-MM-DD' strings
            const formattedDates = selectedDates.map(date => date.toISOString().split('T')[0]);

            await createEvent(eventName, formattedDates, invitees);
            navigate("/home");
        } catch (error) {
            console.error("Error during event creation:", error);
            alert("An error occurred during event creation. Please try again.");
        }
    };

    const handleCancel = () => {
        navigate("/home");
    };

    // Highlight selected dates in the calendar
    const isDateSelected = (date) => {
        return selectedDates.some((d) => d.toDateString() === date.toDateString());
    };

    return (
        <div>
            <h1>Create Event</h1>
            <div style={{ marginBottom: "15px" }}>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                    Event Name:
                </label>
                <input
                    type="text"
                    value={eventName}
                    onChange={(e) => setEventName(e.target.value)}
                    placeholder="Enter event name"
                    style={{ padding: "8px", fontSize: "16px", width: "300px" }}
                />
            </div>

            <div style={{ marginBottom: "15px" }}>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                    Select Proposed Dates:
                </label>
                <p style={{ margin: "0 0 10px 0", fontSize: "14px", color: "#666" }}>
                    Click on dates to select/deselect them
                </p>
                <DatePicker
                    onChange={handleDateChange}
                    inline
                    dayClassName={(date) =>
                        isDateSelected(date) ? "selected-date" : undefined
                    }
                />
                <style>
                    {`
                        .selected-date {
                            background-color: #007bff !important;
                            color: white !important;
                            border-radius: 50%;
                        }
                    `}
                </style>
            </div>

            {selectedDates.length > 0 && (
                <div style={{ marginBottom: "15px" }}>
                    <strong>Selected dates ({selectedDates.length}):</strong>
                    <ul style={{ margin: "5px 0", paddingLeft: "20px" }}>
                        {selectedDates.map((date, index) => (
                            <li key={index} style={{ marginBottom: "5px" }}>
                                {date.toLocaleDateString()}
                                <button
                                    onClick={() => removeDate(date)}
                                    style={{
                                        marginLeft: "10px",
                                        padding: "2px 8px",
                                        fontSize: "12px",
                                        cursor: "pointer"
                                    }}
                                >
                                    Remove
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div style={{ marginBottom: "15px" }}>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>
                    Invite Users (optional):
                </label>
                <input
                    type="text"
                    value={inviteesInput}
                    onChange={(e) => setInviteesInput(e.target.value)}
                    placeholder="Enter user IDs separated by commas (e.g., 2, 3, 5)"
                    style={{ padding: "8px", fontSize: "16px", width: "300px" }}
                />
                <p style={{ margin: "5px 0 0 0", fontSize: "14px", color: "#666" }}>
                    Enter the user IDs of people you want to invite
                </p>
            </div>

            <div>
                <button
                    style={{ backgroundColor: 'blue', color: 'white', marginRight: '10px', padding: '8px 16px' }}
                    onClick={handleSubmit}
                >
                    Create Event
                </button>
                <button
                    style={{ padding: '8px 16px' }}
                    onClick={handleCancel}
                >
                    Cancel
                </button>
            </div>
        </div>
    );
};

export default CreateEvent;
