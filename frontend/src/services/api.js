import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000/api', // Django backend URL
    headers: {
        'Content-Type': 'application/json',
    },
});

/**
 * Helper to get authorization headers with the stored token.
 */
const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return token ? { Authorization: `Token ${token}` } : {};
};

/**
 * Fetch all events for the authenticated user (owned or invited to).
 */
export const fetchUserEvents = async () => {
    const response = await api.get("/events/", {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Fetch all invites received by the authenticated user.
 */
export const fetchReceivedInvites = async () => {
    const response = await api.get("/invites/", {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Create a new event with proposed dates and optional invitees.
 * @param {string} eventName - The name of the event
 * @param {string[]} proposedDates - Array of dates in 'YYYY-MM-DD' format
 * @param {string[]} invitees - Optional array of usernames to invite
 */
export const createEvent = async (eventName, proposedDates, invitees = []) => {
    const response = await api.post("/events/create/", {
        event_name: eventName,
        proposed_dates: proposedDates,
        invitees: invitees,
    }, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Fetch a single event by ID (includes proposed_dates with vote_summary).
 * @param {number} eventId - The event ID
 */
export const fetchEvent = async (eventId) => {
    const response = await api.get(`/events/${eventId}/`, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Add a proposed date to an event.
 * @param {number} eventId - The event ID
 * @param {string} date - Date in 'YYYY-MM-DD' format
 */
export const addProposedDate = async (eventId, date) => {
    const response = await api.post(`/events/${eventId}/dates/add/`, {
        date: date,
    }, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Remove a proposed date from an event.
 * @param {number} eventId - The event ID
 * @param {number} dateId - The proposed date ID
 */
export const removeProposedDate = async (eventId, dateId) => {
    await api.delete(`/events/${eventId}/dates/${dateId}/delete/`, {
        headers: getAuthHeaders(),
    });
};

/**
 * Confirm an event with a specific proposed date.
 * @param {number} eventId - The event ID
 * @param {number} proposedDateId - The proposed date ID to confirm
 */
export const confirmEvent = async (eventId, proposedDateId) => {
    const response = await api.post(`/events/${eventId}/confirm/`, {
        proposed_date_id: proposedDateId,
    }, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Cancel an event.
 * @param {number} eventId - The event ID
 */
export const cancelEvent = async (eventId) => {
    const response = await api.post(`/events/${eventId}/cancel/`, {}, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Fetch the current user's votes for an event.
 * @param {number} eventId - The event ID
 * @returns {Promise<Array>} Array of DateVote objects keyed by proposed_date id
 */
export const fetchMyVotes = async (eventId) => {
    const response = await api.get(`/votes/events/${eventId}/mine/`, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Post or update the current user's vote on a proposed date.
 * @param {number} eventId - The event ID
 * @param {number} dateId - The proposed date ID
 * @param {string} availability - One of AVAILABLE, MAYBE, NOT_AVAILABLE
 */
export const voteOnDate = async (eventId, dateId, availability) => {
    const response = await api.post(`/votes/events/${eventId}/dates/${dateId}/`, {
        availability: availability,
    }, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Delete the current user's vote on a proposed date.
 * @param {number} eventId - The event ID
 * @param {number} dateId - The proposed date ID
 */
export const deleteVote = async (eventId, dateId) => {
    await api.delete(`/votes/events/${eventId}/dates/${dateId}/delete/`, {
        headers: getAuthHeaders(),
    });
};

export default api;
