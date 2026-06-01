"""
Invoice schemas.

InvoiceCreate — freelancer raises an invoice
InvoiceUpdate — edit billing fields or advance status
InvoiceOut    — list / create / update response
InvoiceDetail — single invoice with nested client + project

Totals are always computed server-side in the service:
    subtotal     = hours_worked * hourly_rate
    tax_amount   = subtotal * tax_rate / 100
    total_amount = subtotal + tax_amount

Clients receive the invoice_number but cannot set it —
it is auto-generated as INV-{YEAR}-{SEQ:03d}.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.invoice import InvoiceStatus
from app.schemas.client  import ClientOut
from app.schemas.project import ProjectOut


class InvoiceCreate(BaseModel):
    """
    All the information needed to raise a new invoice.
    project_id is optional — some invoices are not tied to a specific project.
    tax_rate defaults to 0 (no tax).
    """
    client_id:    int
    project_id:   Optional[int]  = None
    issue_date:   date
    due_date:     Optional[date] = None
    hours_worked: float          = Field(..., ge=0,  description="Decimal hours billed")
    hourly_rate:  float          = Field(..., ge=0,  description="Rate in your currency")
    tax_rate:     float          = Field(0.0, ge=0, le=100, description="Tax percentage e.g. 16 = 16%")
    notes:        Optional[str]  = Field(None, max_length=2000)


class InvoiceUpdate(BaseModel):
    """
    PATCH — all fields optional.

    Freelancer can update billing fields; totals are recomputed.
    Client can only set status → paid (enforced in service).
    Setting status → paid automatically records paid_at timestamp.
    """
    hours_worked: Optional[float]         = Field(None, ge=0)
    hourly_rate:  Optional[float]         = Field(None, ge=0)
    tax_rate:     Optional[float]         = Field(None, ge=0, le=100)
    status:       Optional[InvoiceStatus] = None
    due_date:     Optional[date]          = None
    notes:        Optional[str]           = Field(None, max_length=2000)


class InvoiceOut(BaseModel):
    """
    Standard invoice response.
    All computed totals (subtotal, tax_amount, total_amount) are included.
    """
    id:             int
    invoice_number: str
    freelancer_id:  int
    client_id:      int
    project_id:     Optional[int]      = None
    hours_worked:   float
    hourly_rate:    float
    subtotal:       float
    tax_rate:       float
    tax_amount:     float
    total_amount:   float
    status:         InvoiceStatus
    issue_date:     date
    due_date:       Optional[date]     = None
    paid_at:        Optional[datetime] = None
    notes:          Optional[str]      = None
    created_at:     datetime

    model_config = {"from_attributes": True}


class InvoiceDetail(InvoiceOut):
    """
    Single invoice view — adds nested client and project objects.
    Used by GET /invoices/{id}.
    """
    client:  Optional[ClientOut]  = None
    project: Optional[ProjectOut] = None

    model_config = {"from_attributes": True}