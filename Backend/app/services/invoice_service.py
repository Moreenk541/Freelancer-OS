"""
Invoice service.

Business rules:
  - Only freelancers and admins can create invoices.
  - Clients can only mark an invoice as paid.
  - Paid invoices cannot be deleted.
  - Invoice numbers are auto-generated: INV-{YEAR}-{SEQ:03d}, per freelancer per year.
  - All monetary totals are computed server-side on create and recalculated on update.
"""
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, invoice_id: int) -> Invoice:
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found.")
    return invoice


def _assert_access(invoice: Invoice, current_user: User) -> None:
    if current_user.has_role("admin"):
        return
    if current_user.has_role("freelancer") and invoice.freelancer_id == current_user.id:
        return
    if current_user.has_role("client"):
        # Client portal: invoice must belong to their linked client record
        from app.models.client import Client
        client = db_get_client_for_user(invoice.freelancer_id, current_user)
        if client and invoice.client_id == client.id:
            return
    raise HTTPException(status_code=403, detail="You do not have access to this invoice.")


def db_get_client_for_user(freelancer_id, current_user: User):
    """Placeholder — actual client lookup is done inline where the DB session is available."""
    return None


def _generate_invoice_number(db: Session, freelancer_id: int) -> str:
    """Generate INV-{YEAR}-{SEQ:03d}, sequential per freelancer per calendar year."""
    year = date.today().year
    count = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.freelancer_id == freelancer_id,
            extract("year", Invoice.created_at) == year,
        )
        .scalar() or 0
    )
    return f"INV-{year}-{count + 1:03d}"


def _compute_totals(hours: float, rate: float, tax_rate: float) -> dict:
    subtotal   = round(hours * rate, 2)
    tax_amount = round(subtotal * tax_rate / 100, 2)
    return {
        "subtotal":     subtotal,
        "tax_amount":   tax_amount,
        "total_amount": round(subtotal + tax_amount, 2),
    }


# ── CRUD ──────────────────────────────────────────────────────────────────────

def list_invoices(
    db: Session,
    current_user: User,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Invoice]:
    q = db.query(Invoice)

    if current_user.has_role("admin"):
        pass
    elif current_user.has_role("freelancer"):
        q = q.filter(Invoice.freelancer_id == current_user.id)
    elif current_user.has_role("client"):
        from app.models.client import Client
        client = db.query(Client).filter(Client.user_id == current_user.id).first()
        if not client:
            return []
        q = q.filter(Invoice.client_id == client.id)

    if status_filter:
        q = q.filter(Invoice.status == status_filter)

    return q.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()


def get_invoice(db: Session, invoice_id: int, current_user: User) -> Invoice:
    invoice = _get_or_404(db, invoice_id)

    if current_user.has_role("admin"):
        return invoice
    if current_user.has_role("freelancer") and invoice.freelancer_id == current_user.id:
        return invoice
    if current_user.has_role("client"):
        from app.models.client import Client
        client = db.query(Client).filter(Client.user_id == current_user.id).first()
        if client and invoice.client_id == client.id:
            return invoice

    raise HTTPException(status_code=403, detail="You do not have access to this invoice.")


def create_invoice(db: Session, data: InvoiceCreate, current_user: User) -> Invoice:
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        raise HTTPException(status_code=403, detail="Clients cannot create invoices.")

    totals = _compute_totals(data.hours_worked, data.hourly_rate, data.tax_rate)

    invoice = Invoice(
        **data.model_dump(),
        freelancer_id=current_user.id,
        invoice_number=_generate_invoice_number(db, current_user.id),
        **totals,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def update_invoice(db: Session, invoice_id: int, data: InvoiceUpdate, current_user: User) -> Invoice:
    invoice = get_invoice(db, invoice_id, current_user)

    # Clients can only mark as paid
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        if data.status != InvoiceStatus.PAID:
            raise HTTPException(status_code=403, detail="Clients can only mark invoices as paid.")
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invoice)
        return invoice

    updates = data.model_dump(exclude_none=True)

    # Recompute totals if any billing field changed
    hours    = updates.get("hours_worked", invoice.hours_worked)
    rate     = updates.get("hourly_rate",  invoice.hourly_rate)
    tax_rate = updates.get("tax_rate",     invoice.tax_rate)
    updates.update(_compute_totals(hours, rate, tax_rate))

    # Auto-record paid_at when status transitions to PAID
    if updates.get("status") == InvoiceStatus.PAID and invoice.status != InvoiceStatus.PAID:
        updates["paid_at"] = datetime.now(timezone.utc)

    for field, value in updates.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)
    return invoice


def delete_invoice(db: Session, invoice_id: int, current_user: User) -> None:
    if current_user.has_role("client") and not current_user.has_role("freelancer", "admin"):
        raise HTTPException(status_code=403, detail="Clients cannot delete invoices.")

    invoice = get_invoice(db, invoice_id, current_user)

    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(status_code=400, detail="Paid invoices cannot be deleted.")

    db.delete(invoice)
    db.commit()