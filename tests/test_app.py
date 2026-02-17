"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    yield
    # Cleanup after test
    activities.clear()


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_includes_participants(self, client):
        """Test that activities include participant emails"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_success(self, client):
        """Test successful signup for a new participant"""
        response = client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert "newstudent@mergington.edu" in activities_response.json()["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client):
        """Test that duplicate signup returns 400 error"""
        response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup to nonexistent activity returns 404"""
        response = client.post("/activities/Nonexistent Club/signup?email=newstudent@mergington.edu")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_different_participants(self, client):
        """Test that multiple different participants can sign up"""
        response1 = client.post("/activities/Programming Class/signup?email=student1@mergington.edu")
        response2 = client.post("/activities/Programming Class/signup?email=student2@mergington.edu")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both were added
        activities_response = client.get("/activities")
        participants = activities_response.json()["Programming Class"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


class TestUnregisterFromActivity:
    """Test the DELETE /activities/{activity_name}/signup endpoint"""
    
    def test_unregister_existing_participant_success(self, client):
        """Test successful unregistration of an existing participant"""
        response = client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert "michael@mergington.edu" not in activities_response.json()["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering a non-participant returns 400"""
        response = client.delete("/activities/Chess Club/signup?email=notasignup@mergington.edu")
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test that unregistering from nonexistent activity returns 404"""
        response = client.delete("/activities/Nonexistent Club/signup?email=michael@mergington.edu")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_multiple_participants(self, client):
        """Test removing multiple participants"""
        response1 = client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
        response2 = client.delete("/activities/Chess Club/signup?email=daniel@mergington.edu")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both were removed
        activities_response = client.get("/activities")
        participants = activities_response.json()["Chess Club"]["participants"]
        assert len(participants) == 0


class TestSignupAndUnregisterFlow:
    """Test combined signup and unregister flows"""
    
    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "testflow@mergington.edu"
        
        # Sign up
        signup_response = client.post(f"/activities/Programming Class/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Programming Class"]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/Programming Class/signup?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Programming Class"]["participants"]
    
    def test_signup_duplicate_after_unregister(self, client):
        """Test that a participant can re-signup after unregistering"""
        email = "testflow2@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Gym Class/signup?email={email}")
        
        # Unregister
        client.delete(f"/activities/Gym Class/signup?email={email}")
        
        # Re-signup (should succeed)
        response = client.post(f"/activities/Gym Class/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant is back
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Gym Class"]["participants"]


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
