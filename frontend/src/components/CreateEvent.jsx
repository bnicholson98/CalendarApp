import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { createEvent } from "../services/api";

const CreateEvent = () => {
    const [eventName, setEventName] = useState("");
    const [selectedDates, setSelectedDates] = useState([]);
    const [inviteesInput, setInviteesInput] = useState("");
    const [inviteeWarnings, setInviteeWarnings] = useState([]);
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

        const usernames = inviteesInput
            .split(",")
            .map((name) => name.trim())
            .filter((name) => name !== "");

        return [...new Set(usernames)]; // Remove duplicates
    };

    const handleInviteesChange = (e) => {
        setInviteesInput(e.target.value);
        // Clear any previous warnings when the user edits the field
        setInviteeWarnings([]);
    };

    const handleSubmit = async () => {
        // Clear previous warnings before every submission attempt
        setInviteeWarnings([]);

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

            const responseData = await createEvent(eventName, formattedDates, invitees);

            // Surface any invitee warnings the backend returned without blocking navigation
            if (responseData.warnings && responseData.warnings.length > 0) {
                setInviteeWarnings(responseData.warnings);
            } else {
                navigate("/home");
            }
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
                    onChange={handleInviteesChange}
                    placeholder="Enter usernames separated by commas (e.g., Alice, Bob)"
                    style={{ padding: "8px", fontSize: "16px", width: "300px" }}
                />
                <p style={{ margin: "5px 0 0 0", fontSize: "14px", color: "#666" }}>
                    Enter the usernames of people you want to invite
                </p>

                {inviteeWarnings.length > 0 && (
                    <div style={{
                        marginTop: "10px",
                        padding: "10px 14px",
                        backgroundColor: "#fff3cd",
                        border: "1px solid #ffc107",
                        borderRadius: "4px",
                        color: "#856404",
                    }}>
                        <strong>⚠️ Invitee warnings — the event was created but some invites were skipped:</strong>
                        <ul style={{ margin: "8px 0 0 0", paddingLeft: "20px" }}>
                            {inviteeWarnings.map((warning, idx) => (
                                <li key={idx} style={{ marginBottom: "4px" }}>
                                    {warning.message}
                                </li>
                            ))}
                        </ul>
                        <button
                            onClick={() => navigate("/home")}
                            style={{
                                marginTop: "8px",
                                padding: "6px 14px",
                                backgroundColor: "#007bff",
                                color: "white",
                                border: "none",
                                borderRadius: "4px",
                                cursor: "pointer",
                            }}
                        >
                            Go to Home
                        </button>
                    </div>
                )}
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
