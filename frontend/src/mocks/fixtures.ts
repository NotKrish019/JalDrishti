/**
 * ====================================================================
 *                 MOCK FIXTURE — LOCAL DEVELOPMENT ONLY
 * ====================================================================
 * 
 * DISCLAIMER & POLICY COMPLIANCE:
 * This fixture is strictly intended for frontend interface scaffolding,
 * layout validation, and UI component development during Phase 1.
 * 
 * UNDER NO CIRCUMSTANCES should this fixture be presented as certified,
 * live AI model output or verified archaeological findings.
 * 
 * Contract Schema: /contracts/analysis.schema.json
 * ====================================================================
 */

import { AnalysisResultContract } from '../types';

export const IS_MOCK_FIXTURE = true;
export const MOCK_FIXTURE_LABEL = "Development UI Fixture (Non-Invasive Prototype Sample)";

export const MOCK_ANALYSIS_FIXTURE: AnalysisResultContract = {
  project_version: "0.1.0",
  structure: {
    type: "baoli",
    name: "Sample Subterranean Stepwell (Architectural Study)",
    region: "Rajasthan / Shekhawati Region",
    source_images: [
      "/samples/stepwell_ashlar_wall.svg"
    ]
  },
  vision: {
    structure_type: "baoli",
    image_dimensions: {
      width_pixels: 1920,
      height_pixels: 1080
    },
    scale_reference: {
      calibrated: false,
      pixels_per_millimeter: 0,
      method: "uncalibrated_pixel_space"
    },
    detections: [
      {
        class_name: "crack",
        confidence: 0.88,
        bounding_box: [420, 280, 890, 620],
        pixel_area: 12450,
        coverage_ratio: 0.006,
        component_count: 3,
        total_length_pixels: 640,
        largest_component_length_pixels: 380,
        relative_severity: "moderate"
      },
      {
        class_name: "vegetation_root_intrusion",
        confidence: 0.92,
        bounding_box: [150, 110, 480, 490],
        pixel_area: 28900,
        coverage_ratio: 0.014,
        component_count: 5,
        total_length_pixels: 420,
        largest_component_length_pixels: 210,
        relative_severity: "severe"
      },
      {
        class_name: "spalling",
        confidence: 0.79,
        bounding_box: [980, 520, 1420, 860],
        pixel_area: 18200,
        coverage_ratio: 0.009,
        component_count: 2,
        relative_severity: "moderate"
      }
    ],
    processing_metadata: {
      inference_latency_ms: 142.5,
      model_version: "development-fixture (no model run)"
    }
  },
  visual_condition: {
    value: 68.5,
    scale_min: 0,
    scale_max: 100,
    method: "deterministic_area_severity_weighted_formula_v1",
    confidence: 0.85,
    limitations: [
      "Based strictly on photographic 2D visible surface pixels",
      "Internal masonry voiding and foundation settlement cannot be detected from single-angle photography",
      "Requires physical on-site conservation engineering audit"
    ]
  },
  visual_crack_burden: {
    value: 42.0,
    scale_min: 0,
    scale_max: 100,
    method: "skeletonized_length_density_ratio_v1",
    confidence: 0.88,
    limitations: [
      "Image-space skeletonized pixel centerline length relative to segmented masonry area",
      "Micro-fractures smaller than optical camera resolution (sub-pixel) are not registered"
    ]
  },
  sub_scores: {
    vegetation_intrusion_index: {
      value: 65.0,
      scale_min: 0,
      scale_max: 100,
      method: "root_canopy_joint_penetration_index_v1",
      confidence: 0.92,
      limitations: ["Calculated from visible vegetation foliage and root bounding extent"]
    },
    masonry_integrity_index: {
      value: 71.0,
      scale_min: 0,
      scale_max: 100,
      method: "ashlar_bedding_spalling_cohesion_v1",
      confidence: 0.84,
      limitations: ["Evaluates surface loss without core ultrasonic velocity testing"]
    },
    siltation_obstruction_index: {
      value: 48.0,
      scale_min: 0,
      scale_max: 100,
      method: "catchment_aperture_sediment_ratio_v1",
      confidence: 0.76,
      limitations: ["Depth of bottom silt layer estimated from lower step submersion"]
    },
    visual_crack_burden: {
      value: 42.0,
      scale_min: 0,
      scale_max: 100,
      method: "skeletonized_length_density_ratio_v1",
      confidence: 0.88,
      limitations: ["Centerline pixels per square meter of surveyed surface"]
    }
  },
  water_functionality: {
    value: 54.0,
    scale_min: 0,
    scale_max: 100,
    method: "hydrological_catchment_aquifer_continuity_rule_v1",
    confidence: 0.78,
    limitations: [
      "Inlet siltation estimated from visual basin sediment coverage",
      "Aquifer recharge rate requires piezometric hydrological measurements"
    ]
  },
  restoration_priority_score: {
    value: 78.5,
    scale_min: 0,
    scale_max: 100,
    method: "deterministic_synthesis_priority_index_v1",
    confidence: 0.82,
    limitations: [
      "Synthesizes structural urgency against aquifer revival potential",
      "Prioritizes dry-season masonry stabilization over wet-season intervention"
    ]
  },
  material: {
    original_material: "sandstone_dholpur_with_hydraulic_lime_mortar",
    original_material_confidence: 0.82,
    verification_required: true,
    recommended_tests: [
      "X-ray diffraction (XRD) of mortar binder matrix",
      "Acid-insoluble residue determination for aggregate grading",
      "Phenolphthalein carbonation depth testing on exposed core sample"
    ],
    candidate_interventions: [
      {
        intervention_material: "slaked_lime_putty_with_surkhi_pozzolana",
        compatibility_score: 92.5,
        compatibility_dimensions: {
          mechanical: 9.2,
          moisture: 9.5,
          thermal: 8.8,
          chemical: 9.4,
          reversibility: 9.0,
          heritage: 9.6,
          visual: 9.2
        },
        recommendation: "strongly_recommended",
        warnings: [
          "Ensure aged fat lime putty (>90 days slaking) is utilized to avoid unsound lime popping"
        ]
      },
      {
        intervention_material: "ordinary_portland_cement_opc_43",
        compatibility_score: 18.0,
        compatibility_dimensions: {
          mechanical: 2.0,
          moisture: 1.2,
          thermal: 2.5,
          chemical: 1.8,
          reversibility: 1.0,
          heritage: 1.0,
          visual: 3.1
        },
        recommendation: "prohibited_incompatible",
        warnings: [
          "CRITICAL RISK: High modulus of elasticity causes irreversible stone spalling under thermal cycles",
          "Dense non-breathable matrix traps rising dampness and groundwater salts behind masonry face",
          "Soluble sodium and potassium sulfates cause destructive cryptoflorescence"
        ]
      }
    ]
  },
  root_cause: [
    {
      finding: "Vegetation root expansion along primary ashlar masonry bed joints",
      probable_cause: "Mortar loss from historic unmaintained joints followed by windborne seed germination in microclimatic dampness",
      evidence_rules: [
        "Root intrusion connected to visible bedding joint line",
        "Displaced sandstone facing stones localized to root clusters"
      ],
      urgency: "critical"
    },
    {
      finding: "Efflorescence and sub-surface salt spalling at lower basin tier",
      probable_cause: "Intermittent ground moisture rising through capillary action without evaporation relief due to debris accumulation",
      evidence_rules: [
        "Defects concentrated within 1.5m above current sediment line"
      ],
      urgency: "high"
    }
  ],
  restoration: {
    restoration_strategy: "hydrological_revival",
    prioritized_actions: [
      {
        step: 1,
        phase: "phase_1_immediate_stabilization",
        action_title: "Non-Destructive Vegetation Extraction & Biocidal Poulticing",
        target_defect: "vegetation_root_intrusion",
        recommended_technique: "Selective stem cutting followed by biodegradable ammonium salt biocidal application without mechanical leverage against historic masonry",
        material_specification: "pH-neutral heritage-safe biocide, mechanical hand extraction",
        urgency: "immediate",
        preconditions: [
          "Temporary shoring of loose ashlar blocks prior to deep root extraction"
        ]
      },
      {
        step: 2,
        phase: "phase_2_hydrological_remediation",
        action_title: "Silt De-sedimentation and Drainage Gradient Clearance",
        target_defect: "siltation_obstruction",
        recommended_technique: "Manual dredging of bottom catchment basin down to historic paved tier without mechanical excavators",
        material_specification: "Manual vacuum/silt removal tools",
        urgency: "high"
      },
      {
        step: 3,
        phase: "phase_3_masonry_and_iks_consolidation",
        action_title: "Traditional Hydraulic Lime & Surkhi Deep Joint Repointing",
        target_defect: "crack_and_joint_failure",
        recommended_technique: "Raking out compromised modern/degraded mortar to 25mm depth followed by pressurized gravity-fed traditional lime grout",
        material_specification: "1:2 Slaked Lime Putty to graded washed Surkhi (brick dust) with organic jaggery extract (0.5% weight)",
        urgency: "medium",
        preconditions: [
          "Pre-wetting of stone joints with demineralized water for 24 hours"
        ]
      },
      {
        step: 4,
        phase: "phase_4_long_term_monitoring",
        action_title: "Seasonal Piezometric and Photographic Baseline Tracking",
        target_defect: "general_conservation",
        recommended_technique: "Quarterly photographic survey and crack gauge measurement following monsoon inundation cycle",
        material_specification: "Calibrated tell-tale acrylic crack gauges",
        urgency: "routine"
      }
    ],
    incompatible_practices: [
      {
        prohibited_action: "OPC Portland Cement pointing or gunite plastering over stone surfaces",
        failure_mechanism: "Irreversible entrapment of salt solutions, accelerated edge spalling of soft sandstone",
        severity: "destructive"
      },
      {
        prohibited_action: "High-pressure abrasive sandblasting for surface lichen removal",
        failure_mechanism: "Erosion of protective original stone patina and relief carving details",
        severity: "destructive"
      }
    ],
    iks_guidelines: {
      traditional_mortar_recipe: "Traditional Chuna-Surkhi blend: 1 part slaked fat lime putty (calcium oxide thoroughly slaked and matured), 2 parts pulverized well-burnt clay brick dust (surkhi) passing 1.18mm sieve, enriched with fermented methi (fenugreek) water and gur (unrefined sugarcane jaggery) for enhanced workability and biological resistance.",
      craftsmanship_references: [
        "Aparajitaprccha of Bhuvanadeva (12th Century CE) — Principles of Jaladurga and Vapi Construction",
        "Mayamatam Treatise on Traditional Indian Architecture (Chapters on stone jointing & hydraulic lime plaster)"
      ],
      seasonal_curing_rules: "Must be wet-cured under damp jute burlap sacking continuously for minimum 21 days during mild temperatures; avoid execution during hot dry pre-monsoon winds."
    }
  },
  metadata: {
    created_at: "2026-10-08T12:00:00Z",
    pipeline_status: "completed",
    orchestrated_by: "development fixture — not produced by the pipeline"
  }
};
