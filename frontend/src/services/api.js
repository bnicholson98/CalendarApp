import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000/api', // Django backend URL
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
 * @param {number[]} invitees - Optional array of user IDs to invite
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

export default api;
