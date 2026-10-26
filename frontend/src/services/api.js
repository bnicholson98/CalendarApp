import axios from 'axios';

const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api',
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
 * A 401 on an authenticated request means the stored token is no longer valid
 * Clear the session and send the user back to login.
 */
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && error.config?.headers?.Authorization) {
            localStorage.removeItem("token");
            localStorage.removeItem("userId");
            localStorage.removeItem("userName");
            window.location.assign("/login");
        }
        return Promise.reject(error);
    }
);

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

/**
 * Fetch all invites for a specific event (owner only).
 * @param {number} eventId - The event ID
 */
export const fetchEventInvites = async (eventId) => {
    const response = await api.get(`/invites/events/${eventId}/`, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Create an invite for an event by username.
 * @param {number} eventId - The event ID
 * @param {string} username - Username of the user to invite
 */
export const createEventInvite = async (eventId, username) => {
    const response = await api.post("/invites/create/", {
        event: eventId,
        username: username,
    }, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

/**
 * Delete an invite by ID.
 * @param {number} inviteId - The invite ID
 */
export const deleteEventInvite = async (inviteId) => {
    await api.delete(`/invites/${inviteId}/delete/`, {
        headers: getAuthHeaders(),
    });
};

/**
 * Fetch all votes for an event (per-date breakdown with per-user detail).
 * @param {number} eventId - The event ID
 */
export const fetchEventVotes = async (eventId) => {
    const response = await api.get(`/votes/events/${eventId}/`, {
        headers: getAuthHeaders(),
    });
    return response.data;
};

export default api;
