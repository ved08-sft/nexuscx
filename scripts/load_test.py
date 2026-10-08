#!/usr/bin/env python3
"""
Load testing script for NexusCX.
Simulates multiple concurrent sessions to test system performance.
"""

import asyncio
import aiohttp
import time
import json
from typing import List

async def simulate_session(session_id: str, session_num: int):
    """Simulate a single user session."""
    async with aiohttp.ClientSession() as session:
        # Login to get token
        login_data = {
            "username": f"agent{session_num}",
            "password": "agent1-pass"
        }

        try:
            async with session.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data
            ) as resp:
                if resp.status != 200:
                    print(f"Session {session_num}: Login failed")
                    return

                login_result = await resp.json()
                token = login_result.get("access_token")

                if not token:
                    print(f"Session {session_num}: No token received")
                    return
        except Exception as e:
            print(f"Session {session_num}: Login error - {e}")
            return

        # Set headers for authenticated requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Ingest a ticket to start a session
        ticket_data = {
            "source_type": "ticket",
            "ticket_id": f"TKT-2026-{session_num:06d}",
            "customer_id": f"CUST-{1000 + session_num}",
            "channel": "voice",
            "raw_text": "Meri flight cancel ho gayi, refund kab milega?",
            "language": "hinglish",
            "received_at": "2026-10-05T10:15:00+05:30",
            "metadata": {
                "vertical": "flight",
                "hold_count": 1,
                "transfer_count": 0,
                "prior_tickets_30d": 3
            }
        }

        try:
            async with session.post(
                "http://localhost:8000/api/v1/tickets/ingest",
                headers=headers,
                json=ticket_data
            ) as resp:
                if resp.status not in [200, 202]:
                    print(f"Session {session_num}: Ticket ingest failed - {resp.status}")
                    return

                result = await resp.json()
                print(f"Session {session_num}: Session started - {result.get('session_id')}")
        except Exception as e:
            print(f"Session {session_num}: Ticket ingest error - {e}")
            return

        # Wait a bit to simulate processing
        await asyncio.sleep(2)

async def main():
    """Run load test with multiple concurrent sessions."""
    num_sessions = 50  # As specified in the requirements

    print(f"Starting load test with {num_sessions} concurrent sessions...")
    start_time = time.time()

    # Create tasks for all sessions
    tasks = [
        simulate_session(f"sess-{i}", i)
        for i in range(num_sessions)
    ]

    # Run all sessions concurrently
    await asyncio.gather(*tasks, return_exceptions=True)

    end_time = time.time()
    duration = end_time - start_time

    print(f"Load test completed in {duration:.2f} seconds")
    print(f"Average session time: {duration/num_sessions:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())