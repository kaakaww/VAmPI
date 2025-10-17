"""
Test Broken Object Level Authorization (BOLA) Vulnerability (API1:2023)

This test demonstrates BOLA vulnerability in the GET /books/v1/{book_title} endpoint.
When vuln=1, any authenticated user can access any book by title, regardless of ownership.
Users should only be able to access their own books, but the vulnerable code fails to check ownership.

OWASP Reference: https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/

Vulnerability Location: api_views/books.py:50-60
"""

import pytest
import requests
import uuid


def test_bola_access_other_user_book(api_base_url: str, user1_token: str, user2_token: str):
    """
    Test BOLA by accessing another user's book.

    This test demonstrates that user1 can access user2's book by simply knowing
    the book title, without any ownership verification.

    Steps:
        1. User2 creates a book with a unique title
        2. User1 attempts to access that book using only the title
        3. When vulnerable, user1 can see user2's book and secret

    Expected behavior when vuln=1:
        - User1 can access user2's book
        - Returns 200 with book data including secret

    Expected behavior when vuln=0:
        - User1 cannot access user2's book
        - Returns 404 (book not found) because ownership check prevents access
    """
    # Step 1: User2 creates a book with a unique title
    unique_title = f"Secret Diary {uuid.uuid4().hex[:8]}"
    user2_secret = "This is user2's private secret that user1 should not see!"

    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    create_response = requests.post(
        f"{api_base_url}/books/v1",
        headers=user2_headers,
        json={
            "book_title": unique_title,
            "secret": user2_secret
        }
    )

    assert create_response.status_code == 200, \
        f"Failed to create book for user2. Expected 200, got {create_response.status_code}"

    # Step 2: User1 attempts to access user2's book by title
    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    access_response = requests.get(
        f"{api_base_url}/books/v1/{unique_title}",
        headers=user1_headers
    )

    # When vulnerable (BOLA), this should succeed with 200
    # When secure, this should fail with 404
    assert access_response.status_code == 200, \
        f"BOLA vulnerability appears patched. User1 cannot access user2's book. " \
        f"Expected 200, got {access_response.status_code}"

    # Verify we actually got user2's secret data
    book_data = access_response.json()
    assert book_data.get("book_title") == unique_title, \
        "Book title mismatch"
    assert book_data.get("secret") == user2_secret, \
        "Did not receive user2's secret content - BOLA may be partially patched"
    assert book_data.get("owner") == "name2", \
        f"Expected owner to be 'name2', got {book_data.get('owner')}"


def test_bola_enumerate_books_by_title(api_base_url: str, user1_token: str, user2_token: str):
    """
    Test BOLA by enumerating books from other users using real book titles.

    This test first queries user2's books, then tries to access them as user1,
    demonstrating the BOLA vulnerability.

    Expected behavior when vuln=1:
        - User1 can access books that don't belong to them if they know the title
        - Returns 200 with book data

    Expected behavior when vuln=0:
        - Returns 404 for books not owned by user1
    """
    # First, get user2's books to know what titles exist
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    user2_books_response = requests.get(
        f"{api_base_url}/books/v1",
        headers=user2_headers
    )

    assert user2_books_response.status_code == 200, \
        "Failed to get user2's books for test setup"

    user2_books = user2_books_response.json().get("Books", [])

    # Filter to only books owned by user2
    user2_owned_books = [b for b in user2_books if b.get("user") == "name2"]

    assert len(user2_owned_books) > 0, \
        "User2 has no books - test data issue"

    # Now try to access user2's books as user1
    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    books_accessed = []

    for book in user2_owned_books[:3]:  # Try first 3 books
        title = book.get("book_title")
        response = requests.get(
            f"{api_base_url}/books/v1/{title}",
            headers=user1_headers
        )

        if response.status_code == 200:
            book_data = response.json()
            owner = book_data.get("owner")

            # If we accessed user2's book, that's BOLA
            if owner == "name2":
                books_accessed.append({
                    "title": title,
                    "owner": owner,
                    "secret": book_data.get("secret")
                })

    # When vulnerable, we should be able to access user2's books
    assert len(books_accessed) > 0, \
        f"BOLA vulnerability could not be demonstrated. " \
        f"Attempted to access {len(user2_owned_books)} of user2's books but none were accessible."


def test_bola_access_own_book_still_works(api_base_url: str, user1_token: str):
    """
    Control test: Verify that users can still access their own books.

    This ensures that the endpoint works correctly for legitimate access
    (users accessing their own books).

    Expected behavior (both vuln=1 and vuln=0):
        - User can access their own books
        - Returns 200 with book data
    """
    # User1 creates a book
    unique_title = f"My Own Book {uuid.uuid4().hex[:8]}"
    my_secret = "This is my own secret"

    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    create_response = requests.post(
        f"{api_base_url}/books/v1",
        headers=user1_headers,
        json={
            "book_title": unique_title,
            "secret": my_secret
        }
    )

    assert create_response.status_code == 200, "Failed to create own book"

    # Access own book
    access_response = requests.get(
        f"{api_base_url}/books/v1/{unique_title}",
        headers=user1_headers
    )

    assert access_response.status_code == 200, \
        "User cannot access their own book - API may be broken"

    book_data = access_response.json()
    assert book_data.get("secret") == my_secret, "Secret content mismatch"
    assert book_data.get("owner") == "name1", "Owner should be name1"


def test_bola_cannot_access_without_authentication(api_base_url: str, user2_token: str):
    """
    Control test: Verify that unauthenticated requests are rejected.

    This ensures that some authentication is required, even if authorization
    is broken (BOLA).

    Expected behavior (both vuln=1 and vuln=0):
        - Requests without auth token should fail with 401
    """
    # User2 creates a book
    unique_title = f"Auth Test Book {uuid.uuid4().hex[:8]}"

    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    create_response = requests.post(
        f"{api_base_url}/books/v1",
        headers=user2_headers,
        json={
            "book_title": unique_title,
            "secret": "test secret"
        }
    )

    assert create_response.status_code == 200, "Failed to create book"

    # Try to access without authentication
    no_auth_response = requests.get(
        f"{api_base_url}/books/v1/{unique_title}"
        # No Authorization header
    )

    # Should fail with 401 regardless of BOLA vulnerability
    assert no_auth_response.status_code == 401, \
        f"Unauthenticated access should fail. Expected 401, got {no_auth_response.status_code}"


def test_bola_nonexistent_book_returns_404(api_base_url: str, user1_token: str):
    """
    Control test: Verify that accessing non-existent books returns 404.

    This establishes baseline behavior for books that don't exist in the system.

    Expected behavior (both vuln=1 and vuln=0):
        - Returns 404 for books that don't exist
    """
    nonexistent_title = f"This Book Does Not Exist {uuid.uuid4().hex[:8]}"

    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    response = requests.get(
        f"{api_base_url}/books/v1/{nonexistent_title}",
        headers=user1_headers
    )

    assert response.status_code == 404, \
        f"Non-existent book should return 404. Got {response.status_code}"


def test_bola_admin_can_access_any_book(api_base_url: str, admin_token: str, user1_token: str):
    """
    Test that admin users have legitimate access to all books.

    This is a control test to verify that admin access is intentional and not
    considered BOLA. The BOLA vulnerability is specifically about regular users
    accessing other users' resources.

    Expected behavior (both vuln=1 and vuln=0):
        - Admin users should be able to access books (this is by design)
        - Regular users should not be able to access others' books (when vuln=0)
    """
    # User1 creates a book
    unique_title = f"Admin Access Test {uuid.uuid4().hex[:8]}"
    user1_secret = "User1's secret"

    user1_headers = {"Authorization": f"Bearer {user1_token}"}
    create_response = requests.post(
        f"{api_base_url}/books/v1",
        headers=user1_headers,
        json={
            "book_title": unique_title,
            "secret": user1_secret
        }
    )

    assert create_response.status_code == 200, "Failed to create book"

    # Admin attempts to access user1's book
    # Note: The current vulnerable code doesn't actually check for admin vs regular user
    # It just checks authentication and then (when vuln=1) returns any book by title
    # This test documents the current behavior
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_response = requests.get(
        f"{api_base_url}/books/v1/{unique_title}",
        headers=admin_headers
    )

    # When vuln=1, admin can access (but so can everyone else)
    # This test just verifies admin access works
    assert admin_response.status_code == 200, \
        "Admin should be able to access books"

    book_data = admin_response.json()
    assert book_data.get("secret") == user1_secret, \
        "Admin did not receive correct book data"
