"""
FSM states for ticket creation flow.
"""

from aiogram.fsm.state import State, StatesGroup


class TicketCreation(StatesGroup):
    """States for ticket creation flow."""
    
    waiting_category = State()       # User selecting category
    waiting_description = State()    # User typing description
    waiting_attachments = State()    # User attaching files (optional)
    
    # Summary / preview step
    showing_summary = State()        # Showing ticket preview before submit
    
    # Edit states (when user wants to change something from summary)
    editing_category = State()       # User re-selecting category
    editing_description = State()    # User re-typing description
    editing_attachments = State()    # User re-attaching files
    
    # For "Urgent" category only
    waiting_urgency_level = State()  # How blocking is the issue
    waiting_urgency_details = State()  # What exactly doesn't work


class TriageFlow(StatesGroup):
    """States for unknown user triage."""
    
    waiting_code = State()           # User typing invite code
    waiting_company = State()        # User typing company name
    waiting_contact = State()        # User typing contact info (optional)


class FeedbackFlow(StatesGroup):
    """States for CSAT feedback."""
    
    waiting_comment = State()        # User typing negative feedback comment
    
    # Detailed CSAT states
    rating_speed = State()           # Rating speed (1-5)
    rating_quality = State()         # Rating quality (1-5)
    rating_politeness = State()      # Rating politeness (1-5)


class OperatorFlow(StatesGroup):
    """States for operator actions."""
    
    waiting_details_question = State()  # Operator typing custom details request
    waiting_pause_reason = State()      # Operator typing pause reason
    waiting_cancel_reason = State()     # Operator typing cancellation reason
