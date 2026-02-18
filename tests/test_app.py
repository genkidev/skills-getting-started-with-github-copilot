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


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
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
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_contains_correct_structure(self, client, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_includes_participants(self, client, reset_activities):
        """Test that participants are included in activities"""
        response = client.get("/activities")
        data = response.json()
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that signing up a duplicate participant fails"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that signup increases the participant count"""
        initial_count = len(activities["Programming Class"]["participants"])
        client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert len(activities["Programming Class"]["participants"]) == initial_count + 1
    
    def test_signup_with_different_emails(self, client, reset_activities):
        """Test signing up multiple different participants"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        for email in emails:
            response = client.post(
                "/activities/Gym%20Class/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        for email in emails:
            assert email in activities["Gym Class"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_existing_participant(self, client, reset_activities):
        """Test removing an existing participant"""
        response = client.delete(
            "/activities/Chess%20Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
    
    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """Test that removing a nonexistent participant fails"""
        response = client.delete(
            "/activities/Chess%20Club/participants/notaperson@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """Test that removing from a nonexistent activity fails"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/participants/student@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_remove_decreases_participant_count(self, client, reset_activities):
        """Test that removal decreases participant count"""
        initial_count = len(activities["Chess Club"]["participants"])
        client.delete(
            "/activities/Chess%20Club/participants/michael@mergington.edu"
        )
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1
    
    def test_remove_multiple_participants(self, client, reset_activities):
        """Test removing multiple participants"""
        # Add some new participants first
        client.post("/activities/Chess%20Club/signup", params={"email": "new1@mergington.edu"})
        client.post("/activities/Chess%20Club/signup", params={"email": "new2@mergington.edu"})
        
        # Remove them
        response1 = client.delete("/activities/Chess%20Club/participants/new1@mergington.edu")
        response2 = client.delete("/activities/Chess%20Club/participants/new2@mergington.edu")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert "new1@mergington.edu" not in activities["Chess Club"]["participants"]
        assert "new2@mergington.edu" not in activities["Chess Club"]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_remove_workflow(self, client, reset_activities):
        """Test complete signup and removal workflow"""
        email = "integrationtest@mergington.edu"
        activity = "Programming Class"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Remove
        remove_response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/participants/{email}"
        )
        assert remove_response.status_code == 200
        assert email not in activities[activity]["participants"]
    
    def test_cannot_signup_twice_even_after_removal(self, client, reset_activities):
        """Test that after removal, patient can sign up again"""
        email = "testuser@mergington.edu"
        activity = "Chess Club"
        
        # Sign up
        client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        assert email in activities[activity]["participants"]
        
        # Remove
        client.delete(
            f"/activities/{activity.replace(' ', '%20')}/participants/{email}"
        )
        assert email not in activities[activity]["participants"]
        
        # Sign up again should succeed
        response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        assert email in activities[activity]["participants"]
