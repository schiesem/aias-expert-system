# Testing the Annotation API

This guide explains how to test the annotation mechanism backend.

## Prerequisites

1. **Python environment activated**:
   ```bash
   cd backend
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Dependencies installed**:
   ```bash
   pip install requests  # If not already installed
   ```

3. **Flask server running**:
   ```bash
   python server.py
   ```

   You should see:
   ```
   * Running on http://localhost:5000
   ```

## Running the Test Script

### Basic Test Run

In a **new terminal** (keep the server running):

```bash
cd backend
python test_annotation_api.py
```

### Expected Output

You should see colored output with test results:

```
╔════════════════════════════════════════════════════════════════════╗
║          ANNOTATION API TEST SUITE                                ║
╚════════════════════════════════════════════════════════════════════╝

======================================================================
TEST 1: Health Check
======================================================================

ℹ GET http://localhost:5000/api/annotations/health
  Status: 200
  Response: {
    "success": true,
    "message": "Annotation service is running",
    "manager_initialized": true
  }
✓ Health check passed

[... more tests ...]

======================================================================
TEST SUMMARY
======================================================================

Results:
  [PASS] Health Check
  [PASS] Get Relations Level 1
  [PASS] Get Relations Multi-Level
  [PASS] Create Test Element
  [PASS] Create Annotation
  [PASS] Get Annotations
  [PASS] Get Annotation Count
  [PASS] Delete Annotation
  [PASS] Verify Deletion

✓ ALL TESTS PASSED (9/9)
```

## Test Coverage

The test script covers:

1. **Health Check** - Verify annotation service is running
2. **Relation Discovery (Level 1)** - Get direct relations for a class
3. **Relation Discovery (Multi-Level)** - Get relations up to level 2
4. **Annotation Creation** - Create a new annotation instance
5. **Annotation Retrieval** - Get all annotations for an element
6. **Annotation Count** - Get count of annotations
7. **Annotation Deletion** - Delete an annotation
8. **Deletion Verification** - Verify annotation was removed

## Manual Testing with cURL

### 1. Health Check

```bash
curl http://localhost:5000/api/annotations/health
```

### 2. Get Relations for Training Class

```bash
curl "http://localhost:5000/api/annotations/relations/Training?level=1"
```

### 3. Create Annotation

First, create a test element via the frontend, then:

```bash
curl -X POST http://localhost:5000/api/annotations/TestTraining1 \
  -H "Content-Type: application/json" \
  -d '{
    "relation_property": "isExecutedBy",
    "target_class": "Model",
    "instance_data": {
      "name": "TestModel",
      "properties": {
        "version": "1.0"
      }
    }
  }'
```

### 4. Get Annotations

```bash
curl "http://localhost:5000/api/annotations/TestTraining1?max_depth=2"
```

### 5. Get Annotation Count

```bash
curl http://localhost:5000/api/annotations/TestTraining1/count
```

### 6. Delete Annotation

```bash
curl -X DELETE http://localhost:5000/api/annotations/TestTraining1/isExecutedBy/TestModel
```

## Troubleshooting

### Test Fails: "Connection refused"

**Problem**: Flask server is not running

**Solution**:
```bash
cd backend
python server.py
```

### Test Fails: "Element not found"

**Problem**: Test element doesn't exist in ontology

**Solution**:
1. Open the frontend: `http://localhost:5173`
2. Create a Function node with ID: `TestTraining1`
3. Set its class to: `Training`
4. Save the model
5. Run tests again

### Test Fails: "Class not found"

**Problem**: Ontology not loaded properly

**Solution**:
1. Check that `backend/expert_system/ontologies/AIAS.owl` exists
2. Check that ODPs are in `backend/expert_system/ontologies/ODP/`
3. Restart Flask server
4. Check server console for ontology loading errors

### Test Passes but Annotation Not Visible

**Problem**: Frontend not refreshing

**Solution**:
1. Refresh the frontend page
2. Double-click the element to open annotation window
3. Click "Refresh" in annotation window

## Next Steps

After all tests pass:

1. **Test via Frontend** - Use the actual annotation UI (Phase 1.2)
2. **Integration Testing** - Test complete workflow end-to-end
3. **Performance Testing** - Test with many annotations
4. **Edge Cases** - Test error handling, invalid inputs, etc.

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/annotations/health` | Health check |
| GET | `/api/annotations/relations/<class>` | Get relations |
| GET | `/api/annotations/<element_id>` | Get annotations |
| POST | `/api/annotations/<element_id>` | Create annotation |
| DELETE | `/api/annotations/<element_id>/<prop>/<instance>` | Delete annotation |
| GET | `/api/annotations/<element_id>/count` | Get count |

## Debugging

To see detailed logs:

1. Check Flask server console output
2. Look for `✅`, `❌`, `⚠️` emoji indicators
3. Enable Flask debug mode (already enabled in `server.py`)

For more details, see [Prio1.md](../Prio1.md) for the full implementation plan.
