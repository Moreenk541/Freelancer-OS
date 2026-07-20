"""
app.routes — all HTTP route handlers.

Every module owns one resource and one URL prefix.
All routers are registered in app/main.py under /api/v1/.

┌─────────────────┬──────────────────────┬───────────────────────────────────────┐
│ Module          │ Prefix               │ Responsibility                        │
├─────────────────┼──────────────────────┼───────────────────────────────────────┤
│ auth            │ /auth                │ Register, login, refresh, /me         │
│ users           │ /users               │ Profile management, admin user ops    │
│ clients         │ /clients             │ Client CRUD scoped to freelancer      │
│ projects        │ /projects            │ Project CRUD with role-scoped access  │
│ tasks           │ /tasks               │ Task CRUD inside a project            │
│ time_entries    │ /time                │ Live timer + manual time logging      │
│ invoices        │ /invoices            │ Invoice CRUD with billing logic       │
│ files           │ /files               │ File upload and management            │
│ dashboard       │ /dashboard           │ Role-specific KPI stats + activity    │
└─────────────────┴──────────────────────┴───────────────────────────────────────┘

Dependency chain for every request:
    HTTP → Router → Dependency (auth + RBAC) → Service (business logic) → DB
"""
from app.routes.auth         import router as auth_router
from app.routes.users        import router as users_router
from app.routes.clients      import router as clients_router
from app.routes.projects     import router as projects_router
from app.routes.tasks        import router as tasks_router
from app.routes.time_entries import router as time_router
from app.routes.invoices     import router as invoices_router
from app.routes.files        import router as files_router
from app.routes.dashboard    import router as dashboard_router

# Expose all routers so main.py can do:
#   from app.routes import all_routers
#   for router in all_routers:
#       app.include_router(router, prefix="/api/v1")
all_routers = [
    auth_router,
    users_router,
    clients_router,
    projects_router,
    tasks_router,
    time_router,
    invoices_router,
    files_router,
    dashboard_router,
]

__all__ = [
    "auth_router",
    "users_router",
    "clients_router",
    "projects_router",
    "tasks_router",
    "time_router",
    "invoices_router",
    "files_router",
    "dashboard_router",
    "all_routers",
]