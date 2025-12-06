/**
 * API Configuration
 * 
 * Centralized configuration for backend API endpoints
 * Can be overridden via environment variables
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

export const API_ENDPOINTS = {
  BASE_URL: API_BASE_URL,
  
  // Simulation endpoints
  RUN_SIMULATION: `${API_BASE_URL}/run-simulation`,
  STATUS: `${API_BASE_URL}/status`,
  RESULTS: `${API_BASE_URL}/results`,
  
  // Miner endpoints
  MINER_SUBMIT: `${API_BASE_URL}/miner-submit`,
  GET_APPLICANTS: `${API_BASE_URL}/get-applicants`,
  
  // Selection endpoints
  SELECT_PARTICIPANTS: `${API_BASE_URL}/select-participants`,
  START_POS: `${API_BASE_URL}/start-pos`,
  
  // Debug
  DEBUG: `${API_BASE_URL}/debug`,
};

/**
 * Helper function to make API calls with error handling
 */
export const apiCall = async (endpoint, options = {}) => {
  try {
    const response = await fetch(endpoint, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API call failed: ${endpoint}`, error);
    throw error;
  }
};

export default API_ENDPOINTS;

