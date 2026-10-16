# Reflection

## 1. What did static analysis reveal about the original program?

The tools found both style problems and issues that could affect behavior or security. Bandit flagged SQL built from user input, execution of promo text with `exec`, weak SHA-1 hashing, unsafe temporary receipt creation, overly permissive file permissions, and other risky patterns. Pylint and Flake8 also identified a mutable default argument, inconsistent naming, missing documentation, and formatting violations. Running the demo exposed logic errors too: a reversed rental period and a negative daily rate produced a negative charge, and rented cars remained available.

## 2. Which issue was most important to fix, and why?

The promo rule's use of `exec` was especially serious because rule text could run arbitrary Python code. SQL injection was another high priority because crafted customer names could alter a database query. I replaced dynamic SQL with parameterized queries and replaced `exec` with validation for a limited percentage multiplier format. I also changed the licence digest to SHA-256 and made receipt files uniquely created with restrictive default permissions.

## 3. What was challenging about fixing the issues?

The main challenge was preserving useful behavior while rejecting invalid input safely. Rental validation now checks that the customer exists, the car is known and available, the dates are in order, and the rate is non-negative. I also corrected the demo inputs so its sample rental is valid. After those changes, I reran all three tools and adjusted the code until the reports were clean.

## 4. How did static analysis improve the program, and what are its limits?

Static analysis gave specific, repeatable feedback and helped catch unsafe patterns before relying on the program. Pylint reports 10.00/10, Bandit reports no issues, and Flake8 reports no violations on the final code. These results do not prove every behavior is correct: running the demo was still useful for spotting the negative rental charge and checking that an SQL injection attempt no longer returned customer records. Code review and runtime checks remain useful alongside static analysis.
