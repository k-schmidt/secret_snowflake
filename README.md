# Secret Snowflake

A Python-based Secret Santa gift exchange manager that automatically generates random matches while respecting constraints, and sends personalized email notifications to participants.

## Features

- Random matching algorithm with intelligent backtracking for deadlock resolution
- Constraint support (prevent specific pairings, family members, previous year matches)
- Automatic email notifications via Gmail SMTP
- CSV-based participant management
- Comprehensive validation and error handling
- Reproducible matching with optional random seed
- Detailed logging to file and console

## Requirements

- Python 3.7+
- pandas
- python-dotenv

## Installation

1. Clone the repository:
```bash
git clone https://github.com/k-schmidt/secret_snowflake.git
cd secret_snowflake
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install pandas python-dotenv
```

## Setup

### 1. Configure Environment Variables

Create a `.env` file in the project root with your Gmail credentials and participant emails:

```env
# Gmail Configuration (see Gmail Setup section below)
GMAIL_EMAIL=your.email@gmail.com
GMAIL_PW=your_app_password_here

# Optional: Random seed for reproducible matching
RANDOM_SEED=42

# Participant Emails
EMAIL_MOM=mom@example.com
EMAIL_DAD=dad@example.com
EMAIL_KYLE=kyle@example.com
EMAIL_JOYCE=joyce@example.com
EMAIL_MADISON=madison@example.com
EMAIL_JULIAN=julian@example.com
# ... add more participants as needed
```

### 2. Gmail Setup (IMPORTANT)

Gmail requires App Passwords for SMTP access:

1. **Enable 2-Step Verification** on your Google account:
   - Go to https://myaccount.google.com/security
   - Turn on "2-Step Verification"

2. **Generate an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" for app, "Other" for device
   - Name it (e.g., "Secret Snowflake")
   - Copy the 16-character password

3. **Update `.env`**:
   - Use the app password (without spaces) as `GMAIL_PW`
   - Use your full Gmail address as `GMAIL_EMAIL`

### 3. Prepare Participant Data

Create a CSV file at `data/schmidt+_2025.csv` with the following columns:

```csv
timestamp,email_address,name,mailing_address,gift_ideas
2025-11-25,kyle@example.com,Kyle Schmidt,123 Main St,Books and tech gadgets
2025-11-25,joyce@example.com,Joyce,456 Oak Ave,Art supplies
...
```

Required columns:
- `timestamp`: Date of entry
- `email_address`: Participant's email
- `name`: Participant's display name
- `mailing_address`: Full mailing address
- `gift_ideas`: Gift preferences and ideas

### 4. Configure Matching Constraints

Edit `configs/config.py` to set up the `NO_MATCH_LIST`:

```python
NO_MATCH_LIST = [
    # Family constraints (prevent family members from matching)
    (EMAIL_MOM, EMAIL_DAD),
    (EMAIL_DAD, EMAIL_MOM),
    (EMAIL_KYLE, EMAIL_JOYCE),
    (EMAIL_JOYCE, EMAIL_KYLE),

    # Previous year matches (prevent repeats)
    (EMAIL_MOM, EMAIL_KYLE),
    (EMAIL_JULIAN, EMAIL_JOYCE),

    # Any other custom constraints...
]
```

## Usage

Run the matching and email sending:

```bash
python main.py
```

The program will:
1. Load and validate participant data from CSV
2. Generate matches respecting all constraints
3. Send personalized emails to each giver with their match details
4. Log all activity to `secret_snowflake.log`

### Output

Console output shows match generation and email sending progress:
```
2025-11-25 10:30:00 - INFO - Starting Secret Snowflake matching process
2025-11-25 10:30:00 - INFO - Loaded 10 participants
2025-11-25 10:30:00 - INFO - Data validation passed
2025-11-25 10:30:00 - INFO - Generating matches...
Kyle Schmidt Julian
Joyce Madison Carbajales
...
2025-11-25 10:30:01 - INFO - Successfully generated 10 matches
2025-11-25 10:30:05 - INFO - ✓ Email sent to Kyle Schmidt (kyle@example.com)
...
```

## Code Style

This project follows Python best practices:

- **Imports**: Grouped by standard library → third-party → local
- **Type Annotations**: Full type hints using typing module
- **Naming**: snake_case for variables/functions, UPPER_CASE for constants
- **Indentation**: 4 spaces
- **Line Length**: Maximum 100 characters
- **Docstrings**: Required for all functions with parameter descriptions

### Code Quality Tools

```bash
# Lint code
pylint main.py configs/

# Type checking
mypy main.py configs/

# Sort imports
isort main.py configs/
```

## How It Works

### Matching Algorithm

The `gen_matches()` function implements a constraint-satisfaction algorithm with backtracking:

1. **Constraint Tracking**: Uses two sets to ensure:
   - Each person gives to exactly one other person (`already_gave`)
   - Each person receives from exactly one other person (`already_matched`)

2. **Random Selection**: For each giver, randomly selects from available valid recipients

3. **Deadlock Recovery**: If no valid matches remain, reshuffles participants and retries (up to 100 attempts)

4. **Validation**: Ensures exactly N matches are generated for N participants

### Email Notifications

Each giver receives an HTML email containing:
- Recipient's name
- Recipient's email address
- Recipient's mailing address
- Recipient's gift ideas

## Troubleshooting

### SMTP Authentication Error (535)

**Problem**: "Username and Password not accepted"

**Solution**: You need to use a Gmail App Password (not your regular password). See the [Gmail Setup](#2-gmail-setup-important) section.

### Match Generation Fails

**Problem**: "Could not generate valid matches after 100 attempts"

**Solution**: Your `NO_MATCH_LIST` constraints may be too restrictive. Review the constraints to ensure a valid matching is possible.

### Missing Participant Data

**Problem**: "Missing required column" or "Invalid email address"

**Solution**: Ensure your CSV has all required columns and valid email formats.

## Project Structure

```
secret_snowflake/
├── main.py                    # Main application logic
├── configs/
│   └── config.py             # Configuration and constraints
├── data/
│   └── schmidt+_2025.csv     # Participant data (gitignored)
├── .env                      # Environment variables (gitignored)
├── secret_snowflake.log      # Application logs (gitignored)
├── CLAUDE.md                 # Project coding guidelines
└── README.md                 # This file
```

## Contributing

When contributing to this project:

1. Follow the code style guidelines in [CLAUDE.md](CLAUDE.md)
2. Ensure all functions have type hints and docstrings
3. Run linting and type checking before committing
4. Keep functions pure with clear input/output when possible

## License

MIT License

## Author

Kyle Schmidt
- GitHub: [@k-schmidt](https://github.com/k-schmidt)
