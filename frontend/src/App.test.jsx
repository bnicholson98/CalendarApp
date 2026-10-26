import { render, screen } from '@testing-library/react';
import { vi, test, expect, beforeEach } from 'vitest';
import App from './App';
import { fetchUserEvents, fetchReceivedInvites, fetchMyVotes } from './services/api';

vi.mock('./services/api', () => ({
	default: { post: vi.fn() },
	fetchUserEvents: vi.fn(),
	fetchReceivedInvites: vi.fn(),
	fetchMyVotes: vi.fn(),
}));

beforeEach(() => {
	fetchUserEvents.mockResolvedValue([]);
	fetchReceivedInvites.mockResolvedValue([]);
	fetchMyVotes.mockResolvedValue([]);
	localStorage.clear();
	window.history.pushState({}, '', '/');
});

test('redirects unauthenticated users to the login page', () => {
	render(<App />);
	expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument();
});

test('redirects unauthenticated users away from protected routes', () => {
	window.history.pushState({}, '', '/create-event');
	render(<App />);
	expect(window.location.pathname).toBe('/login');
});

test('sends users with a stored token from login to home', async () => {
	localStorage.setItem('token', 'abc123');
	localStorage.setItem('userName', 'alice');
	window.history.pushState({}, '', '/login');
	render(<App />);
	expect(window.location.pathname).toBe('/home');
	expect(await screen.findByRole('button', { name: /logout/i })).toBeInTheDocument();
});
