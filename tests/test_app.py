"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create a test client
client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_list(self):
        """Test that /activities returns a list of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

    def test_get_activities_contains_chess_club(self):
        """Test that activities list contains Chess Club"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data
        assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"

    def test_activity_has_required_fields(self):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self):
        """Test signing up a new participant for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Fake Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_already_registered(self):
        """Test that signing up twice fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_adds_participant_to_list(self):
        """Test that participant is actually added to the activity"""
        email = "verify@mergington.edu"
        activity_name = "Programming Class"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity_name]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify count increased
        response = client.get("/activities")
        new_count = len(response.json()[activity_name]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()[activity_name]["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_participant(self):
        """Test unregistering a participant from an activity"""
        # First sign up
        email = "unregister@mergington.edu"
        activity_name = "Drama Club"
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/Fake Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_not_registered(self):
        """Test unregistering someone who is not registered"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_removes_participant(self):
        """Test that participant is actually removed from the activity"""
        email = "remove@mergington.edu"
        activity_name = "Art Workshop"
        
        # Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Verify signed up
        response = client.get("/activities")
        assert email in response.json()[activity_name]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity_name}/unregister?email={email}")
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()[activity_name]["participants"]
