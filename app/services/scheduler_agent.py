"""Agent for handling the patient scheduling workflow."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

from .conversation_states import ConversationState, PatientType
from app.services.helpers import match_user_input

logger = logging.getLogger(__name__)

class SchedulerAgent:
    """Handles the patient scheduling conversation flow."""
    
    def __init__(self):
        """Initialize the SchedulerAgent."""
        self.state = {}
        self.patient_type: Optional[PatientType] = None
        self.patient_info: Dict = {
            'first_name': '',
            'last_name': '',
            'dob': '',
            'phone': '',
            'reason': '',
            'insurance_type': '',
            'medicaid_id': '',
            'commercial_insurance': '',
            'insurance_member_id': '',
            'insurance_group_number': '',
            'insurance_subscriber_name': '',
            'insurance_subscriber_relationship': '',
            'insurance_subscriber_phone': '',
            'insurance_subscriber_dob': '',
            'insurance_subscriber_sex': ''
        }
        self.available_providers: List[Dict] = [
            {"id": "1", "name": "Dr. Smith", "specialty": "Family Medicine"},
            {"id": "2", "name": "Dr. Johnson", "specialty": "Internal Medicine"},
            {"id": "3", "name": "Dr. Williams", "specialty": "Pediatrics"}
        ]
        self.available_slots: List[Dict] = []
        self.selected_provider: Optional[Dict] = None
        self.selected_slot: Optional[Dict] = None
        self.current_page = 0  # For pagination of appointment slots
    
    async def process_input(self, user_input: str) -> Tuple[str, Optional[list]]:
        state = self.state

        if "name" not in state:
            state["name"] = user_input
            return "What is your date of birth?", None

        elif "dob" not in state:
            state["dob"] = user_input
            return "What is your phone number?", None

        elif "phone" not in state:
            state["phone"] = user_input
            return "What is the reason for your call? (Schedule appointment, Referral, Speak to a Nurse)", ["Schedule appointment", "Referral", "Speak to a Nurse"]

        elif "reason" not in state:
            reason = match_user_input(user_input, ["Schedule appointment", "Referral", "Speak to a Nurse"])
            if not reason:
                return "Sorry, I didn't get that. Are you calling to schedule an appointment, for a referral, or to speak to a nurse?", None
            state["reason"] = reason

            if reason in ["Referral", "Speak to a Nurse"]:
                return f"Okay, I will transfer you now to the appropriate department for {reason.lower()}. Goodbye.", None
            else:
                return "Are you a new or existing patient?", ["New", "Existing"]

        elif "patient_type" not in state:
            patient_type = match_user_input(user_input, ["New", "Existing"])
            if not patient_type:
                return "Are you a new or existing patient?", ["New", "Existing"]
            state["patient_type"] = patient_type
            return f"Which provider would you like to see? {os.getenv('PROVIDER_1_NAME')} or {os.getenv('PROVIDER_2_NAME')}?", None

        elif "provider" not in state:
            provider = match_user_input(user_input, [
                os.getenv("PROVIDER_1_NAME", "Dr. Ahmed"),
                os.getenv("PROVIDER_2_NAME", "Sarah Eannarelli")
            ])
            if not provider:
                return "Please tell me which provider you'd like to see.", None
            state["provider"] = provider
            return "What type of insurance do you have? Medicaid or Commercial?", ["Medicaid", "Commercial"]

        elif "insurance" not in state:
            insurance_type = match_user_input(user_input, ["Medicaid", "Commercial"])
            if not insurance_type:
                return "Do you have Medicaid or Commercial insurance?", ["Medicaid", "Commercial"]
            state["insurance"] = insurance_type

            if insurance_type == "Medicaid":
                return "Please provide your Medicaid ID.", None
            else:
                return "What is your insurance member ID?", None

        elif state["insurance"] == "Medicaid" and "medicaid_id" not in state:
            state["medicaid_id"] = user_input
            return "Thank you. Your Medicaid information has been recorded. Goodbye.", None

        elif state["insurance"] == "Commercial":
            # progressive steps to collect all fields
            required_fields = [
                "member_id", "group_id", "subscriber_name", "subscriber_relationship",
                "subscriber_phone", "subscriber_dob", "subscriber_sex"
            ]
            for field in required_fields:
                if field not in state:
                    prompts = {
                        "member_id": "Please provide your insurance member ID.",
                        "group_id": "What is your group number?",
                        "subscriber_name": "What is the subscriber's full name?",
                        "subscriber_relationship": "What is your relationship to the subscriber?",
                        "subscriber_phone": "What is the subscriber's phone number?",
                        "subscriber_dob": "What is the subscriber's date of birth?",
                        "subscriber_sex": "What is the subscriber's sex?"
                    }
                    state[field] = user_input
                    next_index = required_fields.index(field) + 1
                    if next_index < len(required_fields):
                        next_field = required_fields[next_index]
                        return prompts[next_field], None
                    else:
                        return "Thank you. Your insurance details have been recorded. Goodbye.", None

        return "Thank you. Your information has been saved. Goodbye.", None
