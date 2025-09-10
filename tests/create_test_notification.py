#!/usr/bin/env python3
"""
Create a test notification then start chat
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.approval_callback import callback_service

# Create a test approval notification
approval_id = 'test-456'
callback_service.register_approval_request(approval_id, {
    "type": "leave_request",
    "employee_name": "Test User",
    "leave_start_date": "2025-11-20",
    "leave_end_date": "2025-11-22"
})

# Trigger approved notification
callback_service.handle_approval_response(
    approval_id=approval_id,
    status='APPROVED',
    selected_option='Approve',
    message='Approved by manager - enjoy your vacation!'
)

print("✅ Test notification created!")
print("Now start the chat to see if notification appears...")
print("Run: python src/interactive_chat.py")
