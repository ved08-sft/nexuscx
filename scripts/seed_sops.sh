#!/bin/bash
echo "Seeding SOP files..."

# Create synthetic SOP files for testing
mkdir -p data/sops

# Create a simple flight refund SOP
cat > data/sops/flight_refund_sop.docx << 'EOF'
If an airline cancels a flight, the customer is entitled to a full refund to the original payment method within 7 working days.
For flight disruptions, offer rebooking on the next available flight at no extra charge.
EOF

# Create a simple eKYC checklist
cat > data/sops/ekyc_checklist.pdf << 'EOF'
Verify that the PAN card name exactly matches the name on the Aadhaar document before approving eKYC.
Check that the address on the PAN card matches the address on the Aadhaar document.
Ensure that the date of birth on both documents matches.
EOF

# Create a simple billing disputes SOP
cat > data/sops/billing_disputes.docx << 'EOF'
For a disputed charge, raise a billing dispute ticket and freeze late fees for 14 days.
Investigate the disputed charge within 5 working days.
Provide a resolution to the customer within 10 working days.
EOF

# Create a simple shipment tracking SOP
cat > data/sops/shipment_tracking.pdf << 'EOF'
Provide tracking information to the customer within 24 hours of shipment.
Update tracking status every 24 hours until delivery.
Notify customer of any delays immediately.
EOF

echo "SOP files seeded successfully."