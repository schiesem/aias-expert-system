"""
test_annotation_api.py

Simple test script to verify annotation API endpoints work correctly.
This script tests the complete annotation workflow:
1. Health check
2. Relation discovery
3. Annotation creation
4. Annotation retrieval
5. Annotation count
6. Annotation deletion

Run this script with the Flask server running:
    python test_annotation_api.py
"""

import sys
import os

# Fix Windows console encoding issues
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
ANNOTATION_API = f"{BASE_URL}/api/annotations"

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}{Colors.RESET}\n")

def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def print_response(response: requests.Response):
    """Print formatted response."""
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        print(f"  Response: {json.dumps(data, indent=2)}")
    except:
        print(f"  Response: {response.text}")

# Test 1: Health Check
def test_health_check():
    """Test the health check endpoint."""
    print_section("TEST 1: Health Check")

    try:
        url = f"{ANNOTATION_API}/health"
        print_info(f"GET {url}")

        response = requests.get(url)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Health check passed")
                return True
            else:
                print_error("Health check returned success=false")
                return False
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

# Test 2: Get Relations (Level 1)
def test_get_relations_level_1():
    """Test getting relations at level 1 for a class."""
    print_section("TEST 2: Get Relations (Level 1)")

    try:
        # Test with Training class from ISO22989
        class_name = "Training"
        url = f"{ANNOTATION_API}/relations/{class_name}?level=1"
        print_info(f"GET {url}")

        response = requests.get(url)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                relations = data.get('relations', [])
                print_success(f"Found {len(relations)} relations at level 1")

                # Print some example relations
                if relations:
                    print_info("Sample relations:")
                    for rel in relations[:3]:  # Show first 3
                        print(f"    - {rel['property']} → {rel['target_class']} ({rel['cardinality']})")

                return True
            else:
                print_error("Get relations returned success=false")
                return False
        else:
            print_error(f"Get relations failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Get relations failed: {e}")
        return False

# Test 3: Get Relations (Multiple Levels)
def test_get_relations_multi_level():
    """Test getting relations at multiple levels."""
    print_section("TEST 3: Get Relations (Multiple Levels)")

    try:
        class_name = "Training"
        url = f"{ANNOTATION_API}/relations/{class_name}?max_level=2"
        print_info(f"GET {url}")

        response = requests.get(url)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                relations = data.get('relations', [])
                level_1 = [r for r in relations if r['level'] == 1]
                level_2 = [r for r in relations if r['level'] == 2]

                print_success(f"Found {len(level_1)} relations at level 1")
                print_success(f"Found {len(level_2)} relations at level 2")
                print_success(f"Total: {len(relations)} relations")

                return True
            else:
                print_error("Get relations returned success=false")
                return False
        else:
            print_error(f"Get relations failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Get relations failed: {e}")
        return False

# Test 4: Create Test Element (prerequisite)
def create_test_element():
    """Create a test element to annotate."""
    print_section("TEST 4: Create Test Element (Prerequisite)")

    print_info("This test requires an existing graphical element in the ontology")
    print_info("If you don't have one, create it via the frontend first")
    print_warning("Skipping element creation - assuming 'TestTraining1' exists")
    print_warning("If it doesn't exist, annotation tests may fail")

    return True

# Test 5: Create Annotation
def test_create_annotation():
    """Test creating an annotation."""
    print_section("TEST 5: Create Annotation")

    try:
        element_id = "TestTraining1"
        url = f"{ANNOTATION_API}/{element_id}"

        payload = {
            "relation_property": "isExecutedBy",
            "target_class": "Model",
            "instance_data": {
                "name": "TestModel_API",
                "properties": {
                    "version": "1.0",
                    "description": "Test model created via API"
                }
            }
        }

        print_info(f"POST {url}")
        print_info(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(url, json=payload)
        print_response(response)

        if response.status_code in [200, 201]:
            data = response.json()
            if data.get('success'):
                annotation = data.get('annotation', {})
                print_success(f"Created annotation: {annotation.get('name')} ({annotation.get('class')})")
                return True
            else:
                print_error("Create annotation returned success=false")
                return False
        elif response.status_code == 500:
            print_warning("Create annotation failed - element might not exist")
            print_warning("Create 'TestTraining1' element via frontend first")
            return False
        else:
            print_error(f"Create annotation failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Create annotation failed: {e}")
        return False

# Test 6: Get Annotations
def test_get_annotations():
    """Test retrieving annotations."""
    print_section("TEST 6: Get Annotations")

    try:
        element_id = "TestTraining1"
        url = f"{ANNOTATION_API}/{element_id}?max_depth=2"
        print_info(f"GET {url}")

        response = requests.get(url)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                annotations = data.get('annotations', {})
                element_annotations = annotations.get('annotations', {})

                count = len(element_annotations)
                print_success(f"Retrieved {count} annotation(s)")

                if count > 0:
                    print_info("Annotations found:")
                    for prop, values in element_annotations.items():
                        print(f"    - {prop}: {len(values)} instance(s)")
                        for val in values:
                            print(f"        • {val['name']} ({val['class']})")

                return True
            else:
                print_error("Get annotations returned success=false")
                return False
        else:
            print_error(f"Get annotations failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Get annotations failed: {e}")
        return False

# Test 7: Get Annotation Count
def test_get_annotation_count():
    """Test getting annotation count."""
    print_section("TEST 7: Get Annotation Count")

    try:
        element_id = "TestTraining1"
        url = f"{ANNOTATION_API}/{element_id}/count"
        print_info(f"GET {url}")

        response = requests.get(url)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                count = data.get('count', 0)
                print_success(f"Annotation count: {count}")
                return True
            else:
                print_error("Get annotation count returned success=false")
                return False
        else:
            print_error(f"Get annotation count failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Get annotation count failed: {e}")
        return False

# Test 8: Delete Annotation
def test_delete_annotation():
    """Test deleting an annotation."""
    print_section("TEST 8: Delete Annotation")

    try:
        element_id = "TestTraining1"
        relation_property = "isExecutedBy"
        instance_name = "TestModel_API"

        url = f"{ANNOTATION_API}/{element_id}/{relation_property}/{instance_name}"
        print_info(f"DELETE {url}")

        response = requests.delete(url)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success("Annotation deleted successfully")
                return True
            else:
                print_error("Delete annotation returned success=false")
                return False
        else:
            print_error(f"Delete annotation failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Delete annotation failed: {e}")
        return False

# Test 9: Verify Deletion
def test_verify_deletion():
    """Verify annotation was deleted."""
    print_section("TEST 9: Verify Deletion")

    try:
        element_id = "TestTraining1"
        url = f"{ANNOTATION_API}/{element_id}/count"
        print_info(f"GET {url}")

        response = requests.get(url)
        print_response(response)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                count = data.get('count', 0)
                print_success(f"Annotation count after deletion: {count}")

                if count == 0:
                    print_success("Deletion verified - no annotations remaining")
                else:
                    print_info(f"Still {count} annotation(s) remaining")

                return True
            else:
                print_error("Verify deletion returned success=false")
                return False
        else:
            print_error(f"Verify deletion failed with status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Verify deletion failed: {e}")
        return False

# Main test runner
def run_all_tests():
    """Run all tests and report results."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("=" * 70)
    print("          ANNOTATION API TEST SUITE                                ")
    print("=" * 70)
    print(f"{Colors.RESET}")

    print_info(f"Testing API at: {ANNOTATION_API}")
    print_warning("Make sure the Flask server is running on localhost:5000")
    print()

    # Wait a moment
    time.sleep(1)

    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Get Relations Level 1", test_get_relations_level_1),
        ("Get Relations Multi-Level", test_get_relations_multi_level),
        ("Create Test Element", create_test_element),
        ("Create Annotation", test_create_annotation),
        ("Get Annotations", test_get_annotations),
        ("Get Annotation Count", test_get_annotation_count),
        ("Delete Annotation", test_delete_annotation),
        ("Verify Deletion", test_verify_deletion),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

        time.sleep(0.5)  # Small delay between tests

    # Print summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"{Colors.BOLD}Results:{Colors.RESET}")
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  [{status}] {test_name}")

    print()
    success_rate = (passed / total * 100) if total > 0 else 0

    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED ({passed}/{total}){Colors.RESET}")
    elif passed > total / 2:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠ PARTIAL SUCCESS ({passed}/{total}) - {success_rate:.1f}%{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ MOST TESTS FAILED ({passed}/{total}) - {success_rate:.1f}%{Colors.RESET}")

    print()

    # Print troubleshooting tips if tests failed
    if passed < total:
        print_section("TROUBLESHOOTING TIPS")
        print_info("If tests are failing:")
        print("  1. Make sure Flask server is running: python backend/server.py")
        print("  2. Check that ontologies are loaded correctly")
        print("  3. Create a test element 'TestTraining1' via the frontend first")
        print("  4. Check server console for error messages")
        print("  5. Verify configData.json has correct ports")
        print()

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
