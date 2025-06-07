"""Agent for handling the patient scheduling workflow."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

from app.services.helpers import match_user_input, llm_match_user_input

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
        logger.info(f"Current state: {state}")
        logger.info(f"User input: {user_input}")

        # Define all expected options for each step
        reason_options = ["Schedule appointment", "Referral", "Speak to a Nurse"]
        patient_type_options = ["New", "Existing"]
        insurance_options = ["Medicaid", "Commercial"]
        provider_options = [
            os.getenv("PROVIDER_1_NAME", "Dr. Ahmed"),
            os.getenv("PROVIDER_2_NAME", "Sarah Eannarelli")
        ]

        # Flexible: If user input matches a later intent, jump to that state
        # 1. Reason for call
        reason = llm_match_user_input(user_input, reason_options) or match_user_input(user_input, reason_options)
        if reason and "reason" not in state:
            state["reason"] = reason
            if reason in ["Referral", "Speak to a Nurse"]:
                logger.info(f"Final state: {state}")
                logger.info(f"Agent response: Okay, I will transfer you now to the appropriate department for {reason.lower()}. Goodbye.")
                return f"Okay, I will transfer you now to the appropriate department for {reason.lower()}. Goodbye.", None
            else:
                return "Are you a new or existing patient?", patient_type_options

        # 2. Patient type
        patient_type = llm_match_user_input(user_input, patient_type_options) or match_user_input(user_input, patient_type_options)
        if patient_type and "patient_type" not in state and "reason" in state:
            state["patient_type"] = patient_type
            return f"Which provider would you like to see? {provider_options[0]} or {provider_options[1]}?", None

        # 3. Provider
        provider = llm_match_user_input(user_input, provider_options) or match_user_input(user_input, provider_options)
        if provider and "provider" not in state and "patient_type" in state:
            state["provider"] = provider
            return "What type of insurance do you have? Medicaid or Commercial?", insurance_options

        # 4. Insurance type
        insurance_type = llm_match_user_input(user_input, insurance_options) or match_user_input(user_input, insurance_options)
        if insurance_type and "insurance" not in state and "provider" in state:
            state["insurance"] = insurance_type
            if insurance_type == "Medicaid":
                return "Please provide your Medicaid ID.", None
            else:
                return "What is your insurance member ID?", None

        # 5. Medicaid ID
        if "insurance" in state and state["insurance"] == "Medicaid" and "medicaid_id" not in state and user_input.strip():
            state["medicaid_id"] = user_input.strip()
            logger.info(f"Final state: {state}")
            logger.info("Agent response: Thank you. Your Medicaid information has been recorded. Goodbye.")
            return "Thank you. Your Medicaid information has been recorded. Goodbye.", None

        # 6. Commercial insurance fields
        if "insurance" in state and state["insurance"] == "Commercial":
            required_fields = [
                "member_id", "group_id", "subscriber_name", "subscriber_relationship",
                "subscriber_phone", "subscriber_dob", "subscriber_sex"
            ]
            prompts = {
                "member_id": "Please provide your insurance member ID.",
                "group_id": "What is your group number?",
                "subscriber_name": "What is the subscriber's full name?",
                "subscriber_relationship": "What is your relationship to the subscriber?",
                "subscriber_phone": "What is the subscriber's phone number?",
                "subscriber_dob": "What is the subscriber's date of birth?",
                "subscriber_sex": "What is the subscriber's sex?"
            }
            for field in required_fields:
                if field not in state:
                    state[field] = user_input.strip()
                    next_index = required_fields.index(field) + 1
                    if next_index < len(required_fields):
                        next_field = required_fields[next_index]
                        return prompts[next_field], None
                    else:
                        logger.info(f"Final state: {state}")
                        logger.info("Agent response: Thank you. Your insurance details have been recorded. Goodbye.")
                        return "Thank you. Your insurance details have been recorded. Goodbye.", None

        # 7. Name
        if "name" not in state:
            state["name"] = user_input
            return "What is your date of birth?", None

        # 8. DOB
        elif "dob" not in state:
            state["dob"] = user_input
            return "What is your phone number?", None

        # 9. Phone
        elif "phone" not in state:
            state["phone"] = user_input
            return "What is the reason for your call? (Schedule appointment, Referral, Speak to a Nurse)", reason_options

        # At the end, check for missing required fields and prompt for the next one
        required_fields = ["name", "dob", "phone", "reason", "patient_type", "provider", "insurance"]
        for field in required_fields:
            if field not in state:
                prompts = {
                    "name": "What is your name?",
                    "dob": "What is your date of birth?",
                    "phone": "What is your phone number?",
                    "reason": "What is the reason for your call? (Schedule appointment, Referral, Speak to a Nurse)",
                    "patient_type": "Are you a new or existing patient?",
                    "provider": f"Which provider would you like to see? {provider_options[0]} or {provider_options[1]}?",
                    "insurance": "What type of insurance do you have? Medicaid or Commercial?"
                }
                return prompts[field], None

        logger.info(f"Final state: {state}")
        logger.info("Agent response: Thank you. Your information has been saved. Goodbye.")
        return "Thank you. Your information has been saved. Goodbye.", None
