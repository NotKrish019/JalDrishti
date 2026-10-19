/**
 * JalDrishti API client.
 *
 * Talks to the FastAPI backend owned by Swastik Parmar. Request and response
 * shapes follow /contracts. Cloudinary credentials never reach the browser:
 * images are stored through the backend `POST /images/upload` endpoint.
 *
 * Owner: Anika Jain (Frontend)
 */

import {
  AnalysisRequestPayload,
  AnalysisResultContract,
  ImageUploadResult,
  KnowledgeSource,
  MaterialCompatibilityContract,
  StructureKnowledgeRecord,
  StructureTypology,
} from '../types';
import { MOCK_ANALYSIS_FIXTURE } from '../mocks/fixtures';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

/** Mirrors the backend default MAX_UPLOAD_SIZE_BYTES (10 MB). */
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export interface HealthResponse {
  status: string;
  project: string;
  version: string;
}

/** Error carrying the HTTP status and the backend's own explanation. */
export class ApiError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
  }
}

/** Turn a FastAPI error body (`detail` string or validation list) into readable text. */
const describeFailure = (status: number, body: unknown): string => {
  let detail = '';
  if (body && typeof body === 'object' && 'detail' in body) {
    const raw = (body as { detail: unknown }).detail;
    if (typeof raw === 'string') {
      detail = raw;
    } else if (Array.isArray(raw)) {
      detail = raw
        .map((item) => {
          if (item && typeof item === 'object' && 'msg' in item) {
            const loc = 'loc' in item && Array.isArray(item.loc) ? `${item.loc.join('.')}: ` : '';
            return `${loc}${String(item.msg)}`;
          }
          return String(item);
        })
        .join('; ');
    }
  }

  const fallback: Record<number, string> = {
    400: 'The server rejected the request.',
    404: 'The requested resource was not found.',
    413: 'The image exceeds the server upload limit.',
    422: 'The request did not match the expected format.',
    500: 'The server hit an internal error.',
    502: 'The image storage provider did not accept the upload.',
    503: 'The service is not available right now.',
  };

  return detail || fallback[status] || `Request failed with HTTP ${status}.`;
};

const parseJson = (text: string): unknown => {
  try {
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
};

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 60000): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { Accept: 'application/json', ...(init.headers ?? {}) },
    });
  } catch (error: unknown) {
    const aborted = error instanceof DOMException && error.name === 'AbortError';
    throw new ApiError(
      aborted
        ? 'The JalDrishti API did not respond in time.'
        : 'Could not reach the JalDrishti API. Check that the backend is running.',
    );
  } finally {
    clearTimeout(timeoutId);
  }

  const body = parseJson(await response.text());
  if (!response.ok) {
    throw new ApiError(describeFailure(response.status, body), response.status);
  }
  return body as T;
}

/** `GET /health` */
export function checkBackendHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health', {}, 4000);
}

export interface UploadMetadata {
  structureType?: StructureTypology;
  structureName?: string;
  notes?: string;
  inspectionId?: string;
}

/**
 * `POST /images/upload` — stores the image in Cloudinary through the backend.
 * Uses XMLHttpRequest so the caller receives real byte-level upload progress.
 * Storing an image does not analyse it.
 */
export function uploadInspectionImage(
  file: File,
  meta: UploadMetadata,
  onProgress?: (fraction: number) => void,
): Promise<ImageUploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (meta.structureType) formData.append('structure_type', meta.structureType);
  if (meta.structureName) formData.append('structure_name', meta.structureName);
  if (meta.notes) formData.append('notes', meta.notes);
  if (meta.inspectionId) formData.append('inspection_id', meta.inspectionId);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/images/upload`);
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.timeout = 120000;

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(event.loaded / event.total);
      }
    };

    xhr.onload = () => {
      const body = parseJson(xhr.responseText);
      if (xhr.status >= 200 && xhr.status < 300 && body) {
        resolve(body as ImageUploadResult);
      } else {
        reject(new ApiError(describeFailure(xhr.status, body), xhr.status));
      }
    };
    xhr.onerror = () =>
      reject(new ApiError('Could not reach the JalDrishti API. Check that the backend is running.'));
    xhr.ontimeout = () => reject(new ApiError('The image upload timed out.'));

    xhr.send(formData);
  });
}

/** `DELETE /images/{image_id}` — removes the Cloudinary asset and its metadata record. */
export function deleteInspectionImage(imageId: string): Promise<{ status: string; detail: string }> {
  return request(`/images/${encodeURIComponent(imageId)}`, { method: 'DELETE' });
}

/**
 * `POST /analyze` — runs the vision → engineering → material → restoration pipeline.
 *
 * `roi_box` is only sent when the user explicitly drew a region. It is sent in
 * image pixels [x, y, width, height], which is what the backend expects.
 */
export function submitAnalysisRequest(payload: AnalysisRequestPayload): Promise<AnalysisResultContract> {
  const formData = new FormData();

  if (payload.imageFile) formData.append('images', payload.imageFile);
  if (payload.imageId) formData.append('image_id', payload.imageId);
  formData.append('structure_type', payload.structureType);
  if (payload.structureName) formData.append('name', payload.structureName);
  if (payload.region) formData.append('region', payload.region);
  if (payload.notes) formData.append('notes', payload.notes);
  if (payload.roi && !payload.roi.isNormalized) {
    const { x, y, width, height } = payload.roi;
    formData.append('roi_box', JSON.stringify([x, y, width, height].map((v) => Math.round(v))));
  }

  return request<AnalysisResultContract>('/analyze', { method: 'POST', body: formData }, 120000);
}

/** `GET /knowledge/structures` */
export function fetchStructures(): Promise<StructureKnowledgeRecord[]> {
  return request<StructureKnowledgeRecord[]>('/knowledge/structures', {}, 10000);
}

/** `GET /knowledge/structures/{id}` */
export function fetchStructure(id: string): Promise<StructureKnowledgeRecord> {
  return request<StructureKnowledgeRecord>(`/knowledge/structures/${encodeURIComponent(id)}`, {}, 10000);
}

/** `GET /knowledge/sources` */
export function fetchSources(): Promise<KnowledgeSource[]> {
  return request<KnowledgeSource[]>('/knowledge/sources', {}, 10000);
}

/** `POST /material-compatibility` — rule-based evaluation, not a laboratory result. */
export function evaluateMaterialCompatibility(
  originalMaterial: string,
  candidateMaterials?: string[],
): Promise<MaterialCompatibilityContract> {
  return request<MaterialCompatibilityContract>(
    '/material-compatibility',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        original_material: originalMaterial,
        ...(candidateMaterials ? { candidate_materials: candidateMaterials } : {}),
      }),
    },
    15000,
  );
}

/**
 * Local development fixture. Must always be presented as a sample, never as
 * an inspection result. Loaded only on explicit user action.
 */
export async function getDevelopmentMockFixture(): Promise<AnalysisResultContract> {
  return JSON.parse(JSON.stringify(MOCK_ANALYSIS_FIXTURE));
}
