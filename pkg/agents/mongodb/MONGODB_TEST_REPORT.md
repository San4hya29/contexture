\# MongoDB Agentic Copilot Test Report



\## Application

E-commerce Dataset



\## OCS Schema



\### customers

Fields:

\- customer\_id

\- name

\- email

\- city



\### products

Fields:

\- product\_id

\- name

\- category

\- price

\- stock



\### orders

Fields:

\- order\_id

\- customer\_id

\- product\_id

\- quantity

\- order\_date



\## Relationships



customers → orders → products



\## Test Cases



\### Test 1: MongoDB Connection

PASS



\### Test 2: Collections Loaded

PASS



\### Test 3: Relationship Query



Query:

What products did Rahul buy?



Output:

Rahul bought Laptop, Mouse



PASS



\### Test 4: Generic Query using Ollama



Query:

What is MongoDB?



PASS



\## Conclusion



OCS schema verified successfully.

Relationship traversal and context-aware query execution are working correctly.

