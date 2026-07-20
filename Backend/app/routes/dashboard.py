"""
Dashboard routes  ·  /api/v1/dashboard

GET  /         Role-specific KPI stats and recent activity feed

This is a read-only endpoint — no writes happen here.
All aggregation is done in dashboard_service using efficient
SQL aggregate functions (COUNT, SUM, extract) rather than
loading records into Python.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.constants import InvoiceStatus, ProjectStatus, TaskStatus
from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardOut
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "",
    response_model=DashboardOut,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard overview",
    response_description="KPI stats and activity feed tailored to the current user's role",
    responses={
        401: {"description": "Not authenticated"},
    },
)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardOut:
    """
    Return a role-tailored dashboard payload in a single request.

    ---

    ### Freelancer dashboard

    **Stats (`stats` object):**

    | Field                | Description                                              |
    |----------------------|----------------------------------------------------------|
    | `active_projects`    | Projects with status `active`                           |
    | `total_clients`      | All clients owned by this freelancer                    |
    | `pending_tasks`      | Tasks with status `todo` or `in_progress`               |
    | `monthly_earnings`   | Sum of **paid** invoices issued this calendar month     |
    | `total_earnings`     | All-time sum of **paid** invoices                       |
    | `outstanding_amount` | Sum of `sent`, `viewed`, `overdue` invoices (unpaid)    |
    | `hours_this_month`   | Tracked hours with a completed timer this calendar month|

    **Activity feed (`recent_activity` list):**
    - Up to 10 items, newest first
    - Covers: invoices marked paid, projects completed or approved
    - Each item has: `entity_type`, `entity_id`, `action`, `occurred_at`

    ---

    ### Admin dashboard

    Same stat fields as the freelancer view but **platform-wide** totals
    (not scoped to a single user). No activity feed is included.

    ---

    ### Client dashboard

    Minimal view — only fields relevant to a client are populated:

    | Field                | Description                                 |
    |----------------------|---------------------------------------------|
    | `active_projects`    | Active projects linked to this client       |
    | `outstanding_amount` | Total unpaid invoices addressed to them     |

    All other fields return `0`. No activity feed.

    ---

    **Status definitions used in aggregations:**
    - Active projects: `{ProjectStatus.ACTIVE}`
    - Pending tasks: `{', '.join(TaskStatus.PENDING)}`
    - Outstanding invoices: `{', '.join(InvoiceStatus.UNPAID)}`
    """
    return dashboard_service.get_dashboard(db, current_user)