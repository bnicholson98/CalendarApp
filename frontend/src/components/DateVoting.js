import React, { useState, useEffect } from "react";
import { fetchMyVotes, voteOnDate, deleteVote } from "../services/api";

/**
 * DateVoting renders a voting panel for every proposed date on a single event.
 *
 * Props:
 *   eventId        – numeric event ID
 *   proposedDates  – array of proposed-date objects from the event detail response
 *                    (each has at least { id, date })
 *   onVoteChange   – callback invoked after any vote is posted or deleted so the
 *                    parent can refresh the event (and therefore vote_summary counts)
 */
const DateVoting = ({ eventId, proposedDates, onVoteChange }) => {
    // Map: proposed_date id  →  current availability string (or null when no vote)
    const [myVotes, setMyVotes] = useState({});
    const [loading, setLoading] = useState(true);

    const loadMyVotes = async () => {
        try {
            const votes = await fetchMyVotes(eventId);
            // Index by proposed_date id for O(1) lookup
            const indexed = {};
            votes.forEach((v) => {
                indexed[v.proposed_date] = v.availability;
            });
            setMyVotes(indexed);
        } catch (err) {
            console.error("Error loading votes:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadMyVotes();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [eventId]);

    const handleVote = async (dateId, availability) => {
        try {
            await voteOnDate(eventId, dateId, availability);
            setMyVotes((prev) => ({ ...prev, [dateId]: availability }));
            onVoteChange();
        } catch (err) {
            console.error("Error posting vote:", err);
            alert("Could not save your vote.");
        }
    };

    const handleClear = async (dateId) => {
        try {
            await deleteVote(eventId, dateId);
            setMyVotes((prev) => {
                const next = { ...prev };
                delete next[dateId];
                return next;
            });
            onVoteChange();
        } catch (err) {
            console.error("Error clearing vote:", err);
            alert("Could not clear your vote.");
        }
    };

    if (loading) return <p style={{ color: "#666", fontSize: "14px" }}>Loading your votes…</p>;

    const OPTIONS = [
        { value: "AVAILABLE", label: "Available", color: "#28a745" },
        { value: "MAYBE", label: "Maybe", color: "#ffc107" },
        { value: "NOT_AVAILABLE", label: "Not Available", color: "#dc3545" },
    ];

    return (
        <section style={{ marginBottom: "24px" }}>
            <h3>Your Availability</h3>
            <ul style={{ padding: 0, listStyle: "none" }}>
                {proposedDates.map((pd) => {
                    const current = myVotes[pd.id] || null;
                    return (
                        <li
                            key={pd.id}
                            style={{
                                padding: "10px 14px",
                                marginBottom: "8px",
                                border: "1px solid #ccc",
                                borderRadius: "4px",
                            }}
                        >
                            <div style={{ marginBottom: "8px", fontWeight: "bold" }}>
                                {new Date(pd.date + "T00:00:00").toLocaleDateString()}
                            </div>
                            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
                                {OPTIONS.map((opt) => {
                                    const isSelected = current === opt.value;
                                    return (
                                        <button
                                            key={opt.value}
                                            onClick={() => handleVote(pd.id, opt.value)}
                                            style={{
                                                padding: "5px 12px",
                                                border: isSelected
                                                    ? `2px solid ${opt.color}`
                                                    : "1px solid #ccc",
                                                borderRadius: "4px",
                                                backgroundColor: isSelected ? opt.color : "transparent",
                                                color: isSelected ? "white" : "#333",
                                                fontWeight: isSelected ? "bold" : "normal",
                                                cursor: "pointer",
                                                transition: "all 0.15s ease",
                                            }}
                                        >
                                            {opt.label}
                                        </button>
                                    );
                                })}
                                {current && (
                                    <button
                                        onClick={() => handleClear(pd.id)}
                                        style={{
                                            padding: "5px 10px",
                                            border: "1px solid #999",
                                            borderRadius: "4px",
                                            backgroundColor: "transparent",
                                            color: "#666",
                                            fontSize: "12px",
                                            cursor: "pointer",
                                        }}
                                    >
                                        Clear
                                    </button>
                                )}
                            </div>
                        </li>
                    );
                })}
            </ul>
        </section>
    );
};

export default DateVoting;
