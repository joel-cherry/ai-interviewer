from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.candidate_profile import CandidateProfileCreate, CandidateProfileRead, CandidateProfileUpdate
from app.schemas.job_description import JobDescriptionMatchResult, JobDescriptionRead
from app.schemas.resume_document import ResumeDocumentRead
from app.services.candidate_profile_service import CandidateProfileService
from app.services.job_description_service import JobDescriptionService
from app.services.resume_document_service import ResumeDocumentService

router = APIRouter(prefix="/candidate-profiles", tags=["candidate-profiles"])


@router.post("", response_model=CandidateProfileRead, status_code=status.HTTP_201_CREATED)
async def create_candidate_profile(
    payload: CandidateProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileRead:
    service = CandidateProfileService(db)
    candidate = await service.create(payload)
    return CandidateProfileRead.model_validate(candidate)


@router.get("", response_model=list[CandidateProfileRead])
async def list_candidate_profiles(
    db: AsyncSession = Depends(get_db),
    user_id: UUID | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[CandidateProfileRead]:
    service = CandidateProfileService(db)
    if user_id is not None:
        candidates = await service.get_by_user_id(user_id)
    else:
        candidates = await service.list(offset=offset, limit=limit)
    return [CandidateProfileRead.model_validate(candidate) for candidate in candidates]


@router.get("/{candidate_profile_id}", response_model=CandidateProfileRead)
async def get_candidate_profile(candidate_profile_id: UUID, db: AsyncSession = Depends(get_db)) -> CandidateProfileRead:
    service = CandidateProfileService(db)
    candidate = await service.get_by_id(candidate_profile_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")
    return CandidateProfileRead.model_validate(candidate)


@router.put("/{candidate_profile_id}", response_model=CandidateProfileRead)
async def update_candidate_profile(
    candidate_profile_id: UUID,
    payload: CandidateProfileUpdate,
    db: AsyncSession = Depends(get_db),
) -> CandidateProfileRead:
    service = CandidateProfileService(db)
    candidate = await service.update(candidate_profile_id, payload)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")
    return CandidateProfileRead.model_validate(candidate)


@router.delete("/{candidate_profile_id}", status_code=status.HTTP_200_OK)
async def delete_candidate_profile(candidate_profile_id: UUID, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    service = CandidateProfileService(db)
    deleted = await service.delete(candidate_profile_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")
    return {"detail": "Candidate profile deleted successfully"}


@router.post("/{candidate_profile_id}/resumes", response_model=ResumeDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_candidate_resume(
    candidate_profile_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ResumeDocumentRead:
    service = CandidateProfileService(db)
    candidate = await service.get_by_id(candidate_profile_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")

    raw_bytes = await file.read()
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume file is empty")

    resume_service = ResumeDocumentService(db)
    resume = await resume_service.create_for_candidate(
        candidate_profile_id=candidate_profile_id,
        file_name=file.filename or "resume.txt",
        content_type=file.content_type,
        raw_text=raw_text,
    )
    return ResumeDocumentRead.model_validate(resume)


@router.get("/{candidate_profile_id}/resumes", response_model=list[ResumeDocumentRead])
async def list_candidate_resumes(candidate_profile_id: UUID, db: AsyncSession = Depends(get_db)) -> list[ResumeDocumentRead]:
    service = CandidateProfileService(db)
    candidate = await service.get_by_id(candidate_profile_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")

    resume_service = ResumeDocumentService(db)
    resumes = await resume_service.list_for_candidate(candidate_profile_id)
    return [ResumeDocumentRead.model_validate(resume) for resume in resumes]


@router.post("/{candidate_profile_id}/job-descriptions", response_model=JobDescriptionRead, status_code=status.HTTP_201_CREATED)
async def upload_job_description(
    candidate_profile_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> JobDescriptionRead:
    service = CandidateProfileService(db)
    candidate = await service.get_by_id(candidate_profile_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")

    raw_bytes = await file.read()
    raw_text = raw_bytes.decode("utf-8", errors="replace")
    if not raw_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description file is empty")

    jd_service = JobDescriptionService(db)
    job_description = await jd_service.create_for_candidate(
        candidate_profile_id=candidate_profile_id,
        file_name=file.filename or "job_description.txt",
        content_type=file.content_type,
        raw_text=raw_text,
    )
    return JobDescriptionRead.model_validate(job_description)


@router.get("/{candidate_profile_id}/job-descriptions", response_model=list[JobDescriptionRead])
async def list_job_descriptions(candidate_profile_id: UUID, db: AsyncSession = Depends(get_db)) -> list[JobDescriptionRead]:
    service = CandidateProfileService(db)
    candidate = await service.get_by_id(candidate_profile_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")

    jd_service = JobDescriptionService(db)
    job_descriptions = await jd_service.list_for_candidate(candidate_profile_id)
    return [JobDescriptionRead.model_validate(job_description) for job_description in job_descriptions]


@router.post("/{candidate_profile_id}/job-descriptions/{job_description_id}/match", response_model=JobDescriptionMatchResult)
async def match_resume_to_job_description(
    candidate_profile_id: UUID,
    job_description_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> JobDescriptionMatchResult:
    service = CandidateProfileService(db)
    candidate = await service.get_by_id(candidate_profile_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found")

    jd_service = JobDescriptionService(db)
    job_description = await jd_service.get_by_id(job_description_id)
    if job_description is None or job_description.candidate_profile_id != candidate_profile_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    resume_service = ResumeDocumentService(db)
    resumes = await resume_service.list_for_candidate(candidate_profile_id)
    resume_skills: set[str] = set()
    for resume in resumes:
        for skill in resume.skills or []:
            resume_skills.add(skill)

    payload = jd_service.match_resume(job_description=job_description, resume_skills=resume_skills)
    return JobDescriptionMatchResult.model_validate(payload)
