INSTALLATION

To install this web application:

1. Ensure you have a working Django environment by following the instructions on the Django homepage.
2. Ensure your Django version matches up with the one listed in requirements.txt.
3. Open a terminal (Linux/OS X) or command prompt (Windows) in the project directory that contains manage.py.
4. Execute the command "python manage.py syncdb", and when prompted to create a super user, type "no"
5. Execute the command "python manage.py runserver" to bring up the server in development mode.
6. Open a web browser.
7. Navigate to "localhost:8000" (8000 is the default port, it may be different depending on your individual configuration).

REGISTRATION

A user can register using a name, a zipcode, an email, and a password.

LOGGING IN

In order to log in, a user provides the email and password they registered with.

Emails and passwords are case sensitive in all cases.

Initial Fixure (for Testing) Emails and Passwords:
Email               Password
admin@venture.com   pass
test@venture.com    pass

DISCLAIMERS

Known Bugs:
- (Django session middleware contrib tests fail on Windows; this is a known Django bug)

Known Non-compliances:
- You can return a tool before your reservation is over, but the tool stays reserved for the entire reservation period
- Individual tools do not have preferred sharing methods

Known Missing Release Two Features:
- Email Notifications
    - We were told to not worry about them, so we did not
- Return Reminders
    - These require emails and a timed events server to properly work
- Mobile site
    - Not fully implemented because we were told not to emphasize it
