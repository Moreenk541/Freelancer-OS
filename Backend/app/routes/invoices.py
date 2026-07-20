"""
Invoice routes  ·  /api/v1/invoices
 
GET    /              List invoices — role-scoped
POST   /              Raise a new invoice
GET    /{invoice_id}  Full detail with nested client + project
PATCH  /{invoice_id}  Update invoice — clients restricted to marking paid only
DELETE /{invoice_id}  Delete invoice — blocked once status is paid
 
Role matrix:
    Action          Freelancer   Client       Admin
    ─────────────   ──────────   ──────────   ─────
    List            Own only     Own only     All
    Create          ✓            ✗            ✓
    Read detail     Own only     Own only     All
    Update          ✓ (any)      Paid only    ✓ (any)
    Delete          ✓            ✗            ✓
 
Business rules enforced by invoice_service:
    - invoice_number is auto-generated  →  INV-{YEAR}-{SEQ:03d}
    - subtotal, tax_amount, total_amount are always computed server-side
    - Setting status → paid auto-records paid_at timestamp
    - Paid invoices cannot be deleted
"""

from typing import List, Optional
 
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
 
from app.core.constants import ErrorMessage, InvoiceStatus, Pagination
from app.core.dependencies import freelancer_required, get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceDetail, InvoiceOut, InvoiceUpdate
from app.services import invoice_service
 
router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.get("/", response_model=List[InvoiceOut])
def list_invoices(
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description = (
            "Filter by invoice status."
            f"Valid values : {'|'.join(InvoiceStatus.ALL)}"
            f"unpaid group shortcut: {'|'.join(InvoiceStatus.UNPAID)}"
        ),
    ),
     skip:  int = Query(
        Pagination.DEFAULT_SKIP,
        ge=0,
        description="Number of records to skip (pagination offset)",
    ),
    limit: int = Query(
        Pagination.DEFAULT_LIMIT,
        le=Pagination.MAX_LIMIT,
        description=f"Maximum records to return (hard cap: {Pagination.MAX_LIMIT})",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ) -> List[InvoiceOut]:
     return invoice_service.list_invoices(
        db,
        current_user,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )
     
"""
    Return invoices scoped to the caller's role.
 
    **Freelancer** — invoices they raised, newest first.
 
    **Client** — invoices addressed to their linked client record.
    Requires the client's user account to be linked via `clients.user_id`.
 
    **Admin** — all invoices on the platform.
 
    Use the `status` query param to filter. Common filters:
    - `?status=draft` — invoices not yet sent
    - `?status=overdue` — past due date, unpaid
    - `?status=paid` — completed payments
    """
    

@router.post(
    "",
    response_model=InvoiceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invoice",
    response_description="Newly created invoice with computed totals and auto-generated number",
    responses={
        403: {"description": ErrorMessage.CLIENT_CANNOT_CREATE_INVOICE},
    },
)
def create_invoice(
    data: InvoiceCreate,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> InvoiceOut:
    """
    Raise a new invoice against a client.
 
    **Required fields:** `client_id`, `issue_date`, `hours_worked`, `hourly_rate`
 
    **Optional fields:** `project_id`, `due_date`, `tax_rate` (default 0), `notes`
 
    **Computed server-side — do not include in the request body:**
 
    | Field            | Formula                          |
    |------------------|----------------------------------|
    | `invoice_number` | `INV-{YEAR}-{SEQ:03d}` per freelancer per year |
    | `subtotal`       | `hours_worked × hourly_rate`     |
    | `tax_amount`     | `subtotal × tax_rate / 100`      |
    | `total_amount`   | `subtotal + tax_amount`          |
 
    Invoice starts with status **draft**.
    Change to **sent** once you have delivered it to the client.
    """
    return invoice_service.create_invoice(db, data, current_user)
 
 
@router.get(
    "/{invoice_id}",
    response_model=InvoiceDetail,
    status_code=status.HTTP_200_OK,
    summary="Get invoice detail",
    response_description="Full invoice with nested client and project objects",
    responses={
        403: {"description": ErrorMessage.NOT_YOUR_INVOICE},
        404: {"description": ErrorMessage.INVOICE_NOT_FOUND},
    },
)
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvoiceDetail:
    """
    Return a single invoice by ID.
 
    Response includes nested `client` and `project` objects so the
    frontend can render a complete invoice view without extra requests.
    """
    return invoice_service.get_invoice(db, invoice_id, current_user)
 
 
@router.patch(
    "/{invoice_id}",
    response_model=InvoiceOut,
    status_code=status.HTTP_200_OK,
    summary="Update an invoice",
    response_description="Updated invoice with recomputed totals",
    responses={
        403: {"description": f"{ErrorMessage.NOT_YOUR_INVOICE} | {ErrorMessage.CLIENT_PAID_ONLY}"},
        404: {"description": ErrorMessage.INVOICE_NOT_FOUND},
    },
)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvoiceOut:
    """
    Update an invoice.
 
    **Freelancers / Admins** can update any of these fields:
    - `hours_worked`, `hourly_rate`, `tax_rate` — totals recomputed automatically
    - `status` — advance through the workflow
    - `due_date`, `notes`
 
    **Clients** can only set `status → paid`.
    This automatically records `paid_at` with the current UTC timestamp.
 
    **Status workflow:**
    ```
    draft → sent → viewed → paid
                          ↘ overdue  (past due_date)
    any   → cancelled
    ```
    """
    return invoice_service.update_invoice(db, invoice_id, data, current_user)
 
 
@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an invoice",
    responses={
        400: {"description": ErrorMessage.PAID_INVOICE_LOCKED},
        403: {"description": f"{ErrorMessage.CLIENT_CANNOT_DELETE_INVOICE} | {ErrorMessage.NOT_YOUR_INVOICE}"},
        404: {"description": ErrorMessage.INVOICE_NOT_FOUND},
    },
)
def delete_invoice(
    invoice_id: int,
    current_user: User = Depends(freelancer_required),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete an invoice.
 
    **Blocked** when `status = paid` — paid invoices are permanent financial
    records. Cancel the invoice instead if you need to void it.
 
    Safe to delete invoices in `draft`, `sent`, `viewed`, `overdue`,
    or `cancelled` status.
    """
    invoice_service.delete_invoice(db, invoice_id, current_user)
 