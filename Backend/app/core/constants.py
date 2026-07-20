"""
app.core.constants — every shared constant used across the project.

Rules for this file:
  - Zero imports from the rest of the app (safe to import anywhere)
  - No logic — only data
  - Grouped by domain with clear section headers
  - Use these instead of raw strings or numbers scattered in services/routes

Import examples:
    from app.core.constants import RoleName
    from app.core.constants import ProjectStatus, TaskStatus, TaskPriority
    from app.core.constants import InvoiceStatus
    from app.core.constants import Pagination, TokenType, FileUpload, ErrorMessage
"""


# ══════════════════════════════════════════════════════════════════════════════
# ROLES
# ══════════════════════════════════════════════════════════════════════════════

class RoleName:
    """
    The three built-in platform roles.

    These strings must match the `name` column in the `roles` table exactly.
    They are seeded once by app/seed.py and never created via the API.

    Usage:
        if current_user.has_role(RoleName.ADMIN):
            ...

        role_required(RoleName.FREELANCER, RoleName.ADMIN)
    """
    ADMIN      = "admin"
    FREELANCER = "freelancer"
    CLIENT     = "client"

    # Ordered list — used by the seed script to create roles in sequence
    ALL: list = [ADMIN, FREELANCER, CLIENT]


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT
# ══════════════════════════════════════════════════════════════════════════════

class ProjectStatus:
    """
    All valid values for projects.status.

    Lifecycle:
        DRAFT → ACTIVE → COMPLETED → APPROVED  (normal flow)
                       → ON_HOLD   → ACTIVE     (paused and resumed)
                       → CANCELLED              (abandoned at any stage)

    Who can set each status:
        DRAFT      freelancer (default on create)
        ACTIVE     freelancer
        ON_HOLD    freelancer
        COMPLETED  freelancer
        APPROVED   client only  (via PATCH /projects/{id})
        CANCELLED  freelancer or admin
    """
    DRAFT     = "draft"       # Just created — not yet in progress
    ACTIVE    = "active"      # Work is underway
    ON_HOLD   = "on_hold"     # Temporarily paused
    COMPLETED = "completed"   # Freelancer has marked it done
    APPROVED  = "approved"    # Client confirmed delivery
    CANCELLED = "cancelled"   # Abandoned — no further work expected

    ALL: list = [DRAFT, ACTIVE, ON_HOLD, COMPLETED, APPROVED, CANCELLED]

    # Terminal states — once here, no further transitions are expected
    TERMINAL: list = [APPROVED, CANCELLED]

    # States where the project is considered billable / chargeable
    BILLABLE: list = [ACTIVE, ON_HOLD, COMPLETED, APPROVED]

    # Valid transitions — used by the service layer for state-machine checks
    # Key: current status  →  Value: list of allowed next statuses
    TRANSITIONS: dict = {
        DRAFT:     [ACTIVE, CANCELLED],
        ACTIVE:    [ON_HOLD, COMPLETED, CANCELLED],
        ON_HOLD:   [ACTIVE, CANCELLED],
        COMPLETED: [APPROVED, ACTIVE],    # ACTIVE allows reopening
        APPROVED:  [],                     # Terminal
        CANCELLED: [],                     # Terminal
    }

    @classmethod
    def can_transition(cls, current: str, next_: str) -> bool:
        """Return True if moving from `current` to `next_` is allowed."""
        return next_ in cls.TRANSITIONS.get(current, [])


# ══════════════════════════════════════════════════════════════════════════════
# TASK
# ══════════════════════════════════════════════════════════════════════════════

class TaskStatus:
    """
    All valid values for tasks.status.

    Normal flow:
        TODO → IN_PROGRESS → IN_REVIEW → DONE

    Side-effects managed by task_service:
        → DONE        sets   completed_at = now()
        ← DONE        clears completed_at = None
    """
    TODO        = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW   = "in_review"
    DONE        = "done"
    CANCELLED   = "cancelled"

    ALL: list      = [TODO, IN_PROGRESS, IN_REVIEW, DONE, CANCELLED]
    ACTIVE: list   = [TODO, IN_PROGRESS, IN_REVIEW]   # Not yet finished
    CLOSED: list   = [DONE, CANCELLED]                 # No further work needed
    PENDING: list  = [TODO, IN_PROGRESS]               # Used in dashboard "pending tasks" count


class TaskPriority:
    """
    All valid values for tasks.priority.
    Defaults to MEDIUM on create if not supplied.
    """
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    URGENT = "urgent"

    ALL: list = [LOW, MEDIUM, HIGH, URGENT]

    # Numeric weight — useful for sorting by priority in queries
    WEIGHT: dict = {
        LOW:    1,
        MEDIUM: 2,
        HIGH:   3,
        URGENT: 4,
    }


# ══════════════════════════════════════════════════════════════════════════════
# INVOICE
# ══════════════════════════════════════════════════════════════════════════════

class InvoiceStatus:
    """
    All valid values for invoices.status.

    Normal flow:
        DRAFT → SENT → VIEWED → PAID

    Who can set each status:
        DRAFT      freelancer  (default on create)
        SENT       freelancer  (invoice delivered to client)
        VIEWED     freelancer  (or set automatically when client opens it)
        PAID       client      (via PATCH /invoices/{id})
                   freelancer  (can also mark as paid if payment received offline)
        OVERDUE    system job  (set when due_date has passed and status ≠ PAID)
        CANCELLED  freelancer or admin
    """
    DRAFT     = "draft"      # Created — not yet sent to client
    SENT      = "sent"       # Delivered to client, awaiting payment
    VIEWED    = "viewed"     # Client has opened the invoice
    PAID      = "paid"       # Payment received
    OVERDUE   = "overdue"    # Past due_date, still unpaid
    CANCELLED = "cancelled"  # Void — will not be paid

    ALL: list      = [DRAFT, SENT, VIEWED, PAID, OVERDUE, CANCELLED]
    TERMINAL: list = [PAID, CANCELLED]               # Cannot change after these
    UNPAID: list   = [SENT, VIEWED, OVERDUE]          # Used in "outstanding amount" queries
    OPEN: list     = [DRAFT, SENT, VIEWED, OVERDUE]   # Not yet resolved


# ══════════════════════════════════════════════════════════════════════════════
# TOKEN
# ══════════════════════════════════════════════════════════════════════════════

class TokenType:
    """
    JWT `type` claim values.

    Stamped into every token so access tokens cannot be used as refresh
    tokens and vice versa. Validated in get_current_user().
    """
    ACCESS  = "access"
    REFRESH = "refresh"


# ══════════════════════════════════════════════════════════════════════════════
# PAGINATION
# ══════════════════════════════════════════════════════════════════════════════

class Pagination:
    """
    Default and maximum values for list endpoint pagination.

    Used in route Query() defaults:
        skip:  int = Query(Pagination.DEFAULT_SKIP,  ge=0)
        limit: int = Query(Pagination.DEFAULT_LIMIT, le=Pagination.MAX_LIMIT)
    """
    DEFAULT_SKIP:  int = 0
    DEFAULT_LIMIT: int = 50
    MAX_LIMIT:     int = 200

    # Time entries have higher defaults because they are more granular
    TIME_DEFAULT_LIMIT: int = 100
    TIME_MAX_LIMIT:     int = 500


# ══════════════════════════════════════════════════════════════════════════════
# FILE UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

class FileUpload:
    """
    File upload constraints used by file_service and route docstrings.

    ALLOWED_MIME_TYPES is checked in file_service.upload_file().
    Set to an empty list to allow all MIME types.
    """
    ALLOWED_MIME_TYPES: list = [
        # Images
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        # Documents
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        # Spreadsheets
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        # Plain text
        "text/plain",
        "text/csv",
        # Archives
        "application/zip",
        "application/x-zip-compressed",
    ]

    # Friendly extensions listed in Swagger upload description
    ALLOWED_EXTENSIONS: list = [
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
        ".pdf", ".doc", ".docx",
        ".xls", ".xlsx",
        ".txt", ".csv",
        ".zip",
    ]


# ══════════════════════════════════════════════════════════════════════════════
# INVOICE NUMBER FORMAT
# ══════════════════════════════════════════════════════════════════════════════

class InvoiceNumber:
    """
    Format rules for auto-generated invoice numbers.

    Pattern : INV-{YEAR}-{SEQ:03d}
    Examples: INV-2024-001, INV-2024-042, INV-2025-001

    The sequence resets to 001 at the start of each calendar year,
    per freelancer (not platform-wide).
    """
    PREFIX:         str = "INV"
    SEPARATOR:      str = "-"
    SEQUENCE_WIDTH: int = 3      # zero-padded to 3 digits → 001, 042

    @classmethod
    def build(cls, year: int, sequence: int) -> str:
        """
        Build a formatted invoice number.

        Args:
            year:     The calendar year  e.g. 2024
            sequence: The per-freelancer sequence for this year  e.g. 7

        Returns:
            "INV-2024-007"
        """
        seq = str(sequence).zfill(cls.SEQUENCE_WIDTH)
        return f"{cls.PREFIX}{cls.SEPARATOR}{year}{cls.SEPARATOR}{seq}"


# ══════════════════════════════════════════════════════════════════════════════
# ERROR MESSAGES
# ══════════════════════════════════════════════════════════════════════════════

class ErrorMessage:
    """
    Reusable error message strings for HTTPException `detail` fields.

    Use these in services instead of hardcoding strings:
        raise NotFoundError(ErrorMessage.USER_NOT_FOUND)
        raise ForbiddenError(ErrorMessage.NOT_YOUR_CLIENT)

    Keeping messages here makes them easy to audit, translate, or
    replace with error codes for API consumers.
    """

    # ── Auth ──────────────────────────────────────────────────────────
    INVALID_CREDENTIALS    = "Invalid email or password."
    ACCOUNT_DEACTIVATED    = "This account has been deactivated."
    INVALID_TOKEN          = "Could not validate credentials."
    INVALID_TOKEN_TYPE     = "Invalid token type. Use an access token, not a refresh token."
    EXPIRED_REFRESH_TOKEN  = "Invalid or expired refresh token."
    ROLES_NOT_SEEDED       = "Roles are not seeded. Run: python -m app.seed"

    # ── User ──────────────────────────────────────────────────────────
    EMAIL_ALREADY_EXISTS   = "An account with this email already exists."
    USER_NOT_FOUND         = "User not found."
    WRONG_CURRENT_PASSWORD = "Current password is incorrect."
    CANNOT_DEACTIVATE_SELF = "You cannot deactivate your own account."
    LAST_ROLE_REMOVAL      = "Cannot remove the user's only role. Assign another role first."
    ROLE_NOT_FOUND         = "Role '{role_name}' does not exist. Valid roles: admin, freelancer, client."
    USER_ALREADY_HAS_ROLE  = "User already has the role '{role_name}'."
    USER_LACKS_ROLE        = "User does not have role '{role_name}'."

    # ── Client ────────────────────────────────────────────────────────
    CLIENT_NOT_FOUND       = "Client not found."
    NOT_YOUR_CLIENT        = "You do not have access to this client."

    # ── Project ───────────────────────────────────────────────────────
    PROJECT_NOT_FOUND      = "Project not found."
    NOT_YOUR_PROJECT       = "You do not have access to this project."
    CLIENT_NOT_YOURS       = "That client does not belong to you."
    CLIENT_APPROVE_ONLY    = "Clients can only set project status to 'approved'."
    CLIENT_CANNOT_DELETE   = "Clients cannot delete projects."
    INVALID_STATUS_TRANSITION = "Cannot transition project from '{current}' to '{next}'."

    # ── Task ──────────────────────────────────────────────────────────
    TASK_NOT_FOUND         = "Task not found."
    CLIENT_CANNOT_CREATE_TASK  = "Clients cannot create tasks."
    CLIENT_CANNOT_EDIT_TASK    = "Clients cannot edit tasks."
    CLIENT_CANNOT_DELETE_TASK  = "Clients cannot delete tasks."

    # ── Time entry ────────────────────────────────────────────────────
    TIME_ENTRY_NOT_FOUND   = "Time entry not found."
    TIMER_ALREADY_RUNNING  = "You already have a running timer (id={entry_id}). Stop it before starting a new one."
    TIMER_ALREADY_STOPPED  = "This timer has already been stopped."
    END_BEFORE_START       = "end_time must be after start_time."
    CLIENT_CANNOT_TRACK    = "Clients cannot track time."
    NOT_YOUR_TIME_ENTRY    = "You do not own this time entry."

    # ── Invoice ───────────────────────────────────────────────────────
    INVOICE_NOT_FOUND      = "Invoice not found."
    NOT_YOUR_INVOICE       = "You do not have access to this invoice."
    CLIENT_CANNOT_CREATE_INVOICE = "Clients cannot create invoices."
    CLIENT_PAID_ONLY       = "Clients can only mark invoices as paid."
    CLIENT_CANNOT_DELETE_INVOICE = "Clients cannot delete invoices."
    PAID_INVOICE_LOCKED    = "Paid invoices cannot be deleted."

    # ── File ──────────────────────────────────────────────────────────
    FILE_NOT_FOUND         = "File not found."
    NOT_YOUR_FILE          = "Only the uploader or an admin can delete this file."
    FILE_TOO_LARGE         = "File exceeds the {max_mb} MB size limit."
    UNSUPPORTED_FILE_TYPE  = "File type '{mime_type}' is not allowed."


# ══════════════════════════════════════════════════════════════════════════════
# HTTP STATUS ALIASES
# ══════════════════════════════════════════════════════════════════════════════

class HttpStatus:
    """
    Readable aliases for the HTTP status codes used in this project.

    Optional — use fastapi.status directly if you prefer.
    These exist for teams that find numeric codes less readable in PRs.

    Usage:
        raise HTTPException(status_code=HttpStatus.NOT_FOUND, ...)
    """
    OK                    = 200
    CREATED               = 201
    NO_CONTENT            = 204
    BAD_REQUEST           = 400
    UNAUTHORIZED          = 401
    FORBIDDEN             = 403
    NOT_FOUND             = 404
    CONFLICT              = 409
    UNPROCESSABLE_ENTITY  = 422
    TOO_LARGE             = 413
    INTERNAL_SERVER_ERROR = 500