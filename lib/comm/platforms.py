from comm import slack
from comm import email

# Platform adapter classes by name
platform_class = {
    'slack': slack.Slack,
    'email': email.Email,
}

# Platform names by adapter class
platform_name = {v: k for k, v in platform_class.items()}
