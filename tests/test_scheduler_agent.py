import pytest
from app.services.scheduler_agent import SchedulerAgent
import asyncio

@pytest.mark.asyncio
async def test_scheduler_agent_main_flow():
    agent = SchedulerAgent()
    # Simulate a full conversation
    steps = [
        ("John Doe", "What is your date of birth?"),
        ("01/01/1990", "What is your phone number?"),
        ("5551234567", "What is the reason for your call? (Schedule appointment, Referral, Speak to a Nurse)"),
        ("I want to book an appointment", "Are you a new or existing patient?"),
        ("new", "Which provider would you like to see?"),
        ("Dr. Ahmed", "What type of insurance do you have? Medicaid or Commercial?"),
        ("Medicaid", "Please provide your Medicaid ID."),
        ("A123456789", "Thank you. Your Medicaid information has been recorded. Goodbye.")
    ]
    for user_input, expected_response in steps:
        response, _ = await agent.process_input(user_input)
        print(f"User: {user_input} | Agent: {response}")
        assert expected_response.split('?')[0].lower() in response.lower()

@pytest.mark.asyncio
async def test_scheduler_agent_fuzzy_matching():
    agent = SchedulerAgent()
    await agent.process_input("Jane Smith")
    await agent.process_input("02/02/1985")
    await agent.process_input("5559876543")
    # Loop on reason input until agent advances
    for _ in range(3):
        response, _ = await agent.process_input("I want to schedule an appointment")
        print(f"User: I want to schedule an appointment | Agent: {response}")
        if "new or existing patient" in response.lower():
            break
        assert "reason for your call" in response.lower()  # Should prompt again if not matched
    else:
        assert False, "Agent did not advance to patient type after repeated reason input"
    response, _ = await agent.process_input("new")
    print(f"User: new | Agent: {response}")
    assert "which provider would you like to see" in response.lower()
    response, _ = await agent.process_input("Dr. Ahmed")
    print(f"User: Dr. Ahmed | Agent: {response}")
    assert "what type of insurance" in response.lower()
    response, _ = await agent.process_input("Medicaid")
    print(f"User: Medicaid | Agent: {response}")
    assert "please provide your medicaid id" in response.lower()
    response, _ = await agent.process_input("A123456789")
    print(f"User: A123456789 | Agent: {response}")
    assert "thank you. your medicaid information has been recorded. goodbye." in response.lower() 