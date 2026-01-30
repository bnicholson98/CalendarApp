import React, { useState, useEffect } from "react";
import { fetchEventInvites, createEventInvite, deleteEventInvite, fetchEventVotes } from "../services/api";

/**
 * InviteeManagement renders the owner-facing invitee list for a single event.
 *
 * Props:
 *   eventId        – numeric event ID
 *   proposedDates  – array of proposed-date objects from the event detail response
 *   onInviteeChange – callback invoked after any invite is created or deleted so
 *                     the parent can refresh the event if needed
 */
const InviteeManagement = ({ eventId, proposedDates, onInviteeChange }) => {
    const [invites, setInvites] = useState([]);
    const [votesByUser, setVotesByUser] = useState({});
    const [loading, setLoading] = useState(true);
    const [newUsername, setNewUsername] = useState("");

    const loadData = async () => {
        try {
            const [inviteList, eventVotes] = await Promise.all([
                fetchEventInvites(eventId),
                fetchEventVotes(eventId),
            ]);
            setInvites(inviteList);

            // Pivot per-date vote data into per-user totals:
            // { userId: { AVAILABLE: n, MAYBE: n, NOT_AVAILABLE: n } }
            const byUser = {};
            eventVotes.forEach((dateEntry) => {
                dateEntry.votes.forEach((vote) => {
                    if (!byUser[vote.user_id]) {
                        byUser[vote.user_id] = { AVAILABLE: 0, MAYBE: 0, NOT_AVAILABLE: 0 };
                    }
                    byUser[vote.user_id][vote.availability]++;
                });
            });
            setVotesByUser(byUser);
        } catch (err) {
            console.error("Error loading invitee data:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [eventId]);

    const handleAdd = async () => {
        const trimmed = newUsername.trim();
        if (!trimmed) return;
        try {
            await createEventInvite(eventId, trimmed);
            setNewUsername("");
            await loadData();
            onInviteeChange();
        } catch (err) {
            console.error("Error adding invitee:", err);
            alert("Could not add that invitee. The username may not exist or they may already be invited.");
        }
    };

    const handleRemove = async (inviteId) => {
        try {
            await deleteEventInvite(inviteId);
            await loadData();
            onInviteeChange();
        } catch (err) {
            console.error("Error removing invitee:", err);
            alert("Could not remove that invitee.");
        }
    };

    // ── rendering helpers ──────────────────────────────────────────────────────

    const getInviteStatusBadgeStyle = (status) => {
        switch (status) {
            case "PENDING":
                return { backgroundColor: "#fff3cd", color: "#856404" };
            case "ACCEPTED":
                return { backgroundColor: "#d4edda", color: "#155724" };
            case "DECLINED":
                return { backgroundColor: "#f8d7da", color: "#721c24" };
            case "MAYBE":
                return { backgroundColor: "#e2e3e5", color: "#383d41" };
            default:
                return { backgroundColor: "#e2e3e5", color: "#383d41" };
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

    const badgeStyle = {
        padding: "2px 8px",
        borderRadius: "12px",
        fontSize: "12px",
    };

    // ── early return ───────────────────────────────────────────────────────────

    if (loading) return <p style={{ color: "#666", fontSize: "14px" }}>Loading invitees…</p>;

    // ── main render ────────────────────────────────────────────────────────────

    return (
        <section style={{ marginBottom: "24px" }}>
            <h3>Invitees</h3>

            {invites.length === 0 ? (
                <p style={{ color: "#666" }}>No invitees yet.</p>
            ) : (
                <ul style={{ padding: 0, listStyle: "none" }}>
                    {invites.map((invite) => {
                        const userVotes = votesByUser[invite.invitee] || { AVAILABLE: 0, MAYBE: 0, NOT_AVAILABLE: 0 };
                        const totalVoted = userVotes.AVAILABLE + userVotes.MAYBE + userVotes.NOT_AVAILABLE;
                        const notVoted = proposedDates.length - totalVoted;

                        return (
                            <li
                                key={invite.id}
                                style={{
                                    padding: "10px 14px",
                                    marginBottom: "8px",
                                    border: "1px solid #ccc",
                                    borderRadius: "4px",
                                }}
                            >
                                <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                                    <strong>{invite.invitee_username}</strong>

                                    <span style={{ ...getInviteStatusBadgeStyle(invite.status), ...badgeStyle }}>
                                        {invite.status}
                                    </span>

                                    {/* Vote summary badges */}
                                    <span style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                                        {[
                                            { label: "available", display: "Available", count: userVotes.AVAILABLE },
                                            { label: "maybe", display: "Maybe", count: userVotes.MAYBE },
                                            { label: "not_available", display: "Unavailable", count: userVotes.NOT_AVAILABLE },
                                        ].map(({ label, display, count }) => (
                                            <span key={label} style={{ ...getVoteBadgeStyle(label), ...badgeStyle }}>
                                                {display}: {count}
                                            </span>
                                        ))}
                                        {notVoted > 0 && (
                                            <span style={{ ...getVoteBadgeStyle("default"), ...badgeStyle }}>
                                                Not voted: {notVoted}
                                            </span>
                                        )}
                                    </span>

                                    {/* Remove button */}
                                    <button
                                        onClick={() => handleRemove(invite.id)}
                                        style={{
                                            marginLeft: "auto",
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
                                </div>
                            </li>
                        );
                    })}
                </ul>
            )}

            {/* Add invitee input */}
            <div style={{ marginTop: "12px" }}>
                <label style={{ display: "block", marginBottom: "6px", fontWeight: "bold", fontSize: "14px" }}>
                    Add an invitee:
                </label>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <input
                        type="text"
                        value={newUsername}
                        onChange={(e) => setNewUsername(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                        placeholder="Enter username"
                        style={{
                            padding: "6px 10px",
                            fontSize: "14px",
                            borderRadius: "4px",
                            border: "1px solid #ccc",
                        }}
                    />
                    <button
                        onClick={handleAdd}
                        disabled={!newUsername.trim()}
                        style={{
                            padding: "6px 14px",
                            backgroundColor: newUsername.trim() ? "#007bff" : "#ccc",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: newUsername.trim() ? "pointer" : "not-allowed",
                        }}
                    >
                        Add
                    </button>
                </div>
            </div>
        </section>
    );
};

export default InviteeManagement;
