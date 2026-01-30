import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import {
    fetchEvent,
    addProposedDate,
    removeProposedDate,
    confirmEvent,
    cancelEvent,
} from "../services/api";
import DateVoting from "./DateVoting";
import InviteeManagement from "./InviteeManagement";

const EventDetails = () => {
    const { eventId } = useParams();
    const navigate = useNavigate();

    const [event, setEvent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Inline date-picker state for adding a new proposed date
    const [newDate, setNewDate] = useState(null);

    // Confirmation flow state
    const [confirmingDateId, setConfirmingDateId] = useState(null);

    const loadEvent = async () => {
        try {
            const data = await fetchEvent(eventId);
            setEvent(data);
        } catch (err) {
            console.error("Error fetching event:", err);
            setError("Could not load event details.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadEvent();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [eventId]);

    // ── helpers ──────────────────────────────────────────────────────────────

    const isOwner = () => {
        const userId = parseInt(localStorage.getItem("userId"), 10);
        return event && event.user === userId;
    };

    const isProposed = () => event && event.status === "PROPOSED";

    const handleAddDate = async () => {
        if (!newDate) return;
        const formatted = newDate.toISOString().split("T")[0];
        try {
            await addProposedDate(eventId, formatted);
            setNewDate(null);
            await loadEvent(); // refresh
        } catch (err) {
            console.error("Error adding date:", err);
            alert("Could not add that date. It may already exist.");
        }
    };

    const handleRemoveDate = async (dateId) => {
        try {
            await removeProposedDate(eventId, dateId);
            await loadEvent();
        } catch (err) {
            console.error("Error removing date:", err);
            alert("Could not remove that date.");
        }
    };

    const handleConfirm = async () => {
        if (!confirmingDateId) return;
        try {
            await confirmEvent(eventId, confirmingDateId);
            setConfirmingDateId(null);
            await loadEvent();
        } catch (err) {
            console.error("Error confirming event:", err);
            alert("Could not confirm the event.");
        }
    };

    const handleCancel = async () => {
        try {
            await cancelEvent(eventId);
            await loadEvent();
        } catch (err) {
            console.error("Error cancelling event:", err);
            alert("Could not cancel the event.");
        }
    };

    // ── date already selected guard for the add-date picker ──────────────────
    const existingDateStrings = event
        ? event.proposed_dates.map((pd) => pd.date)
        : [];

    const isDateAlreadyProposed = (date) => {
        const formatted = date.toISOString().split("T")[0];
        return existingDateStrings.includes(formatted);
    };

    // ── rendering helpers ────────────────────────────────────────────────────

    const getStatusStyle = (status) => {
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

    const getVoteBadgeStyle = (label) => {
        switch (label) {
            case "available":
                return { backgroundColor: "#d4edda", color: "#155724" };
            case "maybe":
                return { backgroundColor: "#fff3cd", color: "#856404" };
            case "not_available":
                return { backgroundColor: "#f8d7da", color: "#721c24" };
            default:
                return { backgroundColor: "#e2e3e5", color: "#383d41" };
        }
    };

    // ── early returns ────────────────────────────────────────────────────────

    if (loading) return <div>Loading event details...</div>;
    if (error) return <div style={{ color: "red" }}>{error}</div>;
    if (!event) return <div>Event not found.</div>;

    // ── main render ──────────────────────────────────────────────────────────

    return (
        <div>
            {/* Header */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }}>
                <button onClick={() => navigate("/home")} style={{ padding: "6px 12px", cursor: "pointer" }}>
                    ← Back
                </button>
                <h1 style={{ margin: 0 }}>{event.event_name}</h1>
                <span style={{ ...getStatusStyle(event.status), fontSize: "14px" }}>
                    ({event.status})
                </span>
            </div>

            {/* Cancelled banner */}
            {event.status === "CANCELLED" && (
                <div style={{
                    padding: "12px 16px",
                    marginBottom: "20px",
                    backgroundColor: "#f8d7da",
                    border: "1px solid #dc3545",
                    borderRadius: "4px",
                    color: "#721c24",
                }}>
                    This event has been cancelled.
                </div>
            )}

            {/* Confirmed banner */}
            {event.status === "CONFIRMED" && event.confirmed_date && (
                <div style={{
                    padding: "12px 16px",
                    marginBottom: "20px",
                    backgroundColor: "#d4edda",
                    border: "1px solid #28a745",
                    borderRadius: "4px",
                    color: "#155724",
                }}>
                    <strong>Confirmed date:</strong>{" "}
                    {new Date(event.confirmed_date.date + "T00:00:00").toLocaleDateString()}
                </div>
            )}

            {/* Proposed dates */}
            <section style={{ marginBottom: "24px" }}>
                <h3>Proposed Dates</h3>
                {event.proposed_dates.length === 0 ? (
                    <p style={{ color: "#666" }}>No proposed dates yet.</p>
                ) : (
                    <ul style={{ padding: 0, listStyle: "none" }}>
                        {event.proposed_dates.map((pd) => {
                            const isConfirmedDate =
                                event.confirmed_date && event.confirmed_date.id === pd.id;
                            return (
                                <li
                                    key={pd.id}
                                    style={{
                                        padding: "10px 14px",
                                        marginBottom: "8px",
                                        border: isConfirmedDate
                                            ? "2px solid #28a745"
                                            : "1px solid #ccc",
                                        borderRadius: "4px",
                                        backgroundColor: isConfirmedDate ? "#f0fff4" : "transparent",
                                    }}
                                >
                                    <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                                        <strong>
                                            {new Date(pd.date + "T00:00:00").toLocaleDateString()}
                                        </strong>
                                        {isConfirmedDate && (
                                            <span style={{ fontSize: "12px", color: "#28a745", fontWeight: "bold" }}>
                                                ✓ Confirmed
                                            </span>
                                        )}

                                        {/* Vote summary badges */}
                                        {pd.vote_summary && (
                                            <span style={{ display: "flex", gap: "6px", marginLeft: "auto" }}>
                                                {[
                                                    { label: "available", display: "Available" },
                                                    { label: "maybe", display: "Maybe" },
                                                    { label: "not_available", display: "Unavailable" },
                                                ].map(({ label, display }) => (
                                                    <span
                                                        key={label}
                                                        style={{
                                                            ...getVoteBadgeStyle(label),
                                                            padding: "2px 8px",
                                                            borderRadius: "12px",
                                                            fontSize: "12px",
                                                        }}
                                                    >
                                                        {display}: {pd.vote_summary[label]}
                                                    </span>
                                                ))}
                                            </span>
                                        )}

                                        {/* Remove button — owner only, proposed status, more than one date */}
                                        {isOwner() && isProposed() && event.proposed_dates.length > 1 && (
                                            <button
                                                onClick={() => handleRemoveDate(pd.id)}
                                                style={{
                                                    marginLeft: "8px",
                                                    padding: "3px 10px",
                                                    fontSize: "12px",
                                                    color: "#dc3545",
                                                    border: "1px solid #dc3545",
                                                    borderRadius: "4px",
                                                    backgroundColor: "transparent",
                                                    cursor: "pointer",
                                                }}
                                            >
                                                Remove
                                            </button>
                                        )}
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                )}

                {/* Add date — owner only, proposed status */}
                {isOwner() && isProposed() && (
                    <div style={{ marginTop: "12px" }}>
                        <label style={{ display: "block", marginBottom: "6px", fontWeight: "bold", fontSize: "14px" }}>
                            Add a proposed date:
                        </label>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <DatePicker
                                selected={newDate}
                                onChange={(date) => setNewDate(date)}
                                placeholderText="Pick a date"
                                dayClassName={(date) =>
                                    isDateAlreadyProposed(date) ? "already-proposed" : undefined
                                }
                            />
                            <button
                                onClick={handleAddDate}
                                disabled={!newDate}
                                style={{
                                    padding: "6px 14px",
                                    backgroundColor: newDate ? "#007bff" : "#ccc",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "4px",
                                    cursor: newDate ? "pointer" : "not-allowed",
                                }}
                            >
                                Add
                            </button>
                        </div>
                        <style>
                            {`
                                .already-proposed {
                                    opacity: 0.4 !important;
                                    pointer-events: none !important;
                                }
                            `}
                        </style>
                    </div>
                )}
            </section>

            {/* Voting panel — visible while the event is still PROPOSED */}
            {isProposed() && (
                <DateVoting
                    eventId={event.id}
                    proposedDates={event.proposed_dates}
                    onVoteChange={loadEvent}
                />
            )}

            {/* Invitee management — owner only */}
            {isOwner() && (
                <InviteeManagement
                    eventId={event.id}
                    proposedDates={event.proposed_dates}
                    onInviteeChange={loadEvent}
                />
            )}

            {/* Action buttons — owner only, not already cancelled */}
            {isOwner() && event.status !== "CANCELLED" && (
                <section style={{ marginBottom: "24px" }}>
                    <h3>Actions</h3>

                    {/* Confirm flow — only while still PROPOSED */}
                    {isProposed() && (
                        confirmingDateId === null ? (
                            <button
                                onClick={() => setConfirmingDateId("pending")}
                                style={{
                                    marginRight: "10px",
                                    padding: "8px 16px",
                                    backgroundColor: "#28a745",
                                    color: "white",
                                    border: "none",
                                    borderRadius: "4px",
                                    cursor: "pointer",
                                }}
                            >
                                Confirm Event
                            </button>
                        ) : (
                            <div style={{
                                padding: "12px 14px",
                                border: "1px solid #28a745",
                                borderRadius: "4px",
                                marginBottom: "12px",
                            }}>
                                <p style={{ margin: "0 0 10px 0", fontWeight: "bold" }}>
                                    Select the date to confirm:
                                </p>
                                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                                    {event.proposed_dates.map((pd) => (
                                        <label
                                            key={pd.id}
                                            style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}
                                        >
                                            <input
                                                type="radio"
                                                name="confirm-date"
                                                checked={confirmingDateId === pd.id}
                                                onChange={() => setConfirmingDateId(pd.id)}
                                            />
                                            {new Date(pd.date + "T00:00:00").toLocaleDateString()}
                                        </label>
                                    ))}
                                </div>
                                <div style={{ marginTop: "10px", display: "flex", gap: "8px" }}>
                                    <button
                                        onClick={handleConfirm}
                                        disabled={confirmingDateId === "pending"}
                                        style={{
                                            padding: "6px 14px",
                                            backgroundColor: confirmingDateId !== "pending" ? "#28a745" : "#ccc",
                                            color: "white",
                                            border: "none",
                                            borderRadius: "4px",
                                            cursor: confirmingDateId !== "pending" ? "pointer" : "not-allowed",
                                        }}
                                    >
                                        Confirm
                                    </button>
                                    <button
                                        onClick={() => setConfirmingDateId(null)}
                                        style={{
                                            padding: "6px 14px",
                                            border: "1px solid #ccc",
                                            borderRadius: "4px",
                                            cursor: "pointer",
                                            backgroundColor: "transparent",
                                        }}
                                    >
                                        Cancel selection
                                    </button>
                                </div>
                            </div>
                        )
                    )}

                    {/* Cancel event — available for both PROPOSED and CONFIRMED */}
                    <button
                        onClick={handleCancel}
                        style={{
                            padding: "8px 16px",
                            backgroundColor: "#dc3545",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: "pointer",
                        }}
                    >
                        Cancel Event
                    </button>
                </section>
            )}
        </div>
    );
};

export default EventDetails;
