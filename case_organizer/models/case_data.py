"""Standard case data model for case-organizer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PatientProfile(BaseModel):
    name: str | None = None
    age: int | None = None
    sex: str | None = None
    phone: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    medical_record_no: str | None = None


class Diagnosis(BaseModel):
    primary_diagnosis: str | None = None
    stage: str | None = None
    initial_diagnosis_date: str | None = None
    current_phase: str | None = None
    surgery_summary: str | None = None


class PathologyReport(BaseModel):
    report_date: str | None = None
    diagnosis: str | None = None
    grade: str | None = None
    stage: str | None = None
    margin_status: str | None = None
    neural_invasion: str | None = None
    vascular_invasion: str | None = None
    lymph_node_status: str | None = None
    immunohistochemistry: dict[str, str] = Field(default_factory=dict)


class GenomicsReport(BaseModel):
    report_date: str | None = None
    institution: str | None = None
    summary: str | None = None
    variants: list[str] = Field(default_factory=list)
    mss_status: str | None = None
    tmb: str | None = None
    pd_l1: str | None = None
    source_file: str | None = None


class LabResult(BaseModel):
    test_date: str | None = None
    test_name: str | None = None
    value: str | None = None
    unit: str | None = None
    reference_low: str | None = None
    reference_high: str | None = None
    status: str | None = None
    source_file: str | None = None


class TumorMarker(BaseModel):
    test_date: str | None = None
    indicator_name: str | None = None
    indicator_value: float | None = None
    unit: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    source_file: str | None = None
    source_page: int | None = None
    confidence: float | None = None


class TreatmentPhase(BaseModel):
    phase_id: str
    regimen_name: str
    start_date: str | None = None
    end_date: str | None = None
    intent: str | None = None
    cycles: str | None = None
    drugs: list[str] = Field(default_factory=list)
    response_summary: str | None = None
    adverse_events: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)


class ImagingStudy(BaseModel):
    date: str | None = None
    modality: str | None = None
    body_part: str | None = None
    hospital: str | None = None
    findings: str | None = None
    impression: str | None = None
    comparison: str | None = None
    source_file: str | None = None


class ClinicalEvent(BaseModel):
    event_date: str | None = None
    event_type: str | None = None
    title: str | None = None
    description: str | None = None
    doctor_note: str | None = None
    patient_note: str | None = None
    next_step: str | None = None
    related_sources: list[str] = Field(default_factory=list)


class CurrentStatus(BaseModel):
    physical_state: str | None = None
    appetite: str | None = None
    sleep: str | None = None
    weight_change: str | None = None
    bowel_urine: str | None = None
    adverse_events: list[str] = Field(default_factory=list)
    main_concerns: list[str] = Field(default_factory=list)


class ConsultQuestion(BaseModel):
    question: str
    priority: str | None = None
    context: str | None = None


class StandardCase(BaseModel):
    patient_profile: PatientProfile = Field(default_factory=PatientProfile)
    diagnosis: Diagnosis = Field(default_factory=Diagnosis)
    pathology: PathologyReport = Field(default_factory=PathologyReport)
    genomics: list[GenomicsReport] = Field(default_factory=list)
    lab_results: list[LabResult] = Field(default_factory=list)
    tumor_markers: list[TumorMarker] = Field(default_factory=list)
    treatments: list[TreatmentPhase] = Field(default_factory=list)
    imaging_studies: list[ImagingStudy] = Field(default_factory=list)
    clinical_events: list[ClinicalEvent] = Field(default_factory=list)
    current_status: CurrentStatus = Field(default_factory=CurrentStatus)
    consult_questions: list[ConsultQuestion] = Field(default_factory=list)
    source_documents: list[dict[str, str]] = Field(default_factory=list)

