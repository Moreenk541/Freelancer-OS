"""
Dashboard service — aggregates KPIs and recent activity per role.

Freelancer view: their own projects, clients, tasks, earnings, hours.
Admin view:      platform-wide totals.
Client view:     their own active projects and outstanding invoices.
"""
from calendar import monthrange
from datetime import date, datetime, timezone
from typing import List

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.invoice import Invoice, InvoiceStatus
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus
from app.models.time_entry import TimeEntry
from app.models.user import User
from app.schemas.dashboard import DashboardStats, RecentActivity, DashboardOut


# ── Helpers ───────────────────────────────────────────────────────────────────

def _month_bounds() -> tuple[date, date]:
    today = date.today()
    _, last = monthrange(today.year, today.month)
    return date(today.year, today.month, 1), date(today.year, today.month, last)


# ── Role-specific stats ───────────────────────────────────────────────────────

def _freelancer_stats(db: Session, user_id: int) -> DashboardStats:
    month_start, month_end = _month_bounds()

    active_projects = (
        db.query(func.count(Project.id))
        .filter(Project.freelancer_id == user_id, Project.status == ProjectStatus.ACTIVE)
        .scalar() or 0
    )
    total_clients = (
        db.query(func.count(Client.id))
        .filter(Client.freelancer_id == user_id)
        .scalar() or 0
    )
    pending_tasks = (
        db.query(func.count(Task.id))
        .join(Project, Task.project_id == Project.id)
        .filter(
            Project.freelancer_id == user_id,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
        )
        .scalar() or 0
    )
    monthly_earnings = (
        db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0))
        .filter(
            Invoice.freelancer_id == user_id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.issue_date >= month_start,
            Invoice.issue_date <= month_end,
        )
        .scalar() or 0.0
    )
    total_earnings = (
        db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0))
        .filter(Invoice.freelancer_id == user_id, Invoice.status == InvoiceStatus.PAID)
        .scalar() or 0.0
    )
    outstanding_amount = (
        db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0))
        .filter(
            Invoice.freelancer_id == user_id,
            Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.OVERDUE]),
        )
        .scalar() or 0.0
    )
    hours_this_month = (
        db.query(func.coalesce(func.sum(TimeEntry.duration), 0.0))
        .filter(
            TimeEntry.freelancer_id == user_id,
            TimeEntry.end_time != None,  # noqa: E711
            extract("year",  TimeEntry.start_time) == month_start.year,
            extract("month", TimeEntry.start_time) == month_start.month,
        )
        .scalar() or 0.0
    ) / 3600  # seconds → hours

    return DashboardStats(
        active_projects=active_projects,
        total_clients=total_clients,
        pending_tasks=pending_tasks,
        monthly_earnings=round(monthly_earnings, 2),
        total_earnings=round(total_earnings, 2),
        outstanding_amount=round(outstanding_amount, 2),
        hours_this_month=round(hours_this_month, 2),
    )


def _admin_stats(db: Session) -> DashboardStats:
    month_start, month_end = _month_bounds()

    return DashboardStats(
        active_projects=(
            db.query(func.count(Project.id))
            .filter(Project.status == ProjectStatus.ACTIVE)
            .scalar() or 0
        ),
        total_clients=db.query(func.count(Client.id)).scalar() or 0,
        pending_tasks=(
            db.query(func.count(Task.id))
            .filter(Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]))
            .scalar() or 0
        ),
        monthly_earnings=round(
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0))
            .filter(Invoice.status == InvoiceStatus.PAID,
                    Invoice.issue_date >= month_start,
                    Invoice.issue_date <= month_end)
            .scalar() or 0.0, 2
        ),
        total_earnings=round(
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0))
            .filter(Invoice.status == InvoiceStatus.PAID)
            .scalar() or 0.0, 2
        ),
        outstanding_amount=round(
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0))
            .filter(Invoice.status.in_([
                InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.OVERDUE,
            ]))
            .scalar() or 0.0, 2
        ),
        hours_this_month=round(
            (db.query(func.coalesce(func.sum(TimeEntry.duration), 0.0))
             .filter(TimeEntry.end_time != None,  # noqa: E711
                     extract("year",  TimeEntry.start_time) == month_start.year,
                     extract("month", TimeEntry.start_time) == month_start.month)
             .scalar() or 0.0) / 3600, 2
        ),
    )


def _client_stats(db: Session, current_user: User) -> DashboardStats:
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if not client:
        return DashboardStats(
            active_projects=0, total_clients=0, pending_tasks=0,
            monthly_earnings=0.0, total_earnings=0.0,
            outstanding_amount=0.0, hours_this_month=0.0,
        )
    return DashboardStats(
        active_projects=(
            db.query(func.count(Project.id))
            .filter(Project.client_id == client.id, Project.status == ProjectStatus.ACTIVE)
            .scalar() or 0
        ),
        total_clients=1,
        pending_tasks=0,
        monthly_earnings=0.0,
        total_earnings=0.0,
        outstanding_amount=round(
            db.query(func.coalesce(func.sum(Invoice.total_amount), 0.0))
            .filter(Invoice.client_id == client.id,
                    Invoice.status.in_([
                        InvoiceStatus.SENT, InvoiceStatus.VIEWED, InvoiceStatus.OVERDUE,
                    ]))
            .scalar() or 0.0, 2
        ),
        hours_this_month=0.0,
    )


# ── Activity feed ─────────────────────────────────────────────────────────────

def _recent_activity(db: Session, current_user: User) -> List[RecentActivity]:
    """
    Build a short activity feed from recent invoices and projects.
    Returns at most 10 items sorted newest first.
    """
    feed: List[RecentActivity] = []

    # Recent paid invoices
    paid_invoices = (
        db.query(Invoice)
        .filter(
            Invoice.freelancer_id == current_user.id,
            Invoice.status == InvoiceStatus.PAID,
            Invoice.paid_at != None,  # noqa: E711
        )
        .order_by(Invoice.paid_at.desc())
        .limit(5)
        .all()
    )
    for inv in paid_invoices:
        feed.append(RecentActivity(
            entity_type="invoice",
            entity_id=inv.id,
            action=f"Invoice {inv.invoice_number} marked as paid (${inv.total_amount:,.2f})",
            occurred_at=inv.paid_at,
        ))

    # Recently completed projects
    completed = (
        db.query(Project)
        .filter(
            Project.freelancer_id == current_user.id,
            Project.status.in_([ProjectStatus.COMPLETED, ProjectStatus.APPROVED]),
        )
        .order_by(Project.updated_at.desc())
        .limit(5)
        .all()
    )
    for proj in completed:
        feed.append(RecentActivity(
            entity_type="project",
            entity_id=proj.id,
            action=f"Project '{proj.title}' marked as {proj.status.value}",
            occurred_at=proj.updated_at,
        ))

    # Sort combined feed newest first and cap at 10 items
    feed.sort(key=lambda x: x.occurred_at, reverse=True)
    return feed[:10]


# ── Public entry point ────────────────────────────────────────────────────────

def get_dashboard(db: Session, current_user: User) -> DashboardOut:
    if current_user.has_role("admin"):
        stats = _admin_stats(db)
    elif current_user.has_role("freelancer"):
        stats = _freelancer_stats(db, current_user.id)
    else:
        stats = _client_stats(db, current_user)

    activity = (
        _recent_activity(db, current_user)
        if current_user.has_role("freelancer", "admin")
        else []
    )

    return DashboardOut(stats=stats, recent_activity=activity)