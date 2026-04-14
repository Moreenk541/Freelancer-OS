from enum  import Enum

class UserRole(str,Enum):
    ADMIN = "admin"
    FREELANCER = "freelancer"
    CLIENT = "client"

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED  = "completed"
    CANCELLED = "cancelled"  

class TaskStatus(str, Enum) :
    TODO = "todo"
    IN_PROGESS = "in_progress"  
    REVIEW = "review"
    COMPLETED ="completed"

class InvoiceStatus(str, Enum): 
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"




