#!/usr/bin/env python3
"""
Bootstrap utility for VAmPI

This script populates the database with a healthy amount of sample data
for testing and demonstration purposes.

Usage:
    python tools/bootstrap.py [--users N] [--books-per-user N]
"""

import sys
import os
import argparse
from random import randrange, choice, sample

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import db, vuln_app
from models.user_model import User
from models.books_model import Book


# Sample data for generating realistic content
FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
    "Iris", "Jack", "Kate", "Liam", "Maya", "Noah", "Olivia", "Peter",
    "Quinn", "Rachel", "Sam", "Tara", "Uma", "Victor", "Wendy", "Xavier",
    "Yara", "Zach", "Aria", "Blake", "Chloe", "Derek"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark"
]

BOOK_GENRES = [
    "Mystery", "SciFi", "Fantasy", "Romance", "Thriller", "Horror",
    "Historical", "Biography", "Technical", "Poetry", "Drama", "Comedy"
]

BOOK_TOPICS = [
    "Dragons", "Space", "Magic", "Detective", "Love", "War", "Time Travel",
    "Artificial Intelligence", "Ancient Civilizations", "Vampires", "Zombies",
    "Robots", "Pirates", "Ninjas", "Superheroes", "Mythology", "Ocean",
    "Mountain", "Desert", "Forest", "Castle", "Laboratory", "City", "Village"
]

SECRET_PREFIXES = [
    "The hidden truth about", "The secret behind", "What nobody knows about",
    "The mystery of", "The untold story of", "The real meaning of",
    "The classified information regarding", "The confidential details about"
]


def generate_username(first_name, last_name, existing_usernames):
    """Generate a unique username"""
    base_username = f"{first_name.lower()}.{last_name.lower()}"
    username = base_username
    counter = 1

    while username in existing_usernames:
        username = f"{base_username}{counter}"
        counter += 1

    return username


def generate_email(username, domain=None):
    """Generate an email address"""
    domains = ["example.com", "test.com", "demo.com", "sample.org", "vampi.io"]
    domain = domain or choice(domains)
    return f"{username}@{domain}"


def generate_book_title(genre, topic):
    """Generate a book title"""
    templates = [
        f"The {genre} of {topic}",
        f"{topic}: A {genre} Story",
        f"The {topic} {genre}",
        f"{genre} in {topic}",
        f"Tales of {topic}",
        f"The Last {topic}",
        f"Journey to {topic}",
        f"Chronicles of {topic}",
        f"The {topic} Conspiracy",
        f"Secrets of {topic}"
    ]
    return choice(templates)


def generate_secret(book_title):
    """Generate a secret for a book"""
    prefix = choice(SECRET_PREFIXES)
    suffixes = [
        "the main character's true identity",
        "the ending nobody expected",
        "the author's real inspiration",
        "the hidden chapter that was removed",
        "the alternate ending",
        "the sequel that never happened",
        "the real-life events it's based on",
        "the controversial plot twist"
    ]
    return f"{prefix} '{book_title}': {choice(suffixes)}"


def bootstrap_database(num_users=20, books_per_user=5):
    """
    Bootstrap the database with sample data

    Args:
        num_users: Number of users to create (default: 20)
        books_per_user: Number of books per user (default: 5)
    """
    print("=" * 70)
    print("VAmPI Database Bootstrap")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  - Users to create: {num_users}")
    print(f"  - Books per user: {books_per_user}")
    print(f"  - Total books: ~{num_users * books_per_user}")
    print("\n" + "-" * 70)

    # Run within Flask application context
    with vuln_app.app.app_context():
        # Drop and recreate all tables
        print("\n[1/3] Resetting database...")
        db.drop_all()
        db.create_all()
        print("      Database tables created successfully")

        # Create default admin and test users
        print("\n[2/3] Creating default users...")
        default_users = [
            ("admin", "pass1", "admin@mail.com", True),
            ("name1", "pass1", "mail1@mail.com", False),
            ("name2", "pass2", "mail2@mail.com", False),
        ]

        existing_usernames = set()

        for username, password, email, is_admin in default_users:
            user = User(username=username, password=password, email=email, admin=is_admin)
            db.session.add(user)
            existing_usernames.add(username)
            role = "admin" if is_admin else "user"
            print(f"      Created {role}: {username}")

        db.session.commit()
        print(f"      {len(default_users)} default users created")

        # Create additional users with books
        print("\n[3/3] Creating sample users and books...")
        users_created = 0
        books_created = 0

        # Track all used book titles globally (must be unique across all users)
        all_used_titles = set()

        # Shuffle names for variety
        first_names = sample(FIRST_NAMES, min(num_users, len(FIRST_NAMES)))
        last_names = sample(LAST_NAMES, min(num_users, len(LAST_NAMES)))

        for i in range(num_users):
            first_name = first_names[i % len(first_names)]
            last_name = last_names[i % len(last_names)]

            username = generate_username(first_name, last_name, existing_usernames)
            existing_usernames.add(username)

            password = f"pass{randrange(1000, 9999)}"
            email = generate_email(username)

            # Occasionally create an admin user (10% chance)
            is_admin = randrange(100) < 10

            user = User(username=username, password=password, email=email, admin=is_admin)
            db.session.add(user)
            users_created += 1

            # Create books for this user
            user_books = []

            for _ in range(books_per_user):
                # Generate unique book title (globally unique, not just per user)
                attempts = 0
                while attempts < 100:  # Increased attempts for global uniqueness
                    genre = choice(BOOK_GENRES)
                    topic = choice(BOOK_TOPICS)
                    title = generate_book_title(genre, topic)

                    if title not in all_used_titles:
                        all_used_titles.add(title)
                        break
                    attempts += 1
                else:
                    # Fallback with counter to ensure uniqueness
                    title = f"Book {randrange(10000, 99999)}-{i}-{books_created}"

                secret = generate_secret(title)
                book = Book(book_title=title, secret_content=secret, user_id=None)
                user_books.append(book)
                books_created += 1

            user.books = user_books

            # Progress indicator
            if (i + 1) % 5 == 0 or (i + 1) == num_users:
                print(f"      Progress: {i + 1}/{num_users} users created...")

        # Commit all changes
        db.session.commit()

        # Summary
        print("\n" + "=" * 70)
        print("Bootstrap Complete!")
        print("=" * 70)
        print(f"\nDatabase Summary:")
        print(f"  - Total users created: {users_created + len(default_users)}")
        print(f"    - Default users: {len(default_users)}")
        print(f"    - Sample users: {users_created}")
        print(f"  - Total books created: {books_created}")
        print(f"\nDefault credentials:")
        print(f"  - Admin: admin / pass1")
        print(f"  - User1: name1 / pass1")
        print(f"  - User2: name2 / pass2")
        print("\nThe database is now ready for use!")
        print("=" * 70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Bootstrap VAmPI database with sample data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/bootstrap.py                    # Use defaults (20 users, 5 books each)
  python tools/bootstrap.py --users 50         # Create 50 users
  python tools/bootstrap.py --books-per-user 10  # 10 books per user
  python tools/bootstrap.py --users 100 --books-per-user 3
        """
    )

    parser.add_argument(
        '--users',
        type=int,
        default=20,
        help='Number of users to create (default: 20)'
    )

    parser.add_argument(
        '--books-per-user',
        type=int,
        default=5,
        help='Number of books per user (default: 5)'
    )

    args = parser.parse_args()

    # Validation
    if args.users < 1:
        print("Error: --users must be at least 1")
        sys.exit(1)

    if args.books_per_user < 1:
        print("Error: --books-per-user must be at least 1")
        sys.exit(1)

    if args.users > 1000:
        print("Warning: Creating more than 1000 users may take a while...")

    try:
        bootstrap_database(args.users, args.books_per_user)
    except Exception as e:
        print(f"\n[ERROR] Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
