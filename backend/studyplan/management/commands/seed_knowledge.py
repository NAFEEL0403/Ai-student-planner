from django.core.management.base import BaseCommand
from studyplan.models import StudyKnowledge
from studyplan.services import EmbeddingService

class Command(BaseCommand):
    help = 'Seeds initial study knowledge for DBMS, Python, Django, and DSA with embeddings.'

    def handle(self, *args, **options):
        # Initial small dataset for database seeding
        knowledge_data = [
            # DBMS Chunks
            {
                "title": "SQL Joins and Query Optimization",
                "subject": "DBMS",
                "content": "SQL Joins combine rows from multiple tables using related columns. Types include INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL JOIN. Query optimization improves database speed by creating indexes on WHERE/JOIN columns, avoiding SELECT *, and reading EXPLAIN plans to analyze database scans."
            },
            {
                "title": "Database Normalization and Anomalies",
                "subject": "DBMS",
                "content": "Normalization structures databases to minimize redundancy and prevent insertion, update, and deletion anomalies. Forms include 1NF (atomic columns), 2NF (no partial dependencies on composite keys), 3NF (no transitive dependencies), and BCNF (stricter version of 3NF)."
            },
            {
                "title": "ACID Properties and Transactions",
                "subject": "DBMS",
                "content": "A transaction is an execution unit containing multiple database operations. Transactions must guarantee ACID properties: Atomicity (all changes commit or rollback), Consistency (preserves database rules), Isolation (concurrent executions do not interfere), and Durability (saved changes persist even in system failures)."
            },
            # Python Chunks
            {
                "title": "Python OOP Concepts",
                "subject": "Python",
                "content": "Object-Oriented Programming (OOP) uses classes and objects. Key pillars: Inheritance (derived classes inherit attributes/methods from base classes), Polymorphism (subclasses override common methods), Encapsulation (hiding data using double underscores like __private), and Abstraction (exposing interfaces while hiding details)."
            },
            {
                "title": "Python Basics and Exception Handling",
                "subject": "Python",
                "content": "Python is a dynamic, high-level language. Basic collections include lists, tuples, sets, and dictionaries. Exceptions represent runtime errors and are managed using try-except-else-finally blocks, allowing programs to recover or fail gracefully rather than crashing."
            },
            # Django Chunks
            {
                "title": "Django Models and Migrations",
                "subject": "Django",
                "content": "Django Models map Python classes to database tables. Attributes define columns and field types (e.g. CharField, IntegerField). Django Migrations record updates to models and apply them to the SQL database using 'makemigrations' and 'migrate' commands."
            },
            {
                "title": "Django REST Framework and Views",
                "subject": "Django",
                "content": "Django REST Framework (DRF) is used to build RESTful APIs. Serializers translate database instances into JSON and validate incoming payloads. Views handle HTTP requests and return standard responses, supported by SimpleJWT to secure endpoints using Bearer tokens."
            },
            # DSA Chunks
            {
                "title": "Arrays, Strings, and Two Pointer Technique",
                "subject": "DSA",
                "content": "Arrays and strings store linear sequences of elements. The Two Pointer technique optimizes index traversals by operating two references (e.g., left and right boundaries) to solve string reversal, sorting, or target-sum problems in O(N) linear time."
            },
            {
                "title": "Sliding Window and Sliding Arrays",
                "subject": "DSA",
                "content": "The Sliding Window algorithm tracks contiguous subarrays or substrings of varying or fixed sizes. By adding new elements at the leading edge and dropping old elements from the trailing edge, it converts O(N^2) brute force searches into optimal O(N) complexity."
            }
        ]

        self.stdout.write(self.style.WARNING("Starting to seed database knowledge with embeddings..."))
        
        for item in knowledge_data:
            exists = StudyKnowledge.objects.filter(subject=item["subject"], title=item["title"]).exists()
            if not exists:
                self.stdout.write(f"Generating embedding for: {item['subject']} - {item['title']}...")
                # Call embedding service locally to generate vector
                embedding = EmbeddingService.generate_embedding(item["content"])
                
                # Save chunk to Database
                StudyKnowledge.objects.create(
                    title=item["title"],
                    subject=item["subject"],
                    content=item["content"],
                    embedding=embedding
                )
                self.stdout.write(self.style.SUCCESS(f"Successfully seeded: {item['title']}"))
            else:
                self.stdout.write(self.style.NOTICE(f"Already exists: {item['title']}"))

        self.stdout.write(self.style.SUCCESS("Database seeding completed!"))
