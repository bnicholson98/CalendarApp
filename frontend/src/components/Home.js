import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api, { fetchUserEvents, fetchReceivedInvites } from "../services/api";

const Home = ({ onLogout }) => {
    const navigate = useNavigate();
    const userName = localStorage.getItem("userName");

    const [myEvents, setMyEvents] = useState([]);
    const [invitedEvents, setInvitedEvents] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [events, invites] = await Promise.all([
                    fetchUserEvents(),
                    fetchReceivedInvites(),
                ]);

                // Create a map of event ID to event details for quick lookup
                const eventsById = {};
                events.forEach(event => {
                    eventsById[event.id] = event;
                });

                // Filter events by ownership using stored userId
                const userId = parseInt(localStorage.getItem("userId"), 10);
                const ownedEvents = events.filter(event => event.user === userId);
                setMyEvents(ownedEvents);

                // Enrich invites with event details
                const enrichedInvites = invites.map(invite => ({
                    ...invite,
                    eventDetails: eventsById[invite.event] || null,
                }));
                setInvitedEvents(enrichedInvites);
            } catch (error) {
                console.error("Error loading data:", error);
                alert("An error occurred while loading your events. Please try again.");
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    const handleLogout = async () => {
        try {
            const token = localStorage.getItem("token");

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
                onLogout?.();
                navigate("/login");
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

    const getEventStatusStyle = (status) => {
        switch (status) {
            case "CONFIRMED":
                return { color: "green", fontWeight: "bold" };
            case "CANCELLED":
                return { color: "gray", textDecoration: "line-through" };
            case "PROPOSED":
            default:
                return { color: "blue" };
        }
    };

    const getInviteStatusStyle = (status) => {
        switch (status) {
            case "PENDING":
                return {
                    backgroundColor: "#fff3cd",
                    border: "2px solid #ffc107",
                    fontWeight: "bold",
                };
            case "ACCEPTED":
                return { backgroundColor: "#d4edda", border: "1px solid #28a745" };
            case "DECLINED":
                return { backgroundColor: "#f8d7da", border: "1px solid #dc3545" };
            case "MAYBE":
                return { backgroundColor: "#e2e3e5", border: "1px solid #6c757d" };
            default:
                return {};
        }
    };

    const listItemStyle = {
        padding: "10px",
        marginBottom: "8px",
        borderRadius: "4px",
        listStyle: "none",
    };

    if (loading) {
        return <div>Loading...</div>;
    }

    return (
        <div>
            <h1>Home</h1>
            {userName && <h2>Welcome, {userName}!</h2>}
            <button style={{ backgroundColor: 'blue', color: 'white' }} onClick={handleCreateEvent}>Create Event</button>
            <button onClick={handleLogout}>Logout</button>

            <section style={{ marginTop: "20px" }}>
                <h3>My Events</h3>
                {myEvents.length === 0 ? (
                    <p>You haven't created any events yet.</p>
                ) : (
                    <ul style={{ padding: 0 }}>
                        {myEvents.map((event) => (
                            <li key={event.id} style={{ ...listItemStyle, border: "1px solid #ccc" }}>
                                <strong>{event.event_name}</strong>
                                <span style={{ marginLeft: "10px", ...getEventStatusStyle(event.status) }}>
                                    ({event.status})
                                </span>
                            </li>
                        ))}
                    </ul>
                )}
            </section>

            <section style={{ marginTop: "20px" }}>
                <h3>Invited Events</h3>
                {invitedEvents.length === 0 ? (
                    <p>You have no event invitations.</p>
                ) : (
                    <ul style={{ padding: 0 }}>
                        {invitedEvents.map((invite) => (
                            <li
                                key={invite.id}
                                style={{ ...listItemStyle, ...getInviteStatusStyle(invite.status) }}
                            >
                                <strong>
                                    {invite.eventDetails ? invite.eventDetails.event_name : `Event #${invite.event}`}
                                </strong>
                                {invite.eventDetails && (
                                    <span style={{ marginLeft: "10px", ...getEventStatusStyle(invite.eventDetails.status) }}>
                                        ({invite.eventDetails.status})
                                    </span>
                                )}
                                <span style={{ marginLeft: "10px" }}>
                                    - Your Response: {invite.status}
                                    {invite.status === "PENDING" && " ⚠️ Action Required"}
                                </span>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </div>
    );
};

export default Home;
