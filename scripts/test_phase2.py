#!/usr/bin/env python3
"""
Test script for Phase 2 implementation.
Tests RAG pipeline and WEKA integration.
"""

import sys
import os
# Add the backend directory to the path so we can find the app and ml modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', 'backend')
sys.path.insert(0, backend_dir)
# Also add the parent of backend so we can find ml as a top-level module
parent_of_backend = os.path.dirname(backend_dir)
sys.path.insert(0, parent_of_backend)

def test_rag_store():
    """Test the RAG store implementation."""
    print("Testing RAG store...")

    try:
        from app.rag.store import SopStore, search_sops, upsert_sop_chunks

        # Create a store instance
        store = SopStore(persist_directory="/tmp/test_chroma")

        # Test upserting chunks
        test_chunks = [
            {
                "id": "test_1",
                "text": "If an airline cancels a flight, the customer is entitled to a full refund within 7 working days.",
                "source": "test_sop.docx",
                "page": 1,
                "vertical": "flight",
                "sop_version": "v1",
                "section_title": "Flight Refund Policy"
            },
            {
                "id": "test_2",
                "text": "Verify that the PAN card name exactly matches the name on the Aadhaar document before approving eKYC.",
                "source": "test_sop.pdf",
                "page": 2,
                "vertical": "ekyc",
                "sop_version": "v1",
                "section_title": "eKYC Verification"
            }
        ]

        count = upsert_sop_chunks(test_chunks)
        print(f"Upserted {count} chunks")

        # Test search
        results, confidence = search_sops("refund for cancelled flight", vertical="flight")
        print(f"Search returned {len(results)} results with confidence {confidence}")

        if len(results) > 0:
            print(f"First result: {results[0].text[:50]}...")
            print(f"Source: {results[0].source}, Page: {results[0].page}")
            print(f"Score: {results[0].score}")

        # Test low confidence search
        results2, confidence2 = search_sops("best recipe for chocolate cake", vertical="flight")
        print(f"Low confidence search returned {len(results2)} results with confidence {confidence2}")

        # Clean up
        store.clear()

        print("RAG store test: PASSED")
        return True

    except Exception as e:
        print(f"RAG store test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_calculation():
    """Test the risk calculation engine."""
    print("\nTesting risk calculation...")

    try:
        from app.ml.risk import calculate_risk_score, get_risk_band, is_critical_risk

        # Test basic risk calculation
        risk_score = calculate_risk_score(
            weka_probability=0.8,
            sentiment_score=-0.6,
            hold_count=2.0
        )
        print(f"Risk score: {risk_score}")

        # Test risk bands
        assert get_risk_band(0.3) == "low"
        assert get_risk_band(0.6) == "medium"
        assert get_risk_band(0.8) == "high"
        assert get_risk_band(0.9) == "critical"
        print("Risk bands: PASSED")

        # Test critical risk detection
        assert is_critical_risk(0.9) == True
        assert is_critical_risk(0.8) == False
        print("Critical risk detection: PASSED")

        # Test edge cases
        # For (0.0, 0.0, 0.0):
        # P_weka=0.0, sentiment=0.0 -> S_neg=(1-0)/2=0.5, hold_count=0.0 -> T_hold=0
        # Risk = 0.55*0.0 + 0.30*0.5 + 0.15*0.0 = 0.15
        assert abs(calculate_risk_score(0.0, 0.0, 0.0) - 0.15) < 0.001

        # For (1.0, 1.0, 10.0):
        # P_weka=1.0, sentiment=1.0 -> S_neg=(1-1)/2=0.0, hold_count=10.0 -> T_hold=min(10/3,1)=1.0
        # Risk = 0.55*1.0 + 0.30*0.0 + 0.15*1.0 = 0.55 + 0.0 + 0.15 = 0.70
        assert abs(calculate_risk_score(1.0, 1.0, 10.0) - 0.70) < 0.001

        print("Edge cases: PASSED")

        print("Risk calculation test: PASSED")
        return True

    except Exception as e:
        print(f"Risk calculation test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_synthetic_data_generation():
    """Test synthetic data generation."""
    print("\nTesting synthetic data generation...")

    try:
        # Test that we can import the module
        from ml.synth_data import generate_synthetic_data
        print("Synthetic data module imported successfully")

        # Actually generating data would take time and space, so we'll just test import
        print("Synthetic data generation test: PASSED (import only)")
        return True

    except Exception as e:
        print(f"Synthetic data generation test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Phase 2 tests."""
    print("=== Phase 2 Implementation Tests ===")

    tests = [
        test_rag_store,
        test_risk_calculation,
        test_synthetic_data_generation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("All Phase 2 tests PASSED!")
        return 0
    else:
        print("Some Phase 2 tests FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())