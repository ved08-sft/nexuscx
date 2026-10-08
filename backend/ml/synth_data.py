#!/usr/bin/env python3
"""
Generate synthetic ARFF datasets for WEKA model training.
"""

import argparse
import csv
import random
from typing import List, Tuple
import numpy as np


def generate_synthetic_data(rows: int = 20000, seed: int = 42,
                           output_file: str = "data.csv") -> None:
    """
    Generate synthetic BPO call center data for WEKA training.

    Columns: handle_time_sec, sentiment_score, past_ticket_freq_30d,
             hold_count, transfer_count, vertical, escalated
    """
    random.seed(seed)
    np.random.seed(seed)

    # Define possible values
    verticals = ["billing", "technical", "flight", "ekyc", "shipment", "hr"]

    # Generate data
    data = []

    for i in range(rows):
        # Handle time: normally distributed around 300 seconds (5 minutes)
        # but clipped to reasonable range
        handle_time = max(60, min(1800, np.random.normal(300, 100)))

        # Sentiment score: -1 to 1, with bias toward negative for escalated cases
        # We'll determine escalation first, then generate sentiment accordingly
        will_escalate = random.random() < 0.3  # 30% base escalation rate

        if will_escalate:
            sentiment = np.random.uniform(-0.8, -0.2)  # More negative for escalated
        else:
            sentiment = np.random.uniform(-0.2, 0.6)   # More positive/neutral for non-escalated

        # Past ticket frequency: Poisson distribution
        past_tickets = np.random.poisson(3)

        # Hold count: typically 0-3 for most calls
        hold_count = min(5, np.random.poisson(1.5))

        # Transfer count: usually 0-2
        transfer_count = min(3, np.random.poisson(0.8))

        # Vertical: weighted distribution
        vertical = random.choice(verticals)

        # Adjust escalation probability based on factors
        escalation_prob = 0.1  # Base probability

        # Increase probability based on risk factors
        if handle_time > 600:  # Long calls more likely to escalate
            escalation_prob += 0.2
        if sentiment < -0.5:  # Very negative sentiment
            escalation_prob += 0.3
        if past_tickets > 5:  # Many recent tickets
            escalation_prob += 0.15
        if hold_count > 3:  # Long hold times
            escalation_prob += 0.1
        if transfer_count > 2:  # Many transfers
            escalation_prob += 0.15

        # Vertical-specific adjustments
        if vertical == "flight":
            escalation_prob += 0.1  # Flights often have time-sensitive issues
        elif vertical == "technical":
            escalation_prob += 0.05

        # Cap probability
        escalation_prob = min(0.95, escalation_prob)

        # Determine final escalation outcome
        escalated = random.random() < escalation_prob

        # If we determined escalation based on probability, adjust sentiment
        # to be more consistent
        if escalated and sentiment > -0.3:
            sentiment = random.uniform(-0.8, -0.3)
        elif not escalated and sentiment < -0.1:
            sentiment = random.uniform(-0.1, 0.5)

        data.append([
            round(handle_time, 1),
            round(sentiment, 3),
            past_tickets,
            hold_count,
            transfer_count,
            vertical,
            "yes" if escalated else "no"
        ])

    # Write to CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow([
            'handle_time_sec', 'sentiment_score', 'past_ticket_freq_30d',
            'hold_count', 'transfer_count', 'vertical', 'escalated'
        ])
        # Write data rows
        writer.writerows(data)

    print(f"Generated {rows} rows of synthetic data in {output_file}")

    # Print some statistics
    escalated_count = sum(1 for row in data if row[6] == "yes")
    print(f"Escalated cases: {escalated_count} ({escalated_count/rows*100:.1f}%)")

    avg_handle_time = sum(row[0] for row in data) / len(data)
    print(f"Average handle time: {avg_handle_time:.1f} seconds")

    avg_sentiment = sum(row[1] for row in data) / len(data)
    print(f"Average sentiment: {avg_sentiment:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic data for WEKA")
    parser.add_argument("--rows", type=int, default=20000,
                       help="Number of rows to generate (default: 20000)")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed (default: 42)")
    parser.add_argument("--output", type=str, default="data.csv",
                       help="Output CSV file (default: data.csv)")

    args = parser.parse_args()

    generate_synthetic_data(rows=args.rows, seed=args.seed, output_file=args.output)