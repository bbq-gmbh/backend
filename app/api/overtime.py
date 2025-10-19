from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUserDep, OvertimeRecordServiceDep
from app.schemas.overtime import (
    OvertimeRecordCreate,
    OvertimeRecordResponse,
    OvertimeRecordUpdate,
    OvertimeSummary,
)


router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=OvertimeRecordResponse,
)
def create_overtime_record(
    record_data: OvertimeRecordCreate,
    user: CurrentUserDep,
    overtime_service: OvertimeRecordServiceDep,
) -> OvertimeRecordResponse:
    """
    Create a new overtime record for the authenticated user.
    
    Args:
        record_data: The overtime record data including date, work start/end times
        user: The authenticated user
        overtime_service: The overtime service dependency
        
    Returns:
        The created overtime record with calculated overtime hours
    """
    record = overtime_service.create_overtime_record(user=user, record_data=record_data)
    return OvertimeRecordResponse.model_validate(record)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[OvertimeRecordResponse],
)
def get_user_overtime_records(
    user: CurrentUserDep,
    overtime_service: OvertimeRecordServiceDep,
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
) -> list[OvertimeRecordResponse]:
    """
    Get all overtime records for the authenticated user.
    
    Optionally filter by date range.
    
    Args:
        user: The authenticated user
        overtime_service: The overtime service dependency
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        List of overtime records
    """
    if start_date and end_date:
        records = overtime_service.get_user_overtime_by_date_range(
            user_id=user.id, start_date=start_date, end_date=end_date
        )
    else:
        records = overtime_service.get_user_overtime_records(user_id=user.id)
    
    return [OvertimeRecordResponse.model_validate(record) for record in records]


@router.get(
    "/summary",
    status_code=status.HTTP_200_OK,
    response_model=OvertimeSummary,
)
def get_overtime_summary(
    user: CurrentUserDep,
    overtime_service: OvertimeRecordServiceDep,
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
) -> OvertimeSummary:
    """
    Get overtime summary for the authenticated user.
    
    Includes total overtime hours and all records.
    
    Args:
        user: The authenticated user
        overtime_service: The overtime service dependency
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        Overtime summary with total hours and records
    """
    if start_date and end_date:
        records = overtime_service.get_user_overtime_by_date_range(
            user_id=user.id, start_date=start_date, end_date=end_date
        )
    else:
        records = overtime_service.get_user_overtime_records(user_id=user.id)
    
    total_overtime = sum(record.overtime_hours for record in records)
    
    return OvertimeSummary(
        user_id=user.id,
        total_overtime_hours=total_overtime,
        record_count=len(records),
        records=[OvertimeRecordResponse.model_validate(record) for record in records],
    )


@router.get(
    "/{record_id}",
    status_code=status.HTTP_200_OK,
    response_model=OvertimeRecordResponse,
)
def get_overtime_record(
    record_id: int,
    user: CurrentUserDep,
    overtime_service: OvertimeRecordServiceDep,
) -> OvertimeRecordResponse:
    """
    Get a specific overtime record by ID.
    
    Users can only access their own records.
    
    Args:
        record_id: The ID of the overtime record
        user: The authenticated user
        overtime_service: The overtime service dependency
        
    Returns:
        The overtime record
        
    Raises:
        HTTPException: If record not found or user is not authorized
    """
    record = overtime_service.get_overtime_record_by_id(record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overtime record not found",
        )
    
    # Check if the record belongs to the user
    if record.user_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this record",
        )
    
    return OvertimeRecordResponse.model_validate(record)


@router.put(
    "/{record_id}",
    status_code=status.HTTP_200_OK,
    response_model=OvertimeRecordResponse,
)
def update_overtime_record(
    record_id: int,
    update_data: OvertimeRecordUpdate,
    user: CurrentUserDep,
    overtime_service: OvertimeRecordServiceDep,
) -> OvertimeRecordResponse:
    """
    Update an existing overtime record.
    
    Users can only update their own records.
    
    Args:
        record_id: The ID of the overtime record to update
        update_data: The fields to update
        user: The authenticated user
        overtime_service: The overtime service dependency
        
    Returns:
        The updated overtime record
        
    Raises:
        HTTPException: If record not found or user is not authorized
    """
    record = overtime_service.get_overtime_record_by_id(record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overtime record not found",
        )
    
    # Check if the record belongs to the user
    if record.user_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this record",
        )
    
    updated_record = overtime_service.update_overtime_record(
        record_id=record_id, update_data=update_data, user=user
    )
    
    if not updated_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update record",
        )
    
    return OvertimeRecordResponse.model_validate(updated_record)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_overtime_record(
    record_id: int,
    user: CurrentUserDep,
    overtime_service: OvertimeRecordServiceDep,
) -> None:
    """
    Delete an overtime record.
    
    Users can only delete their own records.
    
    Args:
        record_id: The ID of the overtime record to delete
        user: The authenticated user
        overtime_service: The overtime service dependency
        
    Raises:
        HTTPException: If record not found or user is not authorized
    """
    record = overtime_service.get_overtime_record_by_id(record_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overtime record not found",
        )
    
    # Check if the record belongs to the user
    if record.user_id != user.id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this record",
        )
    
    success = overtime_service.delete_overtime_record(record_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to delete record",
        )


@router.get(
    "/admin/all",
    status_code=status.HTTP_200_OK,
    response_model=list[OvertimeRecordResponse],
)
def get_all_overtime_records_admin(
    user: CurrentUserDep,
    overtime_service: OvertimeRecordServiceDep,
) -> list[OvertimeRecordResponse]:
    """
    Get all overtime records (admin only).
    
    Args:
        user: The authenticated user (must be superuser)
        overtime_service: The overtime service dependency
        
    Returns:
        List of all overtime records
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access all records",
        )
    
    records = overtime_service.get_all_overtime_records()
    return [OvertimeRecordResponse.model_validate(record) for record in records]
