/**
 * BaoliGuard API Service Layer
 *
 * Implements client communication interface with FastAPI backend orchestrator (Swastik Parmar).
 * Strict adherence to contracts in /contracts.
 *
 * Phase 1: Establishes typed endpoints and non-blocking mock fallback for development.
 *
 * Owner: Anika Jain (Frontend / PWA / Digital Twin)
 */

import { AnalysisResultContract, AnalysisRequestPayload } from '../types';
import { MOCK_ANALYSIS_FIXTURE } from '../mocks/fixtures';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

export interface HealthResponse {
  status: string;
  project: string;
  version: string;
}

export interface ApiError {
  message: string;
  statusCode?: number;
  details?: unknown;
}

/**
 * Checks backend health status (`GET /health`).
 */
export async function checkBackendHealth(): Promise<HealthResponse> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json'
      }
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown backend connection error';
    throw new Error(`FastAPI Orchestrator connection failed: ${message}`);
  }
}

/**
 * Submits an inspection analysis request (`POST /analyze`).
 *
 * In Phase 1, when backend `/analyze` is under construction,
 * this function securely prepares the multipart payload matching the contract.
 */
export async function submitAnalysisRequest(payload: AnalysisRequestPayload): Promise<AnalysisResultContract> {
  const formData = new FormData();
  
  if (payload.imageFile) {
    formData.append('images', payload.imageFile);
  }
  formData.append('structure_type', payload.structureType);
  if (payload.structureName) {
    formData.append('name', payload.structureName);
  }
  if (payload.region) {
    formData.append('region', payload.region);
  }
  if (payload.notes) {
    formData.append('notes', payload.notes);
  }
  if (payload.roi) {
    formData.append('roi_box', JSON.stringify([payload.roi.x, payload.roi.y, payload.roi.width, payload.roi.height]));
  }

  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      body: formData,
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      // If endpoint is not yet wired in backend during Phase 1, throw descriptive error
      throw new Error(`Analysis submission returned HTTP ${response.status}: ${response.statusText}`);
    }

    const data: AnalysisResultContract = await response.json();
    return data;
  } catch (error: unknown) {
    // Transparently surface API communication requirement
    const msg = error instanceof Error ? error.message : 'Submission failed';
    throw new Error(`Backend Analysis API: ${msg}`);
  }
}

/**
 * Retrieves the explicit development UI mock fixture.
 * MUST be clearly indicated in UI as development fixture.
 */
export async function getDevelopmentMockFixture(): Promise<AnalysisResultContract> {
  // Simulate realistic network roundtrip for UI loading validation
  await new Promise((resolve) => setTimeout(resolve, 600));
  return JSON.parse(JSON.stringify(MOCK_ANALYSIS_FIXTURE));
}
