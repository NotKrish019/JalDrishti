/**
 * BaoliGuard Frontend Type Definitions
 *
 * Strictly aligned with backend shared JSON contracts in /contracts:
 * - contracts/analysis.schema.json
 * - contracts/vision_result.schema.json
 * - contracts/engineering_result.schema.json
 * - contracts/material_compatibility.schema.json
 * - contracts/restoration_result.schema.json
 *
 * Owned by: Anika Jain (Frontend / PWA / Digital Twin)
 */

export type StructureTypology = 'baoli' | 'bawari' | 'kund' | 'vav' | 'tank' | 'other';

export interface StructureContext {
  type: StructureTypology;
  name?: string;
  region?: string;
  source_images: string[];
}

export interface ImageDimensions {
  width_pixels: number;
  height_pixels: number;
}

export interface ScaleReference {
  calibrated?: boolean;
  pixels_per_millimeter?: number;
  method?: string;
}

export type DefectSeverity = 'low' | 'moderate' | 'severe';

export interface DetectionItem {
  class_name: string;
  confidence: number;
  bounding_box: [number, number, number, number]; // [x_min, y_min, x_max, y_max]
  segmentation_mask_reference?: string;
  pixel_area: number;
  coverage_ratio: number;
  component_count: number;
  total_length_pixels?: number;
  largest_component_length_pixels?: number;
  relative_severity?: DefectSeverity;
  burden_score?: number;
}

export interface VisionResultContract {
  structure_type: 'baoli' | 'bawari' | 'kund' | 'vav' | 'tank' | 'unknown';
  image_dimensions: ImageDimensions;
  scale_reference?: ScaleReference;
  detections: DetectionItem[];
  processing_metadata?: {
    inference_latency_ms?: number;
    model_version?: string;
  };
}

export interface MetricScore {
  value: number;
  scale_min: number;
  scale_max: number;
  method: string;
  confidence: number;
  limitations: string[];
}

export interface EngineeringSubScores {
  vegetation_intrusion_index?: MetricScore;
  masonry_integrity_index?: MetricScore;
  siltation_obstruction_index?: MetricScore;
  visual_crack_burden?: MetricScore;
}

export type RootCauseUrgency = 'low' | 'medium' | 'high' | 'critical';

export interface RootCauseItem {
  finding: string;
  probable_cause: string;
  evidence_rules: string[];
  urgency?: RootCauseUrgency;
}

export interface EngineeringResultContract {
  visual_condition_score: MetricScore;
  water_functionality_score: MetricScore;
  restoration_priority_score: MetricScore;
  sub_scores?: EngineeringSubScores;
  root_cause_analysis?: RootCauseItem[];
  engineering_disclaimer: string;
}

export interface CompatibilityDimensions {
  mechanical: number; // 0-10
  moisture: number; // 0-10
  thermal: number; // 0-10
  chemical: number; // 0-10
  reversibility: number; // 0-10
  heritage: number; // 0-10
  visual: number; // 0-10
}

export type RecommendationLevel = 
  | 'strongly_recommended'
  | 'recommended'
  | 'acceptable_conditional'
  | 'prohibited_incompatible';

export interface CandidateIntervention {
  intervention_material: string;
  compatibility_score: number;
  compatibility_dimensions: CompatibilityDimensions;
  recommendation: RecommendationLevel;
  warnings: string[];
}

export interface MaterialCompatibilityContract {
  original_material: string;
  original_material_confidence: number;
  verification_required: boolean;
  recommended_tests?: string[];
  candidate_interventions: CandidateIntervention[];
}

export type RestorationPhase = 
  | 'phase_1_immediate_stabilization'
  | 'phase_2_hydrological_remediation'
  | 'phase_3_masonry_and_iks_consolidation'
  | 'phase_4_long_term_monitoring';

export type ActionUrgency = 'immediate' | 'high' | 'medium' | 'routine';

export interface PrioritizedAction {
  step: number;
  phase: RestorationPhase;
  action_title: string;
  target_defect: string;
  recommended_technique: string;
  material_specification: string;
  urgency: ActionUrgency;
  preconditions?: string[];
}

export type IncompatibleSeverity = 'destructive' | 'high_risk' | 'moderate_risk';

export interface IncompatiblePractice {
  prohibited_action: string;
  failure_mechanism: string;
  severity: IncompatibleSeverity;
}

export interface IKSGuidelines {
  traditional_mortar_recipe: string;
  craftsmanship_references: string[];
  seasonal_curing_rules: string;
}

export type RestorationStrategy = 
  | 'minimal_stabilization'
  | 'material_consolidation'
  | 'hydrological_revival'
  | 'comprehensive_heritage_rehabilitation';

export interface RestorationResultContract {
  restoration_strategy: RestorationStrategy;
  prioritized_actions: PrioritizedAction[];
  incompatible_practices: IncompatiblePractice[];
  iks_guidelines: IKSGuidelines;
}

/** Shape returned by the live `/analyze` endpoint for `root_cause`. */
export interface RootCauseSummary {
  findings: RootCauseItem[];
  primary_cause?: string;
  count?: number;
}

export interface PipelineMetadata {
  created_at: string;
  pipeline_status: 'completed' | 'partial' | 'failed';
  orchestrated_by?: string;
}

/**
 * Unified contract representing contracts/analysis.schema.json
 */
export interface AnalysisResultContract {
  project_version: string;
  structure: StructureContext;
  vision: VisionResultContract;
  visual_condition: MetricScore | { score: MetricScore } | Record<string, unknown>;
  visual_crack_burden?: MetricScore;
  water_functionality: MetricScore | { score: MetricScore } | Record<string, unknown>;
  restoration_priority_score?: MetricScore;
  sub_scores?: EngineeringSubScores;
  material: MaterialCompatibilityContract;
  root_cause: RootCauseSummary | RootCauseItem[] | Record<string, unknown>;
  restoration: RestorationResultContract;
  metadata: PipelineMetadata;
}

/**
 * Frontend Navigation & Application State Types
 */
export type AppRoute = '/' | '/upload' | '/analysis' | '/knowledge' | '/report';

/**
 * Mirrors contracts/image_upload_result.schema.json (POST /images/upload).
 * Cloudinary storage only; an uploaded image has not been analysed.
 */
export interface ImageUploadResult {
  image_id: string;
  inspection_id?: string | null;
  status: 'uploaded' | 'processing' | 'ready' | 'failed' | string;
  preview_url: string;
  original_url?: string | null;
  format: string;
  width: number;
  height: number;
  bytes: number;
  created_at: string;
}

/**
 * Where an analysis result came from. 'fixture' is the local development
 * sample and must never be presented as a real inspection.
 */
export type ResultProvenance = 'live' | 'fixture';

export interface InspectionSession {
  result: AnalysisResultContract;
  provenance: ResultProvenance;
  /** Present only when the image was stored through the backend Cloudinary workflow. */
  image?: ImageUploadResult;
  /** Local object URL of the inspected file, used for overlays when no stored preview exists. */
  localPreviewUrl?: string;
}

/**
 * Region of Interest (ROI) coordinates for focused defect inspection
 */
export interface InspectionROI {
  x: number; // percentage (0-100) or pixel coordinate
  y: number;
  width: number;
  height: number;
  isNormalized?: boolean;
}

export interface AnalysisRequestPayload {
  imageFile?: File;
  /** Backend image id from POST /images/upload, when the image was stored. */
  imageId?: string;
  imagePreviewUrl?: string;
  structureType: StructureTypology;
  structureName?: string;
  region?: string;
  notes?: string;
  roi?: InspectionROI;
}

/**
 * Knowledge base records served by GET /knowledge/structures (knowledge/structures/*.json).
 */
export interface EngineeringPrincipleRecord {
  principle: string;
  what?: string;
  why?: string;
  how?: string;
  engineering_significance?: string;
}

export interface WaterManagementPrincipleRecord {
  principle: string;
  description?: string;
  hydrological_mechanism?: string;
}

export interface TraditionalMaterialRecord {
  material_family: string;
  usage?: string;
  traditional_role?: string;
}

export interface StructureKnowledgeRecord {
  id: string;
  name: string;
  alternate_names?: string[];
  regions?: string[];
  traditional_function?: string[];
  engineering_principles?: EngineeringPrincipleRecord[];
  water_management_principles?: WaterManagementPrincipleRecord[];
  environmental_adaptations?: string[];
  traditional_materials?: TraditionalMaterialRecord[];
  construction_features?: string[];
  common_deterioration_factors?: string[];
  conservation_considerations?: string[];
  sources?: string[];
  limitations?: string[];
}

/** GET /knowledge/sources (knowledge/sources/sources_index.json). */
export interface KnowledgeSource {
  source_id: string;
  title: string;
  publisher?: string;
  year?: number;
  url?: string;
  topic?: string;
  claim_supported?: string;
  claims_supported?: string[];
}
